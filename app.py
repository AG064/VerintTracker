import customtkinter as ctk
import threading
import time
import queue
import keyboard
import winsound
import json
import os
from plyer import notification
from datetime import datetime, timedelta
from verint_tracker import VerintTracker
from stats_manager import StatsManager
from input_monitor import InputMonitor

# Set theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- Theme Definition ---
THEME = {
    "bg_dark": "#1e1e1e",      # App Background
    "bg_card": "#2b2b2b",      # Container Background
    "text_primary": "#e0e0e0", # Primary Text
    "text_secondary": "#a0a0a0", # Secondary Text (Labels)
    "accent": "#88C0D0",       # Nord Blue (Highlights)
    "accent_hover": "#72A0C1", # Nord Blue darker (Hover)
    "active_row": "#3b4252",   # Active Schedule Row
    "btn_primary": "#26A69A",  # Soft Teal (Resume/Start)
    "btn_primary_hover": "#00897B",
    "btn_secondary_border": "#a0a0a0", # Outlined buttons
    "danger": "#BF616A",       # Red
}

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
        
        # Save Button
        self.save_btn = ctk.CTkButton(self, text="Save Settings", command=self.save_settings, fg_color=THEME["btn_primary"], hover_color=THEME["btn_primary_hover"], text_color=THEME["bg_dark"])
        self.save_btn.grid(row=7, column=0, columnspan=2, pady=30)
        
        self.status_label = ctk.CTkLabel(self, text="", text_color=THEME["text_secondary"])
        self.status_label.grid(row=8, column=0, columnspan=2)

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

class TrackerWorker(threading.Thread):
    """
    Dedicated thread for Playwright operations.
    This prevents the GUI from freezing while the browser is being automated.
    """
    def __init__(self, command_queue, result_queue):
        super().__init__(daemon=True)
        self.command_queue = command_queue
        self.result_queue = result_queue
        self.tracker = VerintTracker()
        self.running = True

    def run(self):
        try:
            self.result_queue.put(("status", "Starting browser..."))
            self.tracker.start_browser()
            
            self.result_queue.put(("status", "Navigating to Verint..."))
            success = self.tracker.navigate_to_verint()
            
            # Handle manual login requirement
            if not success:
                self.result_queue.put(("login_required", None))
                # Wait for login confirmation from GUI
                while self.running:
                    try:
                        cmd, args = self.command_queue.get(timeout=1.0)
                        if cmd == "stop":
                            self.running = False
                            return
                        elif cmd == "login_complete":
                            self.result_queue.put(("status", "Verifying login..."))
                            if self.tracker.navigate_to_verint():
                                break
                            else:
                                self.result_queue.put(("login_required", None))
                    except queue.Empty:
                        pass
            
            self.result_queue.put(("status", "Successfully navigated to Verint."))
            
            # Initial fetch of the schedule
            self.fetch_schedule()
            
            # Main worker loop
            while self.running:
                try:
                    # Check for commands (non-blocking)
                    try:
                        cmd, args = self.command_queue.get(timeout=1.0)
                        if cmd == "stop":
                            self.running = False
                            break
                        elif cmd == "refresh":
                            self.fetch_schedule()
                    except queue.Empty:
                        # No command, just continue loop
                        pass
                        
                except Exception as e:
                    self.result_queue.put(("error", str(e)))
                    
        except Exception as e:
            self.result_queue.put(("error", f"Critical worker error: {e}"))
        finally:
            self.tracker.cleanup()
            self.result_queue.put(("stopped", None))

    def fetch_schedule(self):
        """Fetch schedule from Verint and send to GUI."""
        self.result_queue.put(("status", "Fetching schedule..."))
        try:
            items = self.tracker.parse_schedule()
            self.result_queue.put(("schedule", items))
        except Exception as e:
            self.result_queue.put(("error", f"Parse error: {e}"))

