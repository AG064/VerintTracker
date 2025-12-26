# Quick Reference Guide

## Installation (One-time Setup)

### Windows
```batch
setup.bat
```

### Linux/Mac
```bash
bash setup.sh
```

### Manual Installation
```bash
pip install -r requirements.txt
playwright install msedge
```

## Running the App

```bash
python verint_tracker.py
```

Or on Linux/Mac:
```bash
python3 verint_tracker.py
```

## Configuration

Edit `config.json`:

```json
{
  "verint_url": "YOUR_VERINT_URL",
  "notification_minutes_before": 5,
  "check_interval_seconds": 60,
  "browser_type": "msedge"
}
```

## Common Commands

| Task | Command |
|------|---------|
| Verify setup | `python test_setup.py` |
| Inspect Verint page | `python inspect_schedule.py` |
| Run tracker | `python verint_tracker.py` |
| Stop tracker | Press `Ctrl+C` |

## File Overview

| File | Purpose |
|------|---------|
| `verint_tracker.py` | Main application |
| `config.json` | Configuration settings |
| `test_setup.py` | Verify installation |
| `inspect_schedule.py` | Inspect HTML elements |
| `parser_template.py` | Parser examples |
| `README.md` | Main documentation |
| `USAGE_GUIDE.md` | Detailed usage guide |
| `FAQ.md` | Troubleshooting & FAQ |

## Customization Quick Steps

1. **Identify HTML elements:**
   ```bash
   python inspect_schedule.py
   ```

2. **Edit parser:**
   - Open `verint_tracker.py`
   - Find `parse_schedule()` method (around line 105)
   - Use examples from `parser_template.py`

3. **Update selectors:**
   ```python
   time_elements = page.query_selector_all(".your-time-class")
   activity_elements = page.query_selector_all(".your-activity-class")
   ```

4. **Test:**
   ```bash
   python verint_tracker.py
   ```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Dependencies not installed | Run `setup.sh` or `setup.bat` |
| Browser doesn't open | Run `playwright install msedge` |
| Login issues | Delete `playwright-state/` folder |
| Schedule not parsing | Run `inspect_schedule.py` and customize parser |
| No notifications | Check system notification settings |

## Key Directories

- `playwright-state/` - Browser session data (auto-created, gitignored)
- `__pycache__/` - Python cache (auto-created, gitignored)

## Important Notes

- ✅ Keep browser window open while running
- ✅ Computer must stay awake for continuous monitoring
- ✅ First run requires Microsoft account login
- ✅ Session persists between runs (no need to login again)
- ✅ Parser needs customization for your specific Verint page

## Getting Help

1. Check `FAQ.md` for common questions
2. Read `USAGE_GUIDE.md` for detailed instructions
3. Review `README.md` for setup help
4. Look at `parser_template.py` for customization examples

## Project Links

- Main Docs: `README.md`
- Usage Guide: `USAGE_GUIDE.md`
- FAQ: `FAQ.md`
- Project Summary: `PROJECT_SUMMARY.md`

---

**Quick Start:** Run `setup.bat` (Windows) or `bash setup.sh` (Linux/Mac), then `python verint_tracker.py`
