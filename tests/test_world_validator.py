import pytest
from src.models import (
    GameWorld, Scene, Source, SourceType, Clue, ClueType, DeductionLink
)
from src.modules.world_validator import WorldValidator


def test_world_validator_valid_world():
    world = GameWorld(
        truth={"凶手": "管家"},
        scenes=[Scene(id="S1", name="书房", description="书房", connected_scenes=[])],
        sources=[Source(id="NPC1", name="管家", type=SourceType.npc, description="管家", scene_id="S1", hidden_clues=["CLUE_1"])],
        clues=[
            Clue(id="CLUE_1", content="线索", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
        ],
        actions=[]
    )
    validator = WorldValidator()
    is_valid, errors = validator.validate(world)
    assert is_valid is True
    assert len(errors) == 0


def test_world_validator_missing_key_clue_for_dimension():
    world = GameWorld(
        truth={"凶手": "管家", "凶器": "毒药"},  # 两个维度
        scenes=[],
        sources=[],
        clues=[
            Clue(id="CLUE_1", content="线索", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
            # 缺少凶器的key_clue
        ],
        actions=[]
    )
    validator = WorldValidator()
    is_valid, errors = validator.validate(world)
    assert is_valid is False
    assert any("凶器" in e for e in errors)