class CPHTracker(ctk.CTkFrame):
    """
    Frame for the CPH (Contacts Per Hour) Pacing Timer.
    Tracks time per ticket and calculates session statistics.
    """
    def __init__(self, master, stats_manager, input_monitor, target_cph=7.5):
        super().__init__(master, fg_color=THEME["bg_card"], corner_radius=15)
        self.stats_manager = stats_manager
        self.input_monitor = input_monitor
        self.target_cph = target_cph
        self.seconds_per_ticket = int(3600 / target_cph)
        self.remaining_seconds = self.seconds_per_ticket
        self.running = False
        
        # --- Restore Logic ---
        self.session_start_time = datetime.now()
        
        # 1. Restore Session Start from first ticket of the day
        first_ticket = self.stats_manager.get_first_ticket_time_today()
        if first_ticket:
            self.session_start_time = first_ticket
            print(f"Restored session start: {self.session_start_time}")
            
            # 2. Restore Input Stats from today's activity
            today_stats = self.stats_manager.get_activity_stats("today")
            if today_stats:
                self.input_monitor.restore_session_state(
                    keys=today_stats.get("keys", 0),
                    clicks=today_stats.get("clicks", 0),
                    duration_seconds=today_stats.get("duration", 0)
                )
                print(f"Restored input stats: {today_stats}")
        
        self.current_ticket_start_time = None
        
        self.setup_ui()
        self.update_stats_display()
        
        # Setup global hotkey for quick completion
        try:
            keyboard.add_hotkey('-', self.complete_ticket_hotkey)
        except Exception as e:
            print(f"Could not bind hotkey: {e}")
        
    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Header
        self.header = ctk.CTkLabel(self, text="CPH Pacing Timer", font=("Roboto", 16, "bold"), text_color=THEME["text_primary"])
        self.header.grid(row=0, column=0, columnspan=2, pady=(15, 5))
        
        # Timer Display
        self.timer_label = ctk.CTkLabel(self, text=self.format_time(self.remaining_seconds), font=("Roboto", 48, "bold"), text_color=THEME["text_primary"])
        self.timer_label.grid(row=1, column=0, columnspan=2, pady=(5, 0))
        
        # Elapsed Time Display
        self.elapsed_label = ctk.CTkLabel(self, text="Elapsed: 00:00", font=("Roboto", 12), text_color=THEME["text_secondary"])
        self.elapsed_label.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # Info
        self.info_label = ctk.CTkLabel(self, text=f"Target: {self.target_cph} CPH ({self.format_time(self.seconds_per_ticket)} / ticket)", text_color=THEME["text_secondary"])
        self.info_label.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        # Current CPH Display
        self.cph_label = ctk.CTkLabel(self, text="Current Session CPH: 0.0", font=("Roboto", 14, "bold"), text_color=THEME["accent"])
        self.cph_label.grid(row=4, column=0, columnspan=2, pady=(0, 5))
        
        # KPM/CPM Display
        self.input_stats_label = ctk.CTkLabel(self, text="KPM: 0 | CPM: 0", font=("Roboto", 12), text_color=THEME["text_secondary"])
        self.input_stats_label.grid(row=5, column=0, columnspan=2, pady=(0, 10))
        
        # Buttons
        self.start_btn = ctk.CTkButton(self, 
                                       text="Start Ticket", 
                                       command=self.start_timer, 
                                       fg_color=THEME["btn_primary"], 
                                       hover_color=THEME["btn_primary_hover"],
                                       text_color=THEME["bg_dark"],
                                       font=("Roboto", 14, "bold"),
                                       height=40,
                                       corner_radius=8)
        self.start_btn.grid(row=6, column=0, columnspan=2, padx=20, pady=(10, 10), sticky="ew")
        
        self.reply_btn = ctk.CTkButton(self, 
                                       text="Complete (Reply)", 
                                       command=lambda: self.complete_ticket(True), 
                                       fg_color="transparent", 
                                       border_color=THEME["btn_secondary_border"], 
                                       border_width=1,
                                       text_color=THEME["text_primary"],
                                       hover_color=THEME["active_row"],
                                       height=32,
                                       corner_radius=8)
        self.reply_btn.grid(row=7, column=0, padx=(20, 5), pady=(0, 15), sticky="ew")

        self.noreply_btn = ctk.CTkButton(self, 
                                        text="Complete (No Reply)", 
                                        command=lambda: self.complete_ticket(False), 
                                        fg_color="transparent", 
                                        border_color=THEME["btn_secondary_border"], 
                                        border_width=1,
                                        text_color=THEME["text_secondary"],
                                        hover_color=THEME["active_row"],
                                        height=32,
                                        corner_radius=8)
        self.noreply_btn.grid(row=7, column=1, padx=(5, 20), pady=(0, 15), sticky="ew")
        
        self.hotkey_label = ctk.CTkLabel(self, text="Hotkey: Numpad Minus (-) = Reply", text_color=THEME["text_secondary"], font=("Roboto", 10))
        self.hotkey_label.grid(row=8, column=0, columnspan=2, pady=(0, 10))
        
    def format_time(self, seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"
        
    def start_timer(self):
        if not self.running:
            self.running = True
            if self.current_ticket_start_time is None:
                self.current_ticket_start_time = datetime.now()
            self.start_btn.configure(text="Pause", fg_color="orange", hover_color="darkorange")
            self.count_down()
        else:
            self.running = False
            self.start_btn.configure(text="Resume", fg_color=THEME["btn_primary"], hover_color=THEME["btn_primary_hover"]) # Reset to Primary
            
    def complete_ticket_hotkey(self):
        # Called from background thread by keyboard library, so we use after() to run on main thread
        self.after(0, lambda: self.complete_ticket(True, notify=True))

    def complete_ticket(self, has_reply=True, notify=False):
        # Log ticket
        self.stats_manager.log_ticket(has_reply)
        self.update_stats_display()
        
        # Check if we need to restart the loop
        restart_loop = not self.running
        
        # Reset timer
        self.running = True # Auto start next ticket
        self.remaining_seconds = self.seconds_per_ticket
        self.current_ticket_start_time = datetime.now()
        self.timer_label.configure(text=self.format_time(self.remaining_seconds), text_color=THEME["text_primary"])
        self.elapsed_label.configure(text="Elapsed: 00:00")
        self.start_btn.configure(text="Pause", fg_color="orange", hover_color="darkorange")
        
        # Notify if requested (e.g. via hotkey)
        if notify:
            try:
                # Access main app via winfo_toplevel
                self.winfo_toplevel().send_notification(
                    "Ticket Completed", 
                    "Ticket logged successfully.", 
                    focus_window=False
                )
            except AttributeError:
                pass

        # Ensure countdown loop is running if it wasn't
        if restart_loop: 
             self.count_down()

    def update_stats_display(self):
        cph = self.stats_manager.get_current_session_cph(self.session_start_time)
        self.cph_label.configure(text=f"Current Session CPH: {cph}")
        
        # Update KPM/CPM (Current Rolling / Session Average)
        curr_kpm = self.input_monitor.get_current_kpm()
        curr_cpm = self.input_monitor.get_current_cpm()
        avg_kpm = self.input_monitor.get_session_kpm()
        avg_cpm = self.input_monitor.get_session_cpm()
        
        self.input_stats_label.configure(text=f"KPM: {curr_kpm} (Avg: {avg_kpm}) | CPM: {curr_cpm} (Avg: {avg_cpm})")
        
    def count_down(self):
        if self.running:
            # Update elapsed time
            if self.current_ticket_start_time:
                elapsed = datetime.now() - self.current_ticket_start_time
                self.elapsed_label.configure(text=f"Elapsed: {self.format_time(int(elapsed.total_seconds()))}")

            if self.remaining_seconds > 0:
                self.remaining_seconds -= 1
                self.timer_label.configure(text=self.format_time(self.remaining_seconds))
                
                # Visual warning when time is running out
                if self.remaining_seconds < 60:
                    self.timer_label.configure(text_color=THEME["danger"])
            else:
                # Timer reached 0
                self.timer_label.configure(text="00:00", text_color=THEME["danger"])
                # Play a sound or flash window here if possible
                if self.remaining_seconds == 0:
                    self.remaining_seconds = -1 # Mark as passed 0
                    try:
                        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    except:
                        pass
                    try:
                        self.master.master.master.deiconify() # Try to reach root window to bring to front
                        self.master.master.master.lift()
                    except:
                        pass
            
            # Update stats every second while running
            self.update_stats_display()
            
            self.after(1000, self.count_down)

class StatsView(ctk.CTkFrame):
    """
    Frame for displaying long-term statistics.
    """
    def __init__(self, master, stats_manager):
        super().__init__(master, fg_color=THEME["bg_dark"])
        self.stats_manager = stats_manager
        self.setup_ui()
        
    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self, text="Statistics Dashboard", font=("Roboto", 20, "bold"), text_color=THEME["text_primary"]).grid(row=0, column=0, columnspan=2, pady=20)
        
        # Daily Stats
        self.daily_frame = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=10)
        self.daily_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        
        self.daily_avg_label = ctk.CTkLabel(self.daily_frame, text="Avg Tickets/Day: --", font=("Roboto", 14), text_color=THEME["text_primary"])
        self.daily_avg_label.pack(pady=15)
        
        # Weekly/Monthly
        self.period_frame = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=10)
        self.period_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        self.period_frame.grid_columnconfigure(0, weight=1)
        self.period_frame.grid_columnconfigure(1, weight=1)
        
        self.weekly_label = ctk.CTkLabel(self.period_frame, text="This Week: --", font=("Roboto", 16, "bold"), text_color=THEME["accent"])
        self.weekly_label.grid(row=0, column=0, pady=20)
        
        self.monthly_label = ctk.CTkLabel(self.period_frame, text="This Month: --", font=("Roboto", 16, "bold"), text_color=THEME["accent"])
        self.monthly_label.grid(row=0, column=1, pady=20)
        
        # Input Stats
        self.input_frame = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=10)
        self.input_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        
        ctk.CTkLabel(self.input_frame, text="Input Averages (Weekly)", font=("Roboto", 14, "bold"), text_color=THEME["text_primary"]).pack(pady=10)
        self.kpm_label = ctk.CTkLabel(self.input_frame, text="Avg KPM: --", font=("Roboto", 12), text_color=THEME["text_secondary"])
        self.kpm_label.pack(pady=5)
        self.cpm_label = ctk.CTkLabel(self.input_frame, text="Avg CPM: --", font=("Roboto", 12), text_color=THEME["text_secondary"])
        self.cpm_label.pack(pady=(5, 15))
        
        ctk.CTkButton(self, text="Refresh Stats", command=self.refresh_stats, fg_color=THEME["btn_primary"], hover_color=THEME["btn_primary_hover"], text_color=THEME["bg_dark"]).grid(row=4, column=0, columnspan=2, pady=20)
        
        self.refresh_stats()
        
    def refresh_stats(self):
        avg_daily = self.stats_manager.get_average_cph_per_day()
        weekly = self.stats_manager.get_weekly_stats()
        monthly = self.stats_manager.get_monthly_stats()
        
        self.daily_avg_label.configure(text=f"Avg Tickets/Day: {avg_daily}")
        self.weekly_label.configure(text=f"This Week: {weekly}")
        self.monthly_label.configure(text=f"This Month: {monthly}")
        
        # Input stats
        avg_kpm = self.stats_manager.get_average_kpm("week")
        avg_cpm = self.stats_manager.get_average_clicks_per_minute("week")
        self.kpm_label.configure(text=f"Avg KPM: {avg_kpm}")
        self.cpm_label.configure(text=f"Avg CPM: {avg_cpm}")

