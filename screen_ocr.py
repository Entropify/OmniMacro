"""
Screen OCR — Region capture and text extraction using Tesseract OCR.
Captures a user-selected screen region and extracts text via OCR.
Tesseract binary is bundled for PyInstaller distribution.
"""

import sys
import os
import threading
import time
import shutil
import ctypes
from datetime import datetime

from PIL import ImageGrab, ImageEnhance, ImageTk, Image
import pytesseract


# ─── Debug Logging ────────────────────────────────────────────────────────────

def _debug_log(msg):
    """Write debug info to file for diagnosing OCR issues."""
    try:
        with open('debug_log.txt', 'a') as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S.%f')}] {msg}\n")
    except Exception:
        pass


# ─── Tesseract Path Detection ─────────────────────────────────────────────────

def _find_tesseract():
    """Find the Tesseract executable, checking bundled location first."""
    if getattr(sys, 'frozen', False):
        bundled = os.path.join(sys._MEIPASS, 'tesseract', 'tesseract.exe')
        if os.path.exists(bundled):
            os.environ['TESSDATA_PREFIX'] = os.path.join(sys._MEIPASS, 'tesseract', 'tessdata')
            return bundled

    for path in [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ]:
        if os.path.exists(path):
            return path

    found = shutil.which('tesseract')
    if found:
        return found
    return None


_tesseract_path = _find_tesseract()
if _tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_path


def is_tesseract_available():
    return _tesseract_path is not None and os.path.exists(_tesseract_path)


def get_tesseract_status():
    if is_tesseract_available():
        return f"✅ Tesseract found: {_tesseract_path}"
    return "❌ Tesseract not found. Install from: https://github.com/UB-Mannheim/tesseract/wiki"


# ─── Screen OCR Class ─────────────────────────────────────────────────────────

