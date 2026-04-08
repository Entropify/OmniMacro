"""
Crosshair Overlay — Always-on-top, click-through, transparent Win32 window.
Draws a customizable crosshair at screen center using GDI.
Works over borderless-fullscreen and windowed applications.
"""

import ctypes
import ctypes.wintypes as wintypes
import threading

# ─── Win32 Constants ───────────────────────────────────────────────────────────
WS_EX_TOPMOST     = 0x00000008
WS_EX_TRANSPARENT  = 0x00000020
WS_EX_LAYERED      = 0x00080000
WS_EX_TOOLWINDOW   = 0x00000080
WS_EX_NOACTIVATE   = 0x08000000
WS_POPUP           = 0x80000000

SWP_NOMOVE         = 0x0002
SWP_NOSIZE         = 0x0001
SWP_NOACTIVATE     = 0x0010
SWP_SHOWWINDOW     = 0x0040

GWL_EXSTYLE        = -20
LWA_COLORKEY       = 0x00000001
LWA_ALPHA          = 0x00000002

SW_SHOW            = 5
SW_HIDE            = 0

WM_PAINT           = 0x000F
WM_DESTROY         = 0x0002
WM_QUIT            = 0x0012
WM_USER            = 0x0400
WM_UPDATE_CROSSHAIR = WM_USER + 1
WM_TOGGLE_VISIBILITY = WM_USER + 2

SM_CXSCREEN        = 0
SM_CYSCREEN        = 1

IDC_ARROW          = 32512
CS_HREDRAW         = 0x0002
CS_VREDRAW         = 0x0001

PS_SOLID           = 0
NULL_BRUSH         = 5
TRANSPARENT_BK     = 1  # SetBkMode constant

# ─── Win32 Structures ─────────────────────────────────────────────────────────
class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize",        ctypes.c_uint),
        ("style",         ctypes.c_uint),
        ("lpfnWndProc",   ctypes.c_void_p),
        ("cbClsExtra",    ctypes.c_int),
        ("cbWndExtra",    ctypes.c_int),
        ("hInstance",     wintypes.HINSTANCE),
        ("hIcon",         wintypes.HICON),
        ("hCursor",       wintypes.HICON),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName",  wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm",       wintypes.HICON),
    ]

class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hdc",           wintypes.HDC),
        ("fErase",        wintypes.BOOL),
        ("rcPaint",       wintypes.RECT),
        ("fRestore",      wintypes.BOOL),
        ("fIncUpdate",    wintypes.BOOL),
        ("rgbReserved",   ctypes.c_byte * 32),
    ]

# ─── Win32 Function Bindings (with proper argtypes/restype for 64-bit) ────────
_user32 = ctypes.windll.user32
_gdi32 = ctypes.windll.gdi32
_kernel32 = ctypes.windll.kernel32

# kernel32
_kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
_kernel32.GetModuleHandleW.restype = wintypes.HMODULE

_kernel32.GetCurrentThreadId.argtypes = []
_kernel32.GetCurrentThreadId.restype = wintypes.DWORD

# user32 - window management
_user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
_user32.RegisterClassExW.restype = wintypes.ATOM

_user32.CreateWindowExW.argtypes = [
    wintypes.DWORD,   # dwExStyle
    wintypes.LPCWSTR, # lpClassName
    wintypes.LPCWSTR, # lpWindowName
    wintypes.DWORD,   # dwStyle
    ctypes.c_int,     # X
    ctypes.c_int,     # Y
    ctypes.c_int,     # nWidth
    ctypes.c_int,     # nHeight
    wintypes.HWND,    # hWndParent
    wintypes.HMENU,   # hMenu
    wintypes.HINSTANCE, # hInstance
    wintypes.LPVOID,  # lpParam
]
_user32.CreateWindowExW.restype = wintypes.HWND

_user32.DestroyWindow.argtypes = [wintypes.HWND]
_user32.DestroyWindow.restype = wintypes.BOOL

