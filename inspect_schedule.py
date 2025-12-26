#!/usr/bin/env python3
"""
Schedule Parser Inspector

This helper script opens your Verint page and helps you identify
the HTML elements needed to parse your schedule.
"""

import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: Playwright not installed.")
    print("Please run: pip install playwright")
    sys.exit(1)


def inspect_verint_page(url: str):
    """Open Verint and inspect the page structure."""
    print("Opening Verint page for inspection...")
    print("\nInstructions:")
    print("1. The browser will open to your Verint schedule")
    print("2. Open browser DevTools (F12)")
    print("3. Use the element picker to inspect schedule items")
    print("4. Look for patterns in class names, IDs, or structure")
    print("5. Note the selectors you need to extract:")
    print("   - Time information")
    print("   - Activity names")
    print("   - Any grouping containers")
    print("\nPress Enter when ready to start...")
    input()
    
    playwright = sync_playwright().start()
    
    try:
        user_data_dir = Path("playwright-state")
        user_data_dir.mkdir(exist_ok=True)
        
        browser = playwright.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            channel="msedge",
            devtools=True  # Open DevTools automatically
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        print("\nNavigating to Verint...")
        page.goto(url, timeout=60000)
        
        print("\nPage loaded! Inspect the elements in DevTools.")
        print("Press Enter when you're done inspecting...")
        input()
        
        # Print some basic page info
        print("\n" + "="*60)
        print("Page Information:")
        print("="*60)
        print(f"Title: {page.title()}")
        print(f"URL: {page.url}")
        
        # Try to find some common elements
        print("\n" + "="*60)
        print("Found Elements (sample):")
        print("="*60)
        
        selectors_to_try = [
            "table", "tbody", "tr", "td",
            "[class*='schedule']", "[class*='time']", "[class*='activity']",
            "[class*='shift']", "[class*='event']",
            ".schedule", ".time", ".activity"
        ]
        
        for selector in selectors_to_try:
            elements = page.query_selector_all(selector)
            if elements:
                print(f"\n'{selector}': Found {len(elements)} element(s)")
                if len(elements) <= 5:
                    for i, elem in enumerate(elements[:5]):
                        try:
                            text = elem.text_content()[:100]
                            print(f"  [{i}]: {text}")
                        except Exception:
                            # Some elements may not expose text content or may error; skip these
                            pass
        
        print("\n" + "="*60)
        print("Inspection complete!")
        print("="*60)
        
        browser.close()
        
    finally:
        playwright.stop()


def main():
    """Main entry point."""
    import json
    
    # Try to load URL from config
    try:
        with open("config.json", 'r') as f:
            config = json.load(f)
            url = config.get("verint_url")
    except (OSError, json.JSONDecodeError):
        url = None
    
    if not url:
        print("Enter your Verint schedule URL:")
        url = input().strip()
        
        if not url:
            print("Error: No URL provided")
            sys.exit(1)
    
    inspect_verint_page(url)


if __name__ == "__main__":
    main()

