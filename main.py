import flet as ft
import threading
import time
import configparser
import sys
import os
import json
import uuid
import ctypes
import input_utils
from macro_core import core

def main(page: ft.Page):
    # Set AppUserModelID to ensure taskbar icon works on Windows
    myappid = 'omnimacro.app.v1' 
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    page.title = "OmniMacro"
    
    # Custom dark theme with black/grey (no blue tint)
    page.theme = ft.Theme(color_scheme_seed="grey")
    page.dark_theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            background="#121212",
            surface="#1e1e1e",
            on_background="#e0e0e0",
            on_surface="#e0e0e0",
            primary="#9e9e9e",
            on_primary="#000000",
        ),
    )
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#121212"
    
    page.window_width = 800
    page.window_height = 600

    # Determine execution path for assets
    if hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Use .ico for Windows window icon preference
    icon_path = os.path.join(base_dir, "assets", "icon.ico")
    
    # Set window icon for taskbar and title bar (Absolute path to .ico)
    page.window.icon = icon_path
    
    # Macros persistence file (INI format)
    if hasattr(sys, '_MEIPASS'):
        exe_dir = os.path.dirname(sys.executable)
        macros_file = os.path.join(exe_dir, "configs", "macros.ini")
    else:
        macros_file = os.path.join(base_dir, "configs", "macros.ini")
    
    def save_macros():
        try:
            os.makedirs(os.path.dirname(macros_file), exist_ok=True)
            config = configparser.ConfigParser()
            config['Macros'] = {
                'data': json.dumps(core.custom_macros)
            }
            with open(macros_file, 'w') as f:
                config.write(f)
        except Exception as e:
            print(f"Error saving macros: {e}")
    
    def load_macros():
        try:
            if os.path.exists(macros_file):
                config = configparser.ConfigParser()
                config.read(macros_file)
                if 'Macros' in config:
                    data = config['Macros'].get('data', '[]')
                    loaded = json.loads(data)
                    core.update_custom_macros(loaded)
        except Exception as e:
            print(f"Error loading macros: {e}")

    # Initialize Core
    core.start()
    load_macros()

    # --- Recoil Controls ---
    def on_recoil_change(e):
        core.update_recoil(
            recoil_switch.value,
            float(recoil_y_slider.value),
            float(recoil_x_slider.value),
            float(recoil_delay_slider.value) / 1000.0, # Convert ms to seconds
            int(recoil_mode_radio.value)
        )
        recoil_y_input.value = str(round(recoil_y_slider.value, 2))
        recoil_x_input.value = str(round(recoil_x_slider.value, 2))
        page.update()

    def on_recoil_y_text_change(e):
        try:
            val = float(recoil_y_input.value)
            if -50 <= val <= 50:
                recoil_y_slider.value = val
                core.update_recoil(
                    recoil_switch.value,
                    val,
                    float(recoil_x_slider.value),
                    float(recoil_delay_slider.value) / 1000.0,
                    int(recoil_mode_radio.value)
                )
                page.update()
        except ValueError:
            pass

    def on_recoil_x_text_change(e):
        try:
            val = float(recoil_x_input.value)
            if -50 <= val <= 50:
                recoil_x_slider.value = val
                core.update_recoil(
                    recoil_switch.value,
                    float(recoil_y_slider.value),
                    val,
                    float(recoil_delay_slider.value) / 1000.0,
                    int(recoil_mode_radio.value)
                )
                page.update()
        except ValueError:
            pass

    
    # --- Config Save/Load Logic ---
    # Determine execution path
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    config_dir = os.path.join(base_dir, "configs")
    if not os.path.exists(config_dir):
        config_dir = None # FilePicker defaults to standard if None/Invalid

    def save_file_result(e: ft.FilePickerResultEvent):
        if e.path:
            config = configparser.ConfigParser()
            config['Recoil'] = {
                'enabled': str(recoil_switch.value),
                'vertical': str(recoil_y_slider.value),
                'horizontal': str(recoil_x_slider.value),
                'delay': str(recoil_delay_slider.value),
                'mode': str(recoil_mode_radio.value)
            }
            config['Custom'] = {
                'macros': json.dumps(core.custom_macros)
            }
            try:
                with open(e.path, 'w') as configfile:
                    config.write(configfile)
                page.snack_bar = ft.SnackBar(ft.Text("Config saved successfully!"))
                page.snack_bar.open = True
                page.update()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Error saving config: {ex}"))
                page.snack_bar.open = True
                page.update()

    def load_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            path = e.files[0].path
            config = configparser.ConfigParser()
            try:
                config.read(path)
                if 'Recoil' in config:
                    r = config['Recoil']
                    # Update GUI controls
                    recoil_switch.value = r.getboolean('enabled', fallback=False)
                    recoil_y_slider.value = r.getfloat('vertical', fallback=5.0)
                    recoil_x_slider.value = r.getfloat('horizontal', fallback=0.0)
                    recoil_delay_slider.value = r.getfloat('delay', fallback=10.0)
                    recoil_mode_radio.value = r.get('mode', fallback="0")
                    
                    # Update Input Fields to match
                    recoil_y_input.value = str(round(recoil_y_slider.value, 2))
                    recoil_x_input.value = str(round(recoil_x_slider.value, 2))

                    # Update Core
                    core.update_recoil(
                        recoil_switch.value,
                        float(recoil_y_slider.value),
                        float(recoil_x_slider.value),
                        float(recoil_delay_slider.value) / 1000.0,
                        int(recoil_mode_radio.value)
                    )
                    page.update()

                    # Custom Macros
                    if 'Custom' in config:
                        try:
                            m_json = config['Custom'].get('macros', fallback='[]')
                            loaded_macros = json.loads(m_json)
                            core.update_custom_macros(loaded_macros)
                            refresh_macro_list()
                        except Exception as e:
                            print(f"Error loading custom macros: {e}")
                    
                    page.snack_bar = ft.SnackBar(ft.Text("Config loaded successfully!"))
                    page.snack_bar.open = True
                    page.update()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Error loading config: {ex}"))
                page.snack_bar.open = True
                page.update()

    save_file_picker = ft.FilePicker(on_result=save_file_result)
    load_file_picker = ft.FilePicker(on_result=load_file_result)
    page.overlay.extend([save_file_picker, load_file_picker])

    recoil_switch = ft.Switch(label="Enable Recoil Control", on_change=on_recoil_change)
    recoil_y_slider = ft.Slider(min=-50, max=50, divisions=1000, label="{value}", value=5, on_change=on_recoil_change, expand=True)
    recoil_y_input = ft.TextField(value="5.0", width=80, on_change=on_recoil_y_text_change)
    
    recoil_x_slider = ft.Slider(min=-50, max=50, divisions=1000, label="{value}", value=0, on_change=on_recoil_change, expand=True)
    recoil_x_input = ft.TextField(value="0.0", width=80, on_change=on_recoil_x_text_change)

    recoil_delay_slider = ft.Slider(min=1, max=100, divisions=99, label="{value} ms", value=10, on_change=on_recoil_change)
    recoil_mode_radio = ft.RadioGroup(content=ft.Row([
        ft.Radio(value="0", label="LMB Only"),
        ft.Radio(value="1", label="LMB + RMB")
    ]), value="0", on_change=on_recoil_change)
    
    recoil_save_btn = ft.ElevatedButton("Save Config", icon="save", on_click=lambda _: save_file_picker.save_file(allowed_extensions=["ini"], file_name="config.ini", initial_directory=config_dir))
    recoil_load_btn = ft.ElevatedButton("Load Config", icon="upload", on_click=lambda _: load_file_picker.pick_files(allowed_extensions=["ini"], initial_directory=config_dir))

    # --- Animation Utils ---
    def animate_hover(e):
        e.control.scale = 1.05 if e.data == "true" else 1.0
        e.control.update()

    def create_animated_button(text, icon, on_click, width=None, bgcolor=None):
        btn = ft.ElevatedButton(text=text, icon=icon, on_click=on_click, bgcolor=bgcolor)
        return ft.Container(
            content=btn,
            on_hover=animate_hover,
            scale=1.0,
            animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK),
            width=width,
            border_radius=ft.border_radius.all(5),
            padding=5
        )

    # Re-create buttons with animation wrapper
    # Note: Accessing original variables to keep logic, but wrapping them visually is easier if we replace their usage
    
    # Recoil Buttons
    recoil_save_btn_anim = create_animated_button("Save Config", "save", lambda _: save_file_picker.save_file(allowed_extensions=["ini"], file_name="config.ini", initial_directory=config_dir))
    recoil_load_btn_anim = create_animated_button("Load Config", "upload", lambda _: load_file_picker.pick_files(allowed_extensions=["ini"], initial_directory=config_dir))

    recoil_content = ft.Column([
        ft.Text("Recoil Control", style="headlineMedium"),
        ft.Row([recoil_save_btn_anim, recoil_load_btn_anim]), 
        recoil_switch,
        ft.Text("Activation: Press 'F4' to Toggle ON/OFF", color="grey"),
        ft.Text("Activation Mode"),
        recoil_mode_radio,
        ft.Text("Vertical Strength (Positive=Down, Negative=Up)"),
        ft.Row([recoil_y_slider, recoil_y_input], alignment="spaceBetween"),
        ft.Text("Horizontal Strength (Positive=Right, Negative=Left)"),
        ft.Row([recoil_x_slider, recoil_x_input], alignment="spaceBetween"),
        ft.Text("Delay between ticks (ms)"),
        recoil_delay_slider,
    ])

    # --- Auto Clicker Controls ---
    def on_autoclick_change(e):
        core.update_autoclicker(
            autoclick_switch.value,
            float(autoclick_delay_slider.value) / 1000.0
        )
        autoclick_delay_input.value = str(int(autoclick_delay_slider.value))
        page.update()

    def on_autoclick_text_change(e):
        try:
            val = float(autoclick_delay_input.value)
            autoclick_delay_slider.value = val
            core.update_autoclicker(autoclick_switch.value, val / 1000.0)
            page.update()
        except ValueError:
            pass

    autoclick_switch = ft.Switch(label="Enable Auto Clicker", on_change=on_autoclick_change)
    autoclick_delay_slider = ft.Slider(min=10, max=1000, divisions=99, label="{value} ms", value=100, on_change=on_autoclick_change, expand=True)
    autoclick_delay_input = ft.TextField(value="100", width=100, on_change=on_autoclick_text_change, suffix_text="ms")

    # Callback for F6 toggle
    def update_autoclick_switch(state):
        autoclick_switch.value = state
        page.update()
    
    # Callback for F5 toggle
    def update_kb_switch(state):
        kb_switch.value = state
        page.update()
    
    # Callback for F3 toggle
    def update_recoil_switch(state):
        recoil_switch.value = state
        page.update()
    
    # Callback for F7 toggle
    def update_antiafk_switch(state):
        antiafk_switch.value = state
        page.update()
    
    # Callback for F8 toggle
    def update_cameraspin_switch(state):
        cameraspin_switch.value = state
        page.update()
    
    # Callback for Human Typer status
    def update_humantyper_status(state):
        if state:
            humantyper_start_btn.text = "Stop Typing"
            humantyper_start_btn.disabled = False
            humantyper_start_btn.bgcolor = "#ef5350"
            humantyper_resume_btn.visible = False
        else:
            humantyper_start_btn.text = "Start Typing (3s delay)"
            humantyper_start_btn.disabled = False
            humantyper_start_btn.bgcolor = "#616161"
            humantyper_resume_btn.visible = False
            humantyper_pause_text.visible = False
        page.update()
    
    # Callback for Human Typer pause state
    def update_humantyper_pause(is_paused):
        if is_paused:
            humantyper_resume_btn.visible = True
            humantyper_pause_text.visible = True
            humantyper_start_btn.text = "Stop Typing (Paused)"
            humantyper_start_btn.bgcolor = "#ffa726"  # Orange for paused
            # Scroll to bottom so Resume button is visible
            humantyper_content.scroll_to(offset=-1, duration=300)
        else:
            humantyper_resume_btn.visible = False
            humantyper_pause_text.visible = False
            if core.humantyper_active:
                humantyper_start_btn.text = "Stop Typing"
                humantyper_start_btn.bgcolor = "#ef5350"
        page.update()
    
    core.set_callback(update_autoclick_switch, update_kb_switch, update_recoil_switch, update_antiafk_switch, update_cameraspin_switch, update_humantyper_status)
    core.on_humantyper_pause = update_humantyper_pause

    autoclick_content = ft.Column([
        ft.Text("Auto Clicker", style="headlineMedium"),
        autoclick_switch,
        ft.Text("Click Interval"),
        ft.Row([autoclick_delay_slider, autoclick_delay_input], alignment="spaceBetween"),
        ft.Text("Activation: Press 'F6' to Toggle ON/OFF", color="grey"),
        ft.Text("Note: There is a 0.5s delay after activation to prevent accidental toggle-off.", color="grey", size=12, italic=True)
    ])

    # --- Anti-AFK Controls ---
    def on_antiafk_change(e):
        core.update_antiafk(
            antiafk_switch.value,
            int(antiafk_magnitude_slider.value),
            float(antiafk_interval_slider.value)
        )
        antiafk_magnitude_input.value = str(int(antiafk_magnitude_slider.value))
        antiafk_interval_input.value = str(int(antiafk_interval_slider.value))
        page.update()

    def on_antiafk_magnitude_text_change(e):
        try:
            val = int(antiafk_magnitude_input.value)
            if 10 <= val <= 1000:
                antiafk_magnitude_slider.value = val
                core.update_antiafk(antiafk_switch.value, val, float(antiafk_interval_slider.value))
                page.update()
        except ValueError:
            pass

    def on_antiafk_interval_text_change(e):
        try:
            val = int(antiafk_interval_input.value)
            if 1 <= val <= 600:
                antiafk_interval_slider.value = val
                core.update_antiafk(antiafk_switch.value, int(antiafk_magnitude_slider.value), float(val))
                page.update()
        except ValueError:
            pass

    antiafk_switch = ft.Switch(label="Enable Anti-AFK", on_change=on_antiafk_change)
    antiafk_magnitude_slider = ft.Slider(min=10, max=1000, divisions=99, label="{value} px", value=50, on_change=on_antiafk_change, expand=True)
    antiafk_magnitude_input = ft.TextField(value="50", width=100, on_change=on_antiafk_magnitude_text_change, suffix_text="px")
    antiafk_interval_slider = ft.Slider(min=1, max=600, divisions=599, label="{value} s", value=30, on_change=on_antiafk_change, expand=True)
    antiafk_interval_input = ft.TextField(value="30", width=100, on_change=on_antiafk_interval_text_change, suffix_text="s")

    # --- Camera Spin Controls ---
    def on_cameraspin_change(e):
        core.update_cameraspin(
            cameraspin_switch.value,
            int(cameraspin_speed_slider.value),
            int(cameraspin_direction_radio.value)
        )
        cameraspin_speed_input.value = str(int(cameraspin_speed_slider.value))
        page.update()

    def on_cameraspin_speed_text_change(e):
        try:
            val = int(cameraspin_speed_input.value)
            if 1 <= val <= 50:
                cameraspin_speed_slider.value = val
                core.update_cameraspin(cameraspin_switch.value, val, int(cameraspin_direction_radio.value))
                page.update()
        except ValueError:
            pass

    cameraspin_switch = ft.Switch(label="Enable Camera Spin", on_change=on_cameraspin_change)
    cameraspin_speed_slider = ft.Slider(min=1, max=50, divisions=49, label="{value} px/tick", value=5, on_change=on_cameraspin_change, expand=True)
    cameraspin_speed_input = ft.TextField(value="5", width=100, on_change=on_cameraspin_speed_text_change, suffix_text="px/tick")
    cameraspin_direction_radio = ft.RadioGroup(content=ft.Row([
        ft.Radio(value="0", label="Right"),
        ft.Radio(value="1", label="Left")
    ]), value="0", on_change=on_cameraspin_change)

    antiafk_content = ft.Column([
        ft.Text("Anti-AFK", style="headlineMedium"),
        antiafk_switch,
        ft.Text("Activation: Press 'F7' to Toggle ON/OFF", color="grey"),
        ft.Text("Movement Magnitude (pixels)"),
        ft.Row([antiafk_magnitude_slider, antiafk_magnitude_input], alignment="spaceBetween"),
        ft.Text("Movement Interval (seconds)"),
        ft.Row([antiafk_interval_slider, antiafk_interval_input], alignment="spaceBetween"),
        ft.Divider(),
        ft.Text("Camera Spin", style="headlineMedium"),
        cameraspin_switch,
        ft.Text("Activation: Press 'F8' to Toggle ON/OFF", color="grey"),
        ft.Text("Spin Direction"),
        cameraspin_direction_radio,
        ft.Text("Spin Speed (pixels per tick)"),
        ft.Row([cameraspin_speed_slider, cameraspin_speed_input], alignment="spaceBetween"),
    ])

    # --- Human Typer Controls ---
    def on_humantyper_change(e):
        core.update_humantyper(
            int(humantyper_wpm_min_slider.value),
            int(humantyper_wpm_max_slider.value),
            int(humantyper_error_slider.value),
            int(humantyper_correction_slider.value),
            int(humantyper_maxtypos_slider.value),
            int(humantyper_typomode_radio.value),
            int(humantyper_pause_min_slider.value),
            int(humantyper_pause_max_slider.value),
            int(humantyper_pause_freq_slider.value),
            humantyper_synonym_switch.value,
            int(humantyper_synonym_freq_slider.value),
            humantyper_sentence_pause_switch.value,
            int(humantyper_sentence_pause_freq_slider.value),
            int(humantyper_sentence_pause_min_slider.value),
            int(humantyper_sentence_pause_max_slider.value),
            humantyper_para_pause_switch.value,
            int(humantyper_para_pause_freq_slider.value),
            int(humantyper_para_pause_min_slider.value),
            int(humantyper_para_pause_max_slider.value),
            humantyper_special_char_delay_switch.value,
            humantyper_crashout_switch.value,
            int(humantyper_crashout_count_input.value or 1),
            humantyper_nihilism_switch.value,
            int(humantyper_nihilism_count_input.value or 1),
            humantyper_vamp_switch.value,
            int(humantyper_vamp_count_input.value or 1)
        )
        humantyper_wpm_min_input.value = str(int(humantyper_wpm_min_slider.value))
        humantyper_wpm_max_input.value = str(int(humantyper_wpm_max_slider.value))
        humantyper_error_input.value = str(int(humantyper_error_slider.value))
        humantyper_correction_input.value = str(int(humantyper_correction_slider.value))
        humantyper_maxtypos_input.value = str(int(humantyper_maxtypos_slider.value))
        humantyper_pause_min_input.value = str(int(humantyper_pause_min_slider.value))
        humantyper_pause_max_input.value = str(int(humantyper_pause_max_slider.value))
        humantyper_pause_freq_input.value = str(int(humantyper_pause_freq_slider.value))
        humantyper_synonym_freq_input.value = str(int(humantyper_synonym_freq_slider.value))
        humantyper_sentence_pause_freq_input.value = str(int(humantyper_sentence_pause_freq_slider.value))
        humantyper_sentence_pause_min_input.value = str(int(humantyper_sentence_pause_min_slider.value))
        humantyper_sentence_pause_max_input.value = str(int(humantyper_sentence_pause_max_slider.value))
        humantyper_para_pause_freq_input.value = str(int(humantyper_para_pause_freq_slider.value))
        humantyper_para_pause_min_input.value = str(int(humantyper_para_pause_min_slider.value))
        humantyper_para_pause_max_input.value = str(int(humantyper_para_pause_max_slider.value))
        page.update()

    def start_humantyper_click(e):
        # If already typing, stop it
        if core.humantyper_active:
            core.humantyper_active = False
            return
        
        text = humantyper_text_input.value
        if not text:
            page.snack_bar = ft.SnackBar(ft.Text("Please enter text to type!"))
            page.snack_bar.open = True
            page.update()
            return
        
        humantyper_start_btn.text = "Starting in 3..."
        humantyper_start_btn.disabled = True
        page.update()
        
        def countdown_and_type():
            for i in [3, 2, 1]:
                humantyper_start_btn.text = f"Starting in {i}..."
                page.update()
                time.sleep(1)
            core.start_humantyper(text)
        
        threading.Thread(target=countdown_and_type, daemon=True).start()

    humantyper_text_input = ft.TextField(
        label="Text to Type",
        multiline=True,
        min_lines=5,
        max_lines=8,
    )
    humantyper_wpm_min_slider = ft.Slider(min=10, max=150, divisions=28, label="{value}", value=40, on_change=on_humantyper_change, expand=True)
    humantyper_wpm_min_input = ft.TextField(value="40", width=80, on_change=on_humantyper_change)
    humantyper_wpm_max_slider = ft.Slider(min=20, max=200, divisions=36, label="{value}", value=80, on_change=on_humantyper_change, expand=True)
    humantyper_wpm_max_input = ft.TextField(value="80", width=80, on_change=on_humantyper_change)
    humantyper_error_slider = ft.Slider(min=0, max=20, divisions=20, label="{value}%", value=2, on_change=on_humantyper_change, expand=True)
    humantyper_error_input = ft.TextField(value="2", width=80, on_change=on_humantyper_change, suffix_text="%")
    humantyper_typomode_radio = ft.RadioGroup(content=ft.Row([
        ft.Radio(value="0", label="Adjacent Keys (realistic)"),
        ft.Radio(value="1", label="Random Letters")
    ]), value="0", on_change=on_humantyper_change)
    humantyper_correction_slider = ft.Slider(min=20, max=1000, divisions=49, label="{value}ms", value=100, on_change=on_humantyper_change, expand=True)
    humantyper_correction_input = ft.TextField(value="100", width=80, on_change=on_humantyper_change, suffix_text="ms")
    humantyper_maxtypos_slider = ft.Slider(min=1, max=5, divisions=4, label="{value}", value=1, on_change=on_humantyper_change, expand=True)
    humantyper_maxtypos_input = ft.TextField(value="1", width=80, on_change=on_humantyper_change)
    humantyper_pause_min_slider = ft.Slider(min=100, max=2000, divisions=19, label="{value}ms", value=500, on_change=on_humantyper_change, expand=True)
    humantyper_pause_min_input = ft.TextField(value="500", width=80, on_change=on_humantyper_change, suffix_text="ms")
    humantyper_pause_max_slider = ft.Slider(min=500, max=5000, divisions=18, label="{value}ms", value=2000, on_change=on_humantyper_change, expand=True)
    humantyper_pause_max_input = ft.TextField(value="2000", width=80, on_change=on_humantyper_change, suffix_text="ms")
    humantyper_pause_freq_slider = ft.Slider(min=0, max=50, divisions=25, label="{value}%", value=10, on_change=on_humantyper_change, expand=True)
    humantyper_pause_freq_input = ft.TextField(value="10", width=80, on_change=on_humantyper_change, suffix_text="%")
    humantyper_synonym_switch = ft.Switch(label="Enable Synonym Swap", value=False, on_change=on_humantyper_change)
    humantyper_synonym_freq_slider = ft.Slider(min=1, max=75, divisions=74, label="{value}%", value=5, on_change=on_humantyper_change, expand=True)
    humantyper_synonym_freq_input = ft.TextField(value="5", width=80, on_change=on_humantyper_change, suffix_text="%")
    # Sentence pause controls
    humantyper_sentence_pause_switch = ft.Switch(label="Pause after sentences", value=True, on_change=on_humantyper_change)
    humantyper_sentence_pause_freq_slider = ft.Slider(min=0, max=100, divisions=20, label="{value}%", value=80, on_change=on_humantyper_change, expand=True)
    humantyper_sentence_pause_freq_input = ft.TextField(value="80", width=80, on_change=on_humantyper_change, suffix_text="%")
    humantyper_sentence_pause_min_slider = ft.Slider(min=100, max=2000, divisions=19, label="{value}ms", value=300, on_change=on_humantyper_change, expand=True)
    humantyper_sentence_pause_min_input = ft.TextField(value="300", width=80, on_change=on_humantyper_change, suffix_text="ms")
    humantyper_sentence_pause_max_slider = ft.Slider(min=200, max=3000, divisions=14, label="{value}ms", value=1000, on_change=on_humantyper_change, expand=True)
    humantyper_sentence_pause_max_input = ft.TextField(value="1000", width=80, on_change=on_humantyper_change, suffix_text="ms")
    # Paragraph pause controls
    humantyper_para_pause_switch = ft.Switch(label="Pause after paragraphs", value=True, on_change=on_humantyper_change)
    humantyper_para_pause_freq_slider = ft.Slider(min=0, max=100, divisions=20, label="{value}%", value=90, on_change=on_humantyper_change, expand=True)
    humantyper_para_pause_freq_input = ft.TextField(value="90", width=80, on_change=on_humantyper_change, suffix_text="%")
    humantyper_para_pause_min_slider = ft.Slider(min=200, max=3000, divisions=14, label="{value}ms", value=500, on_change=on_humantyper_change, expand=True)
    humantyper_para_pause_min_input = ft.TextField(value="500", width=80, on_change=on_humantyper_change, suffix_text="ms")
    humantyper_para_pause_max_slider = ft.Slider(min=500, max=5000, divisions=18, label="{value}ms", value=2000, on_change=on_humantyper_change, expand=True)
    humantyper_para_pause_max_input = ft.TextField(value="2000", width=80, on_change=on_humantyper_change, suffix_text="ms")
    # Special character delay toggle
    humantyper_special_char_delay_switch = ft.Switch(label="Special Character Delay (pause before symbols)", value=False, on_change=on_humantyper_change)
    # Emotion Simulator controls
    humantyper_crashout_switch = ft.Switch(label="Crashout Mode", value=False, on_change=on_humantyper_change)
    humantyper_crashout_count_input = ft.TextField(value="1", width=50, on_change=on_humantyper_change, text_align=ft.TextAlign.CENTER)
    humantyper_nihilism_switch = ft.Switch(label="Nihilism Mode", value=False, on_change=on_humantyper_change)
    humantyper_nihilism_count_input = ft.TextField(value="1", width=50, on_change=on_humantyper_change, text_align=ft.TextAlign.CENTER)
    humantyper_vamp_switch = ft.Switch(label="Vamp Mode", value=False, on_change=on_humantyper_change)
    humantyper_vamp_count_input = ft.TextField(value="1", width=50, on_change=on_humantyper_change, text_align=ft.TextAlign.CENTER)
    humantyper_start_btn = ft.ElevatedButton(
        text="Start Typing (3s delay)",
        on_click=start_humantyper_click,
        bgcolor="#616161",
        color="white",
        height=45,
        style=ft.ButtonStyle(text_style=ft.TextStyle(size=16))
    )
    
    def resume_humantyper_click(e):
        core.resume_humantyper()
    
    humantyper_resume_btn = ft.ElevatedButton(
        text="Resume Typing (3s delay)",
        on_click=lambda e: resume_with_delay(),
        bgcolor="#4caf50",
        color="white",
        height=45,
        visible=False,
        style=ft.ButtonStyle(text_style=ft.TextStyle(size=16))
    )
    
    humantyper_pause_text = ft.Text(
        "⚠️ Typing paused - mouse click detected. Click Resume to continue from where you stopped.",
        color="#ffa726",
        size=12,
        italic=True,
        visible=False
    )
    
    def resume_with_delay():
        humantyper_resume_btn.text = "Resuming in 3..."
        humantyper_resume_btn.disabled = True
        page.update()
        
        def countdown_and_resume():
            for i in [3, 2, 1]:
                humantyper_resume_btn.text = f"Resuming in {i}..."
                page.update()
                time.sleep(1)
            core.resume_humantyper()
            humantyper_resume_btn.text = "Resume Typing (3s delay)"
            humantyper_resume_btn.disabled = False
            page.update()
        
        threading.Thread(target=countdown_and_resume, daemon=True).start()

    humantyper_content = ft.Column([
        ft.Container(
            content=ft.Column([
                ft.Text("Human Typer", style="headlineMedium"),
                ft.Text("Simulates human-like typing with natural delays and occasional typos.", color="grey"),
                humantyper_text_input,
                ft.Text("Speed Range (WPM)"),
                ft.Row([
                    ft.Text("Min:", width=30),
                    humantyper_wpm_min_slider,
                    humantyper_wpm_min_input,
                    ft.Text("Max:", width=35),
                    humantyper_wpm_max_slider,
                    humantyper_wpm_max_input
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Text("Error Rate (% chance per character)"),
                ft.Row([humantyper_error_slider, humantyper_error_input], alignment="spaceBetween"),
                ft.Text("Typo Style"),
                humantyper_typomode_radio,
                ft.Text("Typo Correction Delay (how fast to fix typos)"),
                ft.Row([humantyper_correction_slider, humantyper_correction_input], alignment="spaceBetween"),
                ft.Text("Max Consecutive Typos"),
                ft.Row([humantyper_maxtypos_slider, humantyper_maxtypos_input], alignment="spaceBetween"),
                ft.Divider(),
                ft.Text("Thinking Pauses", style="titleMedium"),
                ft.Text("Simulates pauses when 'thinking' between words.", color="grey"),
                ft.Text("Pause Duration Range (ms)"),
                ft.Row([
                    ft.Text("Min:", width=30),
                    humantyper_pause_min_slider,
                    humantyper_pause_min_input,
                    ft.Text("Max:", width=35),
                    humantyper_pause_max_slider,
                    humantyper_pause_max_input
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Text("Pause Frequency (% chance at each word)"),
                ft.Row([humantyper_pause_freq_slider, humantyper_pause_freq_input], alignment="spaceBetween"),
                ft.Divider(),
                ft.Text("Sentence / Paragraph Pauses", style="titleMedium"),
                ft.Text("Pauses after sentences (.!?) and paragraphs (new lines).", color="grey"),
                humantyper_sentence_pause_switch,
                ft.Text("Sentence Pause: Frequency"),
                ft.Row([humantyper_sentence_pause_freq_slider, humantyper_sentence_pause_freq_input], alignment="spaceBetween"),
                ft.Text("Sentence Pause: Duration (ms)"),
                ft.Row([
                    ft.Text("Min:", width=30),
                    humantyper_sentence_pause_min_slider,
                    humantyper_sentence_pause_min_input,
                    ft.Text("Max:", width=35),
                    humantyper_sentence_pause_max_slider,
                    humantyper_sentence_pause_max_input
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                humantyper_para_pause_switch,
                ft.Text("Paragraph Pause: Frequency"),
                ft.Row([humantyper_para_pause_freq_slider, humantyper_para_pause_freq_input], alignment="spaceBetween"),
                ft.Text("Paragraph Pause: Duration (ms)"),
                ft.Row([
                    ft.Text("Min:", width=30),
                    humantyper_para_pause_min_slider,
                    humantyper_para_pause_min_input,
                    ft.Text("Max:", width=35),
                    humantyper_para_pause_max_slider,
                    humantyper_para_pause_max_input
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Divider(),
                ft.Text("Special Character Delay", style="titleMedium"),
                ft.Text("Pauses 500-1500ms before typing symbols (simulates looking for keys).", color="grey"),
                humantyper_special_char_delay_switch,
                ft.Divider(),
                ft.Text("Synonym Swap", style="titleMedium"),
                ft.Text("Types a synonym first, then corrects to the intended word.", color="grey"),
                humantyper_synonym_switch,
                ft.Text("Swap Frequency (% chance per word)"),
                ft.Row([humantyper_synonym_freq_slider, humantyper_synonym_freq_input], alignment="spaceBetween"),
                ft.Divider(),
                ft.Text("Emotion Simulator", style="titleMedium"),
                ft.Text("Triggers after 20% of text is typed. Won't happen back-to-back.", color="grey"),
                ft.Row([humantyper_crashout_switch, ft.Text("Times:", size=12), humantyper_crashout_count_input], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Text("Crashout: Quickly spam random letters like raging, then deletes them.", color="grey", size=11, italic=True),
                ft.Row([humantyper_nihilism_switch, ft.Text("Times:", size=12), humantyper_nihilism_count_input], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Text("Nihilism: Type a nihilistic phrase, pause to contemplate, then deletes it.", color="grey", size=11, italic=True),
                ft.Row([humantyper_vamp_switch, ft.Text("Times:", size=12), humantyper_vamp_count_input], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Text("Vamp: Type random Playboi Carti lyrics when bored, then deletes them. (these lyrics are not explicit you won't get in trouble don't worry lol)", color="grey", size=11, italic=True),
                humantyper_start_btn,
                humantyper_resume_btn,
                humantyper_pause_text,
            ], spacing=8),
            padding=ft.padding.only(right=15)
        )
    ], scroll="auto", expand=True)

    # --- Keyboard Macro Controls ---
    def on_kb_change(e):
        try:
            delay = float(kb_delay_slider.value)
        except:
            delay = 100.0
            
        core.update_kb_macro(
            kb_switch.value,
            core.kb_macro_key, # Use current key in core
            delay / 1000.0
        )
        kb_delay_input.value = str(int(kb_delay_slider.value))
        page.update()

    def on_kb_text_change(e):
        try:
            val = float(kb_delay_input.value)
            kb_delay_slider.value = val
            core.update_kb_macro(kb_switch.value, core.kb_macro_key, val / 1000.0)
            page.update()
        except ValueError:
            pass

    def on_bind_click(e):
        kb_bind_btn.text = "Waiting... Press any key"
        kb_bind_btn.disabled = True
        page.update()
        core.start_key_binding(on_kb_bound)

    def on_kb_bound(key_data):
        if isinstance(key_data, dict):
            if key_data['type'] == 'mouse':
                kb_bind_btn.text = "Target Key: Keys Only!"
                page.update()
                kb_bind_btn.disabled = False
                return
            key_name = key_data['name']
        else:
            key_name = str(key_data)

        kb_bind_btn.text = f"Target Key: {key_name}"
        kb_bind_btn.disabled = False
        page.update()
        # Trigger update to ensure core has fresh state if needed, though core.kb_macro_key is already set
        core.update_kb_macro(kb_switch.value, core.kb_macro_key, float(kb_delay_slider.value) / 1000.0)

    kb_switch = ft.Switch(label="Enable Keyboard Macro", on_change=on_kb_change)
    kb_delay_slider = ft.Slider(min=10, max=1000, divisions=99, label="{value} ms", value=100, on_change=on_kb_change, expand=True)
    kb_delay_input = ft.TextField(value="100", width=100, on_change=on_kb_text_change, suffix_text="ms")
    kb_bind_btn = ft.ElevatedButton(text="Target Key: A (Default)", on_click=on_bind_click)

    # KB Bind Button Wrapper
    # Since kb_bind_btn text changes, we need a way to update the button inside the container
    # However, create_animated_button returns a container. The button is content.
    # To support dynamic text updates, it's better to keep the button variable active and just wrap it in-place or use a reference.
    # We'll just define the container inline for dynamic buttons to simple animation
    
    kb_bind_container = ft.Container(
        content=kb_bind_btn,
        on_hover=animate_hover,
        scale=1.0,
        animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK)
    )

    kb_content = ft.Column([
        ft.Text("Keyboard Macro", style="headlineMedium"),
        kb_switch,
        ft.Text("Target Key to Spam"),
        kb_bind_container, # Use container
        ft.Text("Press Interval"),
        ft.Row([kb_delay_slider, kb_delay_input], alignment="spaceBetween"),
        ft.Text("Activation: Press 'F5' to Toggle ON/OFF", color="grey")
    ])

    # --- Custom Macro Page ---
    custom_macros_list = ft.ListView(expand=True, spacing=10)
    
    # Dialog State
    new_macro_name = ft.TextField(label="Macro Name")
    new_macro_trigger = {"type": None, "value": None, "name": "None"}
    new_macro_actions = []
    
    btn_bind_trigger = ft.ElevatedButton("Bind Trigger")
    btn_record_action = ft.ElevatedButton("Record Action (Press Keys)")
    
    def update_trigger_btn():
        btn_bind_trigger.text = f"Trigger: {new_macro_trigger['name']}"
        page.update()

    def on_trigger_bound(data):
        nonlocal new_macro_trigger
        new_macro_trigger = data
        update_trigger_btn()
        btn_bind_trigger.disabled = False
        page.update()

    def bind_trigger_click(e):
        btn_bind_trigger.text = "Waiting..."
        btn_bind_trigger.disabled = True
        page.update()
        core.start_key_binding(on_trigger_bound)

    def on_action_recorded(sc):
        if sc not in new_macro_actions:
            new_macro_actions.append(sc)
        
        try:
            names = [input_utils.get_key_name(int(s)) for s in new_macro_actions]
            display_text = " + ".join(names)
        except Exception as e:
            display_text = f"Err: {e}"
        
        btn_record_action.text = f"Action: {display_text} (Click to Stop)"
        page.update()

    def toggle_record_action(e):
        if core.is_recording_action:
            core.stop_action_recording()
            try:
                names = [input_utils.get_key_name(int(s)) for s in new_macro_actions]
                display_text = " + ".join(names) if names else "None"
            except Exception as e:
                 display_text = f"Err: {e}"
            btn_record_action.text = f"Action: {display_text} (Click to Redo)"
            btn_record_action.bgcolor = None
        else:
            new_macro_actions.clear()
            core.start_action_recording(on_action_recorded)
            btn_record_action.text = "Waiting... Press Keys Now (Click to Stop)"
            btn_record_action.bgcolor = "red"
        page.update()

    def refresh_macro_list():
        custom_macros_list.controls.clear()
        for m in core.custom_macros:
            act_scs = m.get('actions', [])
            try:
                names = [input_utils.get_key_name(int(s)) for s in act_scs]
                display_actions = " + ".join(names) if names else "None"
            except Exception as e:
                display_actions = f"Error: {e}"
                
            custom_macros_list.controls.append(
                ft.ListTile(
                    title=ft.Text(m['name']),
                    subtitle=ft.Text(f"Trigger: {m['trigger']['name']} | Actions: {display_actions}"),
                    trailing=ft.Row([
                        ft.IconButton("edit", on_click=lambda e, mac=m: edit_macro(mac)),
                        ft.IconButton("delete", on_click=lambda e, mid=m['id']: delete_macro(mid))
                    ], alignment=ft.MainAxisAlignment.END, width=100)
                )
            )
        page.update()

    editing_macro_id = None

    def add_macro_click(e):
        try:
            nonlocal editing_macro_id
            if not new_macro_name.value or not new_macro_trigger['value'] or not new_macro_actions:
                page.snack_bar = ft.SnackBar(ft.Text("Please fill all fields!"))
                page.snack_bar.open = True
                page.update()
                return

            if editing_macro_id:
                for m in core.custom_macros:
                    if m['id'] == editing_macro_id:
                        m['name'] = new_macro_name.value
                        m['trigger'] = new_macro_trigger.copy()
                        m['actions'] = new_macro_actions.copy()
                        break
            else:
                macro = {
                    "id": str(uuid.uuid4()),
                    "name": new_macro_name.value,
                    "trigger": new_macro_trigger.copy(),
                    "actions": new_macro_actions.copy()
                }
                core.custom_macros.append(macro)
            
            core.update_custom_macros(core.custom_macros)
            save_macros()
            refresh_macro_list()
            add_macro_dialog.open = False
            editing_macro_id = None
            page.update()
        except Exception as ex:
            add_macro_dialog.title.value = f"Error: {ex}"
            page.update()

    add_macro_dialog = ft.AlertDialog(
        title=ft.Text("Add Custom Macro"),
        content=ft.Column([
            new_macro_name,
            ft.Text("1. Trigger (Key or Mouse Button)"),
            btn_bind_trigger,
            ft.Text("2. Action (Keys to press simultaneously)"),
            btn_record_action
        ], tight=True),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: setattr(add_macro_dialog, 'open', False) or page.update()),
            ft.TextButton("Save", on_click=add_macro_click),
        ],
    )
    page.overlay.append(add_macro_dialog)

    def open_add_macro_dialog(e):
        nonlocal editing_macro_id, new_macro_trigger, new_macro_actions
        editing_macro_id = None
        add_macro_dialog.title.value = "Add Custom Macro"
        
        # Ensure recording is stopped
        core.stop_action_recording()
        core.is_binding = False
        
        new_macro_name.value = ""
        new_macro_trigger = {"type": None, "value": None, "name": "None"}
        new_macro_actions = []
        update_trigger_btn()
        btn_record_action.text = "Record Action"
        btn_record_action.bgcolor = None
        
        add_macro_dialog.open = True
        page.update()

    def edit_macro(macro):
        nonlocal editing_macro_id, new_macro_trigger, new_macro_actions
        editing_macro_id = macro['id']
        add_macro_dialog.title.value = "Edit Custom Macro"
        
        new_macro_name.value = macro['name']
        new_macro_trigger = macro['trigger'].copy()
        new_macro_actions = macro['actions'].copy()
        
        update_trigger_btn()
        btn_record_action.text = f"Action: {len(new_macro_actions)} keys (Click to Redo)"
        btn_record_action.bgcolor = None
        
        add_macro_dialog.open = True
        page.update()

    def delete_macro(m_id):
        core.custom_macros = [m for m in core.custom_macros if m['id'] != m_id]
        core.update_custom_macros(core.custom_macros)
        save_macros()
        refresh_macro_list()

    btn_bind_trigger.on_click = bind_trigger_click
    btn_record_action.on_click = toggle_record_action

    # Custom Macro Buttons with Animation
    btn_bind_trigger_anim = ft.Container(
        content=btn_bind_trigger,
        on_hover=animate_hover,
        scale=1.0,
        animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK)
    )
    btn_record_action_anim = ft.Container(
        content=btn_record_action,
        on_hover=animate_hover,
        scale=1.0,
        animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK)
    )
    
    add_mac_btn = create_animated_button("Add New Macro", "add", open_add_macro_dialog)

    custom_macro_content = ft.Column([
        ft.Row([
            ft.Text("Custom Macros", style="headlineMedium"),
            add_mac_btn
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        custom_macros_list
    ])
    
    # Populate list from loaded macros
    refresh_macro_list()

    # --- Info Controls ---
    feature_cards = []  # Store cards for theme toggle updates
    
    def create_feature_card(title, content):
        """Create a styled container for a feature section."""
        card = ft.Container(
            content=ft.Column([
                ft.Text(title, style="titleMedium", weight="bold"),
                ft.Markdown(content, extension_set="gitHubWeb")
            ], spacing=5),
            bgcolor="#1e1e1e",
            border=ft.border.all(1, "#333333"),
            border_radius=12,
            padding=15,
            expand=True,  # Expand within the Row
        )
        feature_cards.append(card)
        # Row forces full width, Container expand fills it
        return ft.Row([card])
    
    humantyper_info = """
- **Function**: Simulates human-like typing with natural delays and typos.
- **Speed Range**: Set min/max WPM for realistic speed variation.
- **Error Rate**: Adjust typo frequency (0-20%).
- **Typo Style**: Choose adjacent keys (realistic) or random letters.
- **Correction Delay**: Control how fast typos are fixed (20-1000ms).
- **Max Typos**: Allow multiple consecutive typos before correction.
- **Thinking Pauses**: Random pauses between words (100-5000ms).
- **Sentence Pauses**: Pauses after sentences (.!?).
- **Paragraph Pauses**: Pauses after new lines.
- **Special Character Delay**: Pauses 500-1500ms before typing symbols.
- **Synonym Swap**: Types a synonym first, then corrects to intended word.
- **Emotion Simulator**: Simulates emotional moments mid-typing.
  - **Crashout**: Rage-mashes random characters, then deletes.
  - **Nihilism**: Types existential phrases, then deletes.
  - **Vamp**: Types Playboi Carti lyrics, then deletes.
- **Auto-Pause on Click**: Pauses if mouse clicked to prevent wrong location.
- **Resume/Stop**: Continue from where stopped or cancel completely.

*Inspired by Final-Typer by Peteryhs*
"""

    recoil_info = """
- **Save/Load**: Save settings to .ini file or load previous config.
- **Activation**: Choose **LMB Only** or **LMB + RMB**. Hotkey: **F4**.
- **Directional**: Vertical (Up/Down) & Horizontal (Left/Right).
"""

    keyboard_info = """
- **Setup**: Click **"Target Key"** to bind any key.
- **Activation**: Toggle switch or press **F5**.
"""

    autoclicker_info = """
- **Activation**: Toggle switch or press **F6**.
- **Interval**: Adjustable click delay (1-1000ms).
"""

    antiafk_info = """
- **Activation**: Toggle switch or press **F7**.
- **Movement**: Cursor moves in random direction then returns.
- **Random Speed**: Movement speed varies to avoid detection.
- **Settings**: Adjust magnitude and interval.
"""

    cameraspin_info = """
- **Activation**: Toggle switch or press **F8**.
- **Function**: Continuously moves cursor horizontally (spins camera).
- **Direction**: Choose **Right** or **Left** spin direction.
- **Speed**: Adjust pixels per tick for faster/slower spinning.
"""

    custommacro_info = """
- **Create**: Click **+** button to add a new macro.
- **Trigger**: Bind any keyboard key or mouse button.
- **Actions**: Record multiple keys to press simultaneously.
- **Hold to Repeat**: Actions repeat while holding trigger.
- **Persistence**: Macros saved and restored on restart.
- **Edit/Delete**: Use buttons next to each macro.
"""

    humantyper_card = create_feature_card("Human Typer", humantyper_info)
    recoil_card = create_feature_card("Recoil Control", recoil_info)
    keyboard_card = create_feature_card("Keyboard Macro", keyboard_info)
    autoclicker_card = create_feature_card("Auto Clicker", autoclicker_info)
    antiafk_card = create_feature_card("Anti-AFK", antiafk_info)
    cameraspin_card = create_feature_card("Camera Spin", cameraspin_info)
    custommacro_card = create_feature_card("Custom Macros", custommacro_info)
    
    important_card = ft.Container(
        content=ft.Row([
            ft.Icon("warning", color="#c62828", size=30),
            ft.Column([
                ft.Text("IMPORTANT", color="#c62828", weight="bold"),
                ft.Text("Run as Administrator is necessary; features might not work without it.", color="#b71c1c")
            ], spacing=2)
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor="#26ff5252",
        border=ft.border.all(1, "#ef5350"),
        border_radius=10,
        padding=15,
        margin=ft.margin.only(top=10, bottom=20)
    )

    # Logo image (use relative path from assets_dir for Flet to resolve correctly)
    logo_image = ft.Image(src="icon.png", width=40, height=40)

    # Theme toggle
    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = "#fafafa"
            theme_toggle.label = "Light"
            theme_toggle.thumb_icon = "light_mode"
            logo_image.color = "#000000"  # Black logo for light mode
            # Update feature cards for light mode
            for card in feature_cards:
                card.bgcolor = "#ffffff"
                card.border = ft.border.all(1, "#e0e0e0")
        else:
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = "#121212"
            theme_toggle.label = "Dark"
            theme_toggle.thumb_icon = "dark_mode"
            logo_image.color = None  # Original logo for dark mode
            # Update feature cards for dark mode
            for card in feature_cards:
                card.bgcolor = "#1e1e1e"
                card.border = ft.border.all(1, "#333333")
        page.update()
    
    theme_toggle = ft.Switch(
        label="Dark",
        value=True,
        on_change=toggle_theme,
        active_color="#9e9e9e",
        thumb_icon="dark_mode",
    )

    info_content = ft.Column([
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Row([
                            logo_image,
                            ft.Text("OmniMacro", size=30, weight="bold"),
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        ft.Row([
                            ft.Text("made by Entropify", size=12, color="grey", italic=True),
                            ft.Text("•", size=12, color="grey"),
                            ft.Text("v1.0.1", size=12, color="grey", italic=True)
                        ], spacing=5)
                    ], spacing=2),
                    theme_toggle
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Divider(),
                important_card,
                humantyper_card,
                recoil_card,
                keyboard_card,
                autoclicker_card,
                antiafk_card,
                cameraspin_card,
                custommacro_card,
            ], spacing=10),
            padding=ft.padding.only(right=15)
        )
    ], scroll="auto", expand=True)
    
    # Dialog content refresh
    # The dialog uses `btn_bind_trigger` and `btn_record_action`. 
    # We need to make sure the dialog uses the ANIMATED versions (Containers) or we just animate the buttons themselves?
    # Flet buttons don't have scale/animate_scale properties directly, they must be in a container.
    # So we updated the dialog content to use the containers:
    add_macro_dialog.content = ft.Column([
            new_macro_name,
            ft.Text("1. Trigger (Key or Mouse Button)"),
            btn_bind_trigger_anim,
            ft.Text("2. Action (Keys to press simultaneously)"),
            btn_record_action_anim
        ], tight=True)


    # --- Navigation ---
    def on_nav_change(e):
        # Determine which index is selected and change visible content
        idx = e.control.selected_index
        if idx == 0:
            switcher.content = info_content
        elif idx == 1:
            switcher.content = humantyper_content
        elif idx == 2:
            switcher.content = recoil_content
        elif idx == 3:
            switcher.content = kb_content
        elif idx == 4:
            switcher.content = autoclick_content
        elif idx == 5:
            switcher.content = antiafk_content
        elif idx == 6:
            switcher.content = custom_macro_content
        page.update()

    rail = ft.NavigationRail(
        selected_index=0,
        label_type="all",
        min_width=100,
        min_extended_width=200,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon="info", selected_icon="info_outlined", label="Info"
            ),
            ft.NavigationRailDestination(
                icon="edit", selected_icon="edit_outlined", label="Typer"
            ),
            ft.NavigationRailDestination(
                icon="arrow_downward", selected_icon="arrow_downward", label="Recoil"
            ),
            ft.NavigationRailDestination(
                icon="keyboard", selected_icon="keyboard_outlined", label="Keyboard"
            ),
            ft.NavigationRailDestination(
                icon="mouse", selected_icon="mouse_outlined", label="Auto Click"
            ),
            ft.NavigationRailDestination(
                icon="snooze", selected_icon="snooze_outlined", label="Anti-AFK"
            ),
            ft.NavigationRailDestination(
                icon="extension", selected_icon="extension_outlined", label="Custom"
            ),
        ],
        on_change=on_nav_change,
    )

    switcher = ft.AnimatedSwitcher(
        info_content,
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=500,
        reverse_duration=100,
        switch_in_curve=ft.AnimationCurve.EASE_IN,
        switch_out_curve=ft.AnimationCurve.EASE_OUT,
    )

    content_area = ft.Container(content=switcher, expand=True, padding=ft.padding.only(left=20, right=0, bottom=20, top=0))
    
    main_layout = ft.Row(
            [
                rail,
                ft.VerticalDivider(width=1),
                content_area,
            ],
            expand=True,
        )

    page.add(main_layout)

    def on_window_event(e):
        if e.data == "close":
            core.stop()
            page.window_destroy()

    page.on_window_event = on_window_event

ft.app(target=main, assets_dir="assets")
