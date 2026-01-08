# Releases

This repository intentionally does **not** commit built binaries (like `dist/VerintTracker.exe`) to git.

Instead, the recommended approach is:

- Keep source code in the repo
- Build the Windows `.exe` in CI (GitHub Actions)
- Publish the `.exe` as a **GitHub Release** asset (so it’s visible/downloadable on GitHub)

## How to publish a release

1. Ensure `main` is green and all changes are merged.
2. Create a tag like `v1.2.3` and push it.
3. GitHub Actions will:
   - build `VerintTracker.exe`
   - compute a SHA256 hash
   - create a GitHub Release for the tag
   - attach the `.exe` (and `.sha256`) to the Release

## Why not commit the EXE to the repo?

- Git history gets huge fast
- Diffs are meaningless for binaries
- You’ll hit GitHub LFS/bandwidth limits sooner
- Releases are the standard distribution mechanism

## Local build

If you want to build locally, run the normal script:

- `scripts/build.bat`

CI uses `scripts/build_ci.bat` which does not rely on a pre-created venv.
