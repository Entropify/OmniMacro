import ctypes
from ctypes import wintypes
import time

# Types
LONG = ctypes.c_long
DWORD = ctypes.c_ulong
ULONG_PTR = ctypes.POINTER(DWORD)
WORD = ctypes.c_ushort

class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx", LONG),
                ("dy", LONG),
                ("mouseData", DWORD),
                ("dwFlags", DWORD),
                ("time", DWORD),
                ("dwExtraInfo", ULONG_PTR))

class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk", WORD),
                ("wScan", WORD),
                ("dwFlags", DWORD),
                ("time", DWORD),
                ("dwExtraInfo", ULONG_PTR))

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg", DWORD),
                ("wParamL", WORD),
                ("wParamH", WORD))

class _INPUTunion(ctypes.Union):
    _fields_ = (("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT))

class INPUT(ctypes.Structure):
    _fields_ = (("type", DWORD),
                ("union", _INPUTunion))

# Constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000   # map coords to entire virtual desktop (all monitors)
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# Function
SendInput = ctypes.windll.user32.SendInput
SendInput.argtypes = (ctypes.c_uint, ctypes.POINTER(INPUT), ctypes.c_int)
SendInput.restype = ctypes.c_uint

MapVirtualKey = ctypes.windll.user32.MapVirtualKeyW
MapVirtualKey.argtypes = (ctypes.c_uint, ctypes.c_uint)
MapVirtualKey.restype = ctypes.c_uint

MAPVK_VK_TO_VSC = 0

def get_scan_code(vk):
    return MapVirtualKey(vk, MAPVK_VK_TO_VSC)

def _input_mouse(flags, dx=0, dy=0, data=0):
    x = INPUT(type=INPUT_MOUSE,
              union=_INPUTunion(mi=MOUSEINPUT(dx=dx, dy=dy, mouseData=data, dwFlags=flags)))
    return x

def _input_keyboard(code, flags):
    x = INPUT(type=INPUT_KEYBOARD,
              union=_INPUTunion(ki=KEYBDINPUT(wVk=0, wScan=code, dwFlags=flags, time=0, dwExtraInfo=None)))
    return x

def move_relative(dx, dy):
    inp = _input_mouse(MOUSEEVENTF_MOVE, dx, dy)
    SendInput(1, ctypes.pointer(inp), ctypes.sizeof(inp))

def click():
    # Down
    inp_down = _input_mouse(MOUSEEVENTF_LEFTDOWN)
    SendInput(1, ctypes.pointer(inp_down), ctypes.sizeof(inp_down))
    
    time.sleep(0.02) # Hold
    
    # Up
    inp_up = _input_mouse(MOUSEEVENTF_LEFTUP)
    SendInput(1, ctypes.pointer(inp_up), ctypes.sizeof(inp_up))

def press_key(hexKeyCode):
    inp = _input_keyboard(hexKeyCode, KEYEVENTF_SCANCODE)
    SendInput(1, ctypes.pointer(inp), ctypes.sizeof(inp))

def release_key(hexKeyCode):
    inp = _input_keyboard(hexKeyCode, KEYEVENTF_KEYUP | KEYEVENTF_SCANCODE)
    SendInput(1, ctypes.pointer(inp), ctypes.sizeof(inp))

MAPVK_VSC_TO_VK = 1
user32 = ctypes.windll.user32
GetKeyNameText = user32.GetKeyNameTextW

def get_key_name(sc):
    # Shift scan code to bits 16-23 for GetKeyNameText
    lParam = sc << 16
    buf = ctypes.create_unicode_buffer(32)
    GetKeyNameText(lParam, buf, 32)
    return buf.value if buf.value else f"SC({sc})"
# --- Low-Level Keyboard Hook for Type-Along ---
import threading

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
HC_ACTION = 0
LLKHF_INJECTED = 0x00000010

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", DWORD),
        ("scanCode", DWORD),
        ("flags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", ctypes.POINTER(DWORD)),
    ]

# Use proper 64-bit compatible types for hook API
_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32

# GetModuleHandleW - needed for SetWindowsHookEx hMod parameter
GetModuleHandleW = _kernel32.GetModuleHandleW
GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
GetModuleHandleW.restype = ctypes.c_void_p

SetWindowsHookExW = _user32.SetWindowsHookExW
SetWindowsHookExW.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, DWORD]
SetWindowsHookExW.restype = ctypes.c_void_p

