import customtkinter as ctk
import json
import os
from ..theme import THEME

class SettingsView(ctk.CTkFrame):
    """
    Frame for editing application configuration.
    """
    def __init__(self, master, app_instance):
        super().__init__(master, fg_color=THEME["bg_dark"])
        self.app = app_instance
        self.config_file = "config.json"
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        
        # Header
        ctk.CTkLabel(self, text="Application Settings", font=("Roboto", 20, "bold"), text_color=THEME["text_primary"]).grid(row=0, column=0, columnspan=2, pady=20)
        
        # Helper for labels
        def create_label(text, row):
            ctk.CTkLabel(self, text=text, text_color=THEME["text_primary"]).grid(row=row, column=0, sticky="e", padx=10, pady=10)

        # Verint URL
        create_label("Verint URL (Optional):", 1)
        self.url_entry = ctk.CTkEntry(self, width=400, placeholder_text="Leave empty to navigate manually", fg_color=THEME["bg_card"], text_color=THEME["text_primary"])
        self.url_entry.grid(row=1, column=1, sticky="w", padx=10, pady=10)
        
        # Notification Minutes
        create_label("Notify Minutes Before:", 2)
        self.notify_entry = ctk.CTkEntry(self, width=100, fg_color=THEME["bg_card"], text_color=THEME["text_primary"])
        self.notify_entry.grid(row=2, column=1, sticky="w", padx=10, pady=10)
        
        # Check Interval
        create_label("Check Interval (seconds):", 3)
        self.interval_entry = ctk.CTkEntry(self, width=100, fg_color=THEME["bg_card"], text_color=THEME["text_primary"])
        self.interval_entry.grid(row=3, column=1, sticky="w", padx=10, pady=10)
        
        # Browser Type
        create_label("Browser Type:", 4)
        self.browser_var = ctk.StringVar(value="msedge")
        self.browser_menu = ctk.CTkOptionMenu(self, values=["msedge", "chrome"], variable=self.browser_var, fg_color=THEME["bg_card"], button_color=THEME["accent"], button_hover_color=THEME["accent"])
        self.browser_menu.grid(row=4, column=1, sticky="w", padx=10, pady=10)
        
        # Headless Mode
        create_label("Headless Mode:", 5)
        self.headless_var = ctk.BooleanVar(value=False)
        self.headless_switch = ctk.CTkSwitch(self, text="Run browser in background", variable=self.headless_var, text_color=THEME["text_primary"], progress_color=THEME["accent"])
        self.headless_switch.grid(row=5, column=1, sticky="w", padx=10, pady=10)

        # Manual File Mode
        create_label("Debug Mode:", 6)
        self.manual_file_var = ctk.BooleanVar(value=False)
        self.manual_file_switch = ctk.CTkSwitch(self, text="Use manual_schedule.txt", variable=self.manual_file_var, text_color=THEME["text_primary"], progress_color=THEME["accent"])
        self.manual_file_switch.grid(row=6, column=1, sticky="w", padx=10, pady=10)

        # Appearance
        create_label("Theme:", 7)
        self.appearance_var = ctk.StringVar(value=ctk.get_appearance_mode())
        self.appearance_menu = ctk.CTkOptionMenu(self, values=["System", "Light", "Dark"], 
                                                 command=self.change_appearance, 
                                                 variable=self.appearance_var, 
                                                 fg_color=THEME["bg_card"], 
                                                 button_color=THEME["accent"], 
                                                 button_hover_color=THEME["accent_hover"],
                                                 text_color=("black", "white")) # Fix text color for light mode
        self.appearance_menu.grid(row=7, column=1, sticky="w", padx=10, pady=10)
        
        # Save Button
        self.save_btn = ctk.CTkButton(self, text="Save Settings", command=self.save_settings, fg_color=THEME["btn_primary"], hover_color=THEME["btn_primary_hover"], text_color=("white", "black"))
        self.save_btn.grid(row=8, column=0, columnspan=2, pady=30)
        
        self.status_label = ctk.CTkLabel(self, text="", text_color=THEME["text_secondary"])
        self.status_label.grid(row=9, column=0, columnspan=2)

    def change_appearance(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)

    def load_settings(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                self.url_entry.insert(0, config.get("verint_url", ""))
                self.notify_entry.insert(0, str(config.get("notification_minutes_before", 5)))
                self.interval_entry.insert(0, str(config.get("check_interval_seconds", 60)))
                self.browser_var.set(config.get("browser_type", "msedge"))
                self.headless_var.set(config.get("headless", False))
                self.manual_file_var.set(config.get("use_manual_file", False))
                # Restore theme if saved? ctk handles persistence often but we can store it.
        except Exception as e:
            self.status_label.configure(text=f"Error loading settings: {e}", text_color="red")

    def save_settings(self):
        try:
            config = {
                "verint_url": self.url_entry.get(),
                "notification_minutes_before": int(self.notify_entry.get()),
                "check_interval_seconds": int(self.interval_entry.get()),
                "browser_type": self.browser_var.get(),
                "headless": self.headless_var.get(),
                "use_manual_file": self.manual_file_var.get()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
                
            self.status_label.configure(text="Settings saved! Restart application to apply changes.", text_color="green")
            
            # Update app config in real-time where possible
            self.app.config = config
            
        except ValueError:
            self.status_label.configure(text="Error: Please enter valid numbers for minutes/seconds.", text_color="red")
        except Exception as e:
            self.status_label.configure(text=f"Error saving: {e}", text_color="red")
