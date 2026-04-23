# 推理游戏生成系统 (v1)

基于逆向生成证据链的 LLM 推理游戏系统。从真相出发反向构建证据网络，确保玩家一定能推导出正确答案。

## 快速开始

### 安装依赖

```bash
cd v1
pip install -r requirements.txt
```

### 配置 API Key

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 ZHIPUAI_API_KEY
```

### 运行示例游戏

```bash
# 生成游戏世界
python generate.py returning_tide

# 运行生成的游戏
python play.py stories/returning_tide/runs/gen_<timestamp>/game_world.json
```

## 目录结构

```
v1/
├── generate.py              # 单次生成器入口
├── generate_progressive.py  # 渐进式生成器（分步骤，带日志）
├── play.py                  # 游戏入口（CLI 界面）
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量模板
│
├── prompts/                 # LLM 提示词模板
│   ├── game_world_generator.txt   # 单次生成模板
│   ├── story_enricher.txt         # 故事丰富化模板
│   ├── step1_truth.txt            # 渐进式：真相
│   ├── step2_scenes.txt           # 渐进式：场景
│   ├── step3_key_clues.txt        # 渐进式：关键线索
│   ├── step4_sources.txt          # 渐进式：来源（NPC/物品）
│   └── step5_actions.txt          # 渐进式：行动
│
├── src/
│   ├── models.py            # Pydantic 数据模型
│   ├── llm_client.py        # LLM 客户端（双模式 Retry）
│   ├── game/                # 游戏引擎
│   │   ├── engine.py        # 主引擎（协调 ClueManager + DeductionEngine）
│   │   ├── clue_manager.py  # 线索管理（解锁条件）
│   │   ├── deduction_engine.py  # 推理引擎（维度锁定）
│   │   └── cli_interface.py     # CLI 渲染（单页面刷新）
│   └── generators/          # 生成器模块
│       ├── enricher.py      # 故事丰富化
│       ├── progressive.py   # 渐进式生成
│       └── validator.py     # 世界验证器
│
├── stories/                 # 游戏故事库
│   └── <story_name>/
│       ├── story.txt        # 故事提示词
│       └── runs/            # 生成/游玩记录
│           ├── gen_<timestamp>/   # 生成记录
│           │   ├── logs/          # LLM 调用日志
│           │   ├── game_world.json
│           │   └── enriched_story.txt
│           └── play_<timestamp>/  # 游玩记录
│               ├── game_world.json
│               └── result.json
│
└── tests/                   # pytest 测试
```

## 使用方法

### 1. 生成游戏世界

有两种生成模式：

**单次生成** - 一次 LLM 调用生成完整世界：

```bash
python generate.py <story_name>           # 带故事丰富化
python generate.py <story_name> --skip-enrich  # 跳过丰富化
```

**渐进式生成** - 分 5 步生成，每步保存详细日志：

```bash
python generate_progressive.py <story_name>
```

生成步骤：
1. `truth` - 真相（凶手、手法、动机等）
2. `scenes` - 场景
3. `key_clues` - 关键线索（锁定真相维度）
4. `sources` - 来源（NPC、物品）
5. `actions` - 行动（移动、交互）

### 2. 运行游戏

```bash
python play.py stories/<story_name>/runs/<timestamp>/game_world.json
```

游戏流程：
- 输入**数字**选择对应行动（移动到其他场景 / 与 NPC/物品交互）
- 输入 `v` 查看已收集的线索详情
- 收集线索后自动锁定真相维度
- 锁定所有维度即可胜利

### 3. 创建新游戏

1. 创建故事目录和提示词：

```bash
mkdir -p stories/<新游戏名>
```

创建 `stories/<新游戏名>/story.txt`，内容格式：

```
# 故事标题

## 背景
故事背景描述...

## 事件
核心事件描述...

## 人物
- 人物1：描述...
- 人物2：描述...

## 真相
- 凶手：xxx
- 手法：xxx
- 动机：xxx
```

2. 运行生成器：

```bash
python generate.py <新游戏名>
```

3. 运行生成的游戏。

## 核心概念

### 逆向生成

传统推理游戏从线索推导真相，容易出现逻辑漏洞。本系统**从真相出发**反向生成证据链：

```
Truth (真相) → Key Clues (锁定证据) → Sources (来源) → Pre/Filler Clues (辅助线索)
```

确保每个真相维度都有对应的 key_clue，玩家一定能推导出正确答案。

### 维度锁定

真相被分解为多个维度（如 `culprit`, `method`, `motive`）。收集 key_clue 会自动锁定对应维度：

```python
# key_clue 结构示例
{
    "clue_id": "clue_1",
    "clue_type": "key_clue",
    "deduction_link": {
        "truth_dimension": "culprit",  # 锁定哪个维度
        "target_value": "张三"         # 锁定的值
    }
}
```

当所有维度被锁定时，游戏胜利。

### 线索解锁链

pre_clue 和 filler_clue 可以设置解锁条件，形成线索链：

```python
# pre_clue 示例：需要先收集其他线索才能发现
{
    "clue_type": "pre_clue",
    "unlock_condition": ["clue_1", "clue_2"]  # 需要先收集这些线索
}
```

### 双模式 Retry

LLM 调用失败时自动重试，支持两种模式：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `conversation` | 多轮对话，LLM 看到完整历史 | JSON/验证错误修正 |
| `single` | 单次调用，prompt 包含上次输出 | Validator 错误修正 |

默认使用 conversation 模式，修正更自然。

## 数据模型

核心模型定义在 `src/models.py`：

```python
class World:
    truth: dict              # 真相 {"culprit": "xxx", "method": "xxx", ...}
    scenes: List[Scene]      # 场景列表
    sources: List[Source]    # 来源列表（NPC/物品）
    clues: List[Clue]        # 线索列表
    actions: List[Action]    # 行动列表

class Clue:
    clue_type: str           # "key_clue" | "pre_clue" | "filler_clue"
    deduction_link: Optional[DeductionLink]  # 仅 key_clue 有
    unlock_condition: List[str]              # 解锁条件

class Action:
    action_type: str         # "move" | "interact"
    target_scene_id: Optional[str]    # move 目标
    target_source_id: Optional[str]   # interact 目标
```

## 测试

```bash
cd v1
python -m pytest tests/ -v
```

## 许可证

MIT