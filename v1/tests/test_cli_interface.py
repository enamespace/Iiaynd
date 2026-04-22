import pytest
from src.models import (
    World, Scene, Source, SourceType, Clue, ClueType,
    DeductionLink, Action, ActionType, PlayerState
)
from src.game.cli_interface import CLIInterface

def test_cli_interface_render_scene():
    world = World(
        truth={"凶手": "管家"},
        scenes=[
            Scene(id="scene_1", name="书房", description="一间昏暗的书房", connected_scenes=[])
        ],
        sources=[],
        clues=[],
        actions=[]
    )
    state = PlayerState(current_scene_id="scene_1", collected_clues=[], locked_dimensions={"凶手": None})
    interface = CLIInterface(world, state)

    output = interface.render_scene()
    assert "书房" in output
    assert "昏暗" in output

def test_cli_interface_render_status():
    world = World(
        truth={"凶手": "管家", "凶器": "毒药"},
        scenes=[Scene(id="scene_1", name="书房", description="书房", connected_scenes=[])],
        sources=[],
        clues=[],
        actions=[]
    )
    state = PlayerState(
        current_scene_id="scene_1",
        collected_clues=[],
        locked_dimensions={"凶手": None, "凶器": "毒药"}
    )
    interface = CLIInterface(world, state)

    output = interface.render_status()
    assert "凶器: 毒药" in output
    assert "已锁定" in output

def test_cli_interface_render_actions():
    world = World(
        truth={"凶手": "管家"},
        scenes=[Scene(id="scene_1", name="书房", description="书房", connected_scenes=["scene_2"])],
        sources=[],
        clues=[],
        actions=[
            Action(id="action_1", name="前往客厅", action_type=ActionType.move, target_scene_id="scene_2")
        ]
    )
    state = PlayerState(current_scene_id="scene_1", collected_clues=[], locked_dimensions={"凶手": None})
    interface = CLIInterface(world, state)

    output = interface.render_actions()
    assert "前往客厅" in output
    assert "v." in output