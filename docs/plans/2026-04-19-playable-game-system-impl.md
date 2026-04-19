# Playable Game System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the reasoning game generator into a playable terminal game system where players can interact with scenes, collect clues, and deduce the truth.

**Architecture:** Two-phase system: Generation phase (reverse-generates evidence chain from truth) and Play phase (CLI game engine where clues automatically lock truth dimensions).

**Tech Stack:** Python, Pydantic, ZhipuAI LLM (zai-sdk), Terminal CLI

---

## Phase 1: Data Models

### Task 1.1: Create Scene Model

**Files:**
- Modify: `src/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing test**

Create `tests/test_models.py`:

```python
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
    assert scene.connected_scenes == ["S2", "S3"]
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models.py::test_scene_model_creation -v`
Expected: FAIL with "ImportError" or "Scene not defined"

**Step 3: Write minimal implementation**

Add to `src/models.py`:

```python
class Scene(BaseModel):
    id: str = Field(..., description="场景唯一标识符")
    name: str = Field(..., description="场景名称")
    description: str = Field(..., description="场景描述")
    connected_scenes: List[str] = Field(default_factory=list, description="可移动到的其他场景ID列表")
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_models.py::test_scene_model_creation -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_models.py src/models.py
git commit -m "feat: add Scene model"
```

---

### Task 1.2: Create Source Model (NPC/Item)

**Files:**
- Modify: `src/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing test**

Add to `tests/test_models.py`:

```python
from src.models import Source, SourceType

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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models.py::test_source_npc_creation -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Add to `src/models.py`:

```python
from enum import Enum

class SourceType(Enum):
    npc = "npc"
    item = "item"

class Source(BaseModel):
    id: str = Field(..., description="来源唯一标识符")
    name: str = Field(..., description="NPC或物品名称")
    type: SourceType = Field(..., description="来源类型：npc或item")
    description: str = Field(..., description="描述")
    scene_id: str = Field(..., description="所属场景ID")
    hidden_clues: List[str] = Field(default_factory=list, description="隐藏的线索ID列表")
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_models.py::test_source_npc_creation tests/test_models.py::test_source_item_creation -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_models.py src/models.py
git commit -m "feat: add Source model (NPC/Item)"
```

---

### Task 1.3: Create Clue Model with DeductionLink

**Files:**
- Modify: `src/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing test**

Add to `tests/test_models.py`:

```python
from src.models import Clue, ClueType, DeductionLink, UnlockCondition

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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models.py::test_clue_key_clue_creation -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Add to `src/models.py`:

```python
class ClueType(Enum):
    key_clue = "key_clue"
    pre_clue = "pre_clue"
    filler_clue = "filler_clue"

class DeductionLink(BaseModel):
    truth_dimension: str = Field(..., description="指向的真相维度")
    target_value: str = Field(..., description="锁定的值")
    reasoning: str = Field(..., description="推理逻辑说明")

class UnlockCondition(BaseModel):
    required_clues: List[str] = Field(default_factory=list, description="需要先获得的线索ID列表")
    reason: str = Field("", description="解锁条件的原因")

class Clue(BaseModel):
    id: str = Field(..., description="线索唯一标识符")
    content: str = Field(..., description="线索内容")
    clue_type: ClueType = Field(..., description="线索类型")
    deduction_link: Optional[DeductionLink] = Field(None, description="推理链接（仅key_clue有）")
    unlock_condition: Optional[UnlockCondition] = Field(None, description="解锁条件")
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_models.py::test_clue_key_clue_creation tests/test_models.py::test_clue_pre_clue_with_unlock_condition -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_models.py src/models.py
git commit -m "feat: add Clue model with DeductionLink and UnlockCondition"
```

---

### Task 1.4: Extend Action Model

**Files:**
- Modify: `src/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing test**

Add to `tests/test_models.py`:

```python
from src.models import GameAction, ActionType

def test_game_action_interact():
    action = GameAction(
        id="A1",
        name="检查红酒杯",
        action_type=ActionType.interact,
        target_source_id="ITEM1",
        cost={"stamina": 5},
        unlock_condition=None
    )
    assert action.action_type == ActionType.interact
    assert action.target_source_id == "ITEM1"

def test_game_action_move():
    action = GameAction(
        id="A2",
        name="前往客厅",
        action_type=ActionType.move,
        target_scene_id="S2",
        cost={"stamina": 10},
        unlock_condition=None
    )
    assert action.action_type == ActionType.move
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models.py::test_game_action_interact -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Add to `src/models.py`:

```python
class ActionType(Enum):
    move = "move"
    interact = "interact"

