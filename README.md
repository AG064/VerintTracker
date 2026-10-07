# VerintTracker

Desktop schedule notifications and support-work statistics. The application uses
Playwright with a local browser profile for the configured Verint site.

See [the usage guide](docs/USAGE_GUIDE.md) for setup and operation, and
[the project overview](docs/PROJECT_SUMMARY.md) for the component structure.
Use your authorized account and keep the local browser profile private.

Statistics are saved by replacing a completed temporary file. Unreadable statistics
are preserved beside the original file with a `.corrupt-` suffix before a new history
is created. Keep those backups until their contents have been reviewed.

Run the storage regression tests with `python -m unittest discover -s tests -v`.
They use temporary directories and do not access Verint or a real browser profile.