UnhookWindowsHookExW = _user32.UnhookWindowsHookEx
UnhookWindowsHookExW.argtypes = [ctypes.c_void_p]
UnhookWindowsHookExW.restype = ctypes.c_bool

CallNextHookExW = _user32.CallNextHookEx
CallNextHookExW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM]
CallNextHookExW.restype = ctypes.wintypes.LPARAM

GetMessageW = _user32.GetMessageW
PostThreadMessageW = _user32.PostThreadMessageW
GetCurrentThreadId = _kernel32.GetCurrentThreadId
GetLastError = _kernel32.GetLastError
WM_QUIT = 0x0012

# Use LPARAM-sized return and parameters for proper 64-bit Windows compatibility
HOOKPROC = ctypes.WINFUNCTYPE(
    ctypes.wintypes.LPARAM,    # LRESULT return
    ctypes.c_int,              # int nCode
    ctypes.wintypes.WPARAM,    # WPARAM wParam
    ctypes.wintypes.LPARAM     # LPARAM lParam (raw pointer as integer)
)

_hook_handle = None
_hook_thread = None
_hook_thread_id = None
_hook_callback_ref = None  # prevent garbage collection of the callback
_keyboard_suppression_enabled = False
_on_human_keypress = None

def _low_level_keyboard_proc(nCode, wParam, lParam):
    global _keyboard_suppression_enabled
    try:
        if nCode == HC_ACTION and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            # Cast raw lParam integer to pointer to KBDLLHOOKSTRUCT
            kb_struct = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            is_injected = bool(kb_struct.flags & LLKHF_INJECTED)
            
            if not is_injected and _keyboard_suppression_enabled:
                # Human keystroke detected while suppression is on — signal and block
                if _on_human_keypress:
                    _on_human_keypress()
                return 1  # Block the keystroke
        
        # Also block key-up events for suppressed keys to prevent stray key-ups
        if nCode == HC_ACTION and wParam in (WM_KEYUP, WM_SYSKEYUP):
            kb_struct = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            is_injected = bool(kb_struct.flags & LLKHF_INJECTED)
            if not is_injected and _keyboard_suppression_enabled:
                return 1  # Block the key-up too
    except Exception as e:
        print(f"[Type-Along] Hook callback error: {e}")
    
    return CallNextHookExW(_hook_handle, nCode, wParam, lParam)

def install_keyboard_hook(on_keypress_callback):
    """Install a low-level keyboard hook for Type-Along mode."""
    global _hook_handle, _hook_thread, _hook_thread_id, _hook_callback_ref, _on_human_keypress
    
    if _hook_handle is not None:
        return  # Already installed
    
    _on_human_keypress = on_keypress_callback
    _hook_callback_ref = HOOKPROC(_low_level_keyboard_proc)
    
    ready_event = threading.Event()
    
    def hook_thread_func():
        global _hook_handle, _hook_thread_id
        _hook_thread_id = GetCurrentThreadId()
        
        # Get module handle for the current process
        h_mod = GetModuleHandleW(None)
        
        _hook_handle = SetWindowsHookExW(
            WH_KEYBOARD_LL,
            _hook_callback_ref,
            h_mod,
            0
        )
        
        if not _hook_handle:
            err = GetLastError()
            print(f"[Type-Along] Failed to install keyboard hook, error code: {err}")
            ready_event.set()
            return
        
        print(f"[Type-Along] Keyboard hook installed successfully (handle: {_hook_handle})")
        ready_event.set()
        
        # Message pump - REQUIRED for WH_KEYBOARD_LL to receive callbacks
        msg = ctypes.wintypes.MSG()
        while GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            pass  # Just pump messages, the hook callback does the work
        
        # Cleanup when message loop exits
        if _hook_handle:
            UnhookWindowsHookExW(_hook_handle)
            _hook_handle = None
        print("[Type-Along] Keyboard hook uninstalled")
    
    _hook_thread = threading.Thread(target=hook_thread_func, daemon=True)
    _hook_thread.start()
    # Wait for the hook to be installed (with timeout)
    ready_event.wait(timeout=2.0)

