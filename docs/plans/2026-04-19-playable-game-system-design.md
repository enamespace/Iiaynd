# 推理游戏系统设计文档

## 概述

将现有"推理游戏生成器"重构为"可玩的推理游戏系统"。核心理念：**逆向生成证据链**，保证玩家一定能从线索中推导出真相。

## 设计理念

### 问题：正向生成的逻辑断裂

现有系统：LLM正向生成 Evidence/Actions → 无法保证证据能推导出真相。

### 解决方案：逆向生成

```
Truth（真相）
    ↓
KeyClues（关键线索，直接锁定真相维度）
    ↓
PreClues（前置线索，解锁KeyClue的条件）
    ↓
Sources（线索载体：NPC/物品）
    ↓
Scenes（场景布局）
    ↓
Actions（获取线索的路径）
    ↓
ContentFiller（正向填充：氛围、对话风格）
```

---

## 数据模型

### Truth（真相）- 保持原有

```json
{"凶手": "管家", "凶器": "毒药"}
```

### Scene（场景）- 新增

```json
{
  "id": "S1",
  "name": "书房",
  "description": "一间昏暗的书房...",
  "connected_scenes": ["S2", "S3"]
}
```

### Source（来源）- 新增

线索载体，NPC或物品：

```json
{
  "id": "NPC1",
  "name": "管家",
  "type": "npc",
  "description": "一位穿着整洁西装的中年男子...",
  "scene_id": "S2",
  "hidden_clues": ["CLUE_KEY_1"]
}
```

### Clue（线索）- 新增

```json
{
  "id": "CLUE_KEY_1",
  "content": "管家手套内侧有毒药残留",
  "clue_type": "key_clue",
  "deduction_link": {
    "truth_dimension": "凶手",
    "target_value": "管家",
    "reasoning": "手套上有毒药说明管家接触过毒药"
  },
  "unlock_condition": null
}
```

**clue_type 类型：**
- `key_clue`：直接锁定真相维度
- `pre_clue`：解锁其他线索的前置条件
- `filler_clue`：填充内容，无推理价值

**unlock_condition 示例：**

```json
{
  "required_clues": ["CLUE_KEY_2"],
  "reason": "需要先发现红酒有毒"
}
```

### Action（行动）- 扩展

```json
{
  "id": "A1",
  "name": "检查红酒杯",
  "action_type": "interact",
  "target_source_id": "ITEM1",
  "cost": {"stamina": 5},
  "unlock_condition": null
}
```

**action_type 类型：**
- `move`：移动到其他场景
- `interact`：与NPC/物品交互
- `deduce`：提出推理（废弃，改为自动锁定）

### GameWorld（顶层模型）- 新增

整合所有游戏元素：
- `truth`: Dict[str, str]
- `scenes`: List[Scene]
- `sources`: List[Source]
- `clues`: List[Clue]
- `actions`: List[Action]

### PlayerState（玩家状态）- 新增

```python
{
  "current_scene_id": "S1",
  "collected_clues": ["CLUE_KEY_2"],
  "executed_actions": ["A1"],
  "stamina": 100,
  "locked_dimensions": {
    "凶手": null,
    "凶器": "毒药"
  }
}
```

---

## 生成流程

### 步骤

1. **确定 Truth**：手动指定或LLM生成
2. **生成 KeyClues**：为每个真相维度生成关键线索
3. **生成 PreClues**：为KeyClue生成前置条件
4. **分配 Sources**：将Clue分配到NPC/物品
5. **构建 Scenes**：场景布局，分配Source到场景
6. **生成 Actions**：移动行动 +交互行动
7. **填充内容**：FillerClues、NPC性格、场景氛围描述

### 模块划分

| 模块 | 职责 |
|------|------|
| TruthGenerator | 生成真相 |
| ClueChainGenerator | 逆向生成证据链 |
| SourceAllocator | Clue → NPC/物品 |
| SceneBuilder | 构建场景 |
| ActionGenerator | 生成行动 |
| ContentFiller | 正向填充内容 |
| WorldValidator | 验证逻辑链完备性 |

---

## 游玩流程

### 游戏循环

```
显示场景描述
    ↓
显示可用行动
    ↓
接收玩家输入（数字编号 / v查看证据）
    ↓
执行行动
    - 移动：切换场景
    - 交互：揭示线索（检查解锁条件）
    ↓
检查维度锁定（KeyClue自动锁定真相维度）
    ↓
检查胜利条件（所有维度锁定 →胜利）
    ↓
返回循环
```

### 线索揭示逻辑

```
玩家选择交互行动
    ↓
查找目标Source的hidden_clues
    ↓
检查每个Clue的unlock_condition
    - 已满足：揭示线索
    - 未满足：提示需要前置线索
    ↓
揭示KeyClue →自动锁定对应真相维度
```

### 维度锁定机制

- 每条 KeyClue 的 `deduction_link` 指定锁定的真相维度和值
- 获得 KeyClue → 自动更新 `PlayerState.locked_dimensions`
- 所有维度锁定 → 游戏胜利

---

## CLI界面

### 主界面

```
═══════════════════════════════════════════════════════════
【书房】
一间昏暗的书房...
═══════════════════════════════════════════════════════════
【已锁定】 凶器: 毒药 ✓
【待推理】 凶手: ?
体力: 95
═══════════════════════════════════════════════════════════
【可用行动】
1. 前往客厅
2. 前往管家房间
3. 检查红酒杯
v. 查看已收集的证据
═══════════════════════════════════════════════════════════
请输入选择: _
```

### 查看证据界面（输入 v）

显示所有已收集线索及其推理逻辑。

### 胜利界面

显示真相 + 推理路径复盘。

---

## 整体架构

### 两阶段

**Phase 1: 生成阶段**
- `generate_main.py` 入口
- `GameWorldGenerator` 生成 `game_world.json`
- `WorldValidator` 验证完备性

**Phase 2: 游玩阶段**
- `play_main.py` 入口
- `GameEngine` 主引擎
- `PlayerState` 状态管理
- `ClueManager` 线索揭示
- `DeductionEngine` 推理锁定
- `CLIInterface` 终端交互

### 文件结构

```
src/
├── models.py              # 数据模型
├── llm_client.py          # LLM客户端
├── modules/               # 生成阶段
│   ├── game_world_generator.py
│   ├── world_validator.py
├── game/                  # 游玩阶段
│   ├── engine.py
│   ├── player_state.py
│   ├── clue_manager.py
│   ├── deduction_engine.py
│   └── cli_interface.py

generate_main.py           # 生成入口
play_main.py               # 游玩入口
```

---

## 实现路线

| 阶段 | 内容 |
|------|------|
| Phase 1 | 数据模型重构 |
| Phase 2 | 生成阶段实现 |
| Phase 3 | 游玩阶段实现 |
| Phase 4 | 集成测试 |

---

## 现有代码处理

| 模块 | 处理 |
|------|------|
| models.py | 扩展 |
| runner.py | 废弃 |
| modules/generator.py | 重构 |
| modules/simulator.py | 废弃 |
| modules/evaluator.py | 废弃 |
| modules/validator.py | 重构为 WorldValidator |
| main.py | 替换为 generate_main.py / play_main.py |