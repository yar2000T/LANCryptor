import os
import socket
import struct
import secrets
import zipfile
import io
import logging
import threading
import queue
from cryptography.hazmat.primitives import serialization, hashes, padding
from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Configuration
PORT = 5001
BUFFER_SIZE = 65536
AES_KEY_SIZE = 32
KEY_FILE_PRIVATE = "private_key.pem"
KEY_FILE_PUBLIC = "public_key.pem"
RECEIVED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Received")

# Confirmation inter-thread communication for receiver UI
confirmation_queue = queue.Queue()
confirmation_event = threading.Event()
confirmation_result = None  # True/False from UI

def recv_exact(sock, n):
    data = b""
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            raise ConnectionError("Socket connection lost during recv_exact")
        data += packet
    return data

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
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        with open(KEY_FILE_PUBLIC, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

def load_private_key():
    with open(KEY_FILE_PRIVATE, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def load_public_key():
    with open(KEY_FILE_PUBLIC, "rb") as f:
        return serialization.load_pem_public_key(f.read())

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

def decompress_file(zip_data):
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
        zip_file.extractall(RECEIVED_DIR)

def confirm_receiver(pubkey_hash: str) -> bool:
    """Called in receiver thread, blocks until UI thread sets the result."""
    global confirmation_result
    confirmation_queue.put(pubkey_hash)
    confirmation_event.wait()
    confirmation_event.clear()
    return confirmation_result

def set_confirmation_result(result: bool):
    global confirmation_result
    confirmation_result = result
    confirmation_event.set()

def send_file(ip, filepath, progress_callback=None, status_callback=None):
    try:
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File '{filepath}' does not exist.")

        generate_keys()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((ip, PORT))

            s.sendall(b"REQ_PUBLIC_KEY")

            # Receive length-prefixed public key of receiver
            receiver_pubkey_len_bytes = recv_exact(s, 4)
            receiver_pubkey_len = struct.unpack("I", receiver_pubkey_len_bytes)[0]
            pub_key_data = recv_exact(s, receiver_pubkey_len)
            receiver_pubkey = serialization.load_pem_public_key(pub_key_data)

            # Compute receiver's public key hash
            digest = hashes.Hash(hashes.SHA256())
            digest.update(pub_key_data)
            receiver_pubkey_hash = digest.finalize().hex()

            if status_callback:
                status_callback(f"Receiver public key hash:\n{receiver_pubkey_hash}\nWaiting for receiver confirmation...")

            # Wait for confirmation byte from receiver
            confirmation_byte = s.recv(1)
            if confirmation_byte != b'\x01':
                if status_callback:
                    status_callback("Receiver rejected the connection.")
                s.close()
                return

            # Optionally, sender UI can show this hash for sender user awareness
            # Here you could add a prompt or auto-continue

            aes_key = secrets.token_bytes(AES_KEY_SIZE)
            iv = secrets.token_bytes(16)
            encrypted_key = encrypt_aes_key(aes_key + iv, receiver_pubkey)

            s.sendall(struct.pack("I", len(encrypted_key)))
            s.sendall(encrypted_key)

            filename = os.path.basename(filepath)
            s.sendall(filename.encode().ljust(256, b'\x00'))

            compressed_data = compress_file(filepath)

            digest = hashes.Hash(hashes.SHA256())
            digest.update(compressed_data)
            file_hash = digest.finalize()
            s.sendall(file_hash)
            logging.info(f"Sent file hash: {file_hash.hex()}")

            cipher = create_cipher(aes_key, iv)
            encryptor = cipher.encryptor()

            sent = 0
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(compressed_data) + padder.finalize()

            s.sendall(struct.pack("Q", len(padded_data)))

            with io.BytesIO(padded_data) as f:
                while chunk := f.read(BUFFER_SIZE):
                    encrypted = encryptor.update(chunk)
                    s.sendall(encrypted)
                    sent += len(chunk)
                    if progress_callback:
                        progress_callback(sent / len(padded_data) * 100)
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
        conn.settimeout(60)
        if conn.recv(1024) != b"REQ_PUBLIC_KEY":
            conn.close()
            return

        # Send receiver's public key with length prefix
        with open(KEY_FILE_PUBLIC, "rb") as f:
            receiver_pubkey_data = f.read()
        conn.sendall(struct.pack("I", len(receiver_pubkey_data)))
        conn.sendall(receiver_pubkey_data)

        # Calculate receiver's public key hash for confirmation
        digest = hashes.Hash(hashes.SHA256())
        digest.update(receiver_pubkey_data)
        receiver_pubkey_hash = digest.finalize().hex()

        if status_callback:
            status_callback(f"Connection from {addr[0]} - Confirm receiver key:\n{receiver_pubkey_hash}")

        # Ask UI to confirm receiver public key hash
        confirmed = confirm_receiver(receiver_pubkey_hash)
        if not confirmed:
            if status_callback:
                status_callback("Connection rejected by user.")
            conn.sendall(b'\x00')
            conn.close()
            return

        # Send approval to sender
        conn.sendall(b'\x01')

        enc_key_len = struct.unpack("I", recv_exact(conn, 4))[0]
        enc_key = recv_exact(conn, enc_key_len)
        aes_key_iv = decrypt_aes_key(enc_key, load_private_key())
        aes_key, iv = aes_key_iv[:AES_KEY_SIZE], aes_key_iv[AES_KEY_SIZE:]

        filename = recv_exact(conn, 256).rstrip(b'\x00').decode()

        expected_hash = recv_exact(conn, 32)

        filesize = struct.unpack("Q", recv_exact(conn, 8))[0]

        os.makedirs(RECEIVED_DIR, exist_ok=True)

        cipher = create_cipher(aes_key, iv)
        decryptor = cipher.decryptor()

        written = 0
        zip_data = io.BytesIO()
        while written < filesize:
            chunk = conn.recv(min(BUFFER_SIZE, filesize - written))
            if not chunk:
                raise ConnectionError("Connection lost during file receive")
            written += len(chunk)
            decrypted = decryptor.update(chunk)
            zip_data.write(decrypted)
            if progress_callback:
                progress_callback(written / filesize * 100)
        final = decryptor.finalize()
        zip_data.write(final)

        padded = zip_data.getvalue()
        unpadder = padding.PKCS7(128).unpadder()
        unpadded_data = unpadder.update(padded) + unpadder.finalize()

        # Verify hash
        digest = hashes.Hash(hashes.SHA256())
        digest.update(unpadded_data)
        actual_hash = digest.finalize()

        logging.info(f"Expected hash: {expected_hash.hex()}")
        logging.info(f"Actual hash:   {actual_hash.hex()}")

        if actual_hash != expected_hash:
            logging.error("File integrity check failed!")
            if status_callback:
                status_callback("File integrity check failed!")
            conn.close()
            return

        decompress_file(unpadded_data)
        if status_callback:
            status_callback(f"File received: {filename} ✅")
    except Exception as e:
        logging.error(f"Error handling client: {e}")
        if status_callback:
            status_callback(f"Error: {e}")
    finally:
        conn.close()

def receiver_thread(status_callback=None, progress_callback=None):
    generate_keys()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", PORT))
    s.listen()
    if status_callback:
        status_callback("Listening for incoming files...")
    try:
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr, status_callback, progress_callback), daemon=True).start()
    except Exception as e:
        logging.error(f"Receiver thread error: {e}")
    finally:
        s.close()
