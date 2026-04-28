# OmniMacro v1.1.2 — Color Clicker Precision & Stability

## 🖱️ New: Preset Click Position

Click at a fixed screen coordinate instead of wherever the cursor happens to be when the color is detected:

- Click **Set Position** to open a full-screen point picker — the app minimizes for a clean view
- After picking, the coordinates are shown in the UI (`Click Position: (x, y)`)
- Toggle **Click at Preset Position** to activate; when off, the clicker reverts to clicking at the cursor
- After each automated click, the **cursor automatically returns** to where it was before — no interruption to your workflow
- Fully **cross-monitor**: the preset can be on any display in any configuration regardless of DPI or resolution differences

## 🐛 Bug Fixes

- **Cursor precision** — Fixed systematic undershooting on scaled displays (e.g. 1440p @ 150% DPI). Replaced `MOUSEEVENTF_ABSOLUTE` + virtual-desktop normalization with `SetCursorPos` in a forced per-monitor-aware thread context, which places the cursor at exact physical pixels and requires no normalization math
- **Cross-monitor click** — Cursor now correctly teleports to preset positions on secondary monitors regardless of their position, DPI, or offset relative to the primary
- **Eyedropper overlay** — Fixed a Python 3.12 / Tkinter crash where the overlay appeared and immediately disappeared; root cause was a `WM_DPICHANGED` rescale touching a canvas image item with no image set
- **Eyedropper freeze** — Fixed app entering a persistent loading state after picking a color; caused by concurrent individual `control.update()` calls from a background thread conflicting with a simultaneous `page.update()` from the restore step; fixed by batching all UI state mutations into a single `page.update()` at the end of the background worker
- **Overlay robustness** — All three Tkinter overlays (region selector, point picker, eyedropper) now guarantee the Flet window is always restored even if the overlay crashes mid-session, preventing the app from appearing frozen with the main window minimized

## 📝 Other Changes

- `input_utils.py`: `move_to()` and `click_at()` rewritten to use `SetCursorPos` + raw `LEFTDOWN`/`LEFTUP` events (no position flags); 8ms settle delay added between move and click for reliable event dispatch
- `macro_core.py`: cursor position captured before preset click and restored via `SetCursorPos` after click
- `color_picker_overlay.py`: `on_motion` fully wrapped in `try/except`; all three overlay functions use `try/finally` for `restore_fn` to guarantee app restore; individual `control.update()` calls removed from refresh helpers
- README updated with Preset Click Position feature

---

# OmniMacro v1.1.1 — Color Clicker

## 🎨 New Feature: Color Clicker

Monitors a user-defined screen region and automatically left-clicks the mouse when a target color is detected within it.

- Click **Select Region** to draw a rectangle over any area of the screen — the app minimizes first for a clean view
- Use the **Eyedropper** to pick any pixel color from a full-screen overlay with a live magnifying glass
- Or type a **Hex code** (`#RRGGBB`) directly — the color swatch updates in real time, two-way synced with the eyedropper
- **Color Tolerance** slider (0–150) lets you match loosely or exactly using Euclidean RGB distance
- **Pre-Click Delay** (0–5000ms) — wait a configurable time after detecting the color before clicking
- **Scan Interval** (10–1000ms) — control how often the region is sampled; lower = more responsive, more CPU
- Built-in **300ms cooldown** between clicks prevents unintended spam
- **Hotkey**: `F11` to toggle on/off

## 📝 Other Changes

- New **Color Click** tab in the sidebar navigation (icon: color dropper)
- New `color_picker_overlay.py` module — houses both the region selector and eyedropper Tkinter overlays
- Updated Info page with a Color Clicker feature card
- Updated hotkey reference: `F11` → Toggle Color Clicker
- README updated with new feature section, Tkinter badge, updated tech stack table, project structure, and hotkey reference
