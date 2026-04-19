from typing import Tuple, Optional
from ..models import GameWorld, PlayerState, Clue, ClueType

class DeductionEngine:
    def __init__(self, world: GameWorld, state: PlayerState):
        self.world = world
        self.state = state

    def get_clue_by_id(self, clue_id: str) -> Clue | None:
        for clue in self.world.clues:
            if clue.id == clue_id:
                return clue
        return None

    def process_clue(self, clue_id: str) -> Tuple[Optional[str], Optional[str]]:
        """处理线索，如果是key_clue则锁定对应维度"""
        clue = self.get_clue_by_id(clue_id)
        if clue is None:
            return None, None

        if clue.clue_type != ClueType.key_clue:
            return None, None

        if clue.deduction_link is None:
            return None, None

        dimension = clue.deduction_link.truth_dimension
        value = clue.deduction_link.target_value

        # 锁定维度
        self.state.lock_dimension(dimension, value)

        return dimension, value

    def check_victory(self) -> bool:
        """检查是否所有真相维度都已锁定"""
        return self.state.is_all_locked()