_user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.ShowWindow.restype = wintypes.BOOL

_user32.SetLayeredWindowAttributes.argtypes = [wintypes.HWND, wintypes.COLORREF, wintypes.BYTE, wintypes.DWORD]
_user32.SetLayeredWindowAttributes.restype = wintypes.BOOL

_user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
_user32.SetWindowPos.restype = wintypes.BOOL

_user32.InvalidateRect.argtypes = [wintypes.HWND, ctypes.c_void_p, wintypes.BOOL]
_user32.InvalidateRect.restype = wintypes.BOOL

_user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
_user32.GetClientRect.restype = wintypes.BOOL

_user32.FillRect.argtypes = [wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.HBRUSH]
_user32.FillRect.restype = ctypes.c_int

_user32.BeginPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
_user32.BeginPaint.restype = wintypes.HDC

_user32.EndPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
_user32.EndPaint.restype = wintypes.BOOL

_user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
_user32.DefWindowProcW.restype = ctypes.c_longlong

_user32.PostQuitMessage.argtypes = [ctypes.c_int]
_user32.PostQuitMessage.restype = None

_user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
_user32.PostThreadMessageW.restype = wintypes.BOOL

_user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
_user32.GetMessageW.restype = wintypes.BOOL

_user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
_user32.TranslateMessage.restype = wintypes.BOOL

_user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
_user32.DispatchMessageW.restype = ctypes.c_longlong

_user32.LoadCursorW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
_user32.LoadCursorW.restype = ctypes.c_void_p

_user32.GetSystemMetrics.argtypes = [ctypes.c_int]
_user32.GetSystemMetrics.restype = ctypes.c_int

# gdi32
_gdi32.CreateSolidBrush.argtypes = [wintypes.COLORREF]
_gdi32.CreateSolidBrush.restype = wintypes.HBRUSH

_gdi32.CreatePen.argtypes = [ctypes.c_int, ctypes.c_int, wintypes.COLORREF]
_gdi32.CreatePen.restype = wintypes.HPEN

_gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
_gdi32.SelectObject.restype = wintypes.HGDIOBJ

_gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
_gdi32.DeleteObject.restype = wintypes.BOOL

_gdi32.GetStockObject.argtypes = [ctypes.c_int]
_gdi32.GetStockObject.restype = wintypes.HGDIOBJ

_gdi32.MoveToEx.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
_gdi32.MoveToEx.restype = wintypes.BOOL

_gdi32.LineTo.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
_gdi32.LineTo.restype = wintypes.BOOL

_gdi32.Ellipse.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
_gdi32.Ellipse.restype = wintypes.BOOL

_gdi32.SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
_gdi32.SetBkMode.restype = ctypes.c_int

# WNDPROC callback type (64-bit safe)
WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, wintypes.HWND, wintypes.UINT,
                              wintypes.WPARAM, wintypes.LPARAM)

# HWND_TOPMOST needs to be a proper HWND value
HWND_TOPMOST = wintypes.HWND(-1)

# ─── Shape Constants ──────────────────────────────────────────────────────────
SHAPE_CROSS       = 0
SHAPE_CIRCLE      = 1
SHAPE_DOT         = 2
SHAPE_CROSS_CIRCLE = 3
SHAPE_CROSS_DOT   = 4