def uninstall_keyboard_hook():
    """Remove the low-level keyboard hook and stop the message pump."""
    global _hook_handle, _hook_thread, _hook_thread_id, _on_human_keypress, _keyboard_suppression_enabled
    
    _keyboard_suppression_enabled = False
    _on_human_keypress = None
    
    if _hook_thread_id is not None:
        PostThreadMessageW(_hook_thread_id, WM_QUIT, 0, 0)
        _hook_thread_id = None
    
    if _hook_thread is not None:
        _hook_thread.join(timeout=2.0)
        _hook_thread = None
    
    _hook_handle = None

def set_keyboard_suppression(enabled):
    """Toggle whether human keystrokes are suppressed (blocked). Hook must be installed first."""
    global _keyboard_suppression_enabled
    _keyboard_suppression_enabled = enabled


# ─── Absolute Cursor Helpers ──────────────────────────────────────────────────

class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

# DPI Awareness Context constants (Win10 1607+)
_DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)

_u32 = ctypes.windll.user32
try:
    _SetThreadDpiAwarenessContext = _u32.SetThreadDpiAwarenessContext
    _SetThreadDpiAwarenessContext.restype = ctypes.c_void_p
    _SetThreadDpiAwarenessContext.argtypes = [ctypes.c_void_p]
    _HAS_DPI_CONTEXT_API = True
except AttributeError:
    _HAS_DPI_CONTEXT_API = False


def _with_physical_dpi_context(fn):
    """
    Run fn() while thread DPI awareness is forced to PER_MONITOR_AWARE_V2
    so that GetSystemMetrics / GetCursorPos return PHYSICAL pixel values.
    Falls back gracefully on older Windows.
    """
    if _HAS_DPI_CONTEXT_API:
        try:
            prev = _SetThreadDpiAwarenessContext(
                _DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
            )
            try:
                return fn()
            finally:
                if prev:
                    _SetThreadDpiAwarenessContext(ctypes.c_void_p(prev))
            return
        except Exception:
            pass
    return fn()


def get_cursor_pos():
    """Return (x, y) of current cursor in the process's native DPI context."""
    pt = _POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return (pt.x, pt.y)


def get_physical_cursor_pos():
    """
    Return (x, y) of cursor in TRUE PHYSICAL screen pixels.
    Unaffected by process DPI awareness or DPI scaling.
    """
    def _read():
        pt = _POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return (pt.x, pt.y)
    return _with_physical_dpi_context(_read)


def move_to(x, y):
    """
    Move cursor to absolute physical screen coordinates.

    Uses SetCursorPos in a forced per-monitor-aware DPI context so the (x, y)
    values are always interpreted as PHYSICAL pixels — unambiguous, no
    normalisation math, works across all monitors including those with
    different DPI scales.
    """
    _with_physical_dpi_context(
        lambda: ctypes.windll.user32.SetCursorPos(int(x), int(y))
    )


def click_at(x, y):
    """
    Teleport cursor to physical (x, y) and left-click there.

    Why SetCursorPos instead of MOUSEEVENTF_ABSOLUTE:
      MOUSEEVENTF_ABSOLUTE requires normalising (x, y) against the virtual
      desktop dimensions, but the normalisation denominator depends on the
      *process* DPI awareness context (logical vs physical), which can differ
      from the context we used to measure the screen — causing systematic
      mis-click.  SetCursorPos in a forced per-monitor-aware thread context
      always interprets coordinates as physical pixels regardless of process
      DPI awareness, making it completely unambiguous.

    Works cross-monitor: physical coordinates span the entire virtual desktop.
    """
    # Position cursor at exact physical location
    _with_physical_dpi_context(
        lambda: ctypes.windll.user32.SetCursorPos(int(x), int(y))
    )
    # Brief settle — gives the OS time to process the cursor move
    # before the click event is dispatched to the window under the cursor.
    time.sleep(0.008)
    # Fire click at the current cursor position (no ABSOLUTE/MOVE flags —
    # the click is sent to wherever SetCursorPos placed the cursor).
    inputs = (INPUT * 2)(
        _input_mouse(MOUSEEVENTF_LEFTDOWN),
        _input_mouse(MOUSEEVENTF_LEFTUP),
    )
    SendInput(2, inputs, ctypes.sizeof(INPUT))

