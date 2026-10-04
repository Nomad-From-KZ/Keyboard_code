from typing import Dict, Optional, Tuple

VK_CODE_NAMES = {
    0x30: "0", 0x31: "1", 0x32: "2", 0x33: "3", 0x34: "4",
    0x35: "5", 0x36: "6", 0x37: "7", 0x38: "8", 0x39: "9",
    0x41: "A", 0x42: "B", 0x43: "C", 0x44: "D", 0x45: "E",
    0x46: "F", 0x47: "G", 0x48: "H", 0x49: "I", 0x4A: "J",
    0x4B: "K", 0x4C: "L", 0x4D: "M", 0x4E: "N", 0x4F: "O",
    0x50: "P", 0x51: "Q", 0x52: "R", 0x53: "S", 0x54: "T",
    0x55: "U", 0x56: "V", 0x57: "W", 0x58: "X", 0x59: "Y", 0x5A: "Z",
    0x70: "F1", 0x71: "F2", 0x72: "F3", 0x73: "F4",
    0x74: "F5", 0x75: "F6", 0x76: "F7", 0x77: "F8",
    0x78: "F9", 0x79: "F10", 0x7A: "F11", 0x7B: "F12",
}


class HotkeyManager:
    def __init__(self, hotkey_map: Dict[str, str]):
        # hotkey_map: e.g. {"Shift+1": "block_1_v2", "Ctrl+R": "reset_block"}
        self.hotkey_map = hotkey_map

    def update_map(self, hotkey_map: Dict[str, str]) -> None:
        self.hotkey_map = hotkey_map

    @staticmethod
    def build_combo_string(shift: bool, ctrl: bool, alt: bool, vk_code: int) -> Optional[str]:
        key_name = VK_CODE_NAMES.get(vk_code)
        if not key_name:
            return None

        parts = []
        if ctrl:
            parts.append("Ctrl")
        if shift:
            parts.append("Shift")
        if alt:
            parts.append("Alt")
        parts.append(key_name)

        return "+".join(parts)

    def match_action(self, shift: bool, ctrl: bool, alt: bool, vk_code: int) -> Optional[str]:
        combo = self.build_combo_string(shift, ctrl, alt, vk_code)
        if combo in self.hotkey_map:
            return self.hotkey_map[combo]
        return None