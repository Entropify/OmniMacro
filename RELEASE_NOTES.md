# OmniMacro v1.1.0 — Crosshair Overlay + Screen OCR

## 🎯 New Feature: Crosshair Overlay

Always-on-top, click-through crosshair overlay for borderless fullscreen and windowed games.

- **Shapes**: Cross, Circle, Dot, Cross+Circle, Cross+Dot
- **Colors**: Green, Red, Cyan, White, Yellow, Magenta, Orange, or custom RGB
- **Settings**: Size (2-50px), Thickness (1-5px), Opacity (10-100%), Center Gap (0-20px)
- **Extras**: Center Dot toggle, Dark Outline toggle
- **Hotkey**: `F9` to toggle on/off

## 📷 New Feature: Screen OCR (Text Capture)

Capture any region of the screen and extract text using OCR — all from within OmniMacro.

- Click **Capture Region** or press **F10** — the app minimizes for a clean screenshot
- Screen dims with a crosshair cursor — click and drag to select a region
- Extracted text appears in an **editable output box**, allowing you to tweak text before copying
- **Capture History** stores the last 20 captures with timestamps
- Press **ESC** or right-click to cancel safely without stalling the app
- Tesseract OCR engine is **bundled in the exe** — no separate install needed for end users

## 🐛 Bug Fixes

- **Fixed**: Crosshair overlay opacity slider now actually works — previously the opacity value was stored but never applied to the Win32 window
- **Fixed**: Resolved massive Flet UI freeze crashes by surgically decoupling Tkinter Screen Capture from Windows DPI injections
- **Fixed**: OCR executable compile now properly maps the internal `TESSDATA_PREFIX` to the bundled `tessdata` subfolder meaning compiled executables actually read text correctly instead of crashing silently
- **Fixed**: Screen capture correctly handles `ESC` and mouse clicks natively freeing the app from getting stuck in a "capturing" state if abruptly closed

## 📝 Other Changes

- New **OCR** tab in the sidebar navigation
- Updated Info page with Crosshair Overlay and Screen OCR feature cards
- Added `pytesseract` and `Pillow` to dependencies
- Updated build config to bundle Tesseract binary + English training data into the single exe
- README updated with new features, hotkeys, build instructions, and project structure
- **Exe size is now ~170 MB** (up from ~80 MB) — Tesseract OCR and its dependencies (ICU unicode libraries, Leptonica image processing, etc.) are fully bundled so the OCR feature works out-of-the-box with no separate installs for end users
