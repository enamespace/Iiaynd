from typing import Tuple, List
from ..models import GameWorld, ClueType


class WorldValidator:
    def validate(self, world: GameWorld) -> Tuple[bool, List[str]]:
        """验证游戏世界的逻辑链完备性"""
        errors = []

        # 1. 每个真相维度必须至少有一个key_clue
        truth_dimensions = set(world.truth.keys())
        covered_dimensions = set()

        for clue in world.clues:
            if clue.clue_type == ClueType.key_clue and clue.deduction_link:
                covered_dimensions.add(clue.deduction_link.truth_dimension)

        missing_dims = truth_dimensions - covered_dimensions
        for dim in missing_dims:
            errors.append(f"真相维度 '{dim}' 缺少对应的 key_clue")

        # 2. 所有key_clue的target_value必须匹配truth
        for clue in world.clues:
            if clue.clue_type == ClueType.key_clue and clue.deduction_link:
                dim = clue.deduction_link.truth_dimension
                expected = world.truth.get(dim)
                if expected != clue.deduction_link.target_value:
                    errors.append(f"线索 {clue.id} 的 target_value '{clue.deduction_link.target_value}' 与真相 '{expected}' 不匹配")

        return len(errors) == 0, errors