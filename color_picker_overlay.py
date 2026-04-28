"""
Color Picker Overlay — Region selector and eyedropper tool for Color Clicker.
Provides two Tkinter-based screen interaction tools:
  - select_region(): Let user drag-draw a rectangle; returns (x1,y1,x2,y2) or None.
  - pick_color():    Eyedropper with live magnifier; returns (r,g,b) or None.
"""

import ctypes
import threading
import time

from PIL import ImageGrab, ImageEnhance, ImageTk, Image


# ─── Shared Helper ───────────────────────────────────────────────────────────

def _take_screenshot():
    """
    Grab a screenshot and return (image, tk_w, tk_h, scale_x, scale_y).

    IMPORTANT: We deliberately avoid creating a temporary tk.Tk() here.
    Creating and destroying a Tk root, then creating another one in the same
    thread, corrupts the Tcl interpreter state and causes crashes.  Instead,
    we read screen dimensions via Win32 GetSystemMetrics — called in the same
    DPI context as PIL uses — so the numbers match Tkinter's logical pixels
    without ever touching the Tk runtime.
    """
    screenshot = ImageGrab.grab()
    ss_w, ss_h = screenshot.size

    # GetSystemMetrics(0/1) in the current process DPI context matches what
    # Tkinter's winfo_screenwidth/height would return (both use logical coords).
    tk_w = ctypes.windll.user32.GetSystemMetrics(0)  # SM_CXSCREEN
    tk_h = ctypes.windll.user32.GetSystemMetrics(1)  # SM_CYSCREEN
    if tk_w <= 0 or tk_h <= 0:
        tk_w, tk_h = ss_w, ss_h

    scale_x = ss_w / tk_w
    scale_y = ss_h / tk_h
    return screenshot, tk_w, tk_h, scale_x, scale_y


# ─── Region Selector ─────────────────────────────────────────────────────────

def select_region(minimize_fn=None, restore_fn=None):
    """
    Show a fullscreen dimmed overlay and let the user drag-select a rectangle.
    Returns (x1, y1, x2, y2) in true screen coordinates, or None if cancelled.
    """
    if minimize_fn:
        minimize_fn()
        time.sleep(0.45)

    result = {'coords': None}

    def run():
        import tkinter as tk

        screenshot, tk_w, tk_h, scale_x, scale_y = _take_screenshot()

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes('-topmost', True)
        root.configure(cursor='cross')
        root.geometry(f"{tk_w}x{tk_h}+0+0")

        # Scale screenshot for display
        if abs(scale_x - 1.0) > 0.01 or abs(scale_y - 1.0) > 0.01:
            display = screenshot.resize((tk_w, tk_h), Image.LANCZOS)
        else:
            display = screenshot

        canvas = tk.Canvas(root, width=tk_w, height=tk_h,
                           highlightthickness=0, bg='black')
        canvas.pack(fill='both', expand=True)

        dimmed = display.copy()
        dimmed = ImageEnhance.Brightness(dimmed).enhance(0.4)
        photo = ImageTk.PhotoImage(dimmed)
        canvas.create_image(0, 0, anchor='nw', image=photo)

        canvas.create_text(
            tk_w // 2, 32,
            text="Drag to select region  |  ESC or Right-click to cancel",
            fill='white', font=('Segoe UI', 13)
        )

        state = {'x1': 0, 'y1': 0, 'rect': None, 'info': None, 'destroyed': False}

        def close(cancelled=False):
            if state['destroyed']:
                return
            state['destroyed'] = True
            if cancelled:
                result['coords'] = None
            try:
                root.destroy()
            except Exception:
                pass

        def on_press(e):
            state['x1'] = e.x
            state['y1'] = e.y
            if state['rect']:
                canvas.delete(state['rect'])
            state['rect'] = canvas.create_rectangle(
                e.x, e.y, e.x, e.y,
                outline='#00e5ff', width=2, dash=(4, 2)
            )

        def on_drag(e):
            if state['rect']:
                canvas.coords(state['rect'], state['x1'], state['y1'], e.x, e.y)
            # Show size info
            w = abs(e.x - state['x1'])
            h = abs(e.y - state['y1'])
            if state['info']:
                canvas.delete(state['info'])
            state['info'] = canvas.create_text(
                e.x + 10, e.y + 10,
                text=f"{int(w * scale_x)}×{int(h * scale_y)} px",
                fill='#00e5ff', font=('Consolas', 10), anchor='nw'
            )

        def on_release(e):
            x1 = min(state['x1'], e.x)
            y1 = min(state['y1'], e.y)
            x2 = max(state['x1'], e.x)
            y2 = max(state['y1'], e.y)
            # 4 Tk-pixel minimum (tolerant on hi-DPI where scale_x/y > 1)
            if (x2 - x1) > 4 and (y2 - y1) > 4:
                # Convert to true screen pixels
                result['coords'] = (
                    int(x1 * scale_x), int(y1 * scale_y),
                    int(x2 * scale_x), int(y2 * scale_y)
                )
                close()
            else:
                # Show "too small" warning and let the user try again
                if state['info']:
                    canvas.delete(state['info'])
                state['info'] = canvas.create_text(
                    (x1 + x2) // 2, (y1 + y2) // 2 - 16,
                    text="Region too small – drag a larger area",
                    fill='#ff5252', font=('Segoe UI', 12, 'bold'), anchor='center'
                )
                if state['rect']:
                    canvas.itemconfig(state['rect'], outline='#ff5252')
                # Auto-clear the warning after 1.5 s
                def clear_warning():
                    try:
                        if not state['destroyed']:
                            if state['info']:
                                canvas.delete(state['info'])
                                state['info'] = None
                            if state['rect']:
                                canvas.delete(state['rect'])
                                state['rect'] = None
                    except Exception:
                        pass
                root.after(1500, clear_warning)

        canvas.bind('<ButtonPress-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<ButtonRelease-1>', on_release)
        canvas.bind('<ButtonPress-3>', lambda e: close(cancelled=True))

        VK_ESCAPE = 0x1B

        def check_escape():
            if state['destroyed']:
                return
            try:
                if ctypes.windll.user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000:
                    close(cancelled=True)
                    return
                root.after(50, check_escape)
            except Exception:
                pass

        root.update()
        root.lift()
        root.after(100, check_escape)
        try:
            root.mainloop()
        except Exception:
            pass
        finally:
            # Guarantee cleanup even if an unhandled exception fires inside
            # the event loop (prevents the Flet 'failed to remove temp dir' error).
            if not state['destroyed']:
                close(cancelled=True)

    try:
        run()
    except Exception:
        pass
    finally:
        if restore_fn:
            restore_fn()
            time.sleep(0.2)

    return result['coords']


