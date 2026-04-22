import pytest
from src.models import (
    World, Scene, Source, SourceType, Clue, ClueType, DeductionLink, Action, ActionType
)
from src.generators.validator import WorldValidator


def test_world_validator_valid_world():
    world = World(
        truth={"凶手": "管家"},
        scenes=[Scene(id="scene_1", name="书房", description="书房", connected_scenes=[])],
        sources=[Source(id="npc_1", name="管家", type=SourceType.npc, description="管家", scene_id="scene_1", hidden_clues=["clue_1"])],
        clues=[
            Clue(id="clue_1", content="线索", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
        ],
        actions=[
            Action(id="action_1", name="与管家交谈", action_type=ActionType.interact, target_source_id="npc_1")
        ]
    )
    validator = WorldValidator()
    is_valid, errors = validator.validate(world)
    assert is_valid is True
    assert len(errors) == 0


def test_world_validator_missing_key_clue_for_dimension():
    world = World(
        truth={"凶手": "管家", "凶器": "毒药"},  # 两个维度
        scenes=[],
        sources=[],
        clues=[
            Clue(id="clue_1", content="线索", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
            # 缺少凶器的key_clue
        ],
        actions=[]
    )
    validator = WorldValidator()
    is_valid, errors = validator.validate(world)
    assert is_valid is False
    assert any("凶器" in e for e in errors)


def test_world_validator_key_clue_not_reachable():
    """测试 key_clue 未分配给任何 source 的情况"""
    world = World(
        truth={"凶手": "管家"},
        scenes=[Scene(id="scene_1", name="书房", description="书房", connected_scenes=[])],
        sources=[Source(id="npc_1", name="管家", type=SourceType.npc, description="管家", scene_id="scene_1", hidden_clues=[])],
        clues=[
            Clue(id="clue_1", content="关键线索", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
            # clue_1 未分配给任何 source
        ],
        actions=[]
    )
    validator = WorldValidator()
    is_valid, errors = validator.validate(world)
    assert is_valid is False
    assert any("clue_1" in e and "未分配给任何 source" in e for e in errors)


def test_world_validator_source_missing_interact_action():
    """测试有线索的 source 缺少 interact 行动的情况"""
    world = World(
        truth={"凶手": "管家"},
        scenes=[Scene(id="scene_1", name="书房", description="书房", connected_scenes=[])],
        sources=[Source(id="npc_1", name="管家", type=SourceType.npc, description="管家", scene_id="scene_1", hidden_clues=["clue_1"])],
        clues=[
            Clue(id="clue_1", content="关键线索", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
        ],
        actions=[]  # 缺少对 npc_1 的 interact 行动
    )
    validator = WorldValidator()
    is_valid, errors = validator.validate(world)
    assert is_valid is False
    assert any("npc_1" in e and "缺少 interact 行动" in e for e in errors)


def test_world_validator_invalid_clue_reference():
    """测试 source 引用了不存在的线索"""
    world = World(
        truth={"凶手": "管家"},
        scenes=[Scene(id="scene_1", name="书房", description="书房", connected_scenes=[])],
        sources=[Source(
            id="npc_1",
            name="管家",
            type=SourceType.npc,
            description="管家",
            scene_id="scene_1",
            hidden_clues=["clue_1", "clue_999"]  # clue_999 不存在
        )],
        clues=[
            Clue(id="clue_1", content="线索", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
        ],
        actions=[
            Action(id="action_1", name="与管家交谈", action_type=ActionType.interact, target_source_id="npc_1")
        ]
    )
    validator = WorldValidator()
    is_valid, errors = validator.validate(world)
    assert is_valid is False
    assert any("clue_999" in e and "不存在" in e for e in errors)