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

