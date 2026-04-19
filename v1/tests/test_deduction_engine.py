import pytest
from src.models import GameWorld, Clue, ClueType, DeductionLink, PlayerState, UnlockCondition
from src.game.deduction_engine import DeductionEngine

def test_deduction_engine_process_key_clue():
    world = GameWorld(
        truth={"凶手": "管家", "凶器": "毒药"},
        scenes=[],
        sources=[],
        clues=[
            Clue(id="CLUE_1", content="红酒有毒", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶器", target_value="毒药", reasoning="推理"))
        ],
        actions=[]
    )
    state = PlayerState(
        current_scene_id="S1",
        collected_clues=["CLUE_1"],
        locked_dimensions={"凶手": None, "凶器": None}
    )
    engine = DeductionEngine(world, state)

    locked_dim, locked_value = engine.process_clue("CLUE_1")
    assert locked_dim == "凶器"
    assert locked_value == "毒药"
    assert state.locked_dimensions["凶器"] == "毒药"

def test_deduction_engine_check_victory():
    world = GameWorld(
        truth={"凶手": "管家"},
        scenes=[],
        sources=[],
        clues=[],
        actions=[]
    )
    state = PlayerState(
        current_scene_id="S1",
        collected_clues=[],
        locked_dimensions={"凶手": "管家"}
    )
    engine = DeductionEngine(world, state)

    assert engine.check_victory() is True

def test_deduction_engine_process_non_key_clue():
    """Test that process_clue returns (None, None) for non-key_clue types"""
    world = GameWorld(
        truth={"凶手": "管家"},
        scenes=[],
        sources=[],
        clues=[
            Clue(id="CLUE_PRE", content="前置线索", clue_type=ClueType.pre_clue,
                 deduction_link=None, unlock_condition=None)
        ],
        actions=[]
    )
    state = PlayerState(
        current_scene_id="S1",
        collected_clues=["CLUE_PRE"],
        locked_dimensions={"凶手": None}
    )
    engine = DeductionEngine(world, state)

    locked_dim, locked_value = engine.process_clue("CLUE_PRE")
    assert locked_dim is None
    assert locked_value is None

def test_deduction_engine_process_invalid_clue():
    """Test that process_clue returns (None, None) for invalid clue_id"""
    world = GameWorld(
        truth={"凶手": "管家"},
        scenes=[],
        sources=[],
        clues=[],
        actions=[]
    )
    state = PlayerState(
        current_scene_id="S1",
        collected_clues=[],
        locked_dimensions={"凶手": None}
    )
    engine = DeductionEngine(world, state)

    locked_dim, locked_value = engine.process_clue("INVALID_CLUE")
    assert locked_dim is None
    assert locked_value is None

def test_deduction_engine_check_victory_false():
    """Test that check_victory returns False when not all dimensions are locked"""
    world = GameWorld(
        truth={"凶手": "管家", "凶器": "毒药"},
        scenes=[],
        sources=[],
        clues=[],
        actions=[]
    )
    state = PlayerState(
        current_scene_id="S1",
        collected_clues=[],
        locked_dimensions={"凶手": "管家", "凶器": None}  # Only one locked
    )
    engine = DeductionEngine(world, state)

    assert engine.check_victory() is False