from typing import Dict, Optional, List
from models import CodeBlock


class BlockManager:
    def __init__(self, blocks: List[CodeBlock]):
        self.blocks: Dict[str, CodeBlock] = {b.id: b for b in blocks}
        self.active_block_id: Optional[str] = blocks[0].id if blocks else None

    def set_blocks(self, blocks: List[CodeBlock]) -> None:
        self.blocks = {b.id: b for b in blocks}
        if self.active_block_id not in self.blocks and blocks:
            self.active_block_id = blocks[0].id

    def get_active_block(self) -> Optional[CodeBlock]:
        if self.active_block_id and self.active_block_id in self.blocks:
            return self.blocks[self.active_block_id]
        return None

    def select_block(self, block_id: str) -> bool:
        if block_id in self.blocks:
            self.active_block_id = block_id
            return True
        return False

    def reset_current_block(self) -> None:
        active = self.get_active_block()
        if active:
            active.reset()

    def rewind_current_block(self) -> None:
        active = self.get_active_block()
        if active:
            active.rewind()

    def advance_current_block(self) -> None:
        active = self.get_active_block()
        if active:
            active.advance()