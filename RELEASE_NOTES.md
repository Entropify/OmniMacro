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
