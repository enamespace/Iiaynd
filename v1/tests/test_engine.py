import pytest
from src.models import (
    World, Scene, Source, SourceType, Clue, ClueType,
    DeductionLink, Action, ActionType, PlayerState
)
from src.game.engine import GameEngine

def test_game_engine_get_available_actions():
    world = World(
        truth={"凶手": "管家"},
        scenes=[
            Scene(id="scene_1", name="书房", description="书房", connected_scenes=["scene_2"]),
            Scene(id="scene_2", name="客厅", description="客厅", connected_scenes=["scene_1"])
        ],
        sources=[
            Source(id="item_1", name="红酒杯", type=SourceType.item, description="红酒杯", scene_id="scene_1", hidden_clues=["clue_1"])
        ],
        clues=[
            Clue(id="clue_1", content="线索", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
        ],
        actions=[
            Action(id="action_1", name="检查红酒杯", action_type=ActionType.interact, target_source_id="item_1"),
            Action(id="action_2", name="前往客厅", action_type=ActionType.move, target_scene_id="scene_2")
        ]
    )
    state = PlayerState(current_scene_id="scene_1", collected_clues=[], locked_dimensions={"凶手": None})
    engine = GameEngine(world, state)

    actions = engine.get_available_actions()
    # 应包含当前场景的交互行动和移动行动
    assert len(actions) == 2
    assert any(a.id == "action_1" for a in actions)
    assert any(a.id == "action_2" for a in actions)

def test_game_engine_execute_move_action():
    """Test that execute_action correctly handles move actions"""
    world = World(
        truth={"凶手": "管家"},
        scenes=[
            Scene(id="scene_1", name="书房", description="书房", connected_scenes=["scene_2"]),
            Scene(id="scene_2", name="客厅", description="客厅", connected_scenes=["scene_1"])
        ],
        sources=[],
        clues=[],
        actions=[
            Action(id="action_2", name="前往客厅", action_type=ActionType.move, target_scene_id="scene_2", cost={"stamina": 10})
        ]
    )
    state = PlayerState(current_scene_id="scene_1", collected_clues=[], locked_dimensions={"凶手": None}, stamina=100)
    engine = GameEngine(world, state)

    success, message = engine.execute_action("action_2")
    assert success is True
    assert "客厅" in message
    assert state.current_scene_id == "scene_2"
    assert state.stamina == 90
    assert "action_2" in state.executed_actions

def test_game_engine_execute_interact_and_victory():
    """Test that execute_action handles interact and triggers victory"""
    world = World(
        truth={"凶手": "管家"},
        scenes=[
            Scene(id="scene_1", name="书房", description="书房", connected_scenes=[])
        ],
        sources=[
            Source(id="item_1", name="红酒杯", type=SourceType.item, description="红酒杯", scene_id="scene_1", hidden_clues=["clue_1"])
        ],
        clues=[
            Clue(id="clue_1", content="管家手套有毒", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
        ],
        actions=[
            Action(id="action_1", name="检查红酒杯", action_type=ActionType.interact, target_source_id="item_1")
        ]
    )
    state = PlayerState(current_scene_id="scene_1", collected_clues=[], locked_dimensions={"凶手": None})
    engine = GameEngine(world, state)

    # 执行交互行动
    success, message = engine.execute_action("action_1")
    assert success is True
    # 现在消息包含物品描述和线索
    assert "红酒杯" in message
    assert "锁定" in message
    assert state.locked_dimensions["凶手"] == "管家"

    # 检查胜利
    assert engine.deduction_engine.check_victory() is True


def test_game_engine_interact_no_clues():
    """Test that execute_action shows description when source has no clues"""
    world = World(
        truth={"凶手": "管家"},
        scenes=[
            Scene(id="scene_1", name="书房", description="书房", connected_scenes=[])
        ],
        sources=[
            Source(id="item_1", name="古董匕首", type=SourceType.item, description="一把华丽的古董匕首", scene_id="scene_1", hidden_clues=[])
        ],
        clues=[],
        actions=[
            Action(id="action_1", name="检查匕首", action_type=ActionType.interact, target_source_id="item_1")
        ]
    )
    state = PlayerState(current_scene_id="scene_1", collected_clues=[], locked_dimensions={"凶手": None})
    engine = GameEngine(world, state)

    success, message = engine.execute_action("action_1")
    assert success is True
    # 即使没有线索，也应该显示物品描述
    assert "古董匕首" in message
    assert "华丽的古董匕首" in message
    assert "没有发现更多线索" in message