import argparse
import threading
import time
import sys
from gui import LANCryptorApp
import transfer


def run_gui():
    app = LANCryptorApp()
    app.mainloop()


def run_cli_send(ip, file):
    def progress(p):
        print(f"[SEND] Progress: {p:.2f}%")

    def status(msg):
        print(f"[SEND] {msg}")

    transfer.send_file(ip, file, progress_callback=progress, status_callback=status)


def run_cli_receive():
    def progress(p):
        print(f"[RECV] Progress: {p:.2f}%")

    def status(msg):
        print(f"[RECV] {msg}")

    stop_event = threading.Event()
    t = threading.Thread(
        target=transfer.receiver_thread,
        args=(status, progress, stop_event),
        kwargs={"cli": True},
        daemon=True,
    )
    t.start()

    try:
        print("[RECV] Press Ctrl+C to stop...")
        while t.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
        print("[RECV] Stopping receiver...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LANCryptor - LAN File Transfer Tool")
    subparsers = parser.add_subparsers(dest="mode", help="Modes")

    subparsers.add_parser("gui", help="Launch graphical interface")

    send_parser = subparsers.add_parser("send", help="Send a file over the network")
    send_parser.add_argument("--ip", required=True, help="IP address of receiver")
    send_parser.add_argument("--file", required=True, help="File path to send")

    subparsers.add_parser("receive", help="Receive files over the network")

    args = parser.parse_args()

    if len(sys.argv) == 1 or args.mode == "gui":
        run_gui()
    elif args.mode == "send":
        run_cli_send(args.ip, args.file)
    elif args.mode == "receive":
        run_cli_receive()
