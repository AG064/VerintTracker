#!/usr/bin/env python3
"""
Quick test script to verify the installation and configuration.
"""

import json

def check_dependencies():
    """Check if required packages are installed."""
    print("Checking dependencies...")
    
    try:
        import playwright
        print("✓ Playwright installed")
    except ImportError:
        print("✗ Playwright not installed - run: pip install -r requirements.txt")
        return False
    
    try:
        import plyer
        print("✓ Plyer installed")
    except ImportError:
        print("✗ Plyer not installed - run: pip install -r requirements.txt")
        return False
    
    try:
        import dateutil
        print("✓ Python-dateutil installed")
    except ImportError:
        print("✗ Python-dateutil not installed - run: pip install -r requirements.txt")
        return False
    
    return True


def check_config():
    """Check if configuration file exists and is valid."""
    print("\nChecking configuration...")
    
    try:
        with open("config.json", 'r') as f:
            config = json.load(f)
        print("✓ Configuration file found and valid")
        
        required_keys = ["verint_url", "notification_minutes_before", "check_interval_seconds"]
        for key in required_keys:
            if key in config:
                print(f"  ✓ {key}: {config[key]}")
            else:
                print(f"  ✗ Missing required key: {key}")
                return False
        
        return True
    except FileNotFoundError:
        print("✗ Configuration file 'config.json' not found")
        return False
    except json.JSONDecodeError:
        print("✗ Configuration file has invalid JSON")
        return False


def test_notification():
    """Test if notifications work."""
    print("\nTesting notifications...")
    
    try:
        from plyer import notification
        notification.notify(
            title="Verint Tracker Test",
            message="If you see this, notifications are working!",
            app_name="Verint Tracker Test",
            timeout=5
        )
        print("✓ Test notification sent")
        print("  (Check if you received a desktop notification)")
        return True
    except Exception as e:
        print(f"✗ Notification test failed: {e}")
        return False


def main():
    """Run all checks."""
    print("="*60)
    print("Verint Tracker - Installation Verification")
    print("="*60 + "\n")
    
    all_passed = True
    
    if not check_dependencies():
        all_passed = False
    
    if not check_config():
        all_passed = False
    
    if not test_notification():
        all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ All checks passed! You're ready to run the tracker.")
        print("\nStart the tracker with: python verint_tracker.py")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nRefer to README.md for setup instructions.")
    print("="*60)


if __name__ == "__main__":
    main()

