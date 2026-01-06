import re
import subprocess
import time
import json
from pathlib import Path
from typing import List, Dict, Optional
from dateutil import parser
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from datetime import datetime, timedelta

class VerintTracker:
    """
    Handles browser automation for Verint using Playwright.
    Includes robust process management to handle Edge browser instances.
    """
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.user_data_dir = Path("playwright-state").absolute()
        
        # Load config
        self.config = self._load_config()
        self.verint_url = self.config.get("verint_url", "https://verint.com/login") # Placeholder default
        self.headless = self.config.get("headless", False)

    def _load_config(self) -> dict:
        """Load configuration from config.json."""
        try:
            if Path("config.json").exists():
                with open("config.json", "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        return {}

    def _kill_stale_processes(self):
        """
        Kill only the Edge processes that are using our specific user data directory.
        This prevents interfering with the user's personal browser sessions.
        """
        data_dir_str = str(self.user_data_dir).replace("\\", "\\\\")
        
        # PowerShell command to find processes with command line arguments matching our data dir
        ps_command = f"""
        Get-CimInstance Win32_Process | 
        Where-Object {{ $_.Name -eq 'msedge.exe' -and $_.CommandLine -like '*{data_dir_str}*' }} | 
        ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}
        """
        
        try:
            subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
            time.sleep(1) # Give OS time to release locks
        except Exception as e:
            print(f"Warning: Failed to clean up processes: {e}")

    def start_browser(self):
        """Start the browser with persistent context."""
        self._kill_stale_processes()
        
        try:
            self.playwright = sync_playwright().start()
            
            # Launch persistent context
            # We use msedge channel to use the installed Edge browser
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                channel="msedge",
                headless=self.headless,
                # --no-sandbox is NOT used here to avoid the warning.
                # --test-type suppresses the "unsupported command-line flag" warning in some versions.
                # --disable-session-crashed-bubble prevents "Restore pages" popup which might cause multiple tabs
                # --disable-restore-session-state prevents restoring previous tabs
                args=["--start-maximized", "--disable-blink-features=AutomationControlled", "--test-type", "--disable-session-crashed-bubble", "--disable-restore-session-state"],
                viewport=None, # Allow window to size itself (disable viewport emulation)
                ignore_default_args=["--enable-automation"]
            )
            
            # Ensure we only have one page open (close extra tabs from restored session)
            # Wait loop to catch any delayed tab restorations
            print("DEBUG: Waiting for browser tabs to stabilize...")
            start_time = time.time()
            while time.time() - start_time < 5: # Wait up to 5 seconds
                pages = self.context.pages
                if len(pages) > 1:
                    print(f"DEBUG: Detected {len(pages)} pages, closing extras...")
                    # Keep the first page, close others
                    for p in pages[1:]:
                        try:
                            p.close()
                        except Exception as e:
                            print(f"DEBUG: Failed to close page: {e}")
                time.sleep(0.5)
            
            pages = self.context.pages
            print(f"DEBUG: Browser launched with {len(pages)} pages")
            
            if not pages:
                self.page = self.context.new_page()
            else:
                self.page = pages[0]
            
            self.page.bring_to_front()
            self.page.set_default_timeout(30000)
            
        except Exception as e:
            print(f"Failed to start browser: {e}")
            self.cleanup()
            raise

    def navigate_to_verint(self) -> bool:
        """
        Navigate to Verint and check if login is successful.
        Returns True if on schedule page, False if login is required.
        """
        if not self.page:
            return False
            
        try:
            # Only navigate if a URL is provided
            if self.verint_url and self.verint_url.strip():
                self.page.goto(self.verint_url)
                self.page.wait_for_load_state("networkidle")
            else:
                # If no URL, just wait a bit for page to be ready
                try:
                    self.page.wait_for_load_state("domcontentloaded", timeout=5000)
                except:
                    pass
            
            # Check for common login indicators
            if "login" in self.page.url.lower() or self.page.locator("input[type='password']").count() > 0:
                return False
                
            # Check for schedule indicators
            if self.page.locator("text=My Schedule").count() > 0 or \
               self.page.locator(".schedule-container").count() > 0:
                return True
                
            # Ambiguous state, assume success if not on login page? 
            # Safer to return False if unsure, but for now let's assume if no login fields, we might be in.
            return True
            
        except Exception as e:
            print(f"Navigation error: {e}")
            return False

    def parse_schedule(self) -> List[Dict]:
        """
        Attempt to parse the schedule from the current page.
        Tries multiple strategies: Table parsing, Text parsing, Frame parsing.
        """
        # Check if manual file mode is enabled in config
        if self.config.get("use_manual_file", False):
            manual_items = self._parse_strategy_manual_file()
            if manual_items:
                return self._clean_items(manual_items)
            return []

        if not self.page:
            return []

        strategies = [
            self._parse_strategy_table,
            self._parse_strategy_text_content,
            self._parse_strategy_frames
        ]
        
        for strategy in strategies:
            try:
                items = strategy()
                if items:
                    return self._clean_items(items)
            except Exception as e:
                # print(f"Strategy {strategy.__name__} failed: {e}")
                continue
                
        return []

    def _parse_strategy_table(self) -> List[Dict]:
        """Strategy 1: Look for standard HTML tables."""
        items = []
        # Try generic table if specific class not found
        rows = self.page.locator("table tr").all()
        print(f"DEBUG: Found {len(rows)} table rows")
        
        for row in rows:
            cols = row.locator("td").all()
            # Screenshot shows 4 columns: Time, Activity Type, Activity, Duration
            if len(cols) >= 3:
                time_text = cols[0].inner_text().strip()
                # Activity is in 3rd column based on screenshot
                activity_text = cols[2].inner_text().strip()
                
                # Handle date format from screenshot: 12/27/2025 6:00 AM
                if self._is_valid_time(time_text):
                    items.append({"time": time_text, "activity": activity_text})
        
        print(f"DEBUG: Found {len(items)} items via table strategy")
        return items

    def _parse_strategy_frames(self) -> List[Dict]:
        """Strategy 3: Check inside iframes using the robust text strategy."""
        items = []
        print(f"DEBUG: Checking {len(self.page.frames)} frames")
        
        for i, frame in enumerate(self.page.frames):
            try:
                # Skip detached frames
                if frame.is_detached(): continue
                
                # Try to get text content
                try:
                    text = frame.inner_text("body")
                except:
                    try:
                        text = frame.content()
                    except:
                        continue
                
                if len(text) < 100: continue # Skip empty frames
                
                print(f"DEBUG: Frame {i} text length: {len(text)}")
                
                # Use the same logic as text strategy but on frame content
                frame_items = self._extract_items_from_text(text)
                if frame_items:
                    print(f"DEBUG: Found {len(frame_items)} items in frame {i}")
                    items.extend(frame_items)
            except Exception as e:
                print(f"DEBUG: Error parsing frame {i}: {e}")
                continue
                
        return items

    def _parse_strategy_text_content(self) -> List[Dict]:
        """Strategy 2: Regex search on visible text content."""
        # Use inner_text to get visible text, which is cleaner than HTML content
        try:
            text = self.page.inner_text("body")
        except:
            text = self.page.content()
            
        print(f"DEBUG: Page text length: {len(text)}")
        return self._extract_items_from_text(text)

    def _extract_items_from_text(self, text: str) -> List[Dict]:
        """Helper to extract items from text using regex."""
        items = []
        seen = set()
        
        # Split into lines to handle the row-based structure better
        lines = text.split('\n')
        
        # Regex to match the line structure:
        # Date Time (Group 1) ... Activity (Group 2) ... Duration
        # Example: 12/27/2025 12:45 PM	Assigned Work Activities 	2K Games-Email-EN_3057328	1:50
        
        # Pattern breakdown:
        # 1. Start with Date Time: (\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM))
        # 2. Followed by anything (Activity Type): .*?
        # 3. Capture Activity (non-whitespace or with underscores): ([A-Za-z0-9\-_]+(?:_[0-9]+)?)
        # 4. Followed by Duration at the end: \s+(\d{1,2}:\d{2})
        
        pattern = r"(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM))\s+.*?\s+([A-Za-z0-9\-_]+(?:_[0-9]+)?)\s+(\d{1,2}:\d{2})"
        
        today_str = datetime.now().strftime("%m/%d/%Y")
        # Remove leading zero from month/day if needed to match format (e.g. 12/27/2025 vs 12/27/2025)
        # Actually regex handles 1 or 2 digits, so we just need to check if the date part matches today
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            matches = re.findall(pattern, line)
            for time_str, activity, duration in matches:
                # Filter for today only
                if today_str not in time_str and datetime.now().strftime("%-m/%-d/%Y") not in time_str:
                    continue

                # Clean up time string
                try:
                    dt = parser.parse(time_str)
                    time_only = dt.strftime("%I:%M %p").lstrip("0")
                except:
                    time_only = time_str
                    
                key = f"{time_only}-{activity.strip()}"
                if key not in seen:
                    items.append({
                        "time": time_only, 
                        "activity": activity.strip(),
                        "duration": duration
                    })
                    seen.add(key)
        
        return items

    def _parse_strategy_manual_file(self) -> List[Dict]:
        """Fallback: Read from a local file (useful for debugging)."""
        try:
            if Path("manual_schedule.txt").exists():
                with open("manual_schedule.txt", "r") as f:
                    content = f.read()
                    pattern = r"(\d{1,2}:\d{2}\s*(?:AM|PM))\s+([A-Za-z\s\-]+)"
                    matches = re.findall(pattern, content)
                    return [{"time": t, "activity": a.strip()} for t, a in matches]
        except:
            pass
        return []

    def _is_valid_time(self, time_str: str) -> bool:
        try:
            parser.parse(time_str)
            return True
        except:
            return False

    def _clean_items(self, items: List[Dict]) -> List[Dict]:
        """Post-process items to add datetime objects and sort."""
        cleaned = []
        today = datetime.now().date()
        
        for item in items:
            try:
                dt = parser.parse(item['time'])
                # Combine with today's date
                full_dt = datetime.combine(today, dt.time())
                item['datetime'] = full_dt
                cleaned.append(item)
            except:
                continue
                
        return sorted(cleaned, key=lambda x: x['datetime'])

    def cleanup(self):
        """Close browser and playwright."""
        if self.context:
            try:
                self.context.close()
            except:
                pass
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass
        self.page = None
        self.context = None
        self.playwright = None
