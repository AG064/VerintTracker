"""
Custom Schedule Parser Template

This file provides a template for creating a custom schedule parser
for your specific Verint page layout.

INSTRUCTIONS:
1. Run inspect_schedule.py to identify the HTML elements in your Verint page
2. Note the CSS selectors for time and activity elements
3. Copy this template to verint_tracker.py, replacing the parse_schedule() method
4. Customize the selectors and parsing logic below
"""

from datetime import datetime
from typing import List, Dict


def parse_schedule_template(page) -> List[Dict]:
    """
    Template for parsing Verint schedule.
    
    Customize this method based on your Verint page structure.
    
    Args:
        page: Playwright page object
        
    Returns:
        List of schedule items with format:
        [
            {
                "time": "14:00",
                "activity": "Break",
                "datetime": datetime object
            },
            ...
        ]
    """
    schedule_data = []
    
    try:
        # Wait for schedule to load
        page.wait_for_load_state("networkidle", timeout=10000)
        
        # EXAMPLE 1: Table-based schedule
        # If your schedule is in a table with rows
        """
        rows = page.query_selector_all("table.schedule tbody tr")
        for row in rows:
            time_cell = row.query_selector("td.time")
            activity_cell = row.query_selector("td.activity")
            
            if time_cell and activity_cell:
                time_text = time_cell.text_content().strip()
                activity_text = activity_cell.text_content().strip()
                
                # Parse time (adjust format as needed)
                activity_datetime = datetime.strptime(time_text, "%H:%M")
                activity_datetime = activity_datetime.replace(
                    year=datetime.now().year,
                    month=datetime.now().month,
                    day=datetime.now().day
                )
                
                schedule_data.append({
                    "time": time_text,
                    "activity": activity_text,
                    "datetime": activity_datetime
                })
        """
        
        # EXAMPLE 2: Div-based schedule with classes
        # If your schedule uses divs with specific classes
        """
        schedule_items = page.query_selector_all(".schedule-item")
        for item in schedule_items:
            time_elem = item.query_selector(".schedule-time")
            activity_elem = item.query_selector(".schedule-activity")
            
            if time_elem and activity_elem:
                time_text = time_elem.text_content().strip()
                activity_text = activity_elem.text_content().strip()
                
                # Convert time string to datetime
                try:
                    hour, minute = time_text.split(":")
                    activity_datetime = datetime.now().replace(
                        hour=int(hour),
                        minute=int(minute),
                        second=0,
                        microsecond=0
                    )
                    
                    schedule_data.append({
                        "time": time_text,
                        "activity": activity_text,
                        "datetime": activity_datetime
                    })
                except ValueError:
                    continue
        """
        
        # EXAMPLE 3: Using XPath
        # If CSS selectors don't work well
        """
        time_elements = page.locator("xpath=//span[@class='time']").all()
        activity_elements = page.locator("xpath=//span[@class='activity']").all()
        
        for time_elem, activity_elem in zip(time_elements, activity_elements):
            time_text = time_elem.text_content().strip()
            activity_text = activity_elem.text_content().strip()
            
            # Parse and add to schedule
            # ... (similar to above)
        """
        
        # EXAMPLE 4: JSON data in page
        # If schedule data is embedded as JSON in the page
        """
        script_content = page.evaluate('''
            () => {
                // Look for schedule data in window object or data attributes
                return window.scheduleData || [];
            }
        ''')
        
        for item in script_content:
            schedule_data.append({
                "time": item.get("time"),
                "activity": item.get("activity"),
                "datetime": datetime.fromisoformat(item.get("datetime"))
            })
        """
        
        # PLACEHOLDER: Add your custom parsing logic here
        # This is where you customize based on your Verint page
        
        # Example: Get all text from page and try to find patterns
        page_text = page.text_content("body")
        print("Page preview:", page_text[:500])  # Debug: print first 500 chars
        
        # TODO: Replace this with actual parsing logic for your page
        # The examples above show different approaches you can use
        
    except Exception as e:
        print(f"Error in custom parser: {e}")
    
    return schedule_data


# HELPER FUNCTIONS

def parse_time_to_datetime(time_str: str, date_ref: datetime = None) -> datetime:
    """
    Helper function to convert time string to datetime.
    
    Args:
        time_str: Time string like "14:30" or "2:30 PM"
        date_ref: Reference date to use (defaults to today)
    
    Returns:
        datetime object
    """
    if date_ref is None:
        date_ref = datetime.now()
    
    # Handle different time formats
    formats = [
        "%H:%M",           # 24-hour: "14:30"
        "%I:%M %p",        # 12-hour with AM/PM: "2:30 PM"
        "%H:%M:%S",        # 24-hour with seconds: "14:30:00"
        "%I:%M:%S %p",     # 12-hour with seconds and AM/PM: "2:30:00 PM"
    ]
    
    for time_format in formats:
        try:
            parsed_time = datetime.strptime(time_str.strip(), time_format)
            return date_ref.replace(
                hour=parsed_time.hour,
                minute=parsed_time.minute,
                second=0,
                microsecond=0
            )
        except ValueError:
            continue
    
    raise ValueError(f"Could not parse time string: {time_str}")


def extract_schedule_from_table(page, table_selector: str, 
                                time_column: int = 0, 
                                activity_column: int = 1) -> List[Dict]:
    """
    Helper function to extract schedule from HTML table.
    
    Args:
        page: Playwright page object
        table_selector: CSS selector for the table
        time_column: Index of column containing time (0-based)
        activity_column: Index of column containing activity
    
    Returns:
        List of schedule items
    """
    schedule_data = []
    
    try:
        rows = page.query_selector_all(f"{table_selector} tbody tr")
        
        for row in rows:
            cells = row.query_selector_all("td")
            
            if len(cells) > max(time_column, activity_column):
                time_text = cells[time_column].text_content().strip()
                activity_text = cells[activity_column].text_content().strip()
                
                try:
                    activity_datetime = parse_time_to_datetime(time_text)
                    
                    schedule_data.append({
                        "time": time_text,
                        "activity": activity_text,
                        "datetime": activity_datetime
                    })
                except ValueError as e:
                    print(f"Could not parse time '{time_text}': {e}")
                    continue
    
    except Exception as e:
        print(f"Error extracting from table: {e}")
    
    return schedule_data


# TESTING YOUR PARSER

def test_parser_locally():
    """
    Test your parser with a local HTML file.
    
    Save a copy of your Verint schedule page and test parsing without
    needing to log in repeatedly.
    """
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Load local HTML file for testing
        page.goto("file:///path/to/saved/verint/page.html")
        
        # Test your parser
        schedule = parse_schedule_template(page)
        
        print("Parsed schedule:")
        for item in schedule:
            print(f"  {item['time']} - {item['activity']}")
        
        browser.close()


if __name__ == "__main__":
    # Uncomment to test your parser
    # test_parser_locally()
    print("This is a template file. Copy the parse_schedule_template() function")
    print("to verint_tracker.py and customize it for your Verint page.")

