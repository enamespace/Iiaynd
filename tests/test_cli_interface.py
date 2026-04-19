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