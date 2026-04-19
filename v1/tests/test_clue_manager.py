import pytest
from src.models import GameWorld, Scene, Source, Clue, ClueType, DeductionLink, SourceType, PlayerState, UnlockCondition
from src.game.clue_manager import ClueManager

def test_clue_manager_check_unlock_no_condition():
    world = GameWorld(
        truth={"凶手": "管家"},
        scenes=[],
        sources=[],
        clues=[
            Clue(id="CLUE_1", content="线索内容", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"),
                 unlock_condition=None)
        ],
        actions=[]
    )
    state = PlayerState(current_scene_id="S1", collected_clues=[], locked_dimensions={"凶手": None})
    manager = ClueManager(world, state)

    can_unlock, reason = manager.check_unlock("CLUE_1")
    assert can_unlock is True

def test_clue_manager_check_unlock_with_condition_met():
    world = GameWorld(
        truth={"凶手": "管家", "凶器": "毒药"},
        scenes=[],
        sources=[],
        clues=[
            Clue(id="CLUE_1", content="红酒有毒", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶器", target_value="毒药", reasoning="推理"),
                 unlock_condition=None),
            Clue(id="CLUE_2", content="管家手套有毒", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"),
                 unlock_condition=UnlockCondition(required_clues=["CLUE_1"], reason="需要先发现红酒有毒"))
        ],
        actions=[]
    )
    state = PlayerState(
        current_scene_id="S1",
        collected_clues=["CLUE_1"],
        locked_dimensions={"凶手": None, "凶器": None}
    )
    manager = ClueManager(world, state)

    can_unlock, reason = manager.check_unlock("CLUE_2")
    assert can_unlock is True

def test_clue_manager_check_unlock_with_condition_not_met():
    world = GameWorld(
        truth={"凶手": "管家"},
        scenes=[],
        sources=[],
        clues=[
            Clue(id="CLUE_2", content="管家手套有毒", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"),
                 unlock_condition=UnlockCondition(required_clues=["CLUE_1"], reason="需要先发现红酒有毒"))
        ],
        actions=[]
    )
    state = PlayerState(
        current_scene_id="S1",
        collected_clues=[],  # 未收集 CLUE_1
        locked_dimensions={"凶手": None}
    )
    manager = ClueManager(world, state)

    can_unlock, reason = manager.check_unlock("CLUE_2")
    assert can_unlock is False
    assert reason == "需要先发现红酒有毒"