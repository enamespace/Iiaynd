# v1 - 可玩推理游戏系统

基于逆向生成证据链的推理游戏系统。

## 目录结构

```
v1/
├── generate_main.py      # 生成器入口
├── play_main.py          # 游戏入口（单页面刷新）
├── prompts/
│   └── game_world_generator.txt  # LLM 提示词模板
├── src/
│   ├── models.py         # 数据模型
│   ├── llm_client.py     # LLM 客户端
│   ├── game/
│   │   ├── engine.py     # 游戏引擎
│   │   ├── clue_manager.py
│   │   ├── deduction_engine.py
│   │   └── cli_interface.py
│   └── modules/
│       └── world_validator.py  # 验证器
├── stories/
│   └── sample/           # 样例游戏
└── tests/                # 测试文件
```

## 使用方法

### 1. 生成游戏世界

```bash
python generate_main.py <story_name>

# 结果保存到: stories/<story_name>/runs/<timestamp>/game_world.json
```

### 2. 运行游戏

```bash
python play_main.py stories/<story_name>/runs/<timestamp>/game_world.json
```

### 3. 创建新游戏

1. 创建 `stories/<新游戏>/story.txt`，写入故事提示词
2. 运行 `python generate_main.py <新游戏>`
3. 运行生成的 JSON 文件开始游戏

## 核心概念

- **逆向生成**：从真相出发生成证据链，确保玩家一定能推导出真相
- **维度锁定**：收集 key_clue 自动锁定真相维度
- **单页面 CLI**：每次行动后清屏刷新，保持界面整洁

## 测试

```bash
python -m pytest tests/ -v
```