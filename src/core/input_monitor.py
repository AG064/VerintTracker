import keyboard
import threading
import time
import ctypes
from collections import deque

class InputMonitor:
    """
    Monitors keyboard and mouse input in the background.
    Calculates KPM (Keys Per Minute) and CPM (Clicks Per Minute).
    Uses hardware polling for mouse clicks to ensure capture in VDIs.
    """
    def __init__(self, stats_manager):
        self.stats_manager = stats_manager
        
        # Session totals (since app start)
        self.session_keys = 0
        self.session_clicks = 0
        self.session_start = time.time()
        self._session_restored = False
        
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
                self._session_restored = True
            else:
                self.session_start = time.time()
                self._session_restored = False

    def start(self):
        """Start input monitoring and periodic saving."""
        self.running = True
        self._stop_event.clear()
        
        # Only reset session start if NOT restored
        if not self._session_restored:
            self.session_start = time.time()
            
        self._last_save_time = time.time()
        
        # Start periodic save thread
        threading.Thread(target=self._periodic_save, daemon=True).start()
        
        # Start unified input polling thread (Robust for VDI/Omnissa)
        # Replaces keyboard.hook and separate mouse poller
        threading.Thread(target=self._input_poller, daemon=True).start()
        
    def stop(self):
        """Stop monitoring and save remaining stats."""
        self.running = False
        self._stop_event.set()
        
        # Save remaining data
        self._save_deltas()
            
    def _input_poller(self):
        """
        Polls keyboard and mouse using GetAsyncKeyState.
        This technique bypasses hook limitations in VDI environments (Citrix/Omnissa).
        """
        # Track state of all keys (0-255)
        # We start with all assuming False to detect initial presses correctly
        key_states = [False] * 256
        
        # Mouse VKs
        VK_LBUTTON = 0x01
        VK_RBUTTON = 0x02
        VK_MBUTTON = 0x04
        
        while self.running:
            try:
                start_time = time.time()
                
                # Iterate through relevant Virtual Key codes
                # 1-254 (0 is undefined, 255 is reserved)
                # Performance: 255 ctypes calls takes ~2-5ms usually.
                for vk in range(1, 255):
                    # Check if key is down (MSB set)
                    # GetAsyncKeyState returns short
                    state = ctypes.windll.user32.GetAsyncKeyState(vk)
                    is_down = (state & 0x8000) != 0
                    
                    # Rising Edge Detection (Pressed now, wasn't before)
                    if is_down and not key_states[vk]:
                        now = time.time()
                        
                        # Determine if Mouse or Keyboard
                        if vk in (VK_LBUTTON, VK_RBUTTON, VK_MBUTTON):
                            self.session_clicks += 1
                            with self._lock:
                                self._delta_clicks += 1
                                self._click_timestamps.append(now)
                        else:
                            # It's a key
                            self.session_keys += 1
                            with self._lock:
                                self._delta_keys += 1
                                self._key_timestamps.append(now)
                                
                    key_states[vk] = is_down
                    
                # Rate limiting to ~50Hz (20ms is granular enough for typing)
                elapsed = time.time() - start_time
                sleep_time = 0.02 - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                print(f"Input polling error: {e}")
                time.sleep(1)

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
