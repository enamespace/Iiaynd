import pytest
from src.models import Scene, Source, SourceType

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