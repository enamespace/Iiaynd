from typing import List, Tuple
from ..models import (
    World, PlayerState, Action, ActionType, Scene, Source
)
from .clue_manager import ClueManager
from .deduction_engine import DeductionEngine

class GameEngine:
    def __init__(self, world: World, state: PlayerState):
        self.world = world
        self.state = state
        self.clue_manager = ClueManager(world, state)
        self.deduction_engine = DeductionEngine(world, state)

    def get_current_scene(self) -> Scene:
        scene = self.world.get_scene_by_id(self.state.current_scene_id)
        if scene is None:
            raise ValueError(f"Scene {self.state.current_scene_id} not found")
        return scene

    def get_sources_in_current_scene(self) -> List[Source]:
        current_scene = self.get_current_scene()
        return [s for s in self.world.sources if s.scene_id == current_scene.id]

    def get_available_actions(self) -> List[Action]:
        """获取当前可用的行动列表"""
        current_scene = self.get_current_scene()
        scene_sources = self.get_sources_in_current_scene()

        available = []
        seen_move_targets = set()  # 用于去重移动行动

        for action in self.world.actions:
            # 移动行动：目标场景必须是当前场景的连接场景，且去重
            if action.action_type == ActionType.move:
                if action.target_scene_id in current_scene.connected_scenes:
                    if action.target_scene_id not in seen_move_targets:
                        seen_move_targets.add(action.target_scene_id)
                        available.append(action)

            # 交互行动：目标来源必须在当前场景，且去重
            elif action.action_type == ActionType.interact:
                if action.target_source_id in [s.id for s in scene_sources]:
                    # 检查是否已经有相同 target_source_id 的行动
                    if not any(a.target_source_id == action.target_source_id for a in available):
                        available.append(action)

        return available

    def execute_action(self, action_id: str) -> Tuple[bool, str]:
        """执行行动"""
        action = self.world.get_action_by_id(action_id)
        if action is None:
            return False, f"行动 {action_id} 不存在"

        # 扣除体力
        for key, cost in action.cost.items():
            if key == "stamina":
                self.state.stamina -= cost

        # 记录已执行
        if action_id not in self.state.executed_actions:
            self.state.executed_actions.append(action_id)

        if action.action_type == ActionType.move:
            self.state.current_scene_id = action.target_scene_id
            return True, f"你移动到了{self.get_scene_name(action.target_scene_id)}"

        elif action.action_type == ActionType.interact:
            # 获取来源的隐藏线索
            source = self.world.get_source_by_id(action.target_source_id)
            if source is None:
                return False, "目标不存在"

            results = []

            # 先显示物品/NPC的描述
            results.append(f"【{source.name}】\n{source.description}")

            # 处理隐藏线索
            if source.hidden_clues:
                results.append("")  # 分隔线
                for clue_id in source.hidden_clues:
                    can_reveal, reason = self.clue_manager.check_unlock(clue_id)
                    if can_reveal:
                        success, content = self.clue_manager.reveal_clue(clue_id)
                        if success:
                            # 处理推理锁定
                            dim, val = self.deduction_engine.process_clue(clue_id)
                            if dim:
                                results.append(f"【发现线索】{content}\n【锁定】你对【{dim}】已有了确切的结论：{val}")
                            else:
                                results.append(f"【发现线索】{content}")
                    else:
                        results.append(f"【线索提示】目前无法发现更多信息。提示：{reason}")
            else:
                results.append("\n该物品上没有发现更多线索。")

            return True, "\n".join(results)

        return False, "未知行动类型"

    def get_scene_name(self, scene_id: str) -> str:
        scene = self.world.get_scene_by_id(scene_id)
        if scene is None:
            return "未知场景"
        return scene.name