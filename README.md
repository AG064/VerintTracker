# Verint Schedule Tracker

An automated application that monitors your Verint schedule and sends desktop notifications 5 minutes before you need to change your activity status.

## Features

- 🔔 Desktop notifications 5 minutes before activity changes
- 🌐 Automatic browser integration with Microsoft Edge
- 🔐 Maintains your Microsoft account session
- ⏱️ Configurable check intervals and notification timing
- 📋 Displays upcoming schedule activities

## Prerequisites

- Python 3.7 or higher
- Microsoft Edge browser
- Microsoft account with access to Verint

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AG064/work.git
   cd work
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Microsoft Edge browser driver:**
   ```bash
   playwright install msedge
   ```

## Configuration

Edit the `config.json` file to customize settings:

```json
{
  "verint_url": "https://wfo.mt7.verintcloudservices.com/wfo/ui/#wsm%5Bws%5D=legacyWorkspace&url=..%2Fcontrol%2Fshowschedule%3FNEWUINAV%3D1&selTab=1_MY_HOME-%3E1_AM_MYTIME-%3E2_AM_MYTIME_SCHEDULE",
  "notification_minutes_before": 5,
  "check_interval_seconds": 60,
  "browser_type": "msedge"
}
```

**Configuration options:**
- `verint_url`: Your Verint schedule URL
- `notification_minutes_before`: How many minutes before an activity change to notify (default: 5)
- `check_interval_seconds`: How often to check the schedule in seconds (default: 60)
- `browser_type`: Browser to use (default: "msedge")

## Usage

1. **Start the tracker:**
   ```bash
   python verint_tracker.py
   ```

2. **First-time setup:**
   - The application will open Microsoft Edge
   - If you're not logged in, you'll be prompted to log in to your Microsoft account
   - After logging in, the browser will navigate to your Verint schedule
   - Your session will be saved for future runs

3. **Running:**
   - The application will continuously monitor your schedule
   - Console output will show upcoming activities
   - Desktop notifications will appear 5 minutes before changes
   - Press `Ctrl+C` to stop the tracker

## How It Works

1. **Browser Automation**: Uses Playwright to control Microsoft Edge with your existing login session
2. **Schedule Monitoring**: Periodically refreshes the Verint page and parses your schedule
3. **Smart Notifications**: Calculates time until next activity and sends notifications at the configured threshold
4. **Persistent Session**: Maintains your Microsoft account login between runs

## Customization

### Adjusting Schedule Parsing

The application includes a basic schedule parser. If you need to customize it for your specific Verint page layout:

1. Open `verint_tracker.py`
2. Locate the `parse_schedule()` method
3. Modify the selectors and parsing logic to match your page structure

### Notification Settings

You can customize notifications by:
- Changing `notification_minutes_before` in `config.json` (e.g., 10 for 10 minutes)
- Modifying `check_interval_seconds` for more or less frequent checks

## Troubleshooting

**Browser doesn't open:**
- Ensure Microsoft Edge is installed
- Run `playwright install msedge` again

**Login issues:**
- Delete the `playwright-state` folder and restart
- Manually log in when prompted

**Schedule not parsing:**
- The default parser may need customization for your Verint page
- Check console output for parsing errors
- Modify the `parse_schedule()` method as needed

**No notifications appearing:**
- Ensure your system allows desktop notifications
- Check that Python has notification permissions
- Notifications will also print to the console

## Requirements

See `requirements.txt` for Python package dependencies:
- `playwright` - Browser automation
- `plyer` - Cross-platform desktop notifications  
- `python-dateutil` - Date/time handling

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Security Note

This application stores browser session data in the `playwright-state` directory to maintain your login. Keep this directory secure and don't share it. The directory is excluded from git via `.gitignore`.