class GameAction(BaseModel):
    id: str = Field(..., description="行动唯一标识符")
    name: str = Field(..., description="行动名称")
    action_type: ActionType = Field(..., description="行动类型")
    target_source_id: Optional[str] = Field(None, description="交互目标来源ID（interact类型）")
    target_scene_id: Optional[str] = Field(None, description="目标场景ID（move类型）")
    cost: Dict[str, int] = Field(default_factory=dict, description="行动代价")
    unlock_condition: Optional[UnlockCondition] = Field(None, description="解锁条件")
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_models.py::test_game_action_interact tests/test_models.py::test_game_action_move -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_models.py src/models.py
git commit -m "feat: add GameAction model with ActionType"
```

---

### Task 1.5: Create GameWorld Model

**Files:**
- Modify: `src/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing test**

Add to `tests/test_models.py`:

```python
from src.models import GameWorld

def test_game_world_creation():
    world = GameWorld(
        truth={"凶手": "管家", "凶器": "毒药"},
        scenes=[
            Scene(id="S1", name="书房", description="昏暗的书房", connected_scenes=["S2"])
        ],
        sources=[
            Source(id="NPC1", name="管家", type=SourceType.npc, description="管家", scene_id="S2", hidden_clues=["CLUE_1"])
        ],
        clues=[
            Clue(id="CLUE_1", content="线索", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
        ],
        actions=[
            GameAction(id="A1", name="检查", action_type=ActionType.interact, target_source_id="NPC1")
        ]
    )
    assert world.truth["凶手"] == "管家"
    assert len(world.scenes) == 1
    assert len(world.clues) == 1
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models.py::test_game_world_creation -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Add to `src/models.py`:

```python
class GameWorld(BaseModel):
    truth: Dict[str, str] = Field(..., description="真相字典")
    scenes: List[Scene] = Field(default_factory=list, description="场景列表")
    sources: List[Source] = Field(default_factory=list, description="来源列表（NPC/物品）")
    clues: List[Clue] = Field(default_factory=list, description="线索列表")
    actions: List[GameAction] = Field(default_factory=list, description="行动列表")
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_models.py::test_game_world_creation -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_models.py src/models.py
git commit -m "feat: add GameWorld model"
```

---

### Task 1.6: Create PlayerState Model

**Files:**
- Modify: `src/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing test**

Add to `tests/test_models.py`:

```python
from src.models import PlayerState

def test_player_state_creation():
    state = PlayerState(
        current_scene_id="S1",
        collected_clues=["CLUE_1"],
        executed_actions=["A1"],
        stamina=100,
        locked_dimensions={"凶手": None, "凶器": None}
    )
    assert state.current_scene_id == "S1"
    assert state.stamina == 100
    assert state.locked_dimensions["凶手"] is None

def test_player_state_lock_dimension():
    state = PlayerState(
        current_scene_id="S1",
        collected_clues=[],
        executed_actions=[],
        stamina=100,
        locked_dimensions={"凶手": None, "凶器": None}
    )
    state.lock_dimension("凶手", "管家")
    assert state.locked_dimensions["凶手"] == "管家"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models.py::test_player_state_creation tests/test_models.py::test_player_state_lock_dimension -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Add to `src/models.py`:

```python
class PlayerState(BaseModel):
    current_scene_id: str = Field(..., description="当前所在场景ID")
    collected_clues: List[str] = Field(default_factory=list, description="已收集的线索ID列表")
    executed_actions: List[str] = Field(default_factory=list, description="已执行的行动ID列表")
    stamina: int = Field(100, description="体力值")
    locked_dimensions: Dict[str, Optional[str]] = Field(default_factory=dict, description="已锁定的真相维度")

    def lock_dimension(self, dimension: str, value: str):
        """锁定一个真相维度"""
        self.locked_dimensions[dimension] = value

    def is_all_locked(self) -> bool:
        """检查是否所有维度都已锁定"""
        return all(v is not None for v in self.locked_dimensions.values())
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_models.py::test_player_state_creation tests/test_models.py::test_player_state_lock_dimension -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_models.py src/models.py
git commit -m "feat: add PlayerState model with lock_dimension method"
```

---

## Phase 2: Game Engine Components

### Task 2.1: Create ClueManager

**Files:**
- Create: `src/game/clue_manager.py`
- Create: `src/game/__init__.py`
- Test: `tests/test_clue_manager.py`

**Step 1: Write the failing test**

Create `tests/test_clue_manager.py`:

```python
import pytest
from src.models import GameWorld, Scene, Source, Clue, ClueType, DeductionLink, SourceType, PlayerState
from src.game.clue_manager import ClueManager

