# Verint Schedule Tracker

An "automated" application that monitors your Verint WFO schedule and helps you manage your time with a modern GUI.

If you just wanna download the app check [this link](https://github.com/AG064/VerintTracker/releases/tag/v0.0.2-alpha)

Apologize for the usage of AI emojis, heard it gives better visibility :D
Most of the README written by AI, edited by me and updated by me.


Overview of app's interface:
<img width="1017" height="1254" alt="image" src="https://github.com/user-attachments/assets/4d969bf7-9202-469b-8a2b-9c4deb2fce40" />
<img width="1029" height="1268" alt="image" src="https://github.com/user-attachments/assets/4a6124e2-98b0-4301-b4b4-b1ccdea09833" />
<img width="1029" height="1265" alt="image" src="https://github.com/user-attachments/assets/4397adeb-1bcf-4181-969f-4f9f00432b98" />



## Features
- 👤**First Time User Experience**: Upon launch of the app you can quickly configure it.
- 🖥️ **Modern Dark GUI**: Clean, minimalistic interface built with CustomTkinter.
- 🌙 **Light/Dark Theme**: You can change between Light and Dark themes.
- 📅 **Schedule Display**: Shows your daily schedule clearly with "Next Activity" highlighting.
- ⏳ **Countdown Timer**: Shows time remaining until your next activity switch.
- ⏱️ **CPH Pacing Timer**: Built-in timer to help you maintain whatever CPH you want (7.5 is the default go-to).
  - **Reply vs No-Reply**: Track tickets that require replies separately from those that don't to ensure proper CPH tracking only for tickets with replies.
  - **Hotkeys**: Use hotkeys to quickly complete a ticket.
- ⌨️ **Input Monitoring**: Tracks your KPM (Keys Per Minute) and CPM (Clicks Per Minute) locally to help you gauge activity levels.
- **Statistics Tab**: You are able to view daily/weekly/monthly statistics by setting a timeframe you want to check featuring a neat graph (totally isn't copied)
- 🔔 **Smart Notifications**: Audible and visual desktop notifications 5 minutes before activity changes, upon ticket logging and upon running out of ticket time for CPH timer.
- 🔐 **Secure**: Does not relay any credentials anywhere.
- 🌐**Fully open-source**: Feel free to modify the app however you see fit, but I encourage you to ask me for changes.


---
Section below is for folks who like to use the source code instead of just downloading an .exe file from link above. 
---
If you want usage tutorial and just clicking buttons isn't clear enough, check Usage section below.
---

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
   - The app will launch a browser window and FTUE window.
   - Choose your CPH target
   - Choose your browser (chrome might not work yet)
   - Choose a keybind to track tickets (optional, can be done later too)
   - If you are not logged in automatically you will need to login inside Edge and Verint ater that.
   - Log in to your Microsoft account in the browser window.
   - Log in to Verint under the provided credentials from your company.
3. **Verint**:
   - If you set a **Verint URL** in Settings, the browser should navigate to that instead of automatically opening verint WFO login screen.
4. **Dashboard**:
   - View your schedule and countdowns.
   - Use the **CPH Pacing Timer** for your tickets.
   - Quickly check your performance, together with CPM and KPM.
5. **Statistics**:
   - Switch to the "Statistics" tab to view your daily/weekly/monthly/whatever performance and input metrics.

## Configuration

You can configure the application directly via the **Settings** tab:

- **Verint URL**: (Optional) The direct link to your schedule in case it doesn't work automatically.
- **Notify Minutes Before**: How many minutes in advance to get an alert on your desktop (does the windows notification sound).
- **Check Interval**: How often to refresh the schedule. I recommend values not above 15 minutes but it depends on how often whoever plots these for you changes your schedule or in what timeframe usually.
- **Browser Type**: Choose between Edge or Chrome (haven't tested chrome)
- **Headless Mode**: Run browser in background. (untested Experimental feature)

## Troubleshooting

**Browser doesn't open / App hangs / Errors appear:**
- Reinstall app, restart your PC, Delete VerintTracker from /%appdata%/Local
- Close all Microsoft Edge instances.

**Schedule not parsing:**
- The parser tries multiple methods (Table, Text, Frames). If it fails, check the console output for errors and report as an issue or directly contact me.

**Notifications not showing:**
- Ensure Windows Focus Assist (Do Not Disturb) is off or allows notifications from Python. Ensure no other process kills the app or Python instances. Antiviruses might do that, but it should be fine.

## Developer Notes

- **`app.py`**: Main GUI application entry point. (you can run the app just running this in the project's directory, in cli `python app.py`
- **`verint_tracker.py`**: Browser automation logic (Playwright).
- **`stats_manager.py`**: Handles data storage (`ticket_stats.json`).
- **`input_monitor.py`**: Background thread for KPM/CPM tracking.

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Security Note

This application stores browser session data in the `playwright-state` directory or `edge_profile` inside /%appdata%/local to maintain your login. Keep this directory secure and don't share it. The directory is excluded from git via `.gitignore` or created if you just use the `.exe` file