class ScreenOCR:
    """Handles screen region capture and OCR text extraction."""

    def __init__(self):
        self.last_text = ""
        self.history = []
        self._capturing = False

    def capture_and_ocr(self, on_complete=None, on_error=None,
                        on_cancel=None, minimize_window=None,
                        restore_window=None):
        if self._capturing:
            return
        self._capturing = True

        def _run():
            old_dpi_ctx = None
            try:
                _debug_log("OCR capture started")

                if not is_tesseract_available():
                    _debug_log("Tesseract not available")
                    if on_error:
                        on_error(
                            "Tesseract OCR not found.\n"
                            "Install from: https://github.com/UB-Mannheim/tesseract/wiki\n"
                            "Then restart OmniMacro."
                        )
                    return

                # Minimize app window to get clean screenshot
                if minimize_window:
                    minimize_window()
                    time.sleep(0.5)

                # Show region selector and capture
                _debug_log("Starting region selector")
                image = self._select_region()
                _debug_log(f"Region selector returned, image={'present' if image else 'None'}")

                # Restore app window
                if restore_window:
                    restore_window()
                    time.sleep(0.3)

                if image is None:
                    _debug_log("Capture cancelled by user")
                    if on_cancel:
                        on_cancel()
                    return

                _debug_log(f"Captured image size: {image.size}, mode: {image.mode}")

                # Run OCR
                _debug_log("Running pytesseract...")
                text = pytesseract.image_to_string(image).strip()
                _debug_log(f"OCR result length: {len(text)}, preview: {repr(text[:200])}")

                if text:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.history.insert(0, (timestamp, text))
                    if len(self.history) > 20:
                        self.history = self.history[:20]
                    self.last_text = text

                    _debug_log("Calling on_complete callback...")
                    if on_complete:
                        try:
                            on_complete(text)
                        except Exception as cb_err:
                            _debug_log(f"on_complete callback error: {cb_err}")
                    _debug_log("on_complete done")
                else:
                    _debug_log("No text detected")
                    if on_error:
                        on_error("No text detected in the selected region.")

            except Exception as e:
                _debug_log(f"EXCEPTION: {type(e).__name__}: {e}")
                if restore_window:
                    try:
                        restore_window()
                    except Exception:
                        pass
                if on_error:
                    try:
                        on_error(f"OCR Error: {str(e)}")
                    except Exception:
                        pass
            finally:
                self._capturing = False
                _debug_log("Capture flow finished")

        threading.Thread(target=_run, daemon=True).start()

    def _select_region(self):
        """
        Show a fullscreen overlay and let the user drag-select a region.
        Returns a PIL Image of the selected region, or None if cancelled.
        """
        import tkinter as tk

        result = {'image': None}

        # Take screenshot at native resolution
        screenshot = ImageGrab.grab()
        ss_width, ss_height = screenshot.size
        _debug_log(f"Screenshot captured: {ss_width}x{ss_height}")

        def run_selector():
            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes('-topmost', True)
            root.configure(cursor='cross')

            root.update_idletasks()
            tk_width = root.winfo_screenwidth()
            tk_height = root.winfo_screenheight()
            _debug_log(f"Tkinter screen: {tk_width}x{tk_height}")

            # Position window to cover full screen
            root.geometry(f"{tk_width}x{tk_height}+0+0")

            # Calculate scale factors for coordinate mapping
            scale_x = ss_width / tk_width
            scale_y = ss_height / tk_height
            _debug_log(f"Scale factors: x={scale_x:.2f}, y={scale_y:.2f}")

            # Resize screenshot to match tkinter's display dimensions if needed
            if abs(scale_x - 1.0) > 0.01 or abs(scale_y - 1.0) > 0.01:
                display_screenshot = screenshot.resize(
                    (tk_width, tk_height), Image.LANCZOS
                )
            else:
                display_screenshot = screenshot

            # Create canvas filling entire window
            canvas = tk.Canvas(root, width=tk_width, height=tk_height,
                               highlightthickness=0, bg='black')
            canvas.pack(fill='both', expand=True)

            # Dimmed background
            dimmed = display_screenshot.copy()
            enhancer = ImageEnhance.Brightness(dimmed)
            dimmed = enhancer.enhance(0.4)
            photo = ImageTk.PhotoImage(dimmed)
            canvas.create_image(0, 0, anchor='nw', image=photo)

            # Instruction text
            canvas.create_text(
                tk_width // 2, 30,
                text="Click and drag to select a region  |  Press ESC to cancel",
                fill='white', font=('Segoe UI', 14)
            )

            # State tracking
            state = {'x1': 0, 'y1': 0, 'rect_id': None, 'destroyed': False}

            def close_window():
                """Safely close the overlay window once."""
                if state['destroyed']:
                    return
                state['destroyed'] = True
                _debug_log("Closing overlay window")
                try:
                    root.quit()
                    root.destroy()
                except Exception:
                    pass

            def on_press(event):
                state['x1'] = event.x
                state['y1'] = event.y
                _debug_log(f"Mouse press at ({event.x}, {event.y})")
                if state['rect_id']:
                    canvas.delete(state['rect_id'])
                state['rect_id'] = canvas.create_rectangle(
                    event.x, event.y, event.x, event.y,
                    outline='#00bcd4', width=2
                )

            def on_drag(event):
                if state['rect_id']:
                    canvas.coords(state['rect_id'],
                                  state['x1'], state['y1'],
                                  event.x, event.y)

            def on_release(event):
                x1 = min(state['x1'], event.x)
                y1 = min(state['y1'], event.y)
                x2 = max(state['x1'], event.x)
                y2 = max(state['y1'], event.y)

                drag_w = x2 - x1
                drag_h = y2 - y1
                _debug_log(f"Mouse release: ({x1},{y1})-({x2},{y2}) size={drag_w}x{drag_h}")

                if drag_w > 10 and drag_h > 10:
                    crop_x1 = max(0, min(int(x1 * scale_x), ss_width))
                    crop_y1 = max(0, min(int(y1 * scale_y), ss_height))
                    crop_x2 = max(0, min(int(x2 * scale_x), ss_width))
                    crop_y2 = max(0, min(int(y2 * scale_y), ss_height))

                    _debug_log(f"Crop: native ({crop_x1},{crop_y1})-({crop_x2},{crop_y2})")
                    result['image'] = screenshot.crop(
                        (crop_x1, crop_y1, crop_x2, crop_y2)
                    )
                else:
                    _debug_log(f"Selection too small: {drag_w}x{drag_h}")

                close_window()

            # Bind mouse events
            canvas.bind('<ButtonPress-1>', on_press)
            canvas.bind('<B1-Motion>', on_drag)
            canvas.bind('<ButtonRelease-1>', on_release)
            canvas.bind('<ButtonPress-3>', lambda e: close_window())

            # Poll for Escape key via Win32 API — bypasses tkinter focus issues
            VK_ESCAPE = 0x1B

            def check_escape():
                if state['destroyed']:
                    return
                try:
                    if ctypes.windll.user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000:
                        _debug_log("ESC detected via GetAsyncKeyState")
                        close_window()
                        return
                    root.after(50, check_escape)
                except Exception:
                    pass

            # Show window, then force it to the front and start ESC polling
            root.update()
            root.lift()
            root.after(100, check_escape)

            _debug_log("Entering tkinter mainloop")
            root.mainloop()
            _debug_log("Exited tkinter mainloop")

        run_selector()
        return result['image']

    def clear_history(self):
        self.history.clear()
        self.last_text = ""
