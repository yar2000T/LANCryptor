import customtkinter as ctk
from tkinter import filedialog, messagebox
import logging
import threading
from settings import SettingsDialog
from history import FileTransferHistory
from utils import load_language
from transfer import send_file, receiver_thread

class LANCryptorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LANCryptor")
        self.geometry("600x400")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("dark-blue")

        self.language = load_language('en')  # Default language
        self.history = FileTransferHistory()

        self.init_ui()

    def init_ui(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(expand=True, fill="both", padx=10, pady=10)

        self.send_tab = self.tabview.add(self.language["send_tab"])
        self.receive_tab = self.tabview.add(self.language["receive_tab"])
        self.history_tab = self.tabview.add(self.language["history_tab"])

        self.init_send_tab()
        self.init_receive_tab()
        self.init_history_tab()

        self.menu_bar = ctk.CTkFrame(self)
        self.menu_bar.pack(fill="x", padx=10, pady=5)

        self.theme_button = ctk.CTkButton(self.menu_bar, text=self.language["toggle_theme"], command=self.toggle_theme)
        self.theme_button.pack(side="left", padx=5, pady=5)

        self.settings_button = ctk.CTkButton(self.menu_bar, text=self.language["settings"], command=self.open_settings)
        self.settings_button.pack(side="left", padx=5, pady=5)

    def init_send_tab(self):
        self.file_path = ctk.StringVar()
        self.entry_file = ctk.CTkEntry(self.send_tab, textvariable=self.file_path, width=400)
        self.entry_file.pack(pady=10)

        self.browse_button = ctk.CTkButton(self.send_tab, text=self.language["browse"], command=self.browse_file)
        self.browse_button.pack(pady=5)

        self.entry_ip = ctk.CTkEntry(self.send_tab, placeholder_text="Receiver IP")
        self.entry_ip.pack(pady=10)

        self.send_button = ctk.CTkButton(self.send_tab, text=self.language["send_file"], command=self.send_file_thread)
        self.send_button.pack(pady=10)

        self.send_progress = ctk.CTkProgressBar(self.send_tab, width=400)
        self.send_progress.set(0)
        self.send_progress.pack(pady=10)

        self.send_status = ctk.CTkLabel(self.send_tab, text="")
        self.send_status.pack()

    def init_receive_tab(self):
        self.receive_status = ctk.CTkLabel(self.receive_tab, text=self.language["receiver_status"])
        self.receive_status.pack(pady=20)

        self.recv_progress = ctk.CTkProgressBar(self.receive_tab, width=400)
        self.recv_progress.set(0)
        self.recv_progress.pack(pady=10)

        self.start_receiver_button = ctk.CTkButton(self.receive_tab, text="Start Receiver", command=self.start_receiver_thread)
        self.start_receiver_button.pack(pady=10)

    def init_history_tab(self):
        self.history_text = ctk.CTkTextbox(self.history_tab)
        self.history_text.pack(expand=True, fill="both", padx=10, pady=10)
        self.update_history_display()

    def browse_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_path.set(file_path)

    def send_file_thread(self):
        filepath = self.file_path.get()
        ip = self.entry_ip.get().strip()
        if not filepath or not ip:
            self.send_status.configure(text="Please provide file and IP.")
            return
        self.send_status.configure(text="Sending...")
        threading.Thread(
            target=send_file,
            args=(ip, filepath, self.update_send_progress, self.update_send_status),
            daemon=True
        ).start()

    def update_send_progress(self, percent):
        self.send_progress.set(percent / 100)

    def update_send_status(self, msg):
        self.send_status.configure(text=msg)
        self.history.add_transfer(self.file_path.get(), msg)
        self.update_history_display()

    def start_receiver_thread(self):
        threading.Thread(
            target=receiver_thread,
            args=(self.update_recv_status, self.update_recv_progress),
            daemon=True
        ).start()
        self.receive_status.configure(text="Receiver running...")

    def update_recv_status(self, msg):
        self.receive_status.configure(text=msg)
        self.history.add_transfer("Received File", msg)
        self.update_history_display()

    def update_recv_progress(self, percent):
        self.recv_progress.set(percent / 100)

    def toggle_theme(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "light" if current_mode == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)

    def open_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.grab_set()

    def update_history_display(self):
        self.history_text.delete(1.0, ctk.END)
        self.history_text.insert(ctk.END, self.history.get_history())
