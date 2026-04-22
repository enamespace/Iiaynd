import pytest
from src.models import Scene, Source, SourceType, Clue, ClueType, DeductionLink, UnlockCondition, Action, ActionType, World, PlayerState

def test_scene_model_creation():
    scene = Scene(
        id="scene_1",
        name="书房",
        description="一间昏暗的书房",
        connected_scenes=["scene_2", "scene_3"]
    )
    assert scene.id == "scene_1"
    assert scene.name == "书房"
    assert scene.description == "一间昏暗的书房"
    assert scene.connected_scenes == ["scene_2", "scene_3"]

def test_source_npc_creation():
    source = Source(
        id="npc_1",
        name="管家",
        type=SourceType.npc,
        description="一位穿着整洁西装的中年男子",
        scene_id="scene_2",
        hidden_clues=["clue_1"]
    )
    assert source.type == SourceType.npc
    assert source.hidden_clues == ["clue_1"]

def test_source_item_creation():
    source = Source(
        id="item_1",
        name="红酒杯",
        type=SourceType.item,
        description="桌上的半杯红酒",
        scene_id="scene_1",
        hidden_clues=["clue_2"]
    )
    assert source.type == SourceType.item

def test_clue_key_clue_creation():
    clue = Clue(
        id="clue_1",
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
        id="clue_pre_1",
        content="发现管家日记",
        clue_type=ClueType.pre_clue,
        deduction_link=None,
        unlock_condition=UnlockCondition(
            required_clues=["clue_2"],
            reason="需要先发现红酒有毒"
        )
    )
    assert clue.unlock_condition.required_clues == ["clue_2"]

def test_action_interact():
    action = Action(
        id="action_1",
        name="检查红酒杯",
        action_type=ActionType.interact,
        target_source_id="item_1",
        cost={"stamina": 5},
        unlock_condition=None
    )
    assert action.action_type == ActionType.interact
    assert action.target_source_id == "item_1"

def test_action_move():
    action = Action(
        id="action_2",
        name="前往客厅",
        action_type=ActionType.move,
        target_scene_id="scene_2",
        cost={"stamina": 10},
        unlock_condition=None
    )
    assert action.action_type == ActionType.move
    assert action.target_scene_id == "scene_2"

def test_world_creation():
    world = World(
        truth={"凶手": "管家", "凶器": "毒药"},
        scenes=[
            Scene(id="scene_1", name="书房", description="昏暗的书房", connected_scenes=["scene_2"])
        ],
        sources=[
            Source(id="npc_1", name="管家", type=SourceType.npc, description="管家", scene_id="scene_2", hidden_clues=["clue_1"])
        ],
        clues=[
            Clue(id="clue_1", content="线索", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
        ],
        actions=[
            Action(id="action_1", name="检查", action_type=ActionType.interact, target_source_id="npc_1")
        ]
    )
    assert world.truth["凶手"] == "管家"
    assert len(world.scenes) == 1
    assert len(world.clues) == 1

def test_world_query_methods():
    """Test the query methods on World class"""
    world = World(
        truth={"凶手": "管家"},
        scenes=[
            Scene(id="scene_1", name="书房", description="书房", connected_scenes=["scene_2"]),
            Scene(id="scene_2", name="客厅", description="客厅", connected_scenes=["scene_1"])
        ],
        sources=[
            Source(id="npc_1", name="管家", type=SourceType.npc, description="管家", scene_id="scene_1", hidden_clues=["clue_1"])
        ],
        clues=[
            Clue(id="clue_1", content="线索", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
        ],
        actions=[
            Action(id="action_1", name="检查", action_type=ActionType.interact, target_source_id="npc_1")
        ]
    )
    # Test query methods
    assert world.get_scene_by_id("scene_1").name == "书房"
    assert world.get_scene_by_id("invalid") is None
    assert world.get_source_by_id("npc_1").name == "管家"
    assert world.get_source_by_id("invalid") is None
    assert world.get_clue_by_id("clue_1").content == "线索"
    assert world.get_clue_by_id("invalid") is None
    assert world.get_action_by_id("action_1").name == "检查"
    assert world.get_action_by_id("invalid") is None

def test_player_state_creation():
    state = PlayerState(
        current_scene_id="scene_1",
        collected_clues=["clue_1"],
        executed_actions=["action_1"],
        stamina=100,
        locked_dimensions={"凶手": None, "凶器": None}
    )
    assert state.current_scene_id == "scene_1"
    assert state.stamina == 100
    assert state.locked_dimensions["凶手"] is None

def test_player_state_lock_dimension():
    state = PlayerState(
        current_scene_id="scene_1",
        collected_clues=[],
        executed_actions=[],
        stamina=100,
        locked_dimensions={"凶手": None, "凶器": None}
    )
    state.lock_dimension("凶手", "管家")
    assert state.locked_dimensions["凶手"] == "管家"

def test_player_state_is_all_locked():
    state = PlayerState(
        current_scene_id="scene_1",
        collected_clues=[],
        executed_actions=[],
        stamina=100,
        locked_dimensions={"凶手": "管家", "凶器": "毒药"}
    )
    assert state.is_all_locked() is True

def test_player_state_not_all_locked():
    state = PlayerState(
        current_scene_id="scene_1",
        collected_clues=[],
        executed_actions=[],
        stamina=100,
        locked_dimensions={"凶手": "管家", "凶器": None}
    )
    assert state.is_all_locked() is False