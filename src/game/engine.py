from typing import List, Tuple
from ..models import (
    GameWorld, PlayerState, GameAction, ActionType, Scene, Source
)
from .clue_manager import ClueManager
from .deduction_engine import DeductionEngine

class GameEngine:
    def __init__(self, world: GameWorld, state: PlayerState):
        self.world = world
        self.state = state
        self.clue_manager = ClueManager(world, state)
        self.deduction_engine = DeductionEngine(world, state)

    def get_current_scene(self) -> Scene:
        for scene in self.world.scenes:
            if scene.id == self.state.current_scene_id:
                return scene
        raise ValueError(f"Scene {self.state.current_scene_id} not found")

    def get_sources_in_current_scene(self) -> List[Source]:
        current_scene = self.get_current_scene()
        return [s for s in self.world.sources if s.scene_id == current_scene.id]

    def get_available_actions(self) -> List[GameAction]:
        """获取当前可用的行动列表"""
        current_scene = self.get_current_scene()
        scene_sources = self.get_sources_in_current_scene()

        available = []
        for action in self.world.actions:
            # 移动行动：目标场景必须是当前场景的连接场景
            if action.action_type == ActionType.move:
                if action.target_scene_id in current_scene.connected_scenes:
                    available.append(action)

            # 交互行动：目标来源必须在当前场景
            elif action.action_type == ActionType.interact:
                if action.target_source_id in [s.id for s in scene_sources]:
                    available.append(action)

        return available

    def execute_action(self, action_id: str) -> Tuple[bool, str]:
        """执行行动"""
        action = self.get_action_by_id(action_id)
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
            source = self.get_source_by_id(action.target_source_id)
            if source is None:
                return False, "目标不存在"

            results = []
            for clue_id in source.hidden_clues:
                can_reveal, reason = self.clue_manager.check_unlock(clue_id)
                if can_reveal:
                    success, content = self.clue_manager.reveal_clue(clue_id)
                    if success:
                        # 处理推理锁定
                        dim, val = self.deduction_engine.process_clue(clue_id)
                        if dim:
                            results.append(f"{content}\n【锁定】你对【{dim}】已有了确切的结论：{val}")
                        else:
                            results.append(content)
                else:
                    results.append(f"目前无法发现更多信息。提示：{reason}")

            return True, "\n".join(results)

        return False, "未知行动类型"

    def get_action_by_id(self, action_id: str) -> GameAction | None:
        for action in self.world.actions:
            if action.id == action_id:
                return action
        return None

    def get_source_by_id(self, source_id: str) -> Source | None:
        for source in self.world.sources:
            if source.id == source_id:
                return source
        return None

    def get_scene_name(self, scene_id: str) -> str:
        for scene in self.world.scenes:
            if scene.id == scene_id:
                return scene.name
        return "未知场景"