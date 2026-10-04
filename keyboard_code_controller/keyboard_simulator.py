import ctypes
import time
from ctypes import wintypes

# Win32 API Consts
INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

VK_BACK = 0x08
VK_TAB = 0x09
VK_RETURN = 0x0D
VK_SHIFT = 0x10

# C Structures
ULONG_PTR = ctypes.c_ulong if ctypes.sizeof(ctypes.c_void_p) == 4 else ctypes.c_ulonglong


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", INPUT_UNION)]


SendInput = ctypes.windll.user32.SendInput
SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
SendInput.restype = wintypes.UINT


class KeyboardSimulator:
    def __init__(self, delay_ms: int = 0, tab_mode: str = "4_spaces"):
        self.delay_ms = delay_ms
        self.tab_mode = tab_mode

    def set_delay(self, delay_ms: int) -> None:
        self.delay_ms = delay_ms

    def set_tab_mode(self, mode: str) -> None:
        self.tab_mode = mode

    def _send_input_events(self, events: list[KEYBDINPUT]) -> None:
        n_inputs = len(events)
        input_array = (INPUT * n_inputs)()
        for i, ki in enumerate(events):
            input_array[i].type = INPUT_KEYBOARD
            input_array[i].u.ki = ki

        SendInput(n_inputs, input_array, ctypes.sizeof(INPUT))
        if self.delay_ms > 0:
            time.sleep(self.delay_ms / 1000.0)

    def send_unicode_char(self, char: str) -> None:
        code = ord(char)
        ki_down = KEYBDINPUT(
            wVk=0,
            wScan=code,
            dwFlags=KEYEVENTF_UNICODE,
            time=0,
            dwExtraInfo=0,
        )
        ki_up = KEYBDINPUT(
            wVk=0,
            wScan=code,
            dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
            time=0,
            dwExtraInfo=0,
        )
        self._send_input_events([ki_down, ki_up])

    def send_virtual_key(self, vk_code: int) -> None:
        ki_down = KEYBDINPUT(
            wVk=vk_code,
            wScan=0,
            dwFlags=0,
            time=0,
            dwExtraInfo=0,
        )
        ki_up = KEYBDINPUT(
            wVk=vk_code,
            wScan=0,
            dwFlags=KEYEVENTF_KEYUP,
            time=0,
            dwExtraInfo=0,
        )
        self._send_input_events([ki_down, ki_up])

    def send_backspace(self) -> None:
        self.send_virtual_key(VK_BACK)

    def send_enter(self) -> None:
        self.send_virtual_key(VK_RETURN)

    def send_tab(self) -> None:
        if self.tab_mode == "tab":
            self.send_virtual_key(VK_TAB)
        elif self.tab_mode == "2_spaces":
            self.send_unicode_char(" ")
            self.send_unicode_char(" ")
        else:  # 4_spaces
            for _ in range(4):
                self.send_unicode_char(" ")

    def type_char(self, char: str) -> None:
        if char == "\n":
            self.send_enter()
        elif char == "\r":
            pass  # Ignored, handled by \n
        elif char == "\t":
            self.send_tab()
        else:
            self.send_unicode_char(char)