<p align="center">
  <img src="assets/icon.ico" alt="OmniMacro Logo" width="120"/>
</p>

<h1 align="center">OmniMacro</h1>

<p align="center">
  <strong>A powerful, feature-rich automation tool for Windows</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows-blue?logo=windows" alt="Platform"/>
  <img src="https://img.shields.io/badge/Python-3.12+-yellow?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/GUI-Flet-purple" alt="Flet"/>
  <img src="https://img.shields.io/badge/License-Apache_2.0-blue" alt="License"/>
  <img src="https://img.shields.io/badge/Status-Active-success" alt="Status"/>
</p>

---

## 📋 Overview

**OmniMacro** is a comprehensive Windows automation utility designed for gamers, content creators, and power users. It combines multiple automation features into a single, intuitive interface with a modern dark theme.

> ⚠️ **Important**: Run as Administrator for full functionality.

---

## ✨ Features

### 🎯 Recoil Control
- **Vertical & Horizontal compensation** with adjustable strength
- **LMB Only** or **LMB + RMB** activation modes
- **Fine-tuning** with decimal precision (0.1 increments)
- **Save/Load** configuration profiles
- **Hotkey**: `F4`

### ⌨️ Keyboard Macro
- Bind any key for **rapid-fire** repeating
- Adjustable **delay** between key presses
- **Hotkey**: `F5`

### 🖱️ Auto Clicker
- Adjustable **click interval** (1-1000ms)
- **Hotkey**: `F6`

### 💤 Anti-AFK
- **Random direction** cursor movement with return
- **Variable speed** to avoid detection
- Adjustable **magnitude** and **interval**
- **Hotkey**: `F7`

### 🔄 Camera Spin
- **Continuous horizontal** cursor movement
- **Left/Right** direction selection
- Adjustable **speed** (pixels per tick)
- **Hotkey**: `F8`

### 📝 Human Typer
A sophisticated typing simulator that mimics human behavior:

| Feature | Description |
|---------|-------------|
| **Speed Range** | Variable WPM (10-200) for realistic variation |
| **Typo Simulation** | Adjacent keys or random letters with auto-correction |
| **Correction Delay** | Configurable pause before fixing typos (20-1000ms) |
| **Multi-Typos** | Simulate multiple consecutive errors |
| **Thinking Pauses** | Random pauses between words (0-50% frequency) |
| **Sentence Pauses** | Pauses after `.!?` with configurable frequency |
| **Paragraph Pauses** | Pauses after newlines with configurable frequency |
| **Synonym Swap** | Types synonym first, then corrects to intended word |

> 💡 **Synonym Dictionary**: Built-in dictionary with **200+ common words** including verbs, adjectives, nouns, and adverbs.

### 🧩 Custom Macros
- **Unlimited** custom macro slots
- Bind **keyboard keys** or **mouse buttons** as triggers
- **Multi-key actions** - press multiple keys simultaneously
- **Hold-to-repeat** functionality
- **Persistent storage** - macros saved across sessions

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.12+ |
| **GUI Framework** | [Flet](https://flet.dev/) (Flutter-based) |
| **Input Handling** | [pynput](https://pypi.org/project/pynput/) |
| **Packaging** | [PyInstaller](https://pyinstaller.org/) |
| **OS Integration** | Windows API (ctypes) |

---

## 📦 Installation

### Option 1: Download Release
Download the latest `OmniMacro.exe` from the [Releases](../../releases) page.

### Option 2: Build from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/OmniMacro.git
cd OmniMacro

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run directly
python main.py

# Or build executable
pyinstaller OmniMacro.spec --noconfirm
```

---

## 📁 Project Structure

```
macro-master/
├── main.py           # GUI application and UI logic
├── macro_core.py     # Core automation engine
├── input_utils.py    # Low-level Windows input utilities
├── OmniMacro.spec    # PyInstaller build configuration
├── requirements.txt  # Python dependencies
├── assets/
│   └── icon.ico      # Application icon
└── dist/
    └── OmniMacro.exe # Compiled executable
```

---

## 🎮 Usage

1. **Launch** `OmniMacro.exe` as Administrator
2. **Navigate** using the sidebar tabs
3. **Configure** your desired features
4. **Activate** using toggle switches or hotkeys
5. **Save** your settings for future sessions

### Hotkey Reference

| Key | Function |
|-----|----------|
| `F4` | Toggle Recoil Control |
| `F5` | Toggle Keyboard Macro |
| `F6` | Toggle Auto Clicker |
| `F7` | Toggle Anti-AFK |
| `F8` | Toggle Camera Spin |

---

## 🎨 Screenshots

The application features a modern **dark theme** with:
- Clean navigation rail
- Intuitive sliders and toggles
- Real-time setting updates
- Smooth animations

---

## 📄 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

```
Copyright 2024 Entropify

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

## 🙏 Credits & Acknowledgments

- **[Final-Typer](https://github.com/Peteryhs/Final-Typer)** by Peteryhs - Inspiration for the Human Typer feature
- **[Flet](https://flet.dev/)** - Modern Python UI framework
- **[pynput](https://pynput.readthedocs.io/)** - Cross-platform input control

---

## ⚠️ Disclaimer

This software is provided for **educational and personal use only**. The author is not responsible for any misuse of this tool. Use responsibly and in accordance with the terms of service of any applications or games you interact with.

---

<p align="center">
  Made with ❤️ by <strong>Entropify</strong>
</p>
