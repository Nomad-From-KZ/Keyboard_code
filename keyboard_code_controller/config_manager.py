import json
import os
from typing import Any, Dict
from models import AppConfig, CodeBlock


class ConfigManager:
    def __init__(self, filepath: str = "config.json"):
        self.filepath = filepath

    def load_config(self) -> AppConfig:
        if not os.path.exists(self.filepath):
            return self.get_default_config()

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            blocks = []
            for b in data.get("blocks", []):
                blocks.append(
                    CodeBlock(
                        id=b["id"],
                        name=b["name"],
                        code=b["code"],
                        position=b.get("position", 0),
                    )
                )

            return AppConfig(
                tab_mode=data.get("tab_mode", "4_spaces"),
                delay_ms=data.get("delay_ms", 0),
                hotkeys=data.get("hotkeys", self._default_hotkeys()),
                blocks=blocks if blocks else self._default_blocks(),
            )
        except Exception as e:
            print(f"[ConfigManager] Error loading config: {e}. Using defaults.")
            return self.get_default_config()

    def save_config(self, config: AppConfig) -> None:
        data: Dict[str, Any] = {
            "tab_mode": config.tab_mode,
            "delay_ms": config.delay_ms,
            "hotkeys": config.hotkeys,
            "blocks": [
                {
                    "id": b.id,
                    "name": b.name,
                    "code": b.code,
                    "position": b.position,
                }
                for b in config.blocks
            ],
        }
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_default_config(self) -> AppConfig:
        return AppConfig(
            tab_mode="4_spaces",
            delay_ms=0,
            hotkeys=self._default_hotkeys(),
            blocks=self._default_blocks(),
        )

    @staticmethod
    def _default_hotkeys() -> Dict[str, str]:
        return {
            "1": "block_1",
            "2": "block_2",
            "3": "block_3",
            "Shift+1": "block_1_v2",
            "Shift+2": "block_2_v2",
            "Shift+3": "block_3_v2",
            "Ctrl+1": "block_1_v3",
            "Ctrl+2": "block_2_v3",
            "Ctrl+3": "block_3_v3",
            "Ctrl+R": "reset_block",
            "F8": "toggle_pause",
        }

    @staticmethod
    def _default_blocks() -> list[CodeBlock]:
        return [
            CodeBlock(
                id="block_1",
                name="Block 1: Hello World",
                code='print("Hello World")\n',
            ),
            CodeBlock(
                id="block_2",
                name="Block 2: For Loop C++",
                code="for (int i = 0; i < n; i++) {\n    cout << i << endl;\n}\n",
            ),
            CodeBlock(
                id="block_3",
                name="Block 3: Array Sum C++",
                code="int sum = 0;\nfor (int i = 0; i < n; i++) {\n    sum += a[i];\n}\n",
            ),
            CodeBlock(
                id="block_1_v2",
                name="Block 1 (Var 2): Python Def",
                code="def main():\n    print('Hello World')\n\nif __name__ == '__main__':\n    main()\n",
            ),
            CodeBlock(
                id="block_2_v2",
                name="Block 2 (Var 2): While Loop",
                code="int i = 0;\nwhile (i < n) {\n    cout << i;\n    i++;\n}\n",
            ),
            CodeBlock(
                id="block_3_v2",
                name="Block 3 (Var 2): Vector Sum",
                code="int sum = std::accumulate(vec.begin(), vec.end(), 0);\n",
            ),
        ]