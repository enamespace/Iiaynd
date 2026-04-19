import pytest
from src.models import Scene, Source, SourceType, Clue, ClueType, DeductionLink, UnlockCondition

def test_scene_model_creation():
    scene = Scene(
        id="S1",
        name="书房",
        description="一间昏暗的书房",
        connected_scenes=["S2", "S3"]
    )
    assert scene.id == "S1"
    assert scene.name == "书房"
    assert scene.description == "一间昏暗的书房"
    assert scene.connected_scenes == ["S2", "S3"]

def test_source_npc_creation():
    source = Source(
        id="NPC1",
        name="管家",
        type=SourceType.npc,
        description="一位穿着整洁西装的中年男子",
        scene_id="S2",
        hidden_clues=["CLUE_KEY_1"]
    )
    assert source.type == SourceType.npc
    assert source.hidden_clues == ["CLUE_KEY_1"]

def test_source_item_creation():
    source = Source(
        id="ITEM1",
        name="红酒杯",
        type=SourceType.item,
        description="桌上的半杯红酒",
        scene_id="S1",
        hidden_clues=["CLUE_KEY_2"]
    )
    assert source.type == SourceType.item

def test_clue_key_clue_creation():
    clue = Clue(
        id="CLUE_KEY_1",
        content="管家手套内侧有毒药残留",
        clue_type=ClueType.key_clue,
        deduction_link=DeductionLink(
            truth_dimension="凶手",
            target_value="管家",
            reasoning="手套上有毒药说明管家接触过毒药"
        ),
        unlock_condition=None
    )
    assert clue.clue_type == ClueType.key_clue
    assert clue.deduction_link.truth_dimension == "凶手"

def test_clue_pre_clue_with_unlock_condition():
    clue = Clue(
        id="CLUE_PRE_1",
        content="发现管家日记",
        clue_type=ClueType.pre_clue,
        deduction_link=None,
        unlock_condition=UnlockCondition(
            required_clues=["CLUE_KEY_2"],
            reason="需要先发现红酒有毒"
        )
    )
    assert clue.unlock_condition.required_clues == ["CLUE_KEY_2"]