class CrosshairOverlay:
    """Manages a transparent, always-on-top crosshair overlay window."""

    # Background color used as the transparency key (unlikely to appear in crosshair)
    _BG_COLOR = 0x00010101  # Near-black RGB(1,1,1) — used for color-keying

    def __init__(self):
        self.visible = False
        self.shape = SHAPE_CROSS
        self.color = (0, 255, 0)  # RGB green
        self.size = 10            # arm length / radius
        self.thickness = 2
        self.opacity = 100        # percent
        self.gap = 3
        self.dot = True
        self.outline = True

        self._hwnd = None
        self._thread = None
        self._thread_id = None
        self._wndproc_ref = None  # prevent GC
        self._class_atom = None
        self._ready = threading.Event()
        self._lock = threading.Lock()

    def start(self):
        """Start the overlay window thread. Call once at app startup."""
        if self._thread is not None:
            return
        self._ready.clear()
        self._thread = threading.Thread(target=self._window_thread, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=3.0)

    def stop(self):
        """Destroy the overlay window and stop the thread."""
        if self._thread_id is not None:
            _user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None
        self._hwnd = None
        self._thread_id = None

    def show(self):
        """Show the crosshair overlay."""
        self.visible = True
        if self._hwnd and self._thread_id:
            _user32.PostThreadMessageW(self._thread_id, WM_TOGGLE_VISIBILITY, 1, 0)

    def hide(self):
        """Hide the crosshair overlay."""
        self.visible = False
        if self._hwnd and self._thread_id:
            _user32.PostThreadMessageW(self._thread_id, WM_TOGGLE_VISIBILITY, 0, 0)

    def toggle(self):
        """Toggle visibility."""
        if self.visible:
            self.hide()
        else:
            self.show()

    def update_settings(self, shape=None, color=None, size=None, thickness=None,
                        opacity=None, gap=None, dot=None, outline=None):
        """Update crosshair settings and redraw. Pass only changed values."""
        with self._lock:
            if shape is not None:
                self.shape = shape
            if color is not None:
                self.color = color
            if size is not None:
                self.size = max(2, min(50, size))
            if thickness is not None:
                self.thickness = max(1, min(5, thickness))
            if opacity is not None:
                self.opacity = max(10, min(100, opacity))
            if gap is not None:
                self.gap = max(0, min(20, gap))
            if dot is not None:
                self.dot = dot
            if outline is not None:
                self.outline = outline

        # Signal the window thread to reposition/resize and redraw
        if self._hwnd and self._thread_id:
            _user32.PostThreadMessageW(self._thread_id, WM_UPDATE_CROSSHAIR, 0, 0)

    # ─── Internal Window Thread ───────────────────────────────────────────────

    def _window_thread(self):
        self._thread_id = _kernel32.GetCurrentThreadId()

        hInstance = _kernel32.GetModuleHandleW(None)
        class_name = "OmniMacroCrosshair"

        self._wndproc_ref = WNDPROC(self._wnd_proc)

        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.style = CS_HREDRAW | CS_VREDRAW
        wc.lpfnWndProc = ctypes.cast(self._wndproc_ref, ctypes.c_void_p)
        wc.hInstance = hInstance
        wc.hCursor = _user32.LoadCursorW(None, ctypes.c_void_p(IDC_ARROW))
        wc.hbrBackground = _gdi32.CreateSolidBrush(self._BG_COLOR)
        wc.lpszClassName = class_name

        self._class_atom = _user32.RegisterClassExW(ctypes.byref(wc))
        if not self._class_atom:
            err = _kernel32.GetLastError()
            print(f"[Crosshair] Failed to register window class, error: {err}")
            self._ready.set()
            return

        # Calculate initial window size and position
        win_size = self._calc_window_size()
        screen_w = _user32.GetSystemMetrics(SM_CXSCREEN)
        screen_h = _user32.GetSystemMetrics(SM_CYSCREEN)
        win_x = (screen_w - win_size) // 2
        win_y = (screen_h - win_size) // 2

        ex_style = WS_EX_TOPMOST | WS_EX_TRANSPARENT | WS_EX_LAYERED | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE

        self._hwnd = _user32.CreateWindowExW(
            ex_style,
            class_name,
            "OmniMacro Crosshair",
            WS_POPUP,
            win_x, win_y, win_size, win_size,
            None, None, hInstance, None
        )

        if not self._hwnd:
            err = _kernel32.GetLastError()
            print(f"[Crosshair] Failed to create window, error: {err}")
            self._ready.set()
            return

        # Set the color key + per-window alpha for opacity control
        with self._lock:
            alpha = int(self.opacity / 100.0 * 255)
        _user32.SetLayeredWindowAttributes(self._hwnd, self._BG_COLOR, alpha, LWA_COLORKEY | LWA_ALPHA)

        # Start hidden
        _user32.ShowWindow(self._hwnd, SW_HIDE)

        self._ready.set()

        # Message pump
        msg = wintypes.MSG()
        while _user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_UPDATE_CROSSHAIR:
                self._reposition_and_redraw()
            elif msg.message == WM_TOGGLE_VISIBILITY:
                if msg.wParam:
                    self._reposition_and_redraw()
                    _user32.ShowWindow(self._hwnd, SW_SHOW)
                    # Re-assert topmost
                    _user32.SetWindowPos(self._hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
                else:
                    _user32.ShowWindow(self._hwnd, SW_HIDE)
            else:
                _user32.TranslateMessage(ctypes.byref(msg))
                _user32.DispatchMessageW(ctypes.byref(msg))

        # Cleanup
        if self._hwnd:
            _user32.DestroyWindow(self._hwnd)
            self._hwnd = None

    def _wnd_proc(self, hwnd, msg, wParam, lParam):
        if msg == WM_PAINT:
            ps = PAINTSTRUCT()
            hdc = _user32.BeginPaint(hwnd, ctypes.byref(ps))
            if hdc:
                try:
                    self._draw_crosshair(hdc)
                except Exception as e:
                    print(f"[Crosshair] Draw error: {e}")
                _user32.EndPaint(hwnd, ctypes.byref(ps))
            return 0
        elif msg == WM_DESTROY:
            _user32.PostQuitMessage(0)
            return 0
        return _user32.DefWindowProcW(hwnd, msg, wParam, lParam)

    def _calc_window_size(self):
        """Calculate the window size needed for the current crosshair settings."""
        with self._lock:
            base = self.size * 2 + self.thickness + 8
            if self.outline:
                base += 6
            return max(base, 20)

    def _reposition_and_redraw(self):
        """Resize and recenter the window, then trigger a redraw."""
        if not self._hwnd:
            return

        win_size = self._calc_window_size()
        screen_w = _user32.GetSystemMetrics(SM_CXSCREEN)
        screen_h = _user32.GetSystemMetrics(SM_CYSCREEN)
        win_x = (screen_w - win_size) // 2
        win_y = (screen_h - win_size) // 2

        _user32.SetWindowPos(self._hwnd, HWND_TOPMOST,
                            win_x, win_y, win_size, win_size,
                            SWP_NOACTIVATE | SWP_SHOWWINDOW)

        # Re-apply opacity in case it changed
        with self._lock:
            alpha = int(self.opacity / 100.0 * 255)
        _user32.SetLayeredWindowAttributes(self._hwnd, self._BG_COLOR, alpha, LWA_COLORKEY | LWA_ALPHA)

        _user32.InvalidateRect(self._hwnd, None, True)

    def _draw_crosshair(self, hdc):
        """Draw the crosshair onto the device context."""
        with self._lock:
            shape = self.shape
            r, g, b = self.color
            size = self.size
            thickness = self.thickness
            gap = self.gap
            draw_dot = self.dot
            draw_outline = self.outline

        # Window client rect
        rc = wintypes.RECT()
        _user32.GetClientRect(self._hwnd, ctypes.byref(rc))
        cx = (rc.right - rc.left) // 2
        cy = (rc.bottom - rc.top) // 2

        # Fill background with the color key
        bg_brush = _gdi32.CreateSolidBrush(self._BG_COLOR)
        _user32.FillRect(hdc, ctypes.byref(rc), bg_brush)
        _gdi32.DeleteObject(bg_brush)

        # Set transparent background mode
        _gdi32.SetBkMode(hdc, TRANSPARENT_BK)

        color_ref = r | (g << 8) | (b << 16)  # COLORREF is 0x00BBGGRR
        outline_color = 0x00000000  # Black outline

        # Helper: draw a cross shape
        def draw_cross_shape(pen_color, pen_thickness, extra_gap=0):
            pen = _gdi32.CreatePen(PS_SOLID, pen_thickness, pen_color)
            old_pen = _gdi32.SelectObject(hdc, pen)
            g_val = gap + extra_gap

            # Top arm
            _gdi32.MoveToEx(hdc, cx, cy - g_val, None)
            _gdi32.LineTo(hdc, cx, cy - g_val - size)
            # Bottom arm
            _gdi32.MoveToEx(hdc, cx, cy + g_val, None)
            _gdi32.LineTo(hdc, cx, cy + g_val + size)
            # Left arm
            _gdi32.MoveToEx(hdc, cx - g_val, cy, None)
            _gdi32.LineTo(hdc, cx - g_val - size, cy)
            # Right arm
            _gdi32.MoveToEx(hdc, cx + g_val, cy, None)
            _gdi32.LineTo(hdc, cx + g_val + size, cy)

            _gdi32.SelectObject(hdc, old_pen)
            _gdi32.DeleteObject(pen)

        # Helper: draw a circle outline
        def draw_circle_shape(pen_color, pen_thickness, radius):
            pen = _gdi32.CreatePen(PS_SOLID, pen_thickness, pen_color)
            null_brush = _gdi32.GetStockObject(NULL_BRUSH)
            old_pen = _gdi32.SelectObject(hdc, pen)
            old_brush = _gdi32.SelectObject(hdc, null_brush)

            _gdi32.Ellipse(hdc, cx - radius, cy - radius, cx + radius, cy + radius)

            _gdi32.SelectObject(hdc, old_pen)
            _gdi32.SelectObject(hdc, old_brush)
            _gdi32.DeleteObject(pen)

        # Helper: draw a filled dot
        def draw_filled_dot(dot_color, radius):
            brush = _gdi32.CreateSolidBrush(dot_color)
            pen = _gdi32.CreatePen(PS_SOLID, 1, dot_color)
            old_pen = _gdi32.SelectObject(hdc, pen)
            old_brush = _gdi32.SelectObject(hdc, brush)

            _gdi32.Ellipse(hdc, cx - radius, cy - radius, cx + radius, cy + radius)

            _gdi32.SelectObject(hdc, old_pen)
            _gdi32.SelectObject(hdc, old_brush)
            _gdi32.DeleteObject(pen)
            _gdi32.DeleteObject(brush)

        # ── Draw outline first (slightly thicker, black) ──
        if draw_outline:
            if shape in (SHAPE_CROSS, SHAPE_CROSS_CIRCLE, SHAPE_CROSS_DOT):
                draw_cross_shape(outline_color, thickness + 2, extra_gap=0)
            if shape in (SHAPE_CIRCLE, SHAPE_CROSS_CIRCLE):
                draw_circle_shape(outline_color, thickness + 2, size)
            if shape == SHAPE_DOT:
                dot_r = max(thickness + 1, 3)
                draw_filled_dot(outline_color, dot_r + 1)

        # ── Draw main crosshair ──
        if shape in (SHAPE_CROSS, SHAPE_CROSS_CIRCLE, SHAPE_CROSS_DOT):
            draw_cross_shape(color_ref, thickness)
        if shape in (SHAPE_CIRCLE, SHAPE_CROSS_CIRCLE):
            draw_circle_shape(color_ref, thickness, size)
        if shape == SHAPE_DOT:
            dot_r = max(thickness + 1, 3)
            draw_filled_dot(color_ref, dot_r)

        # ── Center dot ──
        if draw_dot and shape != SHAPE_DOT:
            if draw_outline:
                draw_filled_dot(outline_color, thickness + 1)
            draw_filled_dot(color_ref, max(thickness, 2))
