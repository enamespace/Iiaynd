import pytest
from src.models import Scene

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