# Verint Tracker - Usage Guide

## Quick Start

### Windows
1. Open Command Prompt or PowerShell in the project directory
2. Run: `setup.bat`
3. After installation, run: `python verint_tracker.py`

### Linux/Mac
1. Open Terminal in the project directory
2. Run: `bash setup.sh`
3. After installation, run: `python3 verint_tracker.py`

## First Run

When you run the tracker for the first time:

1. **Browser Opens**: Microsoft Edge will open automatically
2. **Login Prompt**: If not logged in, you'll be asked to log in to your Microsoft account
3. **Navigation**: The browser will navigate to your Verint schedule page
4. **Monitoring Starts**: The app will begin checking your schedule every 60 seconds

## Understanding the Console Output

The tracker provides real-time information in the console:

```
[13:45:30] Schedule updated. Next activities:
  - 13:50: Available
  - 14:00: Break
  - 14:15: Available
```

When a change is approaching (5 minutes before), you'll see:

```
============================================================
NOTIFICATION: Change to: Break
At 14:00, change your status to Break
(5 minutes remaining)
============================================================
```

## Notifications

Desktop notifications appear automatically:
- **Title**: "Change to: [Activity Name]"
- **Message**: Time and activity details
- **Timing**: 5 minutes before the change (configurable)

## Customizing the Configuration

Edit `config.json` to adjust settings:

### Change Notification Timing
```json
{
  "notification_minutes_before": 10
}
```
This will notify you 10 minutes before instead of 5.

### Change Check Frequency
```json
{
  "check_interval_seconds": 30
}
```
This will check the schedule every 30 seconds instead of 60.

### Update Verint URL
If your Verint URL changes:
```json
{
  "verint_url": "https://your-new-verint-url.com/..."
}
```

## Advanced: Customizing Schedule Parsing

If the default schedule parser doesn't work with your Verint page:

1. **Inspect Your Page**:
   ```bash
   python3 inspect_schedule.py
   ```
   This opens your Verint page with DevTools to help identify HTML elements.

2. **Identify Selectors**:
   - Look for elements containing time information
   - Look for elements containing activity names
   - Note class names, IDs, or tag patterns

3. **Modify the Parser**:
   - Open `verint_tracker.py`
   - Find the `parse_schedule()` method (around line 83)
   - Update the selectors to match your page

Example modification:
```python
# Replace the placeholder parsing with real selectors
time_elements = self.page.query_selector_all(".schedule-time")
activity_elements = self.page.query_selector_all(".schedule-activity")

for time_elem, activity_elem in zip(time_elements, activity_elements):
    time_text = time_elem.text_content()
    activity_text = activity_elem.text_content()
    # Parse and add to schedule_data
```

## Troubleshooting

### "Browser doesn't open"
- Verify Microsoft Edge is installed
- Run: `playwright install msedge`
- Check that you're running as a user with GUI access

### "Schedule not parsing correctly"
- The default parser is a template and may need customization
- Run `python3 inspect_schedule.py` to identify correct selectors
- Modify the `parse_schedule()` method in `verint_tracker.py`

### "No notifications appearing"
- Check system notification settings
- Ensure Python has permission to show notifications
- Notifications also print to console as a fallback

### "Login issues"
1. Delete the `playwright-state` folder
2. Restart the tracker
3. Log in manually when prompted

### "Session expires"
If your session expires:
1. The tracker will prompt you to log in again
2. Or delete `playwright-state` folder and restart

## Running in the Background

### Windows
Create a scheduled task:
1. Open Task Scheduler
2. Create Basic Task
3. Set to run: `python C:\path\to\verint_tracker.py`
4. Configure trigger (e.g., at startup or login)

### Linux
Use systemd or cron:
```bash
# Add to crontab
@reboot cd /path/to/work && python3 verint_tracker.py
```

### Mac
Create a Launch Agent:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.verint.tracker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/verint_tracker.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

## Best Practices

1. **Keep Browser Window Open**: Don't minimize to ensure schedule loads properly
2. **Stable Internet**: Ensure reliable connection for schedule updates
3. **Regular Updates**: Keep dependencies updated with `pip install -r requirements.txt --upgrade`
4. **Backup Configuration**: Save your customized `config.json` if you modify it
5. **Test Changes**: After modifying the parser, test thoroughly before relying on it

## Privacy and Security

- **Session Data**: Browser session data is stored in `playwright-state/`
- **No Data Collection**: This app doesn't send data anywhere
- **Local Only**: All processing happens on your computer
- **Credentials**: Your Microsoft credentials are handled by Edge, not stored by this app

## Getting Help

If you encounter issues:
1. Run `python3 test_setup.py` to verify installation
2. Check console output for error messages
3. Review this guide and the main README.md
4. Create an issue on GitHub with error details
