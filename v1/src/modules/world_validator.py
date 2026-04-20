from typing import Tuple, List
from ..models import GameWorld, ClueType, ActionType


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

        # 3. 检查移动行动的双向连通性
        move_actions = {}
        for action in world.actions:
            if action.action_type == ActionType.move and action.target_scene_id:
                key = (action.target_scene_id, None)  # 目标场景，来源场景未记录
                move_actions[action.target_scene_id] = action

        # 建立场景连接关系图
        for scene in world.scenes:
            for connected_id in scene.connected_scenes:
                # 检查是否有从当前场景到连接场景的移动行动
                has_move = False
                for action in world.actions:
                    if action.action_type == ActionType.move:
                        # 需要知道行动的起始场景，但当前数据结构不支持
                        # 改为检查连接场景是否有返回行动
                        pass

                # 更简单的方式：检查 connected_scenes 是否对称
                connected_scene = self._get_scene_by_id(world, connected_id)
                if connected_scene and scene.id not in connected_scene.connected_scenes:
                    errors.append(f"场景 '{scene.name}' 连接到 '{connected_scene.name}'，但后者没有返回连接")

        # 4. 检查每个连接是否有对应的 move 行动
        for scene in world.scenes:
            for connected_id in scene.connected_scenes:
                connected_scene = self._get_scene_by_id(world, connected_id)
                if not connected_scene:
                    errors.append(f"场景 '{scene.name}' 连接到不存在场景 '{connected_id}'")
                    continue

                # 检查双向 move 行动
                has_forward = False
                has_backward = False
                for action in world.actions:
                    if action.action_type == ActionType.move:
                        # 由于行动数据不记录起始场景，只能通过检查数量来验证
                        if action.target_scene_id == connected_id:
                            has_forward = True
                        if action.target_scene_id == scene.id:
                            has_backward = True

                if not has_forward:
                    errors.append(f"缺少从 '{scene.name}' 到 '{connected_scene.name}' 的移动行动")
                if not has_backward:
                    errors.append(f"缺少从 '{connected_scene.name}' 到 '{scene.name}' 的移动行动")

        return len(errors) == 0, errors

    def _get_scene_by_id(self, world: GameWorld, scene_id: str):
        for scene in world.scenes:
            if scene.id == scene_id:
                return scene
        return None