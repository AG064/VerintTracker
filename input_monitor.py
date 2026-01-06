from pynput import keyboard, mouse
import threading
import time
from collections import deque

class InputMonitor:
    """
    Monitors keyboard and mouse input in the background.
    Calculates KPM (Keys Per Minute) and CPM (Clicks Per Minute).
    Thread-safe implementation using locks for counter updates.
    """
    def __init__(self, stats_manager):
        self.stats_manager = stats_manager
        
        # Session totals (since app start)
        self.session_keys = 0
        self.session_clicks = 0
        self.session_start = time.time()
        
        # Rolling window for "Current" KPM/CPM (last 60 seconds)
        self._key_timestamps = deque()
        self._click_timestamps = deque()
        
        # Delta counters for saving to persistent storage
        self._delta_keys = 0
        self._delta_clicks = 0
        self._last_save_time = time.time()
        
        self.running = False
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        self.keyboard_listener = None
        self.mouse_listener = None
        
    def restore_session_state(self, keys, clicks, duration_seconds):
        """
        Restore session counters from persistent storage.
        Backdates session_start so that (now - start) approx equals duration_seconds.
        """
        with self._lock:
            self.session_keys = keys
            self.session_clicks = clicks
            # If we have previous duration, we treat 'start' as 'How long ago we would have started
            # to have this much duration', effectively ignoring the gap where app was closed.
            if duration_seconds > 0:
                self.session_start = time.time() - duration_seconds
            else:
                self.session_start = time.time()

    def start(self):
        """Start input monitoring and periodic saving."""
        self.running = True
        self._stop_event.clear()
        self.session_start = time.time()
        self._last_save_time = time.time()
        
        # Start listeners
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        
        self.keyboard_listener.start()
        self.mouse_listener.start()
        
        # Start periodic save thread
        threading.Thread(target=self._periodic_save, daemon=True).start()
        
    def stop(self):
        """Stop monitoring and save remaining stats."""
        self.running = False
        self._stop_event.set()
        
        # Save remaining data
        self._save_deltas()
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
            
    def on_press(self, key):
        """Callback for key press."""
        self.session_keys += 1
        now = time.time()
        with self._lock:
            self._delta_keys += 1
            self._key_timestamps.append(now)
            
    def on_click(self, x, y, button, pressed):
        """Callback for mouse click."""
        if pressed:
            self.session_clicks += 1
            now = time.time()
            with self._lock:
                self._delta_clicks += 1
                self._click_timestamps.append(now)
            
    def _save_deltas(self):
        """Save accumulated deltas to stats manager."""
        with self._lock:
            now = time.time()
            duration = now - self._last_save_time
            self._last_save_time = now
            
            k = self._delta_keys
            c = self._delta_clicks
            
            # Reset deltas
            self._delta_keys = 0
            self._delta_clicks = 0
        
        # Save to stats manager if there was activity
        if k > 0 or c > 0:
            self.stats_manager.update_activity(k, c, duration)

    def _periodic_save(self):
        """Save stats every minute."""
        while self.running:
            if self._stop_event.wait(60):
                break
            self._save_deltas()
            
    def get_session_kpm(self):
        """Calculate KPM for the current session (average)."""
        duration_min = (time.time() - self.session_start) / 60
        if duration_min < 0.01: return 0
        return int(self.session_keys / duration_min)
        
    def get_session_cpm(self):
        """Calculate Clicks Per Minute for the current session (average)."""
        duration_min = (time.time() - self.session_start) / 60
        if duration_min < 0.01: return 0
        return int(self.session_clicks / duration_min)

    def get_current_kpm(self):
        """Calculate KPM over the last 60 seconds (rolling window)."""
        now = time.time()
        cutoff = now - 60
        with self._lock:
            # Remove timestamps older than 60s
            while self._key_timestamps and self._key_timestamps[0] < cutoff:
                self._key_timestamps.popleft()
            return len(self._key_timestamps)

    def get_current_cpm(self):
        """Calculate CPM over the last 60 seconds (rolling window)."""
        now = time.time()
        cutoff = now - 60
        with self._lock:
            while self._click_timestamps and self._click_timestamps[0] < cutoff:
                self._click_timestamps.popleft()
            return len(self._click_timestamps)
