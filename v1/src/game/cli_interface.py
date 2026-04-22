from ..models import World, PlayerState, Action
from .engine import GameEngine

class CLIInterface:
    def __init__(self, world: World, state: PlayerState):
        self.world = world
        self.state = state
        self.engine = GameEngine(world, state)
        self.last_clue_content = None  # 最近获得的线索

    def set_last_clue(self, clue_content: str):
        """设置最近获得的线索内容"""
        self.last_clue_content = clue_content

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

    def render_last_clue(self) -> str:
        """渲染最近获得的线索"""
        if not self.last_clue_content:
            return ""
        lines = [
            "【最近获得线索】",
            self.last_clue_content,
            ""
        ]
        self.last_clue_content = None  # 显示后清空
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
        parts = [
            self.render_scene(),
            self.render_status(),
            "=" * 60,
        ]
        # 如果有最近获得的线索，显示它
        last_clue = self.render_last_clue()
        if last_clue:
            parts.append(last_clue)
        parts.extend([
            self.render_actions(),
            "=" * 60,
            "请输入选择: "
        ])
        return "\n".join(parts)

    def render_evidence(self) -> str:
        """渲染已收集证据"""
        lines = ["=" * 60, "【已收集证据】"]
        for clue_id in self.state.collected_clues:
            clue = self.world.get_clue_by_id(clue_id)
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
            clue = self.world.get_clue_by_id(clue_id)
            if clue and clue.deduction_link:
                lines.append(f"• {clue.content} → 锁定{clue.deduction_link.truth_dimension}：{clue.deduction_link.target_value}")

        lines.append("\n感谢游玩！")
        lines.append("=" * 60)
        return "\n".join(lines)