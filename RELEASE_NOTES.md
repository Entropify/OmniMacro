# OmniMacro v1.0.3 - Type-Along Mode

## ⌨️ New Feature: Type-Along Mode

Added **Type-Along Mode** to the Human Typer — a new way to make typing look natural by tying each output character to a real keypress from the user.

### How It Works:
- Enable the toggle before starting the typer
- Each key you press on your keyboard outputs the **next character** of your text
- Your actual keystrokes are **suppressed** — only the intended text appears
- Stop pressing keys and the typer **waits** until you resume

### What's Active in Type-Along Mode:
- ✅ **Typos & auto-correction** — error rate and correction speed settings fully apply
- ✅ **Synonym Swap** — still fires based on configured frequency
- ✅ **Emotion Simulator** (Crashout / Nihilism / Vamp) — triggers as normal
- ❌ **WPM speed, Thinking/Sentence/Paragraph Pauses, Special Char Delay** — bypassed (pacing is driven by your keystrokes instead)

## 📝 Other Changes
- UI description below the Type-Along switch now lists active/inactive parameters clearly (green ✅ / red ❌)
- Info page entry updated with matching active/inactive breakdown
- WPM max corrected to 300 in README