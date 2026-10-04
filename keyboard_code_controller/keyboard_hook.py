import ctypes
from ctypes import wintypes
from PyQt6.QtCore import QObject, pyqtSignal

# Win32 Constants
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0204

LLKHF_INJECTED = 0x00000010

VK_SHIFT = 0x10
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_CONTROL = 0x11
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_MENU = 0x12
VK_LMENU = 0xA4
VK_RMENU = 0xA5
VK_BACK = 0x08

# Типы Win32 API
ULONG_PTR = ctypes.c_ulong if ctypes.sizeof(ctypes.c_void_p) == 4 else ctypes.c_ulonglong
LRESULT = ctypes.c_ssize_t  # Корректное объявление LRESULT для x64/x86


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


HOOKPROC = ctypes.WINFUNCTYPE(
    LRESULT, ctypes.c_int, wintypes.WPARAM, ctypes.POINTER(KBDLLHOOKSTRUCT)
)

SetWindowsHookExW = ctypes.windll.user32.SetWindowsHookExW
SetWindowsHookExW.argtypes = [
    ctypes.c_int,
    HOOKPROC,
    wintypes.HINSTANCE,
    wintypes.DWORD,
]
SetWindowsHookExW.restype = wintypes.HHOOK

UnhookWindowsHookEx = ctypes.windll.user32.UnhookWindowsHookEx
UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
UnhookWindowsHookEx.restype = wintypes.BOOL

CallNextHookEx = ctypes.windll.user32.CallNextHookEx
CallNextHookEx.argtypes = [
    wintypes.HHOOK,
    ctypes.c_int,
    wintypes.WPARAM,
    ctypes.POINTER(KBDLLHOOKSTRUCT),
]
CallNextHookEx.restype = LRESULT

GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState
GetAsyncKeyState.argtypes = [ctypes.c_int]
GetAsyncKeyState.restype = wintypes.SHORT


class KeyboardHookSignals(QObject):
    action_triggered = pyqtSignal(str)  # Сигнал срабатывания хоткея
    type_trigger = pyqtSignal()         # Сигнал ввода следующего символа
    backspace_trigger = pyqtSignal()    # Сигнал обработки Backspace


class KeyboardHook:
    def __init__(self, hotkey_manager):
        self.hotkey_manager = hotkey_manager
        self.signals = KeyboardHookSignals()
        self.hook_handle = None
        self.enabled = False
        self.is_paused = False  # Флаг паузы
        self._hook_proc_c = HOOKPROC(self._low_level_keyboard_proc)

    def start(self) -> bool:
        if self.hook_handle is not None:
            return True

        self.hook_handle = SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self._hook_proc_c,
            None,
            0,
        )
        if self.hook_handle:
            self.enabled = True
            return True
        return False

    def stop(self) -> None:
        if self.hook_handle:
            UnhookWindowsHookEx(self.hook_handle)
            self.hook_handle = None
        self.enabled = False

    def _is_pressed(self, vk: int) -> bool:
        return bool(GetAsyncKeyState(vk) & 0x8000)

    def _low_level_keyboard_proc(
        self, nCode: int, wParam: wintypes.WPARAM, lParam: ctypes.POINTER(KBDLLHOOKSTRUCT)
    ) -> LRESULT:
        if nCode >= 0 and self.enabled:
            kbd = lParam.contents

            # 1. Защита от бесконечной петли: пропускаем события, сгенерированные через SendInput
            if kbd.flags & LLKHF_INJECTED:
                return CallNextHookEx(self.hook_handle, nCode, wParam, lParam)

            if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                vk = kbd.vkCode

                # Считываем текущее состояние клавиш-модификаторов
                shift = self._is_pressed(VK_SHIFT) or self._is_pressed(VK_LSHIFT) or self._is_pressed(VK_RSHIFT)
                ctrl = self._is_pressed(VK_CONTROL) or self._is_pressed(VK_LCONTROL) or self._is_pressed(VK_RCONTROL)
                alt = self._is_pressed(VK_MENU) or self._is_pressed(VK_LMENU) or self._is_pressed(VK_RMENU)

                # Пропускаем одиночные нажатия клавиш-модификаторов
                if vk in (VK_SHIFT, VK_LSHIFT, VK_RSHIFT, VK_CONTROL, VK_LCONTROL, VK_RCONTROL, VK_MENU, VK_LMENU, VK_RMENU):
                    return CallNextHookEx(self.hook_handle, nCode, wParam, lParam)

                # 2. Проверяем зарегистрированный хоткей
                action = self.hotkey_manager.match_action(shift, ctrl, alt, vk)

                # Переключение паузы обрабатывается всегда
                if action == "toggle_pause":
                    self.signals.action_triggered.emit(action)
                    return 1

                # ЕСЛИ ВКЛЮЧЕНА ПАУЗА:
                # Пропускаем абсолютно все остальные клавиши в Windows!
                if self.is_paused:
                    return CallNextHookEx(self.hook_handle, nCode, wParam, lParam)

                # Если не на паузе, но нажат другой управляющий хоткей
                if action:
                    self.signals.action_triggered.emit(action)
                    return 1

                # 3. Обработка клавиши Backspace
                if vk == VK_BACK:
                    self.signals.backspace_trigger.emit()
                    return 1

                # 4. Обработка обычного ввода (триггер следующего символа блока)
                if not alt and not ctrl:
                    self.signals.type_trigger.emit()
                    return 1

        return CallNextHookEx(self.hook_handle, nCode, wParam, lParam)