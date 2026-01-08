import customtkinter as ctk
import queue
import winsound
import json
import os
import sys
import time
import tkinter.messagebox as messagebox
from plyer import notification
from datetime import datetime, timedelta

# Core Logic
from src.core.stats_manager import StatsManager
from src.core.input_monitor import InputMonitor
from src.core.worker import TrackerWorker

# UI Components
from src.gui.theme import THEME
from src.gui.views.settings import SettingsView
from src.gui.views.stats import StatsView
from src.gui.views.cph import CPHTracker
from src.gui.views.welcome import WelcomeDialog

# Set theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ScheduleApp(ctk.CTk):
    """
    Main Application Window.
    """
    def __init__(self):
        super().__init__(fg_color=THEME["bg_dark"])
        
        self.title("Verint Schedule Tracker")
        self.geometry("900x800")
        
        # Icon Setup
        try:
            # Handle path for dev and PyInstaller
            base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "src", "gui", "assets", "icon.ico")
            
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            else:
                print(f"Icon not found at: {icon_path}")
        except Exception as e:
            print(f"Failed to load icon: {e}")
            
        # Initialize Core Managers
        self.stats_manager = StatsManager()
        self.input_monitor = InputMonitor(self.stats_manager)
        
        # Setup Worker Queues
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
        
        # Start Event Loops
        self.check_queue()
        self.check_notifications()
        
        # Check for first-time run
        self.after(200, self.check_first_run)
        
    def check_first_run(self):
        """Show welcome wizard if config doesn't exist."""
        # Check if config was essentially empty or file didn't exist (load_config handles reading file, 
        # but if file didn't exist self.config might be defaults or empty if I didn't save defaults)
        # Actually load_config creates empty dict if file not found.
        if not os.path.exists("config.json"):
            # Disable main window interaction temporarily
            # WelcomeDialog is modal so this is implicit
            self.welcome_dialog = WelcomeDialog(self, self.on_welcome_complete)

    def on_welcome_complete(self, new_config):
        """Called when Welcome Wizard finishes."""
        self.config = new_config
        
        # Apply new settings to live components
        if hasattr(self, 'cph_tracker'):
             target = float(new_config.get("target_cph", 7.5))
             self.cph_tracker.target_cph = target
             self.cph_tracker.seconds_per_ticket = int(3600 / target)
             self.cph_tracker.remaining_seconds = self.cph_tracker.seconds_per_ticket
             # Update info label
             ticket_time = self.cph_tracker.format_time(self.cph_tracker.seconds_per_ticket)
             self.cph_tracker.info_label.configure(text=f"Target: {target} CPH ({ticket_time} / ticket)")
             
        # Log status
        self.status_bar.configure(text="Setup complete. Ready to track.")

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
        self.tab_view = ctk.CTkTabview(self, fg_color=THEME["bg_dark"], text_color=THEME["text_primary"], 
                                      segmented_button_fg_color=THEME["bg_card"], 
                                      segmented_button_selected_color=THEME["accent"], 
                                      segmented_button_selected_hover_color=THEME["accent_hover"])
        self.tab_view.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        self.tab_dashboard = self.tab_view.add("Dashboard")
        self.tab_stats = self.tab_view.add("Statistics")
        self.tab_settings = self.tab_view.add("Settings")
        
        # --- Dashboard Tab ---
        self.setup_dashboard_tab()
        
        # --- Statistics Tab ---
        self.stats_view = StatsView(self.tab_stats, self.stats_manager)
        self.stats_view.configure(fg_color=THEME["bg_dark"]) # Patch bg
        self.stats_view.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Settings Tab ---
        self.settings_view = SettingsView(self.tab_settings, self)
        self.settings_view.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_dashboard_tab(self):
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
        self.schedule_frame = ctk.CTkScrollableFrame(self.tab_dashboard, label_text="Today's Schedule", label_font=("Roboto", 14, "bold"), 
                                                    label_fg_color=THEME["bg_card"], fg_color=THEME["bg_card"], corner_radius=15)
        self.schedule_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 15))
        self.schedule_frame.grid_columnconfigure(0, weight=1) # Ensure content expands
        
        # CPH Tracker
        target_cph = float(self.config.get("target_cph", 7.5))
        self.cph_tracker = CPHTracker(self.tab_dashboard, self, self.stats_manager, self.input_monitor, target_cph=target_cph)
        self.cph_tracker.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 15))
        
        # Footer
        self.footer_frame = ctk.CTkFrame(self.tab_dashboard, fg_color="transparent")
        self.footer_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))
        
        self.refresh_btn = ctk.CTkButton(self.footer_frame, text="Refresh Schedule", command=self.request_refresh, 
                                        fg_color="transparent", border_width=1, border_color=THEME["btn_secondary_border"], 
                                        text_color=THEME["text_secondary"], hover_color=THEME["active_row"])
        self.refresh_btn.pack(side="right")
        
        self.status_bar = ctk.CTkLabel(self.footer_frame, text="Initializing...", text_color=THEME["text_secondary"], font=("Roboto", 10))
        self.status_bar.pack(side="left")

    def start_worker(self):
        self.worker = TrackerWorker(self.command_queue, self.result_queue)
        self.worker.start()
        
        # Auto refresh timer
        self.after(60000, self.auto_refresh)

    def check_queue(self):
        """Check for messages from the worker thread."""
        try:
            # Limit processing to 5 messages per tick to avoid freezing the GUI
            for _ in range(5):
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
                    messagebox.showerror("Verint Tracker Error", str(data))
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
        # Debounce refresh requests (limit to once per 15 seconds)
        now = time.time()
        if hasattr(self, 'last_refresh_time') and (now - self.last_refresh_time < 15):
            print("Refresh request ignored (rate limit).")
            return
            
        self.last_refresh_time = now
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
            
            # If the activity is within the last minute, treating it as "now" avoids skipping it too early
            # But for scheduling, strict time usually matters.
            # We strictly check if it's in the future. 
            if dt > now and next_activity is None:
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
            
            # Column 1: Time
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
        elif shift_end and shift_end > now:
            self.next_activity_label.configure(text="Shift End")
            self.target_time = shift_end
        else:
            self.next_activity_label.configure(text="Shift Completed" if shift_end else "No upcoming activities")
            self.countdown_label.configure(text="--:--:--")
            if hasattr(self, 'target_time'):
                del self.target_time
        
        # Start countdown loop
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
        try:
            self.input_monitor.stop()
            self.command_queue.put(("stop", None))
        except:
            pass
        self.after(500, self.destroy)

    def check_notifications(self):
        """Check for upcoming schedule changes and notify."""
        if not self.current_schedule:
            self.after(30000, self.check_notifications)
            return

        now = datetime.now()
        minutes_before = self.config.get("notification_minutes_before", 5)
        notification_threshold = timedelta(minutes=minutes_before)
        
        for item in self.current_schedule:
            if 'datetime' not in item: continue
            
            dt = item['datetime']
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
                self.notified_activities.discard(activity_id)
                
        self.after(30000, self.check_notifications)

    def send_notification(self, title, message, focus_window=True):
        """Send visible and audible notification."""
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except:
            pass
            
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Verint Tracker",
                timeout=5
            ) # type: ignore # plyer has some type issues
        except Exception as e:
            print(f"Notification failed: {e}")
            
        if focus_window:
            try:
                self.deiconify()
                self.lift()
                self.attributes("-topmost", True)
                self.after(100, lambda: self.attributes("-topmost", False))
            except:
                pass

if __name__ == "__main__":
    app = ScheduleApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

