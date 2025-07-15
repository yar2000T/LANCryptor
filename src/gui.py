import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import threading
import queue
import transfer  # your transfer.py module

class PlaceholderEntry(tb.Entry):
    def __init__(self, master=None, placeholder="", placeholder_color="grey", normal_color="black", **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.normal_color = normal_color
        self.receive_thread = None
        self.stop_event = threading.Event()

        self.var = self.cget("textvariable")
        if not self.var:
            from tkinter import StringVar
            self.var = StringVar()
            self.configure(textvariable=self.var)

        self.var.set(self.placeholder)
        self.configure(foreground=self.placeholder_color)

        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)

    def _clear_placeholder(self, event):
        if self.var.get() == self.placeholder:
            self.var.set("")
            self.configure(foreground=self.normal_color)

    def _add_placeholder(self, event):
        if not self.var.get():
            self.var.set(self.placeholder)
            self.configure(foreground=self.placeholder_color)

class LANCryptorApp(tb.Window):
    def __init__(self):
        super().__init__(themename="flatly")  # Windows-like theme: "flatly" or "litera" or "solar"
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
        # self.style = tb.Style()

        self.tab_control = tb.Notebook(self, bootstyle="primary")
        self.tab_control.pack(expand=YES, fill=BOTH, padx=10, pady=10)

        self.send_tab = tb.Frame(self.tab_control)
        self.tab_control.add(self.send_tab, text="Send")

        # Repeat for other tabs:
        self.receive_tab = tb.Frame(self.tab_control)
        self.tab_control.add(self.receive_tab, text="Receive")

        self.history_tab = tb.Frame(self.tab_control)
        self.tab_control.add(self.history_tab, text="History")

        self._build_send_tab()
        self._build_receive_tab()
        self._build_history_tab()

        # Bottom frame with buttons
        self.bottom_frame = tb.Frame(self)
        self.bottom_frame.pack(fill=X, padx=10, pady=5)

        self.theme_button = tb.Button(self.bottom_frame, text="Toggle Theme", bootstyle="secondary-outline", command=self.toggle_theme)
        self.theme_button.pack(side=LEFT, padx=5)

        self.settings_button = tb.Button(self.bottom_frame, text="Settings", bootstyle="secondary-outline", command=self.open_settings)
        self.settings_button.pack(side=LEFT, padx=5)

    def _build_send_tab(self):
        frame = self.send_tab

        self.file_path_var = tb.StringVar()
        self.entry_file = tb.Entry(frame, textvariable=self.file_path_var, width=50)
        self.entry_file.pack(pady=(10, 5), padx=10)

        self.browse_button = tb.Button(frame, text="Browse", bootstyle="info", command=self.browse_file)
        self.browse_button.pack(pady=5)

        self.entry_ip = PlaceholderEntry(frame, placeholder="Receiver IP", bootstyle="info", width=40)
        self.entry_ip.pack(pady=10, padx=10)

        self.send_button = tb.Button(frame, text="Send File", bootstyle="success", command=self.send_file_thread)
        self.send_button.pack(pady=10)

        self.send_progress = tb.Progressbar(frame, length=400, bootstyle="success")
        self.send_progress.pack(pady=10)

        self.send_status = tb.Label(frame, text="")
        self.send_status.pack()

    def _build_receive_tab(self):
        frame = self.receive_tab

        self.receive_status = tb.Label(frame, text="Receiver not running")
        self.receive_status.pack(pady=20)

        self.recv_progress = tb.Progressbar(frame, length=400)
        self.recv_progress.pack(pady=10)

        self.start_receiver_button = tb.Button(frame, text="Start Receiver", command=self.start_receiver_thread)
        self.start_receiver_button.pack(pady=10)

        self.stop_recv_button = tb.Button(frame, text="Stop Receiving", command=self.stop_receive)
        self.stop_recv_button.pack(pady=5)

        ip_label = tb.Label(frame, text=f"Your IP: {transfer.get_local_ip()}")
        ip_label.pack(pady=(10, 0), anchor="e", padx=10)

    def _build_history_tab(self):
        frame = self.history_tab
        self.history_text = tb.Text(frame, wrap=WORD)
        self.history_text.pack(expand=YES, fill=BOTH, padx=10, pady=10)
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
            daemon=True
        ).start()

    def stop_receive(self):
        if self.receive_thread and self.receive_thread.is_alive():
            self.stop_event.set()
            self._update_recv_status("Receiver stopped...")
            self.receiver_running = False

    def _update_send_progress(self, percent):
        self.send_progress['value'] = percent

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
            args=(self._update_recv_status, self._update_recv_progress, self.stop_event),
            daemon=True
        )
        self.receive_thread.start()

    def _update_recv_status(self, msg):
        self.receive_status.configure(text=msg)
        self.history.append(f"RECV: {msg}")
        self._update_history_display()

    def _update_recv_progress(self, percent):
        self.recv_progress['value'] = percent

    def toggle_theme(self):
        current_theme = self.style.theme_use()
        new_theme = "darkly" if current_theme == "flatly" else "flatly"
        self.style.theme_use(new_theme)

    def open_settings(self):
        messagebox.showinfo("Settings", "Settings dialog not implemented.")

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
            answer = messagebox.askyesno("Confirm sender public key",
                                         f"Incoming connection with public key hash:\n\n{pubkey_hash}\n\nAccept?")
            transfer.confirmation_result = answer
            transfer.confirmation_event.set()

        self.after(100, self._poll_confirmation)


if __name__ == "__main__":
    app = LANCryptorApp()
    app.mainloop()
