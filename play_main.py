import json
import sys
from pathlib import Path
from src.models import GameWorld, PlayerState
from src.game.cli_interface import CLIInterface
from src.game.engine import GameEngine

def load_game_world(game_file: str) -> GameWorld:
    """加载游戏世界"""
    path = Path(game_file)
    if not path.exists():
        raise FileNotFoundError(f"Game file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return GameWorld(**data)

def main():
    if len(sys.argv) < 2:
        print("Usage: python play_main.py <game_world.json>")
        print("Example: python play_main.py stories/sample/game_world.json")
        sys.exit(1)

    game_file = sys.argv[1]

    try:
        world = load_game_world(game_file)
    except Exception as e:
        print(f"Error loading game: {e}")
        sys.exit(1)

    # 初始化玩家状态
    initial_dimensions = {dim: None for dim in world.truth.keys()}
    state = PlayerState(
        current_scene_id=world.scenes[0].id if world.scenes else "",
        collected_clues=[],
        executed_actions=[],
        stamina=100,
        locked_dimensions=initial_dimensions
    )

    interface = CLIInterface(world, state)
    engine = interface.engine

    print("\n推理游戏开始！收集线索，找出真相。\n")

    while True:
        # 显示界面
        print(interface.render_full_display())

        # 接收输入
        try:
            choice = input().strip().lower()
        except EOFError:
            break

        # 查看证据
        if choice == "v":
            print(interface.render_evidence())
            input()
            continue

        # 选择行动
        try:
            action_index = int(choice) - 1
            actions = engine.get_available_actions()
            if action_index < 0 or action_index >= len(actions):
                print("无效的选择，请重新输入。")
                continue

            action = actions[action_index]
            success, message = engine.execute_action(action.id)

            print("\n" + "=" * 60)
            print(message)
            print("=" * 60 + "\n")

            # 检查胜利
            if engine.deduction_engine.check_victory():
                print(interface.render_victory())
                break

        except ValueError:
            print("请输入数字或 'v' 查看证据。")

if __name__ == "__main__":
    main()