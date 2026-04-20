#!/usr/bin/env python
"""
推理游戏 CLI v1

单页面刷新式界面，结果保存到 runs 目录

用法：python play_main.py <game_world.json>
示例：python play_main.py stories/island/runs/20260420_100000/game_world.json
"""

import json
import sys
import os
import time
from pathlib import Path
from src.models import GameWorld, PlayerState
from src.game.cli_interface import CLIInterface
from src.game.engine import GameEngine

# ANSI 接口控制
CLEAR_SCREEN = "\033[2J\033[H"  # 清屏 + 移到顶部
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def clear():
    """清屏"""
    os.system('clear' if os.name != 'nt' else 'cls')


def load_game_world(game_file: str) -> GameWorld:
    """加载游戏世界"""
    path = Path(game_file)
    if not path.exists():
        raise FileNotFoundError(f"Not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return GameWorld(**json.load(f))


def save_run_result(world: GameWorld, state: PlayerState, game_file: str):
    """保存游玩结果到 runs 目录"""
    # 从 game_file 路径提取 story_name
    # e.g., stories/island/runs/xxx/game_world.json -> island
    parts = Path(game_file).parts
    story_name = parts[1] if len(parts) > 1 else "unknown"

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = Path(f"stories/{story_name}/runs/{timestamp}")
    run_dir.mkdir(parents=True, exist_ok=True)

    # 保存结果
    result = {
        "truth": world.truth,
        "collected_clues": state.collected_clues,
        "locked_dimensions": state.locked_dimensions,
        "executed_actions": state.executed_actions,
        "final_stamina": state.stamina,
        "victory": all(v is not None for v in state.locked_dimensions.values())
    }

    with open(run_dir / "result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return run_dir


def main():
    if len(sys.argv) < 2:
        print("Usage: python play_main.py <game_world.json>")
        print("Example: python play_main.py stories/island/runs/xxx/game_world.json")
        sys.exit(1)

    game_file = sys.argv[1]

    try:
        world = load_game_world(game_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # 初始化
    dimensions = {dim: None for dim in world.truth.keys()}
    state = PlayerState(
        current_scene_id=world.scenes[0].id if world.scenes else "",
        collected_clues=[],
        executed_actions=[],
        stamina=100,
        locked_dimensions=dimensions
    )

    interface = CLIInterface(world, state)
    engine = interface.engine

    print(f"\n{GREEN}推理游戏开始{RESET} - 收集线索，找出真相\n")

    while True:
        clear()

        # 显示主界面
        print(interface.render_full_display())

        try:
            choice = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n游戏结束")
            break

        # 查看证据
        if choice == "v":
            clear()
            print(interface.render_evidence())
            input("按回车返回...")
            continue

        # 选择行动
        try:
            idx = int(choice) - 1
            actions = engine.get_available_actions()
            if idx < 0 or idx >= len(actions):
                continue

            action = actions[idx]
            success, message = engine.execute_action(action.id)

            # 如果是交互行动且有线索，显示线索内容
            if action.action_type.value == "interact" and success:
                interface.set_last_clue(message)

            # 检查胜利
            if engine.deduction_engine.check_victory():
                clear()
                print(interface.render_victory())
                run_dir = save_run_result(world, state, game_file)
                print(f"\n结果已保存: {run_dir / 'result.json'}")
                break

        except ValueError:
            continue

    print(SHOW_CURSOR)


if __name__ == "__main__":
    main()