from typing import Tuple
from ..models import World, PlayerState, Clue, ClueType

class DeductionEngine:
    def __init__(self, world: World, state: PlayerState):
        self.world = world
        self.state = state

    def process_clue(self, clue_id: str) -> Tuple[str | None, str | None]:
        """处理线索，如果是key_clue则锁定对应维度"""
        clue = self.world.get_clue_by_id(clue_id)
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