class ScheduleApp(ctk.CTk):
    """
    Main Application Window.
    """
    def __init__(self):
        super().__init__(fg_color=THEME["bg_dark"])
        
        self.title("Verint Schedule Tracker")
        self.geometry("900x800")
        
        self.stats_manager = StatsManager()
        self.input_monitor = InputMonitor(self.stats_manager)
        self.command_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.worker = None
        
        self.current_schedule = []
        self.notified_activities = set()
        
        # Load config for notifications
        self.config = {}
        self.load_config()
        
        self.setup_ui()
        self.start_worker()
        self.input_monitor.start()
        self.check_queue()
        self.check_notifications()
        
    def load_config(self):
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    self.config = json.load(f)
        except:
            pass

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Tab View
        self.tab_view = ctk.CTkTabview(self, fg_color=THEME["bg_dark"], text_color=THEME["text_primary"], segmented_button_fg_color=THEME["bg_card"], segmented_button_selected_color=THEME["accent"], segmented_button_selected_hover_color=THEME["accent_hover"])
        self.tab_view.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        self.tab_dashboard = self.tab_view.add("Dashboard")
        self.tab_stats = self.tab_view.add("Statistics")
        self.tab_settings = self.tab_view.add("Settings")
        
        # --- Dashboard Tab ---
        self.tab_dashboard.grid_columnconfigure(0, weight=1)
        self.tab_dashboard.grid_rowconfigure(1, weight=1) # List expands
        
        # Status & Next Activity
        self.status_frame = ctk.CTkFrame(self.tab_dashboard, fg_color=THEME["bg_card"], corner_radius=15)
        self.status_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 15))
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.next_activity_label = ctk.CTkLabel(self.status_frame, text="Loading Schedule...", font=("Roboto", 28), text_color=THEME["text_primary"])
        self.next_activity_label.grid(row=0, column=0, pady=(20, 5), padx=30, sticky="w")
        
        self.countdown_label = ctk.CTkLabel(self.status_frame, text="--:--:--", font=("Roboto", 72, "bold"), text_color=THEME["accent"])
        self.countdown_label.grid(row=1, column=0, pady=(0, 25), padx=30, sticky="w")
        
        # Schedule List
        self.schedule_frame = ctk.CTkScrollableFrame(self.tab_dashboard, label_text="Today's Schedule", label_font=("Roboto", 14, "bold"), label_fg_color=THEME["bg_card"], fg_color=THEME["bg_card"], corner_radius=15)
        self.schedule_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 15))
        self.schedule_frame.grid_columnconfigure(0, weight=1) # Ensure content expands
        
        # CPH Tracker
        self.cph_tracker = CPHTracker(self.tab_dashboard, self.stats_manager, self.input_monitor)
        self.cph_tracker.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 15))
        
        # Footer
        self.footer_frame = ctk.CTkFrame(self.tab_dashboard, fg_color="transparent")
        self.footer_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))
        
        self.refresh_btn = ctk.CTkButton(self.footer_frame, text="Refresh Schedule", command=self.request_refresh, fg_color="transparent", border_width=1, border_color=THEME["btn_secondary_border"], text_color=THEME["text_secondary"], hover_color=THEME["active_row"])
        self.refresh_btn.pack(side="right")
        
        self.status_bar = ctk.CTkLabel(self.footer_frame, text="Initializing...", text_color=THEME["text_secondary"], font=("Roboto", 10))
        self.status_bar.pack(side="left")
        
        # --- Statistics Tab ---
        self.stats_view = StatsView(self.tab_stats, self.stats_manager)
        self.stats_view.configure(fg_color=THEME["bg_dark"]) # Patch bg
        self.stats_view.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Settings Tab ---
        self.settings_view = SettingsView(self.tab_settings, self)
        self.settings_view.pack(fill="both", expand=True, padx=10, pady=10)

    def start_worker(self):
        self.worker = TrackerWorker(self.command_queue, self.result_queue)
        self.worker.start()
        
        # Auto refresh timer
        self.after(60000, self.auto_refresh)

    def check_queue(self):
        """Check for messages from the worker thread."""
        try:
            while True:
                msg_type, data = self.result_queue.get_nowait()
                
                if msg_type == "status":
                    self.status_bar.configure(text=data)
                    print(f"STATUS: {data}") # Log to console
                elif msg_type == "schedule":
                    print(f"SCHEDULE: Received {len(data)} items") # Log to console
                    self.update_schedule_ui(data)
                elif msg_type == "error":
                    self.status_bar.configure(text=f"Error: {data}")
                    print(f"Worker Error: {data}")
                elif msg_type == "login_required":
                    self.show_login_dialog()
                elif msg_type == "stopped":
                    self.quit()
                    return
                    
        except queue.Empty:
            pass
        
        self.after(100, self.check_queue)

    def show_login_dialog(self):
        """Show a dialog prompting the user to log in manually."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Login Required")
        dialog.geometry("400x200")
        dialog.attributes("-topmost", True)
        
        ctk.CTkLabel(dialog, text="Manual Login Required", font=("Roboto", 16, "bold")).pack(pady=20)
        ctk.CTkLabel(dialog, text="Please log in to your Microsoft account\nin the browser window that opened.", text_color="gray").pack(pady=10)
        
        def on_confirm():
            self.command_queue.put(("login_complete", None))
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="I have logged in", command=on_confirm).pack(pady=20)

    def request_refresh(self):
        self.command_queue.put(("refresh", None))
        self.status_bar.configure(text="Refresh requested...")

    def auto_refresh(self):
        self.request_refresh()
        self.after(60000, self.auto_refresh)

    def update_schedule_ui(self, items):
        self.status_bar.configure(text=f"Updated at {datetime.now().strftime('%H:%M:%S')}")
        self.current_schedule = items
        
        # Clear existing items
        for widget in self.schedule_frame.winfo_children():
            widget.destroy()
            
        if not items:
            ctk.CTkLabel(self.schedule_frame, text="No schedule found.", text_color=THEME["text_secondary"]).pack(pady=20)
            return

        # Filter out invalid items and sort
        valid_items = [x for x in items if 'datetime' in x]
        if len(valid_items) < len(items):
            print(f"Warning: Ignored {len(items) - len(valid_items)} items missing datetime.")
            
        valid_items.sort(key=lambda x: x['datetime'])
        items = valid_items
        
        now = datetime.now()
        next_activity = None
        
        for item in items:
            dt = item['datetime']
            if dt < now and (now - dt) > timedelta(hours=12):
                dt = dt + timedelta(days=1)
                item['datetime'] = dt
                
            is_past = dt < now
            is_next = False
            
            if not is_past and next_activity is None:
                next_activity = item
                is_next = True
            
            # Row Styling
            bg_color = THEME["active_row"] if is_next else "transparent"
            text_color = THEME["text_secondary"] if is_past else (THEME["accent"] if is_next else THEME["text_primary"])
            weight = "bold" if is_next else "normal"
            corner_radius = 8 if is_next else 0
            
            row = ctk.CTkFrame(self.schedule_frame, fg_color=bg_color, corner_radius=corner_radius)
            row.pack(fill="x", pady=2, padx=5)
            row.columnconfigure(1, weight=1) # Middle column expands
            
            # Column 1: Time (Fixed Width approx via formatting or just consistent alignment)
            # To ensure rigid columns, grid is best inside the row frame, but we need fixed widths for 1 and 3.
            
            time_lbl = ctk.CTkLabel(row, text=item['time'], width=90, anchor="w", text_color=text_color, font=("Roboto", 14, weight))
            time_lbl.grid(row=0, column=0, padx=(10, 5), pady=8)
            
            activity_lbl = ctk.CTkLabel(row, text=item['activity'], anchor="w", text_color=text_color, font=("Roboto", 14, weight))
            activity_lbl.grid(row=0, column=1, sticky="ew", padx=5, pady=8)
            
            if 'duration' in item:
                dur_lbl = ctk.CTkLabel(row, text=item['duration'], width=70, anchor="e", text_color=text_color, font=("Roboto", 14, weight))
                dur_lbl.grid(row=0, column=2, padx=(5, 10), pady=8)

        # Calculate Shift End
        shift_end = None
        if items:
            last_item = items[-1]
            if 'duration' in last_item:
                try:
                    # Parse duration HH:MM
                    h, m = map(int, last_item['duration'].split(':'))
                    dur_delta = timedelta(hours=h, minutes=m)
                    shift_end = last_item['datetime'] + dur_delta
                    
                    end_str = shift_end.strftime("%I:%M %p").lstrip("0")
                    
                    # Add separator 
                    sep = ctk.CTkFrame(self.schedule_frame, height=1, fg_color=THEME["text_secondary"])
                    sep.pack(fill="x", pady=(15, 5), padx=20)
                    
                    end_row = ctk.CTkFrame(self.schedule_frame, fg_color="transparent")
                    end_row.pack(fill="x", pady=5, padx=5)
                    end_row.columnconfigure(1, weight=1)
                    
                    ctk.CTkLabel(end_row, text=end_str, width=90, anchor="w", text_color=THEME["accent"], font=("Roboto", 14, "bold")).grid(row=0, column=0, padx=(10, 5), pady=5)
                    ctk.CTkLabel(end_row, text="Shift End", anchor="w", text_color=THEME["accent"], font=("Roboto", 14, "bold")).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
                    
                except Exception as e:
                    print(f"Error calculating shift end: {e}")

        if next_activity:
            self.next_activity_label.configure(text=f"Next: {next_activity['activity']}")
            self.target_time = next_activity['datetime']
        elif shift_end:
            # If no next activity but we have a shift end, show countdown to shift end
            self.next_activity_label.configure(text="Shift End")
            self.target_time = shift_end
        else:
            self.next_activity_label.configure(text="No upcoming activities")
            self.countdown_label.configure(text="--:--:--")
            if hasattr(self, 'target_time'):
                del self.target_time
        
        # Start countdown loop if not already running (or just ensure it updates)
        self.update_countdown()

    def update_countdown(self):
        now = datetime.now()
        should_continue = False
        
        if hasattr(self, 'target_time'):
            diff = self.target_time - now
            if diff.total_seconds() > 0:
                hours, remainder = divmod(int(diff.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                self.countdown_label.configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
                should_continue = True
            else:
                self.countdown_label.configure(text="00:00:00")
                self.request_refresh()
                return # Refresh will trigger new UI update

        if should_continue:
            self.after(1000, self.update_countdown)

    def on_closing(self):
        self.status_bar.configure(text="Stopping tracker...")
        self.input_monitor.stop()
        self.command_queue.put(("stop", None))
        # Wait for worker to signal stopped via queue in check_queue loop

    def check_notifications(self):
        """Check for upcoming schedule changes and notify."""
        if not self.current_schedule:
            self.after(30000, self.check_notifications)
            return

        now = datetime.now()
        # Notify X minutes before (default 5)
        minutes_before = self.config.get("notification_minutes_before", 5)
        notification_threshold = timedelta(minutes=minutes_before)
        
        for item in self.current_schedule:
            if 'datetime' not in item: continue
            
            dt = item['datetime']
            # Handle midnight crossover logic if needed (already done in update_schedule_ui but good to be safe)
            if dt < now and (now - dt) > timedelta(hours=12):
                dt = dt + timedelta(days=1)
            
            time_until = dt - now
            activity_id = f"{item['time']}_{item['activity']}"
            
            if timedelta(0) < time_until <= notification_threshold:
                if activity_id not in self.notified_activities:
                    mins = int(time_until.total_seconds() / 60) + 1
                    self.send_notification(
                        f"Upcoming Change: {item['activity']}",
                        f"In {mins} minutes: {item['activity']}"
                    )
                    self.notified_activities.add(activity_id)
            elif time_until > notification_threshold:
                # Reset notification if schedule changed or we are far away again
                self.notified_activities.discard(activity_id)
                
        self.after(30000, self.check_notifications)

    def send_notification(self, title, message, focus_window=True):
        """Send visible and audible notification."""
        # 1. Audible Alert
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except:
            pass
            
        # 2. System Notification
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Verint Tracker",
                timeout=5
            )
        except Exception as e:
            print(f"Notification failed: {e}")
            
        # 3. Flash Window / Bring to Front (Optional but helpful)
        if focus_window:
            self.deiconify()
            self.lift()
            self.attributes("-topmost", True)
            self.after(100, lambda: self.attributes("-topmost", False))

if __name__ == "__main__":
    app = ScheduleApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

