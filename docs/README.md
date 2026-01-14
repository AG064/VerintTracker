0# Verint Schedule Tracker

An automated application that monitors your Verint schedule and helps you manage your time with a modern GUI.

## Features

- 🖥️ **Modern Dark GUI**: Clean, minimalistic interface built with CustomTkinter.
- 📅 **Schedule Display**: Shows your daily schedule clearly with "Next Activity" highlighting.
- ⏳ **Countdown Timer**: Shows time remaining until your next activity switch.
- ⏱️ **CPH Pacing Timer**: Built-in timer to help you maintain 7.5 CPH (8 minutes per ticket).
  - **Reply vs No-Reply**: Track tickets that require replies separately from those that don't.
  - **Hotkeys**: Use configured hotkey (default: `Numpad -`) to quickly complete a ticket.
- ⌨️ **Input Monitoring**: Tracks your KPM (Keys Per Minute) and CPM (Clicks Per Minute) locally to help you gauge activity levels.
- 🔔 **Smart Notifications**: Audible and visual desktop notifications 5 minutes before activity changes.
- 🌐 **Robust Automation**: 
  - Connects to Verint using Microsoft Edge.
  - Handles manual login via a GUI prompt if needed.
  - Automatically cleans up "zombie" browser processes to keep your system fast.
- 🔐 **Secure**: Maintains your Microsoft account session locally in a dedicated folder.

## Prerequisites

- **Windows 10 or 11**
- **Python 3.10** or higher
- **Microsoft Edge** browser installed

## Quick Setup (Windows)

1. **Clone or Download** this repository.
2. Double-click **`setup.bat`**.
   - This will automatically create a virtual environment, install all dependencies, and set up the browser driver.

## Building an Executable (.exe)

To package the application into a single `.exe` file for easy distribution:

1. Run **`setup.bat`** first to ensure all dependencies are installed.
2. Double-click **`build.bat`**.
3. Once finished, check the **`dist`** folder.
   - You will find `VerintTracker.exe` and `config.json`.
   - You can move these two files to any computer (ensure Edge is installed on the target machine).

## Usage

1. Double-click **`run.bat`** (or the generated `.exe`) to start the application.
2. **First-time Login**:
   - The app will launch a browser window.
   - If you are not logged in, a "Login Required" dialog will appear in the app.
   - Log in to your Microsoft account in the browser window.
   - Click "I have logged in" in the app dialog.
3. **Navigation**:
   - If you set a **Verint URL** in Settings, the browser navigates automatically.
   - If you left it empty, **manually navigate** to your schedule page.
4. **Dashboard**:
   - View your schedule and countdowns.
   - Use the **CPH Pacing Timer** for your tickets.
5. **Statistics**:
   - Switch to the "Statistics" tab to view your daily/weekly performance and input metrics.

## Configuration

You can configure the application directly via the **Settings** tab:

- **Verint URL**: (Optional) The direct link to your schedule. Leave empty to navigate manually.
- **Notify Minutes Before**: How many minutes in advance to get an alert.
- **Check Interval**: How often to refresh the schedule.
- **Browser Type**: Choose between Edge or Chrome.
- **Headless Mode**: Run browser in background.

## Troubleshooting

**Browser doesn't open / App hangs:**
- Run `setup.bat` again to ensure drivers are installed.
- The app attempts to kill stale Edge processes on startup. If issues persist, restart your computer.

**Schedule not parsing:**
- The parser tries multiple methods (Table, Text, Frames). If it fails, check the console output for errors.

**Notifications not showing:**
- Ensure Windows Focus Assist (Do Not Disturb) is off or allows notifications from Python.

## Developer Notes

- **`app.py`**: Main GUI application entry point.
- **`verint_tracker.py`**: Browser automation logic (Playwright).
- **`stats_manager.py`**: Handles data storage (`ticket_stats.json`).
- **`input_monitor.py`**: Background thread for KPM/CPM tracking.

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Security Note

This application stores browser session data in the `playwright-state` directory to maintain your login. Keep this directory secure and don't share it. The directory is excluded from git via `.gitignore`.

