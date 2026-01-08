import customtkinter as ctk
import json
from ..theme import THEME

class WelcomeDialog(ctk.CTkToplevel):
    def __init__(self, master, on_complete):
        super().__init__(master)
        self.on_complete = on_complete
        
        # Window setup
        self.title("Welcome to Verint Tracker")
        self.geometry("500x450")
        self.resizable(False, False)
        
        # Apply theme
        self.configure(fg_color=THEME["bg_dark"])
        
        self.setup_ui()
        
        # Center on screen
        self.center_window()
        
        # Make modal (delayed to ensure rendering)
        self.attributes("-topmost", True)
        self.after(200, self.enable_modal)
        
    def enable_modal(self):
        """Enable modal behavior after window is ready."""
        self.lift()
        self.focus_force()
        self.grab_set()
        
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        # Welcome Header
        ctk.CTkLabel(self, text="Welcome!", font=("Roboto", 30, "bold"), text_color=THEME["text_primary"]).pack(pady=(40, 10))
        
        ctk.CTkLabel(self, 
                     text="This tracker helps you manage your schedule and\nmonitor your efficiency metrics in real-time.", 
                     font=("Roboto", 14), 
                     text_color=THEME["text_secondary"],
                     justify="center").pack(pady=(0, 30))

        # Form Container
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="x", padx=60)
        form_frame.grid_columnconfigure(1, weight=1)

        # Browser Selection
        ctk.CTkLabel(form_frame, text="Browser:", font=("Roboto", 14, "bold"), text_color=THEME["text_primary"]).grid(row=0, column=0, sticky="w", pady=15)
        self.browser_var = ctk.StringVar(value="msedge")
        browser_menu = ctk.CTkOptionMenu(form_frame, values=["msedge", "chrome"], variable=self.browser_var, 
                                         fg_color=THEME["bg_card"], button_color=THEME["accent"], button_hover_color=THEME["accent"])
        browser_menu.grid(row=0, column=1, sticky="w", padx=(20, 0))

        # Target CPH
        ctk.CTkLabel(form_frame, text="Target CPH:", font=("Roboto", 14, "bold"), text_color=THEME["text_primary"]).grid(row=1, column=0, sticky="w", pady=15)
        self.cph_entry = ctk.CTkEntry(form_frame, width=140, fg_color=THEME["bg_card"], text_color=THEME["text_primary"])
        self.cph_entry.insert(0, "7.5")
        self.cph_entry.grid(row=1, column=1, sticky="w", padx=(20, 0))
        
        # Help text for CPH
        ctk.CTkLabel(form_frame, text="Contacts Per Hour goal (Standard is 7.5)", font=("Roboto", 11), text_color=THEME["text_secondary"]).grid(row=2, column=1, sticky="w", padx=(20, 0), pady=(0, 10))

        # Start Button
        ctk.CTkButton(self, text="Get Started", command=self.save_and_close, 
                      fg_color=THEME["btn_primary"], hover_color=THEME["btn_primary_hover"], 
                      width=200, height=40, font=("Roboto", 16, "bold")).pack(pady=40)

    def save_and_close(self):
        # Validate CPH
        try:
            cph = float(self.cph_entry.get())
        except ValueError:
            self.cph_entry.configure(border_color=THEME["danger"])
            return

        # Create config
        config = {
            "browser_type": self.browser_var.get(),
            "target_cph": cph,
            "verint_url": "https://wfo.mt7.verintcloudservices.com/wfo/control/signin",
            "notification_minutes_before": 5,
            "check_interval_seconds": 60,
            "headless": False,
            "use_manual_file": False
        }

        # Save to file
        try:
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Failed to save initial config: {e}")
            
        # Run callback with new config
        if self.on_complete:
            self.on_complete(config)
            
        self.destroy()