def test_clue_manager_check_unlock_no_condition():
    world = GameWorld(
        truth={"凶手": "管家"},
        scenes=[],
        sources=[],
        clues=[
            Clue(id="CLUE_1", content="线索内容", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"),
                 unlock_condition=None)
        ],
        actions=[]
    )
    state = PlayerState(current_scene_id="S1", collected_clues=[], locked_dimensions={"凶手": None})
    manager = ClueManager(world, state)

    can_unlock, reason = manager.check_unlock("CLUE_1")
    assert can_unlock is True
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_clue_manager.py -v`
Expected: FAIL

**Step 3: Create package init**

Create `src/game/__init__.py`:

```python
from .clue_manager import ClueManager
```

**Step 4: Write minimal implementation**

Create `src/game/clue_manager.py`:

```python
from typing import Tuple
from ..models import GameWorld, PlayerState, Clue

class ClueManager:
    def __init__(self, world: GameWorld, state: PlayerState):
        self.world = world
        self.state = state

    def get_clue_by_id(self, clue_id: str) -> Clue | None:
        for clue in self.world.clues:
            if clue.id == clue_id:
                return clue
        return None

    def check_unlock(self, clue_id: str) -> Tuple[bool, str]:
        """检查线索是否可以被揭示"""
        clue = self.get_clue_by_id(clue_id)
        if clue is None:
            return False, f"线索 {clue_id} 不存在"

        if clue.unlock_condition is None:
            return True, ""

        # 检查是否已收集所有前置线索
        for required_id in clue.unlock_condition.required_clues:
            if required_id not in self.state.collected_clues:
                return False, clue.unlock_condition.reason

        return True, ""

    def reveal_clue(self, clue_id: str) -> Tuple[bool, str]:
        """揭示线索并加入玩家状态"""
        can_unlock, reason = self.check_unlock(clue_id)
        if not can_unlock:
            return False, reason

        clue = self.get_clue_by_id(clue_id)
        if clue is None:
            return False, "线索不存在"

        if clue_id not in self.state.collected_clues:
            self.state.collected_clues.append(clue_id)

        return True, clue.content
```

**Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_clue_manager.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add tests/test_clue_manager.py src/game/__init__.py src/game/clue_manager.py
git commit -m "feat: add ClueManager for clue reveal logic"
```

---

### Task 2.2: Add ClueManager unlock condition test

**Files:**
- Modify: `tests/test_clue_manager.py`

**Step 1: Write the failing test**

Add to `tests/test_clue_manager.py`:

```python
from src.models import UnlockCondition

def test_clue_manager_check_unlock_with_condition_met():
    world = GameWorld(
        truth={"凶手": "管家", "凶器": "毒药"},
        scenes=[],
        sources=[],
        clues=[
            Clue(id="CLUE_1", content="红酒有毒", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶器", target_value="毒药", reasoning="推理"),
                 unlock_condition=None),
            Clue(id="CLUE_2", content="管家手套有毒", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"),
                 unlock_condition=UnlockCondition(required_clues=["CLUE_1"], reason="需要先发现红酒有毒"))
        ],
        actions=[]
    )
    state = PlayerState(
        current_scene_id="S1",
        collected_clues=["CLUE_1"],
        locked_dimensions={"凶手": None, "凶器": None}
    )
    manager = ClueManager(world, state)

    can_unlock, reason = manager.check_unlock("CLUE_2")
    assert can_unlock is True

def test_clue_manager_check_unlock_with_condition_not_met():
    world = GameWorld(
        truth={"凶手": "管家"},
        scenes=[],
        sources=[],
        clues=[
            Clue(id="CLUE_2", content="管家手套有毒", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"),
                 unlock_condition=UnlockCondition(required_clues=["CLUE_1"], reason="需要先发现红酒有毒"))
        ],
        actions=[]
    )
    state = PlayerState(
        current_scene_id="S1",
        collected_clues=[],  # 未收集 CLUE_1
        locked_dimensions={"凶手": None}
    )
    manager = ClueManager(world, state)

    can_unlock, reason = manager.check_unlock("CLUE_2")
    assert can_unlock is False
    assert reason == "需要先发现红酒有毒"
```

**Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_clue_manager.py -v`
Expected: PASS (implementation already handles this)

**Step 3: Commit**

```bash
git add tests/test_clue_manager.py
git commit -m "test: add ClueManager unlock condition tests"
```

---

### Task 2.3: Create DeductionEngine

**Files:**
- Create: `src/game/deduction_engine.py`
- Test: `tests/test_deduction_engine.py`

**Step 1: Write the failing test**

Create `tests/test_deduction_engine.py`:

```python
import pytest
from src.models import GameWorld, Clue, ClueType, DeductionLink, PlayerState
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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_deduction_engine.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/game/deduction_engine.py`:

```python
from typing import Tuple, Optional
from ..models import GameWorld, PlayerState, Clue, ClueType

class DeductionEngine:
    def __init__(self, world: GameWorld, state: PlayerState):
        self.world = world
        self.state = state

    def get_clue_by_id(self, clue_id: str) -> Clue | None:
        for clue in self.world.clues:
            if clue.id == clue_id:
                return clue
        return None

    def process_clue(self, clue_id: str) -> Tuple[Optional[str], Optional[str]]:
        """处理线索，如果是key_clue则锁定对应维度"""
        clue = self.get_clue_by_id(clue_id)
        if clue is None:
            return None, None

        if clue.clue_type != ClueType.key_clue:
            return None, None

        if clue.deduction_link is None:
            return None, None

        dimension = clue.deduction_link.truth_dimension
        value = clue.deduction_link.target_value

        # 锁定维度
        self.state.lock_dimension(dimension, value)

        return dimension, value

    def check_victory(self) -> bool:
        """检查是否所有真相维度都已锁定"""
        return self.state.is_all_locked()
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_deduction_engine.py -v`
Expected: PASS

**Step 5: Update package init**

Modify `src/game/__init__.py`:

```python
from .clue_manager import ClueManager
from .deduction_engine import DeductionEngine
```

**Step 6: Commit**

```bash
git add tests/test_deduction_engine.py src/game/deduction_engine.py src/game/__init__.py
git commit -m "feat: add DeductionEngine for dimension locking"
```

---

### Task 2.4: Create GameEngine

**Files:**
- Create: `src/game/engine.py`
- Test: `tests/test_engine.py`

**Step 1: Write the failing test**

Create `tests/test_engine.py`:

```python
import pytest
from src.models import (
    GameWorld, Scene, Source, SourceType, Clue, ClueType,
    DeductionLink, GameAction, ActionType, PlayerState
)
from src.game.engine import GameEngine

