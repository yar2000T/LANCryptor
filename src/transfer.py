import os
import socket
import struct
import secrets
import zipfile
import io
import logging
import threading
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Configuration
PORT = 5001
BUFFER_SIZE = 65536
AES_KEY_SIZE = 32
KEY_FILE_PRIVATE = "private_key.pem"
KEY_FILE_PUBLIC = "public_key.pem"
RECEIVED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Received")


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def generate_keys():
    if not os.path.exists(KEY_FILE_PRIVATE):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        priv_dir = os.path.dirname(KEY_FILE_PRIVATE)
        if priv_dir:
            os.makedirs(priv_dir, exist_ok=True)

        with open(KEY_FILE_PRIVATE, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        with open(KEY_FILE_PUBLIC, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))


def load_private_key():
    try:
        with open(KEY_FILE_PRIVATE, "rb") as f:
            return serialization.load_pem_private_key(f.read(), password=None)
    except Exception as e:
        logging.error(f"Error loading private key: {e}")
        raise


def load_public_key():
    try:
        with open(KEY_FILE_PUBLIC, "rb") as f:
            return serialization.load_pem_public_key(f.read())
    except Exception as e:
        logging.error(f"Error loading public key: {e}")
        raise


def encrypt_aes_key(aes_key, public_key):
    return public_key.encrypt(
        aes_key,
        asymmetric_padding.OAEP(
            mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )


def decrypt_aes_key(enc_key, private_key):
    return private_key.decrypt(
        enc_key,
        asymmetric_padding.OAEP(
            mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )


def create_cipher(key, iv):
    return Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())


def compress_file(filepath):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.write(filepath, os.path.basename(filepath))
    return zip_buffer.getvalue()


def decompress_file(zip_data, filename):
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
        zip_file.extractall(RECEIVED_DIR)


def send_file(ip, filepath, progress_callback=None, status_callback=None):
    try:
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File '{filepath}' does not exist.")

        generate_keys()

        filesize = os.path.getsize(filepath)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, PORT))
            s.sendall(b"REQ_PUBLIC_KEY")
            pub_key_data = s.recv(8192)
            receiver_pubkey = serialization.load_pem_public_key(pub_key_data)

            aes_key = secrets.token_bytes(AES_KEY_SIZE)
            iv = secrets.token_bytes(16)
            encrypted_key = encrypt_aes_key(aes_key + iv, receiver_pubkey)

            s.sendall(struct.pack("I", len(encrypted_key)))
            s.sendall(encrypted_key)

            filename = os.path.basename(filepath)
            s.sendall(filename.encode().ljust(256, b'\x00'))

            compressed_data = compress_file(filepath)
            s.sendall(struct.pack("Q", len(compressed_data)))

            cipher = create_cipher(aes_key, iv)
            encryptor = cipher.encryptor()

            sent = 0
            with io.BytesIO(compressed_data) as f:
                while chunk := f.read(BUFFER_SIZE):
                    encrypted = encryptor.update(chunk)
                    s.sendall(encrypted)
                    sent += len(chunk)
                    if progress_callback:
                        progress_callback(sent / len(compressed_data) * 100)
                final = encryptor.finalize()
                s.sendall(final)
                if progress_callback:
                    progress_callback(100)
        if status_callback:
            status_callback("File sent successfully ✅")
    except Exception as e:
        logging.error(f"Error sending file: {e}")
        if status_callback:
            status_callback(f"Error: {e}")


def handle_client(conn, addr, status_callback=None, progress_callback=None):
    try:
        if conn.recv(1024) != b"REQ_PUBLIC_KEY":
            return
        with open(KEY_FILE_PUBLIC, "rb") as f:
            conn.sendall(f.read())

        enc_key_len = struct.unpack("I", conn.recv(4))[0]
        enc_key = conn.recv(enc_key_len)
        aes_key_iv = decrypt_aes_key(enc_key, load_private_key())
        aes_key, iv = aes_key_iv[:AES_KEY_SIZE], aes_key_iv[AES_KEY_SIZE:]

        filename = conn.recv(256).rstrip(b'\x00').decode()
        filesize = struct.unpack("Q", conn.recv(8))[0]

        os.makedirs(RECEIVED_DIR, exist_ok=True)

        cipher = create_cipher(aes_key, iv)
        decryptor = cipher.decryptor()

        written = 0
        zip_data = io.BytesIO()
        while written < filesize:
            chunk = conn.recv(BUFFER_SIZE)
            written += len(chunk)
            decrypted = decryptor.update(chunk)
            zip_data.write(decrypted)
            if progress_callback:
                progress_callback(written / filesize * 100)
        final = decryptor.finalize()
        zip_data.write(final)

        decompress_file(zip_data.getvalue(), filename)
        if status_callback:
            status_callback(f"File received: {filename}")
    except Exception as e:
        logging.error(f"Error handling client: {e}")
        if status_callback:
            status_callback(f"Error: {e}")
    finally:
        conn.close()


def receiver_thread(status_callback=None, progress_callback=None):
    generate_keys()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", PORT))
    s.listen()
    if status_callback:
        status_callback("Listening for incoming files...")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr, status_callback, progress_callback), daemon=True).start()
