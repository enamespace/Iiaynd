# Iiaynd - LLM 推理游戏生成系统

基于大语言模型的推理游戏自动生成与运行系统。从真相出发逆向构建证据链，确保逻辑严密、玩家一定能推导出正确答案。

## 项目结构

```
Iiaynd/
├── v1/                      # 当前版本
│   ├── generate.py          # 游戏世界生成器
│   ├── generate_progressive.py  # 渐进式生成器（分步骤）
│   ├── play.py              # 游戏运行入口
│   ├── src/                 # 核心代码
│   │   ├── models.py        # 数据模型
│   │   ├── llm_client.py    # LLM 客户端（双模式 Retry）
│   │   ├── game/            # 游戏引擎
│   │   └── generators/      # 生成器模块
│   ├── prompts/             # LLM 提示词模板
│   ├── stories/             # 游戏故事库
│   └── tests/               # 测试文件
│   └── README.md            # 详细文档
└── docs/                    # 设计文档
```

## 快速开始

```bash
cd v1
pip install -r requirements.txt

# 配置 API Key
cp .env.example .env
# 编辑 .env，填入 ZHIPUAI_API_KEY

# 生成并运行示例游戏
python generate.py returning_tide
python play.py stories/returning_tide/runs/gen_<timestamp>/game_world.json
# 游戏中输入数字选择行动，输入 v 查看线索
```

## 核心特性

- **逆向生成**：从真相出发反向构建证据链，避免逻辑漏洞
- **维度锁定**：收集关键线索自动锁定真相维度
- **线索解锁链**：支持前置线索解锁机制
- **双模式 Retry**：LLM 调用失败时智能重试（多轮对话 / 单次调用）
- **CLI 游戏界面**：单页面刷新，简洁易用

## 详细文档

参见 [v1/README.md](v1/README.md)

## 许可证

MIT