from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CodeBlock:
    id: str
    name: str
    code: str
    position: int = 0

    def get_next_char(self) -> Optional[str]:
        if self.position < len(self.code):
            return self.code[self.position]
        return None

    def advance(self) -> None:
        if self.position < len(self.code):
            self.position += 1

    def rewind(self) -> None:
        if self.position > 0:
            self.position -= 1

    def reset(self) -> None:
        self.position = 0


@dataclass
class AppConfig:
    tab_mode: str = "4_spaces"  # "tab", "4_spaces", "2_spaces"
    delay_ms: int = 0
    hotkeys: Dict[str, str] = field(default_factory=dict)
    blocks: List[CodeBlock] = field(default_factory=list)