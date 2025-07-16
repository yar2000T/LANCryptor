from tkinter import filedialog, messagebox
import customtkinter as ctk
import threading
import queue
import transfer


class PlaceholderEntry(ctk.CTkEntry):
    def __init__(
        self,
        master=None,
        placeholder="",
        placeholder_color="grey",
        normal_color="black",
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.normal_color = normal_color
        self.receive_thread = None
        self.stop_event = threading.Event()

        self.insert(0, self.placeholder)
        self.configure(text_color=self.placeholder_color)
        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)

    def _clear_placeholder(self, event):
        if self.get() == self.placeholder:
            self.delete(0, "end")
            self.configure(text_color=self.normal_color)

    def _add_placeholder(self, event):
        if not self.get():
            self.insert(0, self.placeholder)
            self.configure(text_color=self.placeholder_color)


class LANCryptorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")  # Modes: "System", "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

        self.title("LANCryptor")
        self.geometry("600x400")
        self.receiver_running = False
        self.history = []
        self.confirmation_queue = transfer.confirmation_queue
        self.confirmation_event = transfer.confirmation_event
        self.confirmation_result = transfer.confirmation_result

        self._build_ui()
        self._poll_confirmation()

    def _build_ui(self):
        self.tab_control = ctk.CTkTabview(self)
        self.tab_control.pack(expand=True, fill="both", padx=10, pady=10)

        self.send_tab = self.tab_control.add("Send")
        self.receive_tab = self.tab_control.add("Receive")
        self.history_tab = self.tab_control.add("History")

        self._build_send_tab()
        self._build_receive_tab()
        self._build_history_tab()

    def _build_send_tab(self):
        frame = ctk.CTkFrame(self.send_tab)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.file_path_var = ctk.StringVar()
        self.entry_file = ctk.CTkEntry(
            frame, textvariable=self.file_path_var, width=400
        )
        self.entry_file.pack(pady=(10, 5), padx=10)

        self.browse_button = ctk.CTkButton(
            frame, text="Browse", command=self.browse_file
        )
        self.browse_button.pack(pady=5)

        self.entry_ip = PlaceholderEntry(frame, placeholder="Receiver IP", width=400)
        self.entry_ip.pack(pady=10, padx=10)

        self.send_button = ctk.CTkButton(
            frame, text="Send File", command=self.send_file_thread
        )
        self.send_button.pack(pady=10)

        self.send_progress = ctk.CTkProgressBar(frame, width=400)
        self.send_progress.pack(pady=10)
        self.send_progress.set(0)

        self.send_status = ctk.CTkLabel(frame, text="")
        self.send_status.pack()

    def _build_receive_tab(self):
        frame = ctk.CTkFrame(self.receive_tab)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.receive_status = ctk.CTkLabel(frame, text="Receiver not running")
        self.receive_status.pack(pady=20)

        self.recv_progress = ctk.CTkProgressBar(frame, width=400)
        self.recv_progress.pack(pady=10)
        self.recv_progress.set(0)

        self.start_receiver_button = ctk.CTkButton(
            frame, text="Start Receiver", command=self.start_receiver_thread
        )
        self.start_receiver_button.pack(pady=10)

        self.stop_recv_button = ctk.CTkButton(
            frame, text="Stop Receiving", command=self.stop_receive
        )
        self.stop_recv_button.pack(pady=5)

        ip_label = ctk.CTkLabel(frame, text=f"Your IP: {transfer.get_local_ip()}")
        ip_label.pack(pady=(10, 0), anchor="e", padx=10)

    def _build_history_tab(self):
        frame = ctk.CTkFrame(self.history_tab)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.history_text = ctk.CTkTextbox(frame, wrap="word")
        self.history_text.pack(expand=True, fill="both", padx=10, pady=10)
        self._update_history_display()

    def browse_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_path_var.set(file_path)

    def send_file_thread(self):
        filepath = self.file_path_var.get()
        ip = self.entry_ip.get().strip()
        if not filepath or not ip or ip == "Receiver IP":
            self._update_send_status("Please provide file and IP.")
            return
        self._update_send_status("Sending...")
        threading.Thread(
            target=transfer.send_file,
            args=(ip, filepath, self._update_send_progress, self._update_send_status),
            daemon=True,
        ).start()

    def stop_receive(self):
        if self.receive_thread and self.receive_thread.is_alive():
            self.stop_event.set()
            self._update_recv_status("Receiver stopped...")
            self.receiver_running = False

    def _update_send_progress(self, percent):
        self.send_progress.set(percent)

    def _update_send_status(self, msg):
        self.send_status.configure(text=msg)
        self.history.append(f"SEND: {msg}")
        self._update_history_display()

    def start_receiver_thread(self):
        if self.receiver_running:
            self._update_recv_status("Receiver already running.")
            return
        self.receiver_running = True
        self.receive_status.configure(text="Receiver running...")
        self.stop_event = threading.Event()
        self.receive_thread = threading.Thread(
            target=transfer.receiver_thread,
            args=(
                self._update_recv_status,
                self._update_recv_progress,
                self.stop_event,
            ),
            kwargs={"cli": False},
            daemon=True,
        )
        self.receive_thread.start()

    def _update_recv_status(self, msg):
        self.receive_status.configure(text=msg)
        self.history.append(f"RECV: {msg}")
        self._update_history_display()

    def _update_recv_progress(self, percent):
        self.recv_progress.set(percent)

    def _update_history_display(self):
        self.history_text.delete("1.0", "end")
        self.history_text.insert("end", "\n".join(self.history))
        self.history_text.see("end")

    def _poll_confirmation(self):
        try:
            pubkey_hash = transfer.confirmation_queue.get_nowait()
        except queue.Empty:
            pubkey_hash = None

        if pubkey_hash:
            answer = messagebox.askyesno(
                "Confirm sender public key",
                f"Incoming connection with public key hash:\n\n{pubkey_hash}\n\nAccept?",
            )
            transfer.confirmation_result = answer
            transfer.confirmation_event.set()
        self.after(100, self._poll_confirmation)


if __name__ == "__main__":
    app = LANCryptorApp()
    app.mainloop()
