from ..models import GameWorld, PlayerState, GameAction
from .engine import GameEngine

class CLIInterface:
    def __init__(self, world: GameWorld, state: PlayerState):
        self.world = world
        self.state = state
        self.engine = GameEngine(world, state)

    def render_scene(self) -> str:
        """渲染当前场景"""
        scene = self.engine.get_current_scene()
        lines = [
            "=" * 60,
            f"【{scene.name}】",
            scene.description,
            "=" * 60
        ]
        return "\n".join(lines)

    def render_status(self) -> str:
        """渲染玩家状态"""
        lines = []
        for dim, value in self.state.locked_dimensions.items():
            if value is None:
                lines.append(f"【待推理】 {dim}: ?")
            else:
                lines.append(f"【已锁定】 {dim}: {value} ✓")
        lines.append(f"体力: {self.state.stamina}")
        return "\n".join(lines)

    def render_actions(self) -> str:
        """渲染可用行动"""
        actions = self.engine.get_available_actions()
        lines = ["【可用行动】"]
        for i, action in enumerate(actions, 1):
            lines.append(f"{i}. {action.name}")
        lines.append("v. 查看已收集的证据")
        return "\n".join(lines)

    def render_full_display(self) -> str:
        """渲染完整界面"""
        return "\n".join([
            self.render_scene(),
            self.render_status(),
            "=" * 60,
            self.render_actions(),
            "=" * 60,
            "请输入选择: "
        ])

    def render_evidence(self) -> str:
        """渲染已收集证据"""
        lines = ["=" * 60, "【已收集证据】"]
        for clue_id in self.state.collected_clues:
            clue = self.engine.clue_manager.get_clue_by_id(clue_id)
            if clue:
                lines.append(f"\n[{clue_id}] {clue.content}")
                if clue.deduction_link:
                    lines.append(f"    → 推理：{clue.deduction_link.truth_dimension} = {clue.deduction_link.target_value}")
                    lines.append(f"      ({clue.deduction_link.reasoning})")
        lines.append("\n" + "=" * 60)
        lines.append("按回车返回...")
        return "\n".join(lines)

    def render_victory(self) -> str:
        """渲染胜利界面"""
        lines = [
            "=" * 60,
            "🎉 推理完成！真相揭晓",
            "",
            "【真相】"
        ]
        for dim, value in self.world.truth.items():
            lines.append(f"{dim}: {value}")

        lines.append("\n【推理路径】")
        for clue_id in self.state.collected_clues:
            clue = self.engine.clue_manager.get_clue_by_id(clue_id)
            if clue and clue.deduction_link:
                lines.append(f"• {clue.content} → 锁定{clue.deduction_link.truth_dimension}：{clue.deduction_link.target_value}")

        lines.append("\n感谢游玩！")
        lines.append("=" * 60)
        return "\n".join(lines)