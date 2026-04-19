import pytest
from src.models import (
    GameWorld, Scene, Source, SourceType, Clue, ClueType,
    DeductionLink, GameAction, ActionType, PlayerState
)
from src.game.engine import GameEngine

def test_game_engine_get_available_actions():
    world = GameWorld(
        truth={"凶手": "管家"},
        scenes=[
            Scene(id="S1", name="书房", description="书房", connected_scenes=["S2"]),
            Scene(id="S2", name="客厅", description="客厅", connected_scenes=["S1"])
        ],
        sources=[
            Source(id="ITEM1", name="红酒杯", type=SourceType.item, description="红酒杯", scene_id="S1", hidden_clues=["CLUE_1"])
        ],
        clues=[
            Clue(id="CLUE_1", content="线索", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
        ],
        actions=[
            GameAction(id="A1", name="检查红酒杯", action_type=ActionType.interact, target_source_id="ITEM1"),
            GameAction(id="A2", name="前往客厅", action_type=ActionType.move, target_scene_id="S2")
        ]
    )
    state = PlayerState(current_scene_id="S1", collected_clues=[], locked_dimensions={"凶手": None})
    engine = GameEngine(world, state)

    actions = engine.get_available_actions()
    # 应包含当前场景的交互行动和移动行动
    assert len(actions) == 2
    assert any(a.id == "A1" for a in actions)
    assert any(a.id == "A2" for a in actions)

def test_game_engine_execute_move_action():
    """Test that execute_action correctly handles move actions"""
    world = GameWorld(
        truth={"凶手": "管家"},
        scenes=[
            Scene(id="S1", name="书房", description="书房", connected_scenes=["S2"]),
            Scene(id="S2", name="客厅", description="客厅", connected_scenes=["S1"])
        ],
        sources=[],
        clues=[],
        actions=[
            GameAction(id="A2", name="前往客厅", action_type=ActionType.move, target_scene_id="S2", cost={"stamina": 10})
        ]
    )
    state = PlayerState(current_scene_id="S1", collected_clues=[], locked_dimensions={"凶手": None}, stamina=100)
    engine = GameEngine(world, state)

    success, message = engine.execute_action("A2")
    assert success is True
    assert "客厅" in message
    assert state.current_scene_id == "S2"
    assert state.stamina == 90
    assert "A2" in state.executed_actions

def test_game_engine_execute_interact_and_victory():
    """Test that execute_action handles interact and triggers victory"""
    world = GameWorld(
        truth={"凶手": "管家"},
        scenes=[
            Scene(id="S1", name="书房", description="书房", connected_scenes=[])
        ],
        sources=[
            Source(id="ITEM1", name="红酒杯", type=SourceType.item, description="红酒杯", scene_id="S1", hidden_clues=["CLUE_1"])
        ],
        clues=[
            Clue(id="CLUE_1", content="管家手套有毒", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
        ],
        actions=[
            GameAction(id="A1", name="检查红酒杯", action_type=ActionType.interact, target_source_id="ITEM1")
        ]
    )
    state = PlayerState(current_scene_id="S1", collected_clues=[], locked_dimensions={"凶手": None})
    engine = GameEngine(world, state)

    # 执行交互行动
    success, message = engine.execute_action("A1")
    assert success is True
    assert "锁定" in message
    assert state.locked_dimensions["凶手"] == "管家"

    # 检查胜利
    assert engine.deduction_engine.check_victory() is True