def test_game_engine_get_available_actions():
    world = GameWorld(
        truth={"凶手": "管家"},
        scenes=[
            Scene(id="S1", name="书房", description="书房", connected_scenes=["S2"]),
            Scene(id="S2", name="客厅", description="客厅", connected_scenes=["S1"])
        ],
        sources=[
            Source(id="ITEM1", name="红酒杯", type=SourceType.item, description="红酒杯", scene_id="S1", hidden_clues=["CLUE_1"])
        ],
        clues=[
            Clue(id="CLUE_1", content="线索", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
        ],
        actions=[
            GameAction(id="A1", name="检查红酒杯", action_type=ActionType.interact, target_source_id="ITEM1"),
            GameAction(id="A2", name="前往客厅", action_type=ActionType.move, target_scene_id="S2")
        ]
    )
    state = PlayerState(current_scene_id="S1", collected_clues=[], locked_dimensions={"凶手": None})
    engine = GameEngine(world, state)

    actions = engine.get_available_actions()
    # 应包含当前场景的交互行动和移动行动
    assert len(actions) == 2
    assert any(a.id == "A1" for a in actions)
    assert any(a.id == "A2" for a in actions)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_engine.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/game/engine.py`:

```python
from typing import List, Tuple
from ..models import (
    GameWorld, PlayerState, GameAction, ActionType, Scene, Source
)
from .clue_manager import ClueManager
from .deduction_engine import DeductionEngine

class GameEngine:
    def __init__(self, world: GameWorld, state: PlayerState):
        self.world = world
        self.state = state
        self.clue_manager = ClueManager(world, state)
        self.deduction_engine = DeductionEngine(world, state)

    def get_current_scene(self) -> Scene:
        for scene in self.world.scenes:
            if scene.id == self.state.current_scene_id:
                return scene
        raise ValueError(f"Scene {self.state.current_scene_id} not found")

    def get_sources_in_current_scene(self) -> List[Source]:
        current_scene = self.get_current_scene()
        return [s for s in self.world.sources if s.scene_id == current_scene.id]

    def get_available_actions(self) -> List[GameAction]:
        """获取当前可用的行动列表"""
        current_scene = self.get_current_scene()
        scene_sources = self.get_sources_in_current_scene()

        available = []
        for action in self.world.actions:
            # 移动行动：目标场景必须是当前场景的连接场景
            if action.action_type == ActionType.move:
                if action.target_scene_id in current_scene.connected_scenes:
                    available.append(action)

            # 交互行动：目标来源必须在当前场景
            elif action.action_type == ActionType.interact:
                if action.target_source_id in [s.id for s in scene_sources]:
                    available.append(action)

        return available

    def execute_action(self, action_id: str) -> Tuple[bool, str]:
        """执行行动"""
        action = self.get_action_by_id(action_id)
        if action is None:
            return False, f"行动 {action_id} 不存在"

        # 扣除体力
        for key, cost in action.cost.items():
            if key == "stamina":
                self.state.stamina -= cost

        # 记录已执行
        if action_id not in self.state.executed_actions:
            self.state.executed_actions.append(action_id)

        if action.action_type == ActionType.move:
            self.state.current_scene_id = action.target_scene_id
            return True, f"你移动到了{self.get_scene_name(action.target_scene_id)}"

        elif action.action_type == ActionType.interact:
            # 获取来源的隐藏线索
            source = self.get_source_by_id(action.target_source_id)
            if source is None:
                return False, "目标不存在"

            results = []
            for clue_id in source.hidden_clues:
                can_reveal, reason = self.clue_manager.check_unlock(clue_id)
                if can_reveal:
                    success, content = self.clue_manager.reveal_clue(clue_id)
                    if success:
                        # 处理推理锁定
                        dim, val = self.deduction_engine.process_clue(clue_id)
                        if dim:
                            results.append(f"{content}\n【锁定】你对【{dim}】已有了确切的结论：{val}")
                        else:
                            results.append(content)
                else:
                    results.append(f"目前无法发现更多信息。提示：{reason}")

            return True, "\n".join(results)

        return False, "未知行动类型"

    def get_action_by_id(self, action_id: str) -> GameAction | None:
        for action in self.world.actions:
            if action.id == action_id:
                return action
        return None

    def get_source_by_id(self, source_id: str) -> Source | None:
        for source in self.world.sources:
            if source.id == source_id:
                return source
        return None

    def get_scene_name(self, scene_id: str) -> str:
        for scene in self.world.scenes:
            if scene.id == scene_id:
                return scene.name
        return "未知场景"
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_engine.py -v`
Expected: PASS

**Step 5: Update package init**

Modify `src/game/__init__.py`:

```python
from .clue_manager import ClueManager
from .deduction_engine import DeductionEngine
from .engine import GameEngine
```

**Step 6: Commit**

```bash
git add tests/test_engine.py src/game/engine.py src/game/__init__.py
git commit -m "feat: add GameEngine with action execution"
```

---

### Task 2.5: Add GameEngine victory test

**Files:**
- Modify: `tests/test_engine.py`

**Step 1: Write the test**

Add to `tests/test_engine.py`:

```python
def test_game_engine_execute_interact_and_victory():
    world = GameWorld(
        truth={"凶手": "管家"},
        scenes=[
            Scene(id="S1", name="书房", description="书房", connected_scenes=[])
        ],
        sources=[
            Source(id="ITEM1", name="红酒杯", type=SourceType.item, description="红酒杯", scene_id="S1", hidden_clues=["CLUE_1"])
        ],
        clues=[
            Clue(id="CLUE_1", content="管家手套有毒", clue_type=ClueType.key_clue,
                 deduction_link=DeductionLink(truth_dimension="凶手", target_value="管家", reasoning="推理"))
        ],
        actions=[
            GameAction(id="A1", name="检查红酒杯", action_type=ActionType.interact, target_source_id="ITEM1")
        ]
    )
    state = PlayerState(current_scene_id="S1", collected_clues=[], locked_dimensions={"凶手": None})
    engine = GameEngine(world, state)

    # 执行交互行动
    success, message = engine.execute_action("A1")
    assert success is True
    assert "锁定" in message
    assert state.locked_dimensions["凶手"] == "管家"

    # 检查胜利
    assert engine.deduction_engine.check_victory() is True
```

**Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_engine.py::test_game_engine_execute_interact_and_victory -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_engine.py
git commit -m "test: add GameEngine victory test"
```

---

## Phase 3: CLI Interface

### Task 3.1: Create CLIInterface

**Files:**
- Create: `src/game/cli_interface.py`
- Test: `tests/test_cli_interface.py`

**Step 1: Write the failing test**

Create `tests/test_cli_interface.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli_interface.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/game/cli_interface.py`:

```python
from ..models import GameWorld, PlayerState, GameAction
from .engine import GameEngine

class CLIInterface:
    def __init__(self, world: GameWorld, state: PlayerState):
        self.world = world
        self.state = state
        self.engine = GameEngine(world, state)

    def render_scene(self) -> str:
        """渲染当前场景"""
        scene = self.engine.get_current_scene()
        lines = [
            "=" * 60,
            f"【{scene.name}】",
            scene.description,
            "=" * 60
        ]
        return "\n".join(lines)

    def render_status(self) -> str:
        """渲染玩家状态"""
        lines = []
        for dim, value in self.state.locked_dimensions.items():
            if value is None:
                lines.append(f"【待推理】 {dim}: ?")
            else:
                lines.append(f"【已锁定】 {dim}: {value} ✓")
        lines.append(f"体力: {self.state.stamina}")
        return "\n".join(lines)

    def render_actions(self) -> str:
        """渲染可用行动"""
        actions = self.engine.get_available_actions()
        lines = ["【可用行动】"]
        for i, action in enumerate(actions, 1):
            lines.append(f"{i}. {action.name}")
        lines.append("v. 查看已收集的证据")
        return "\n".join(lines)

    def render_full_display(self) -> str:
        """渲染完整界面"""
        return "\n".join([
            self.render_scene(),
            self.render_status(),
            "=" * 60,
            self.render_actions(),
            "=" * 60,
            "请输入选择: "
        ])

    def render_evidence(self) -> str:
        """渲染已收集证据"""
        lines = ["=" * 60, "【已收集证据】"]
        for clue_id in self.state.collected_clues:
            clue = self.engine.clue_manager.get_clue_by_id(clue_id)
            if clue:
                lines.append(f"\n[{clue_id}] {clue.content}")
                if clue.deduction_link:
                    lines.append(f"    → 推理：{clue.deduction_link.truth_dimension} = {clue.deduction_link.target_value}")
                    lines.append(f"      ({clue.deduction_link.reasoning})")
        lines.append("\n" + "=" * 60)
        lines.append("按回车返回...")
        return "\n".join(lines)

    def render_victory(self) -> str:
        """渲染胜利界面"""
        lines = [
            "=" * 60,
            "🎉 推理完成！真相揭晓",
            "",
            "【真相】"
        ]
        for dim, value in self.world.truth.items():
            lines.append(f"{dim}: {value}")

        lines.append("\n【推理路径】")
        for clue_id in self.state.collected_clues:
            clue = self.engine.clue_manager.get_clue_by_id(clue_id)
            if clue and clue.deduction_link:
                lines.append(f"• {clue.content} → 锁定{clue.deduction_link.truth_dimension}：{clue.deduction_link.target_value}")

        lines.append("\n感谢游玩！")
        lines.append("=" * 60)
        return "\n".join(lines)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli_interface.py -v`
Expected: PASS

**Step 5: Update package init**

Modify `src/game/__init__.py`:

```python
from .clue_manager import ClueManager
from .deduction_engine import DeductionEngine
from .engine import GameEngine
from .cli_interface import CLIInterface
```

**Step 6: Commit**

```bash
git add tests/test_cli_interface.py src/game/cli_interface.py src/game/__init__.py
git commit -m "feat: add CLIInterface for terminal display"
```

---

### Task 3.2: Add CLIInterface render tests

**Files:**
- Modify: `tests/test_cli_interface.py`

**Step 1: Write the tests**

Add to `tests/test_cli_interface.py`:

```python
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
    assert "凶器" in output

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
```

**Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_cli_interface.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_cli_interface.py
git commit -m "test: add CLIInterface render tests"
```

---

### Task 3.3: Create play_main.py entry point

**Files:**
- Create: `play_main.py`

**Step 1: Create the entry point**

Create `play_main.py`:

```python
import json
import sys
from pathlib import Path
from src.models import GameWorld, PlayerState
from src.game.cli_interface import CLIInterface
from src.game.engine import GameEngine

def load_game_world(game_file: str) -> GameWorld:
    """加载游戏世界"""
    path = Path(game_file)
    if not path.exists():
        raise FileNotFoundError(f"Game file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return GameWorld(**data)

def main():
    if len(sys.argv) < 2:
        print("Usage: python play_main.py <game_world.json>")
        print("Example: python play_main.py stories/island/game_world.json")
        sys.exit(1)

    game_file = sys.argv[1]

    try:
        world = load_game_world(game_file)
    except Exception as e:
        print(f"Error loading game: {e}")
        sys.exit(1)

    # 初始化玩家状态
    initial_dimensions = {dim: None for dim in world.truth.keys()}
    state = PlayerState(
        current_scene_id=world.scenes[0].id if world.scenes else "",
        collected_clues=[],
        executed_actions=[],
        stamina=100,
        locked_dimensions=initial_dimensions
    )

    interface = CLIInterface(world, state)
    engine = interface.engine

    print("\n推理游戏开始！收集线索，找出真相。\n")

    while True:
        # 显示界面
        print(interface.render_full_display())

        # 接收输入
        try:
            choice = input().strip().lower()
        except EOFError:
            break

        # 查看证据
        if choice == "v":
            print(interface.render_evidence())
            input()
            continue

        # 选择行动
        try:
            action_index = int(choice) - 1
            actions = engine.get_available_actions()
            if action_index < 0 or action_index >= len(actions):
                print("无效的选择，请重新输入。")
                continue

            action = actions[action_index]
            success, message = engine.execute_action(action.id)

            print("\n" + "=" * 60)
            print(message)
            print("=" * 60 + "\n")

            # 检查胜利
            if engine.deduction_engine.check_victory():
                print(interface.render_victory())
                break

        except ValueError:
            print("请输入数字或 'v' 查看证据。")

if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add play_main.py
git commit -m "feat: add play_main.py entry point for playable game"
```

---

## Phase 4: World Generator (MVP)

### Task 4.1: Create WorldValidator

**Files:**
- Create: `src/modules/world_validator.py`
- Test: `tests/test_world_validator.py`

**Step 1: Write the failing test**

Create `tests/test_world_validator.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_world_validator.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `src/modules/world_validator.py`:

```python
from typing import Tuple, List
from ..models import GameWorld, ClueType

class WorldValidator:
    def validate(self, world: GameWorld) -> Tuple[bool, List[str]]:
        """验证游戏世界的逻辑链完备性"""
        errors = []

        # 1. 每个真相维度必须至少有一个key_clue
        truth_dimensions = set(world.truth.keys())
        covered_dimensions = set()

        for clue in world.clues:
            if clue.clue_type == ClueType.key_clue and clue.deduction_link:
                covered_dimensions.add(clue.deduction_link.truth_dimension)

        missing_dims = truth_dimensions - covered_dimensions
        for dim in missing_dims:
            errors.append(f"真相维度 '{dim}' 缺少对应的 key_clue")

        # 2. 所有key_clue的target_value必须匹配truth
        for clue in world.clues:
            if clue.clue_type == ClueType.key_clue and clue.deduction_link:
                dim = clue.deduction_link.truth_dimension
                expected = world.truth.get(dim)
                if expected != clue.deduction_link.target_value:
                    errors.append(f"线索 {clue.id} 的 target_value '{clue.deduction_link.target_value}' 与真相 '{expected}' 不匹配")

        return len(errors) == 0, errors
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_world_validator.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_world_validator.py src/modules/world_validator.py
git commit -m "feat: add WorldValidator for logic chain validation"
```

---

### Task 4.2: Create sample game world JSON for testing

**Files:**
- Create: `stories/sample/game_world.json`

**Step 1: Create sample game world**

Create `stories/sample/game_world.json`:

```json
{
  "truth": {
    "凶手": "管家",
    "凶器": "毒药"
  },
  "scenes": [
    {
      "id": "S1",
      "name": "书房",
      "description": "一间昏暗的书房，书架上摆满了古籍，桌上有一杯红酒。",
      "connected_scenes": ["S2"]
    },
    {
      "id": "S2",
      "name": "管家房间",
      "description": "管家的私人房间，整洁而简朴。",
      "connected_scenes": ["S1"]
    }
  ],
  "sources": [
    {
      "id": "ITEM1",
      "name": "红酒杯",
      "type": "item",
      "description": "桌上的半杯红酒，杯口有白色粉末残留。",
      "scene_id": "S1",
      "hidden_clues": ["CLUE_KEY_2"]
    },
    {
      "id": "ITEM2",
      "name": "管家手套",
      "type": "item",
      "description": "一副黑色手套，放在床头柜上。",
      "scene_id": "S2",
      "hidden_clues": ["CLUE_KEY_1"]
    }
  ],
  "clues": [
    {
      "id": "CLUE_KEY_2",
      "content": "红酒杯口有白色粉末，这是毒药的残留。",
      "clue_type": "key_clue",
      "deduction_link": {
        "truth_dimension": "凶器",
        "target_value": "毒药",
        "reasoning": "粉末残留说明毒药被放入酒中"
      },
      "unlock_condition": null
    },
    {
      "id": "CLUE_KEY_1",
      "content": "管家手套内侧有毒药残留。",
      "clue_type": "key_clue",
      "deduction_link": {
        "truth_dimension": "凶手",
        "target_value": "管家",
        "reasoning": "手套上有毒药说明管家接触过毒药"
      },
      "unlock_condition": null
    }
  ],
  "actions": [
    {
      "id": "A1",
      "name": "检查红酒杯",
      "action_type": "interact",
      "target_source_id": "ITEM1",
      "cost": {"stamina": 5},
      "unlock_condition": null
    },
    {
      "id": "A2",
      "name": "前往管家房间",
      "action_type": "move",
      "target_scene_id": "S2",
      "cost": {"stamina": 10},
      "unlock_condition": null
    },
    {
      "id": "A3",
      "name": "前往书房",
      "action_type": "move",
      "target_scene_id": "S1",
      "cost": {"stamina": 10},
      "unlock_condition": null
    },
    {
      "id": "A4",
      "name": "检查管家手套",
      "action_type": "interact",
      "target_source_id": "ITEM2",
      "cost": {"stamina": 5},
      "unlock_condition": null
    }
  ]
}
```

**Step 2: Commit**

```bash
git add stories/sample/game_world.json
git commit -m "feat: add sample game world for testing"
```

---

### Task 4.3: Manual integration test

**Step 1: Run the playable game with sample world**

Run: `python play_main.py stories/sample/game_world.json`

Expected output:
```
推理游戏开始！收集线索，找出真相。

============================================================
【书房】
一间昏暗的书房，书架上摆满了古籍，桌上有一杯红酒。
============================================================
【待推理】 凶手: ?
【待推理】 凶器: ?
体力: 100
============================================================
【可用行动】
1. 检查红酒杯
2. 前往管家房间
v. 查看已收集的证据
============================================================
请输入选择:
```

**Step 2: Test gameplay flow**

Input sequence:
1. `1` - 检查红酒杯 → 锁定凶器
2. `2` - 前往管家房间
3. `1` - 检查管家手套 → 锁定凶手
4. 胜利界面显示

**Step 3: Document test result**

If all steps work, proceed to commit.

---

## Summary

完成以上任务后，系统将具备：

1. **完整数据模型**：Scene, Source, Clue, GameAction, GameWorld, PlayerState
2. **游玩引擎**：ClueManager, DeductionEngine, GameEngine
3. **CLI界面**：CLIInterface
4. **入口程序**：play_main.py
5. **验证器**：WorldValidator
6. **测试数据**：sample game_world.json

后续可继续开发：
- GameWorldGenerator（逆向生成流程）
- 更丰富的CLI交互（如场景描述动态生成）
- 多种故事模板