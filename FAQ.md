# Frequently Asked Questions (FAQ)

## General Questions

### Q: What is Verint Tracker?
**A:** Verint Tracker is an automated desktop application that monitors your Verint work schedule and sends you notifications before you need to change your activity status. It helps ensure you never miss a status change.

### Q: Does this work with any version of Verint?
**A:** The tracker is designed to work with Verint WFM (Workforce Management) accessed through a web browser. The schedule parsing may need customization for different Verint versions or configurations.

### Q: Is this an official Verint application?
**A:** No, this is an independent, open-source tool created to help users track their Verint schedules. It is not affiliated with or endorsed by Verint.

## Installation & Setup

### Q: What operating systems are supported?
**A:** Windows, Linux, and macOS are all supported. The application uses Python which is cross-platform.

### Q: Do I need to install Microsoft Edge?
**A:** Yes, the tracker uses Microsoft Edge because Verint requires a Microsoft account login, and Edge provides the best integration for Microsoft authentication.

### Q: Can I use a different browser?
**A:** Yes. You can select between **Microsoft Edge** and **Google Chrome** in the **Settings** tab of the application.

### Q: What Python version do I need?
**A:** Python 3.7 or higher is required. Python 3.8+ is recommended.

## Usage

### Q: Does the browser need to stay open?
**A:** Yes, the browser window should remain open (though it can be in the background) for the tracker to monitor your schedule.

### Q: Can I run this on a work computer?
**A:** Check with your IT department first. The application:
- Doesn't modify Verint
- Only reads schedule information
- Doesn't intercept or store credentials
- Uses standard browser automation

However, some organizations have policies against browser automation tools.

### Q: How much CPU/memory does it use?
**A:** Minimal resources:
- Browser: ~100-200MB RAM (similar to having Verint open normally)
- Python script: ~20-50MB RAM
- CPU: Very low, only checks schedule every 60 seconds

### Q: Will it work if my computer goes to sleep?
**A:** No, the tracker needs your computer to be awake to function. The browser will lose connection if the computer sleeps. Consider adjusting power settings if you need continuous monitoring.

### Q: Can I run multiple instances?
**A:** Not recommended. Running multiple instances may cause conflicts with the browser session. One instance per user is sufficient.

## Notifications

### Q: I'm not receiving notifications. What should I check?
**A:**
1. Check your operating system's notification settings
2. Ensure Python/Terminal has notification permissions
3. Look for notifications in the console output as a fallback
4. On Windows, check Action Center settings
5. On Mac, check System Preferences > Notifications
6. On Linux, ensure you have a notification daemon (like dunst)

### Q: Can I change the notification sound?
**A:** The default notification uses your system's notification sound. To customize, you'd need to modify the `send_notification()` method in `verint_tracker.py` to use a different notification library that supports custom sounds.

### Q: Can I get notifications on my phone?
**A:** Not directly. The app sends desktop notifications only. However, you could:
- Use a service like Pushbullet or Join to mirror desktop notifications to your phone
- Modify the code to integrate with a mobile notification service

### Q: How often can notifications appear?
**A:** The app has a 1-minute cooldown between notifications to prevent spam. Once you're notified about an upcoming change, you won't get another notification for that same change.

## Customization

### Q: The schedule isn't parsing correctly. What do I do?
**A:**
1. Run `python3 inspect_schedule.py` to inspect your Verint page
2. Use browser DevTools (F12) to identify the HTML elements containing schedule data
3. Modify the `parse_schedule()` method in `verint_tracker.py` with the correct selectors
4. Refer to USAGE_GUIDE.md for detailed instructions

### Q: Can I change how far in advance I'm notified?
**A:** Yes! Edit `config.json` and change `notification_minutes_before` to your preferred value (e.g., 10 for 10 minutes before).

### Q: Can I track multiple Verint accounts?
**A:** Not with a single instance. You would need to:
- Create separate directories for each account
- Modify the code to use different browser profiles
- Run separate instances for each account

## Troubleshooting

### Q: I get "Error: Required packages not installed"
**A:** Run the setup script:
- Windows: `setup.bat`
- Linux/Mac: `bash setup.sh`

Or manually: `pip install -r requirements.txt && python -m playwright install msedge`

### Q: The browser shows "Page not found" or "Access denied"
**A:**
1. Verify your Verint URL in `config.json` is correct
2. Try accessing the URL manually in Edge
3. Ensure your Microsoft account has access to Verint
4. Check if your organization requires VPN access

### Q: "Error starting browser: msedge not found"
**A:** Run: `python -m playwright install msedge`

This downloads the browser driver needed for automation.

### Q: My session keeps expiring
**A:** 
- This is usually due to Microsoft's security policies
- You may need to re-login periodically
- Delete the `playwright-state` folder and restart to force a fresh login
- Check if your organization has short session timeout policies

### Q: The app is showing old schedule data
**A:** 
- The page is refreshed every check interval (default 60 seconds)
- Try reducing `check_interval_seconds` in `config.json`
- Ensure your internet connection is stable
- Check if Verint itself is updating properly

## Privacy & Security

### Q: Is my password stored anywhere?
**A:** No. Your credentials are handled by Microsoft Edge's native authentication. The tracker never sees or stores your password.

### Q: What data is stored on my computer?
**A:** Only browser session data (cookies, cache) in the `playwright-state` folder. This is similar to what any browser stores when you stay logged in.

### Q: Can someone access my Verint account through this app?
**A:** Only if they have physical access to your computer while the app is running. The same risk exists with having Verint open in your browser normally.

### Q: Should I delete `playwright-state` folder?
**A:** Only if you want to log out completely. Keeping it allows you to stay logged in between runs.

### Q: Is this app safe to use?
**A:** Yes, the code is open source and you can review it. The app:
- Doesn't send data to external servers
- Doesn't modify your Verint account
- Only reads schedule information
- Uses standard, well-maintained libraries (Playwright, Plyer)

## Development

### Q: Can I contribute to this project?
**A:** Yes! This is an open-source project. Feel free to:
- Report issues
- Submit pull requests
- Suggest improvements
- Share your customizations

### Q: How do I modify the notification format?
**A:** Edit the `send_notification()` method in `verint_tracker.py` to change the title/message format.

### Q: Can I add email notifications instead of desktop notifications?
**A:** Yes, you can modify the `send_notification()` method to send emails using Python's `smtplib` library.

### Q: How do I add logging?
**A:** Add Python's `logging` module to track app behavior:
```python
import logging
logging.basicConfig(filename='verint_tracker.log', level=logging.INFO)
```

## Platform-Specific

### Q: Does this work on Windows 11?
**A:** Yes, fully supported.

### Q: Does this work with WSL (Windows Subsystem for Linux)?
**A:** You can run the Python script in WSL, but the browser window will open in Windows, and notifications may need special configuration.

### Q: Does this work on Mac with M1/M2 chips?
**A:** Yes, Playwright supports Apple Silicon. Just ensure you install the ARM64 version of Python.

### Q: Can I run this on a Raspberry Pi?
**A:** Technically possible but not recommended due to limited resources. Edge may not be available, you'd need to use Chromium instead.

