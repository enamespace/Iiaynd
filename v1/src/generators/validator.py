from typing import Tuple, List
from ..models import World, ClueType, ActionType


class WorldValidator:
    def validate(self, world: World) -> Tuple[bool, List[str]]:
        """验证游戏世界的逻辑链完备性"""
        errors = []

        # 1. 每个真相维度必须至少有一个key_clue
        errors.extend(self._validate_truth_dimensions_covered(world))

        # 2. 所有key_clue的target_value必须匹配truth
        errors.extend(self._validate_key_clue_targets(world))

        # 3. 检查场景连接的双向连通性
        errors.extend(self._validate_scene_connectivity(world))

        # 4. 验证key_clue可获得性
        errors.extend(self._validate_key_clues_reachable(world))

        # 5. 验证有线索的source有对应的interact行动
        errors.extend(self._validate_sources_have_actions(world))

        # 6. 验证所有引用ID存在
        errors.extend(self._validate_reference_integrity(world))

        return len(errors) == 0, errors

    def _validate_truth_dimensions_covered(self, world: World) -> List[str]:
        """验证每个真相维度都有对应的key_clue"""
        errors = []
        truth_dimensions = set(world.truth.keys())
        covered_dimensions = set()

        for clue in world.clues:
            if clue.clue_type == ClueType.key_clue and clue.deduction_link:
                covered_dimensions.add(clue.deduction_link.truth_dimension)

        missing_dims = truth_dimensions - covered_dimensions
        for dim in missing_dims:
            errors.append(f"真相维度 '{dim}' 缺少对应的 key_clue")

        return errors

    def _validate_key_clue_targets(self, world: World) -> List[str]:
        """验证所有key_clue的target_value匹配truth"""
        errors = []
        for clue in world.clues:
            if clue.clue_type == ClueType.key_clue and clue.deduction_link:
                dim = clue.deduction_link.truth_dimension
                expected = world.truth.get(dim)
                if expected != clue.deduction_link.target_value:
                    errors.append(
                        f"线索 {clue.id} 的 target_value '{clue.deduction_link.target_value}' "
                        f"与真相 '{expected}' 不匹配"
                    )
        return errors

    def _validate_scene_connectivity(self, world: World) -> List[str]:
        """验证场景连接的双向连通性"""
        errors = []

        for scene in world.scenes:
            for connected_id in scene.connected_scenes:
                connected_scene = world.get_scene_by_id(connected_id)
                if not connected_scene:
                    errors.append(f"场景 '{scene.name}' 连接到不存在场景 '{connected_id}'")
                    continue

                # 检查对称连接
                if scene.id not in connected_scene.connected_scenes:
                    errors.append(
                        f"场景 '{scene.name}' 连接到 '{connected_scene.name}'，"
                        f"但后者没有返回连接"
                    )

                # 检查双向 move 行动
                has_forward = any(
                    a.action_type == ActionType.move and a.target_scene_id == connected_id
                    for a in world.actions
                )
                has_backward = any(
                    a.action_type == ActionType.move and a.target_scene_id == scene.id
                    for a in world.actions
                )

                if not has_forward:
                    errors.append(f"缺少从 '{scene.name}' 到 '{connected_scene.name}' 的移动行动")
                if not has_backward:
                    errors.append(f"缺少从 '{connected_scene.name}' 到 '{scene.name}' 的移动行动")

        return errors

    def _validate_key_clues_reachable(self, world: World) -> List[str]:
        """验证所有key_clue都分配给了某个source"""
        errors = []

        key_clue_ids = {c.id for c in world.clues if c.clue_type == ClueType.key_clue}
        all_hidden_clues = set()
        for source in world.sources:
            all_hidden_clues.update(source.hidden_clues)

        missing = key_clue_ids - all_hidden_clues
        for clue_id in missing:
            errors.append(
                f"key_clue '{clue_id}' 未分配给任何 source，玩家无法获得"
            )

        return errors

    def _validate_sources_have_actions(self, world: World) -> List[str]:
        """验证每个有hidden_clues的source都有interact行动"""
        errors = []

        interact_targets = {
            a.target_source_id for a in world.actions
            if a.action_type == ActionType.interact and a.target_source_id
        }

        for source in world.sources:
            if source.hidden_clues and source.id not in interact_targets:
                errors.append(
                    f"source '{source.name}' ({source.id}) 有线索但缺少 interact 行动"
                )

        return errors

    def _validate_reference_integrity(self, world: World) -> List[str]:
        """验证所有引用ID都存在"""
        errors = []

        # 收集所有存在的ID
        clue_ids = {c.id for c in world.clues}
        source_ids = {s.id for s in world.sources}
        scene_ids = {s.id for s in world.scenes}

        # 检查 source.hidden_clues 中的线索ID
        for source in world.sources:
            for clue_id in source.hidden_clues:
                if clue_id not in clue_ids:
                    errors.append(
                        f"source '{source.name}' ({source.id}) 引用了不存在的线索 '{clue_id}'"
                    )

        # 检查 source.scene_id
        for source in world.sources:
            if source.scene_id not in scene_ids:
                errors.append(
                    f"source '{source.name}' ({source.id}) 引用了不存在的场景 '{source.scene_id}'"
                )

        # 检查 action.target_source_id
        for action in world.actions:
            if action.action_type == ActionType.interact and action.target_source_id:
                if action.target_source_id not in source_ids:
                    errors.append(
                        f"action '{action.name}' ({action.id}) 引用了不存在的 source '{action.target_source_id}'"
                    )

        # 检查 action.target_scene_id
        for action in world.actions:
            if action.action_type == ActionType.move and action.target_scene_id:
                if action.target_scene_id not in scene_ids:
                    errors.append(
                        f"action '{action.name}' ({action.id}) 引用了不存在的场景 '{action.target_scene_id}'"
                    )

        # 检查线索的 unlock_condition.required_clues
        for clue in world.clues:
            if clue.unlock_condition and clue.unlock_condition.required_clues:
                for req_clue_id in clue.unlock_condition.required_clues:
                    if req_clue_id not in clue_ids:
                        errors.append(
                            f"clue '{clue.id}' 的解锁条件引用了不存在的线索 '{req_clue_id}'"
                        )

        # 检查行动的 unlock_condition.required_clues
        for action in world.actions:
            if action.unlock_condition and action.unlock_condition.required_clues:
                for req_clue_id in action.unlock_condition.required_clues:
                    if req_clue_id not in clue_ids:
                        errors.append(
                            f"action '{action.name}' ({action.id}) 的解锁条件引用了不存在的线索 '{req_clue_id}'"
                        )

        return errors