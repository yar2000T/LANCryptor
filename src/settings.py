import customtkinter as ctk


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("400x300")

        self.theme_label = ctk.CTkLabel(self, text="Theme:")
        self.theme_label.pack(pady=10)

        self.theme_var = ctk.StringVar(value="System")
        self.theme_option = ctk.CTkOptionMenu(
            self, values=["System", "Dark", "Light"], variable=self.theme_var
        )
        self.theme_option.pack(pady=5)

        self.save_button = ctk.CTkButton(self, text="Save", command=self.save_settings)
        self.save_button.pack(pady=20)

    def save_settings(self):
        theme = self.theme_var.get()
        ctk.set_appearance_mode(theme)
        self.destroy()
