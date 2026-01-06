import threading
import queue
from .verint_tracker import VerintTracker

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
            self.result_queue.put(("error", str(e)))
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
