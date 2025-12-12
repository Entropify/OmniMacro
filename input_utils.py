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
