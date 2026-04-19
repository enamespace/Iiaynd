import pytest
from src.models import (
    GameWorld, Scene, Source, SourceType, Clue, ClueType,
    DeductionLink, GameAction, ActionType, PlayerState
)
from src.game.cli_interface import CLIInterface

def test_cli_interface_render_scene():
    world = GameWorld(
        truth={"凶手": "管家"},
        scenes=[
            Scene(id="S1", name="书房", description="一间昏暗的书房", connected_scenes=[])
        ],
        sources=[],
        clues=[],
        actions=[]
    )
    state = PlayerState(current_scene_id="S1", collected_clues=[], locked_dimensions={"凶手": None})
    interface = CLIInterface(world, state)

    output = interface.render_scene()
    assert "书房" in output
    assert "昏暗" in output

def test_cli_interface_render_status():
    world = GameWorld(
        truth={"凶手": "管家", "凶器": "毒药"},
        scenes=[Scene(id="S1", name="书房", description="书房", connected_scenes=[])],
        sources=[],
        clues=[],
        actions=[]
    )
    state = PlayerState(
        current_scene_id="S1",
        collected_clues=[],
        locked_dimensions={"凶手": None, "凶器": "毒药"}
    )
    interface = CLIInterface(world, state)

    output = interface.render_status()
    assert "凶器: 毒药" in output
    assert "已锁定" in output

def test_cli_interface_render_actions():
    world = GameWorld(
        truth={"凶手": "管家"},
        scenes=[Scene(id="S1", name="书房", description="书房", connected_scenes=["S2"])],
        sources=[],
        clues=[],
        actions=[
            GameAction(id="A1", name="前往客厅", action_type=ActionType.move, target_scene_id="S2")
        ]
    )
    state = PlayerState(current_scene_id="S1", collected_clues=[], locked_dimensions={"凶手": None})
    interface = CLIInterface(world, state)

    output = interface.render_actions()
    assert "前往客厅" in output
    assert "v." in output