# ─── Eyedropper ──────────────────────────────────────────────────────────────

def pick_color(minimize_fn=None, restore_fn=None):
    """
    Show a fullscreen eyedropper overlay with a live magnifier.
    Left-click picks the color under the cursor.
    Returns (r, g, b) or None if cancelled.
    """
    if minimize_fn:
        minimize_fn()
        time.sleep(0.45)

    result = {'color': None}

    def run():
        import tkinter as tk

        screenshot, tk_w, tk_h, scale_x, scale_y = _take_screenshot()

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes('-topmost', True)
        root.configure(cursor='crosshair')
        root.geometry(f"{tk_w}x{tk_h}+0+0")

        # Display a slightly dimmed background
        if abs(scale_x - 1.0) > 0.01 or abs(scale_y - 1.0) > 0.01:
            display = screenshot.resize((tk_w, tk_h), Image.LANCZOS)
        else:
            display = screenshot.copy()

        canvas = tk.Canvas(root, width=tk_w, height=tk_h,
                           highlightthickness=0)
        canvas.pack(fill='both', expand=True)

        dimmed = ImageEnhance.Brightness(display.copy()).enhance(0.55)
        bg_photo = ImageTk.PhotoImage(dimmed)
        canvas.create_image(0, 0, anchor='nw', image=bg_photo)

        canvas.create_text(
            tk_w // 2, 32,
            text="Click to pick color  |  ESC or Right-click to cancel",
            fill='white', font=('Segoe UI', 13)
        )

        # Magnifier constants
        MAG_RADIUS = 60    # pixels in the display magnifier box
        MAG_ZOOM = 8       # how many source pixels around cursor to zoom
        MAG_SIZE = MAG_RADIUS * 2

        mag_img_ref = [None]   # keep photo reference alive
        mag_rect = canvas.create_rectangle(0, 0, 0, 0, outline='', fill='')
        mag_canvas_img = canvas.create_image(0, 0, anchor='nw')
        crosshair_items = []
        info_rect = canvas.create_rectangle(0, 0, 0, 0, fill='#222222', outline='#444444')
        info_text = canvas.create_text(0, 0, text='', fill='white',
                                        font=('Consolas', 10), anchor='nw')
        swatch_rect = canvas.create_rectangle(0, 0, 0, 0)

        state = {'destroyed': False}

        def close(cancelled=True):
            if state['destroyed']:
                return
            state['destroyed'] = True
            if cancelled:
                result['color'] = None
            try:
                root.destroy()
            except Exception:
                pass

        def on_motion(e):
            if state['destroyed']:
                return
            try:
                # Sample cursor position in screen coords
                sx = int(e.x * scale_x)
                sy = int(e.y * scale_y)

                # Get pixel color from screenshot at true resolution
                px = max(0, min(sx, screenshot.width - 1))
                py = max(0, min(sy, screenshot.height - 1))
                try:
                    pixel = screenshot.getpixel((px, py))
                    r, g, b = pixel[0], pixel[1], pixel[2]
                except Exception:
                    r, g, b = 0, 0, 0

                hex_color = f"#{r:02X}{g:02X}{b:02X}"
                luma = 0.299 * r + 0.587 * g + 0.114 * b

                # Build magnified patch from display image
                half = MAG_ZOOM
                cx, cy = e.x, e.y
                crop_x1 = max(0, cx - half)
                crop_y1 = max(0, cy - half)
                crop_x2 = min(tk_w, cx + half)
                crop_y2 = min(tk_h, cy + half)

                try:
                    patch = display.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                    mag = patch.resize((MAG_SIZE, MAG_SIZE), Image.NEAREST)
                    mag_photo = ImageTk.PhotoImage(mag)
                    mag_img_ref[0] = mag_photo
                except Exception:
                    mag_photo = None

                # Position magnifier near cursor, avoiding edges
                mg_x = e.x + 20
                mg_y = e.y + 20
                if mg_x + MAG_SIZE + 2 > tk_w:
                    mg_x = e.x - MAG_SIZE - 20
                if mg_y + MAG_SIZE + 80 > tk_h:
                    mg_y = e.y - MAG_SIZE - 80

                # Draw magnified image
                if mag_photo:
                    canvas.coords(mag_canvas_img, mg_x, mg_y)
                    canvas.itemconfig(mag_canvas_img, image=mag_photo)

                # Magnifier border
                canvas.coords(mag_rect, mg_x - 2, mg_y - 2,
                              mg_x + MAG_SIZE + 2, mg_y + MAG_SIZE + 2)
                canvas.itemconfig(mag_rect, outline='#00e5ff', fill='', width=2)

                # Center crosshair on magnifier
                for item in crosshair_items:
                    canvas.delete(item)
                crosshair_items.clear()
                cx_m = mg_x + MAG_SIZE // 2
                cy_m = mg_y + MAG_SIZE // 2
                crosshair_items.append(canvas.create_line(
                    cx_m - 10, cy_m, cx_m + 10, cy_m, fill='white', width=1))
                crosshair_items.append(canvas.create_line(
                    cx_m, cy_m - 10, cx_m, cy_m + 10, fill='white', width=1))

                # Info box below magnifier
                info_y = mg_y + MAG_SIZE + 8
                canvas.coords(info_rect, mg_x - 2, info_y,
                              mg_x + MAG_SIZE + 2, info_y + 52)
                canvas.coords(info_text, mg_x + 4, info_y + 4)
                canvas.itemconfig(info_text,
                                  text=f"R: {r}  G: {g}  B: {b}\n{hex_color}")

                # Color swatch
                canvas.coords(swatch_rect,
                              mg_x - 2, info_y + 52,
                              mg_x + MAG_SIZE + 2, info_y + 72)
                canvas.itemconfig(swatch_rect, fill=hex_color, outline='#444444')

                canvas.tag_raise(mag_canvas_img)
                canvas.tag_raise(mag_rect)
                for item in crosshair_items:
                    canvas.tag_raise(item)
                canvas.tag_raise(info_rect)
                canvas.tag_raise(info_text)
                canvas.tag_raise(swatch_rect)

            except Exception:
                # Never let a motion-event exception escape into Tkinter's
                # event dispatch loop — on Python 3.12 + DPI-aware manifest
                # an uncaught callback exception propagates out of root.update()
                # and leaves the Flet window minimized (app appears frozen).
                pass

        def on_click(e):
            sx = int(e.x * scale_x)
            sy = int(e.y * scale_y)
            px = max(0, min(sx, screenshot.width - 1))
            py = max(0, min(sy, screenshot.height - 1))
            try:
                pixel = screenshot.getpixel((px, py))
                result['color'] = (pixel[0], pixel[1], pixel[2])
            except Exception:
                result['color'] = (0, 0, 0)
            close(cancelled=False)

        canvas.bind('<Motion>', on_motion)
        canvas.bind('<ButtonPress-1>', on_click)
        canvas.bind('<ButtonPress-3>', lambda e: close(cancelled=True))

        VK_ESCAPE = 0x1B

        def check_escape():
            if state['destroyed']:
                return
            if ctypes.windll.user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000:
                close(cancelled=True)
                return
            root.after(50, check_escape)

        root.update()
        root.lift()
        root.after(100, check_escape)
        try:
            root.mainloop()
        except Exception:
            pass
        finally:
            if not state['destroyed']:
                close(cancelled=True)

    try:
        run()
    except Exception:
        pass
    finally:
        if restore_fn:
            restore_fn()
            time.sleep(0.2)

    return result['color']


