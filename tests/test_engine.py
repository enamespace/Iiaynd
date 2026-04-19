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