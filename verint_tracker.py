#!/usr/bin/env python3
"""
Verint Schedule Tracker

This application monitors your Verint schedule and sends notifications
5 minutes before you need to change activities.
"""

import json
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

try:
    from playwright.sync_api import sync_playwright, Browser, Page
    from plyer import notification
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: pip install -r requirements.txt")
    print("Then run: playwright install msedge")
    sys.exit(1)


class VerintTracker:
    """Main class for tracking Verint schedule and sending notifications."""
    
    # Configuration constants for timing
    PAGE_LOAD_WAIT_SECONDS = 5
    PAGE_REFRESH_WAIT_SECONDS = 2
    ERROR_RETRY_WAIT_SECONDS = 30
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the tracker with configuration."""
        self.config = self._load_config(config_path)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.last_notification_time: Optional[datetime] = None
        self.current_schedule: List[Dict] = []
        self.notified_activities: set = set()  # Track notified activities to prevent duplicates
        self.consecutive_parse_failures: int = 0  # Track parsing failures
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Configuration file '{config_path}' not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in configuration file '{config_path}'.")
            sys.exit(1)
    
    def start_browser(self):
        """Start the browser with persistent context for Microsoft account."""
        print("Starting Microsoft Edge browser...")
        self.playwright = sync_playwright().start()
        
        # Use persistent context to maintain Microsoft account login
        user_data_dir = Path("playwright-state")
        user_data_dir.mkdir(exist_ok=True)
        
        try:
            # Launch Edge with persistent context
            # Use headless mode from config if specified, otherwise default to False for initial login
            headless = self.config.get("headless", False)
            browser_channel = self.config.get("browser_type", "msedge")
            
            self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=headless,
                channel=browser_channel
            )
            self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
            print("Browser started successfully.")
        except Exception as e:
            print(f"Error starting browser: {e}")
            print("Make sure Microsoft Edge is installed and run: playwright install msedge")
            sys.exit(1)
    
    def navigate_to_verint(self):
        """Navigate to Verint schedule page."""
        print("Navigating to Verint...")
        try:
            self.page.goto(self.config["verint_url"], timeout=60000)
            time.sleep(self.PAGE_LOAD_WAIT_SECONDS)  # Wait for page to fully load
            
            # Check if login is required
            if "login" in self.page.url.lower() or "signin" in self.page.url.lower():
                print("\n" + "="*60)
                print("MANUAL LOGIN REQUIRED")
                print("="*60)
                print("Please log in to your Microsoft account in the browser window.")
                print("After logging in successfully, press Enter to continue...")
                print("="*60 + "\n")
                input()
                
                # Navigate again after login
                self.page.goto(self.config["verint_url"], timeout=60000)
                time.sleep(self.PAGE_LOAD_WAIT_SECONDS)
            
            print("Successfully navigated to Verint.")
        except Exception as e:
            print(f"Error navigating to Verint: {e}")
            raise
    
    def parse_schedule(self) -> List[Dict]:
        """Parse the schedule from the Verint page."""
        try:
            # Wait for the schedule content to load
            self.page.wait_for_load_state("networkidle", timeout=10000)
            
            # This is a placeholder - actual implementation would need to
            # inspect the Verint page structure and extract schedule data
            # For now, we'll look for common schedule elements
            
            schedule_data = []
            
            # Try to find schedule elements (this will need customization based on actual page structure)
            try:
                # Look for time-based elements
                time_elements = self.page.query_selector_all("[class*='time'], [class*='schedule'], [class*='activity']")
                
                if time_elements:
                    print(f"Found {len(time_elements)} potential schedule elements.")
                    # TODO: Parse actual schedule from page elements
                    # This requires customization based on your Verint page structure
                    # See parser_template.py for examples
                
            except Exception as e:
                print(f"Note: Could not parse schedule automatically: {e}")
                print("You may need to customize the schedule parsing for your specific Verint page.")
            
            return schedule_data
            
        except Exception as e:
            print(f"Error parsing schedule: {e}")
            return []
    
    def check_for_upcoming_changes(self, schedule: List[Dict]):
        """Check if any activity changes are coming up soon."""
        if not schedule:
            return
        
        now = datetime.now()
        notification_threshold = timedelta(minutes=self.config["notification_minutes_before"])
        
        for item in schedule:
            if "datetime" not in item:
                continue
                
            activity_time = item["datetime"]
            
            # Handle midnight boundary: if activity time appears to be in the past but within 12 hours,
            # it's likely tomorrow's schedule
            if activity_time < now and (now - activity_time) > timedelta(hours=12):
                activity_time = activity_time + timedelta(days=1)
                item["datetime"] = activity_time
            
            time_until = activity_time - now
            
            # Create unique identifier for this activity
            activity_id = f"{item['time']}_{item['activity']}"
            
            # Check if we should notify
            if timedelta(0) < time_until <= notification_threshold:
                # Don't send duplicate notifications for the same activity
                if activity_id not in self.notified_activities:
                    self.send_notification(
                        f"Change to: {item['activity']}",
                        f"At {item['time']}, change your status to {item['activity']}\n"
                        f"({int(time_until.total_seconds() / 60)} minutes remaining)"
                    )
                    self.last_notification_time = now
                    self.notified_activities.add(activity_id)
            elif time_until > notification_threshold:
                # Remove from notified set if we're now far from the activity time
                # This allows re-notification if schedule is updated
                self.notified_activities.discard(activity_id)
    
    def send_notification(self, title: str, message: str):
        """Send a desktop notification."""
        print(f"\n{'='*60}")
        print(f"NOTIFICATION: {title}")
        print(f"{message}")
        print(f"{'='*60}\n")
        
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Verint Tracker",
                timeout=10
            )
        except Exception as e:
            print(f"Note: Could not send desktop notification: {e}")
            print("Notification printed to console instead.")
    
    def run(self):
        """Main run loop for the tracker."""
        try:
            print("\n" + "="*60)
            print("Verint Schedule Tracker")
            print("="*60 + "\n")
            
            self.start_browser()
            self.navigate_to_verint()
            
            print("\nStarting monitoring loop...")
            print(f"Checking every {self.config['check_interval_seconds']} seconds.")
            print(f"Notifications will be sent {self.config['notification_minutes_before']} minutes before changes.")
            print("Press Ctrl+C to stop.\n")
            
            # Implement smarter refresh strategy to avoid excessive page loads
            last_reload_time = time.time()
            check_interval = self.config['check_interval_seconds']
            # Reload page every 5 check intervals or at least every 5 minutes
            reload_interval = max(check_interval * 5, 300)
            
            while True:
                try:
                    current_time = time.time()
                    
                    # Refresh the page only if reload interval has elapsed
                    if current_time - last_reload_time >= reload_interval:
                        self.page.reload(timeout=60000)
                        time.sleep(self.PAGE_REFRESH_WAIT_SECONDS)
                        last_reload_time = current_time
                    
                    # Parse current schedule
                    schedule = self.parse_schedule()
                    
                    if schedule:
                        self.consecutive_parse_failures = 0
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Schedule updated. Next activities:")
                        for item in schedule[:3]:  # Show next 3 items
                            print(f"  - {item['time']}: {item['activity']}")
                        
                        # Check for upcoming changes
                        self.check_for_upcoming_changes(schedule)
                    else:
                        self.consecutive_parse_failures += 1
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] No schedule data found.")
                        
                        if self.consecutive_parse_failures >= 5:
                            print("\n" + "!"*60)
                            print("WARNING: Parser has failed 5 times consecutively.")
                            print("The schedule parser likely needs customization for your Verint page.")
                            print("  1. Run the 'inspect_schedule.py' script to identify HTML elements.")
                            print("  2. Edit parse_schedule() method in verint_tracker.py")
                            print("  3. See parser_template.py for examples")
                            print("!"*60 + "\n")
                            self.consecutive_parse_failures = 0  # Reset to avoid spam
                    
                    # Wait before next check
                    time.sleep(self.config["check_interval_seconds"])
                    
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    print(f"Error in monitoring loop: {e}")
                    print(f"Retrying in {self.ERROR_RETRY_WAIT_SECONDS} seconds...")
                    time.sleep(self.ERROR_RETRY_WAIT_SECONDS)
        
        except KeyboardInterrupt:
            print("\n\nStopping tracker...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                # Best-effort cleanup: ignore any errors when closing the browser
                pass
        
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                # Best-effort cleanup: ignore any errors when stopping Playwright
                pass
        
        print("Tracker stopped.")


def main():
    """Main entry point."""
    tracker = VerintTracker()
    tracker.run()


if __name__ == "__main__":
    main()