# ─── Point Picker ─────────────────────────────────────────────────────────────

def pick_point(minimize_fn=None, restore_fn=None):
    """
    Show a fullscreen overlay and let the user click to pick a screen position.
    Returns (x, y) in true screen coordinates, or None if cancelled.
    """
    if minimize_fn:
        minimize_fn()
        time.sleep(0.45)

    result = {'point': None}

    def run():
        import tkinter as tk

        screenshot, tk_w, tk_h, scale_x, scale_y = _take_screenshot()

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes('-topmost', True)
        root.configure(cursor='crosshair')
        root.geometry(f"{tk_w}x{tk_h}+0+0")

        # Dimmed background
        if abs(scale_x - 1.0) > 0.01 or abs(scale_y - 1.0) > 0.01:
            display = screenshot.resize((tk_w, tk_h), Image.LANCZOS)
        else:
            display = screenshot.copy()

        canvas = tk.Canvas(root, width=tk_w, height=tk_h, highlightthickness=0)
        canvas.pack(fill='both', expand=True)

        dimmed = ImageEnhance.Brightness(display.copy()).enhance(0.5)
        bg_photo = ImageTk.PhotoImage(dimmed)
        canvas.create_image(0, 0, anchor='nw', image=bg_photo)

        canvas.create_text(
            tk_w // 2, 32,
            text="Click to set click position  |  ESC or Right-click to cancel",
            fill='white', font=('Segoe UI', 13)
        )

        # Coordinate readout items
        coord_rect = canvas.create_rectangle(0, 0, 0, 0, fill='#222222', outline='#444444')
        coord_text = canvas.create_text(0, 0, text='', fill='white',
                                        font=('Consolas', 11), anchor='nw')

        # Crosshair lines (dynamic)
        crosshair_h = canvas.create_line(0, 0, 0, 0, fill='#00e5ff', width=1, dash=(6, 3))
        crosshair_v = canvas.create_line(0, 0, 0, 0, fill='#00e5ff', width=1, dash=(6, 3))

        state = {'destroyed': False}

        def close(cancelled=True):
            if state['destroyed']:
                return
            state['destroyed'] = True
            if cancelled:
                result['point'] = None
            try:
                root.destroy()
            except Exception:
                pass

        def on_motion(e):
            if state['destroyed']:
                return
            # Use physical cursor position for accurate display
            import input_utils as _iu
            sx, sy = _iu.get_physical_cursor_pos()

            # Update crosshair lines across the full screen
            canvas.coords(crosshair_h, 0, e.y, tk_w, e.y)
            canvas.coords(crosshair_v, e.x, 0, e.x, tk_h)

            # Coordinate readout near cursor
            label = f"  X: {sx}   Y: {sy}  "
            rx = e.x + 14
            ry = e.y + 14
            if rx + 120 > tk_w:
                rx = e.x - 130
            if ry + 30 > tk_h:
                ry = e.y - 38

            canvas.coords(coord_rect, rx - 4, ry - 2, rx + 120, ry + 22)
            canvas.coords(coord_text, rx, ry)
            canvas.itemconfig(coord_text, text=label)

            canvas.tag_raise(crosshair_h)
            canvas.tag_raise(crosshair_v)
            canvas.tag_raise(coord_rect)
            canvas.tag_raise(coord_text)

        def on_click(e):
            import input_utils as _iu
            result['point'] = _iu.get_physical_cursor_pos()
            close(cancelled=False)

        canvas.bind('<Motion>', on_motion)
        canvas.bind('<ButtonPress-1>', on_click)
        canvas.bind('<ButtonPress-3>', lambda e: close(cancelled=True))

        VK_ESCAPE = 0x1B

        def check_escape():
            if state['destroyed']:
                return
            if ctypes.windll.user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000:
                close(cancelled=True)
                return
            root.after(50, check_escape)

        root.update()
        root.lift()
        root.after(100, check_escape)
        try:
            root.mainloop()
        except Exception:
            pass
        finally:
            if not state['destroyed']:
                close(cancelled=True)

    try:
        run()
    except Exception:
        pass
    finally:
        if restore_fn:
            restore_fn()
            time.sleep(0.2)

    return result['point']
