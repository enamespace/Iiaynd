from typing import Tuple
from ..models import GameWorld, PlayerState, Clue

class ClueManager:
    def __init__(self, world: GameWorld, state: PlayerState):
        self.world = world
        self.state = state

    def get_clue_by_id(self, clue_id: str) -> Clue | None:
        for clue in self.world.clues:
            if clue.id == clue_id:
                return clue
        return None

    def check_unlock(self, clue_id: str) -> Tuple[bool, str]:
        """检查线索是否可以被揭示"""
        clue = self.get_clue_by_id(clue_id)
        if clue is None:
            return False, f"线索 {clue_id} 不存在"

        if clue.unlock_condition is None:
            return True, ""

        # 检查是否已收集所有前置线索
        for required_id in clue.unlock_condition.required_clues:
            if required_id not in self.state.collected_clues:
                return False, clue.unlock_condition.reason

        return True, ""

    def reveal_clue(self, clue_id: str) -> Tuple[bool, str]:
        """揭示线索并加入玩家状态"""
        can_unlock, reason = self.check_unlock(clue_id)
        if not can_unlock:
            return False, reason

        clue = self.get_clue_by_id(clue_id)
        if clue is None:
            return False, "线索不存在"

        if clue_id not in self.state.collected_clues:
            self.state.collected_clues.append(clue_id)

        return True, clue.content