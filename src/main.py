import argparse
import threading
import time
import sys
from gui import LANCryptorApp
import transfer
import platform


def log_platform_info():
    global system, release, arch, friendly_arch, python_version, distro_str
    arch_map = {
        "AMD64": "x64",
        "x86": "x86",
        "ARM64": "ARM64",
    }

    system = platform.system()
    release = platform.release()
    arch = platform.architecture()[0]
    machine = platform.machine()
    friendly_arch = arch_map.get(machine, machine)
    python_version = sys.version.split()[0]

    if system == "Linux":
        try:
            import distro
            distro_info = distro.linux_distribution(full_distribution_name=True)
            distro_str = f"{distro_info[0]} {distro_info[1]}"
        except ImportError:
            distro_str = "Unknown Linux (install `distro` for details)"
    elif system == "Darwin":
        distro_str = "macOS " + ".".join(platform.mac_ver()[0].split(".")[:2])
    else:
        distro_str = system


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
    log_platform_info()
    print(f"[Platform] OS: {system} {release} ({distro_str}) | Arch: {arch}| Python: {python_version}")
    tray_thread = threading.Thread(target=transfer.start_tray_icon, daemon=True)
    tray_thread.start()

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
