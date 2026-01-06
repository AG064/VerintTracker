import customtkinter as ctk
import winsound
import keyboard
from datetime import datetime
from ..theme import THEME

class CPHTracker(ctk.CTkFrame):
    """
    Frame for the CPH (Contacts Per Hour) Pacing Timer.
    Tracks time per ticket and calculates session statistics.
    """
    def __init__(self, master, app_instance, stats_manager, input_monitor, target_cph=7.5):
        super().__init__(master, fg_color=THEME["bg_card"], corner_radius=15)
        self.app = app_instance
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
        
        # Totals Display
        self.input_totals_label = ctk.CTkLabel(self, text="Keys: 0 | Clicks: 0", font=("Roboto", 10), text_color=THEME["text_secondary"])
        self.input_totals_label.grid(row=6, column=0, columnspan=2, pady=(0, 5))
        
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
        self.start_btn.grid(row=7, column=0, columnspan=2, padx=20, pady=(10, 10), sticky="ew")
        
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
        self.reply_btn.grid(row=8, column=0, padx=(20, 5), pady=(0, 15), sticky="ew")

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
        self.noreply_btn.grid(row=8, column=1, padx=(5, 20), pady=(0, 15), sticky="ew")
        
        self.hotkey_label = ctk.CTkLabel(self, text="Hotkey: Numpad Minus (-) = Reply", text_color=THEME["text_secondary"], font=("Roboto", 10))
        self.hotkey_label.grid(row=9, column=0, columnspan=2, pady=(0, 10))
        
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
                # Access main app via explicit reference
                self.app.send_notification(
                    "Ticket Completed", 
                    "Ticket logged successfully.", 
                    focus_window=False
                )
            except Exception as e:
                print(f"Failed to send notification: {e}")

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
        
        # Totals
        total_keys = self.input_monitor.session_keys
        total_clicks = self.input_monitor.session_clicks
        
        self.input_stats_label.configure(text=f"KPM: {curr_kpm} (Avg: {avg_kpm}) | CPM: {curr_cpm} (Avg: {avg_cpm})")
        
        # Update Totals Label if it exists (it should now)
        if hasattr(self, 'input_totals_label'):
            self.input_totals_label.configure(text=f"Total: {total_keys} Keys | {total_clicks} Click")
        
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
                        self.winfo_toplevel().deiconify() # Try to reach root window to bring to front
                        self.winfo_toplevel().lift()
                    except:
                        pass
            
            # Update stats every second while running
            self.update_stats_display()
            
            self.after(1000, self.count_down)
