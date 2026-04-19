# Reasoning Game Generator（推理游戏生成引擎）设计大纲

## 1. 项目目标

构建一个自动化系统，将“故事输入”转化为“可推理的游戏设计”，并通过循环优化不断提升游戏质量。

系统核心能力：
- 自动生成推理游戏结构（规则、证据、行动）
- 自动验证游戏是否具备推理性
- 模拟玩家行为进行测试
- 基于评估结果迭代优化设计

---

## 2. 核心理念

### 2.1 推理游戏本质
推理游戏的核心结构：

世界真相（Ground Truth）
→ 证据（Evidence）
→ 玩家假设（Hypothesis）
→ 行动（Action）
→ 反馈（Feedback）

### 2.2 系统核心思想
将“游戏设计”转化为一个可搜索空间：

生成 → 验证 → 模拟 → 评分 → 选择 → 再生成

### 2.3 分期规划 (Phased Implementation)
为了稳步推进项目，我们将其分为以下两个阶段进行：
- **[基础版 (Phase 1: Base Version)](PHASE_1_BASE.md)**: 实现单向流水线与文件 I/O。
- **[增强版 (Phase 2: Enhanced Version)](PHASE_2_ENHANCED.md)**: 实现闭环优化、贝叶斯模拟与可视化。

详细路线图请参阅 **[项目分期路线图 (ROADMAP.md)](ROADMAP.md)**。

---

## 3. 系统整体架构

Story Input
↓
GameDesignOptimizer
    ├── Generator（生成设计）
    ├── Validator（规则校验）
    ├── Simulator（玩家模拟）
    ├── Evaluator（评分）
    └── Selector（选择优化）
↓
Final Game Design

## 4. 项目目录结构与 I/O 规范

为了保证系统的可维护性和可追溯性，采用以下文件组织结构：

### 4.1 目录结构
```text
/
├── stories/                # 输入故事集
│   └── [story_name]/       # 具体故事文件夹
│       ├── story.txt       # 原始故事输入
│       └── runs/           # 运行结果保存（按运行实例划分）
│           └── [run_id]/   # 单次运行结果 (如 run_20240419_1000)
│               ├── design.json       # 最终生成的游戏设计
│               ├── simulations.json  # 模拟运行日志
│               ├── evaluation.json   # 评估报告
│               └── trace.log         # 全程追溯日志
├── prompts/                # Prompt 模板管理
│   ├── generator.txt       # 生成器 Prompt 模板
│   ├── simulator.txt       # 模拟器 Prompt 模板
│   └── evaluator.txt       # 评估器 Prompt 模板
├── src/                    # 引擎源代码
└── docs/                   # 设计文档
```

### 4.2 I/O 规范
- **故事输入**：系统从 `stories/[story_name]/story.txt` 读取原始素材。
- **Prompt 加载**：所有发送给 LLM 的 Prompt 必须通过读取 `prompts/` 目录下的 `.txt` 文件获取，严禁在代码中硬编码长 Prompt。
- **结果持久化**：每次引擎运行必须在对应故事的 `runs/` 目录下创建新文件夹，完整保存该次运行的所有中间产物和最终结论。

---

## 5. 数据结构设计（核心）

### 5.1 Game Design Schema (详细规范)

一个游戏设计（GameDesign）必须包含以下 JSON 结构的定义：

- **世界真相 (truth)**: `Dict[str, str]`
  - 示例: `{"killer": "NPC_A", "weapon": "Knife", "motive": "Money"}`
  - 每一个 Key 代表一个维度，Value 代表该维度的真实状态。

- **证据系统 (evidence)**: `List[EvidenceItem]`
  - `EvidenceItem`:
    - `id`: `str`
    - `content`: `str` (描述性文本)
    - `possible_explanations`: `List[Dict[str, str]]` (每条证据必须指向至少两个可能的真相片段，以产生干扰)
    - `reveal_condition`: `str` (触发该证据显示的条件，如：执行了某个 Action)

- **行动集合 (actions)**: `List[ActionItem]`
  - `ActionItem`:
    - `id`: `str`
    - `name`: `str`
    - `cost`: `Dict[str, int]` (如：消耗体力、时间)
    - `pre_condition`: `str` (执行前提)

- **结果规则 (outcomes)**: `Dict[str, OutcomeEffect]`
  - `OutcomeEffect`:
    - `description`: `str`
    - `state_delta`: `Dict[str, int]` (状态变化，如：`{"health": -10}`)
    - `revealed_evidence_ids`: `List[str]` (此行动揭露的证据 ID)
    - `probability`: `float` (成功的概率)

- **初始状态 (initial_state)**: `Dict[str, Any]`
  - 玩家生命值、金钱、所在位置等。

---

## 6. 模块接口设计 (I/O)

为了保证各模块的解耦，定义以下输入输出规范：

### 6.1 Generator (生成器)
- **输入**: `story_prompt: str`, `target_complexity: int`
- **输出**: `List[GameDesign]` (生成 N 个候选方案)

### 6.2 Validator (验证器)
- **输入**: `design: GameDesign`
- **输出**: `validation_result: bool`, `errors: List[str]`

### 6.3 Simulator (模拟器)
- **输入**: `design: GameDesign`, `strategy: str` (如 "Aggressive", "Cautious")
- **输出**: `SimulationLog`
  - `steps`: `List[SimulationStep]`
    - `step_index`: `int`
    - `current_hypotheses`: `Dict[str, float]` (对真相的各可能性的概率估计)
    - `chosen_action_id`: `str`
    - `reasoning_trace`: `str` (为什么选这个 Action)
    - `outcome_result`: `OutcomeEffect`

### 6.4 Evaluator (评估器)
- **输入**: `design: GameDesign`, `logs: List[SimulationLog]`
- **输出**: `EvaluationReport`
  - `scores`: `Dict[str, float]` (各项指标 0-1 评分)
  - `total_score`: `float` (加权总分)
  - `justification`: `str` (评分理由)

---

## 7. 系统工程化要求 (Traceability, Testability, Visualization)

为了保证引擎的可靠性、可迭代性和透明度，系统必须满足以下工程化要求：

### 7.1 可追溯性 (Traceability)
**目标：** 每一个生成结果、模拟行为和评分结论都必须有据库查。

- **生成溯源：** 每一个生成的游戏元素（truth, evidence, action）必须记录其对应的“故事片段”或“推理逻辑路径”。
- **模拟路径记录：** 模拟器在进行假设（Hypothesis）和行动选择（Action）时，必须记录其决策依据（Reasoning Trace），包括当前已知证据和假设的匹配度。
- **评分依据：** 评估器在给出各项指标评分时，必须附带具体的“扣分项”或“加分理由”（Justification），而非仅仅是数值。
- **版本化：** 所有生成的设计方案、评估结果和模拟日志都应带有唯一标识，并支持历史回溯。

### 7.2 可测试性 (Testability)
**目标：** 确保引擎各组件的逻辑正确且稳定，并支持快速迭代。

- **组件单元测试：** 为 Generator, Validator, Simulator, Evaluator 编写独立的单元测试，通过 Mock 数据验证其核心逻辑。
- **设计回归测试：** 维护一个“金标准游戏设计集”（Gold Standard Set），每次引擎更新后，必须通过该集合的验证和评分回归测试。
- **Validator 边界测试：** 使用已知的“错误设计案例”验证 Validator 的过滤能力，确保其能准确识别无冲突、无推理价值的设计。
- **Simulator 一致性：** 确保模拟器在相同策略和初始条件下，其决策逻辑是可复现的。

### 7.3 可视化 (Visualization)
**目标：** 直观展示游戏逻辑，辅助开发者调试和优化设计。

- **设计图谱可视化：** 将生成的 truth, evidence, actions 及其因果关系可视化为逻辑图（Logic Graph），帮助理解游戏结构。
- **模拟决策树：** 将模拟器的推理过程和行动序列可视化为决策树或时间轴，展示玩家如何在信息增量中修正假设。
- **评估雷达图：** 使用雷达图直观展示游戏设计在“推理深度”、“不确定性”、“决策影响”等多个维度的表现。
- **实时流程监控：** 在生成过程中，实时可视化当前流水线的进度（Generator -> Validator -> Simulator -> Evaluator -> Selector）。

---

## 8. 模块详细算法逻辑

### 8.1 Generator: 提示词与约束
- **Few-shot Prompting**: 提供 2-3 个高质量的设计案例作为示例。
- **Schema Enforcement**: 使用 LLM 的 JSON Mode 或 Pydantic Output Parser 强制输出格式。
- **Truth-Evidence 强绑定**: 要求 LLM 在生成 evidence 时，显式列出它对应的 truth 干扰项。

### 8.2 Simulator: 贝叶斯假设更新 (简版)
- **状态更新**: `P(Truth | Evidence) ∝ P(Evidence | Truth) * P(Truth)`。
- **行动选择**: 模拟器优先选择那些能最大程度降低 `P(Truth)` 分布熵（Entropy）的 Action。

### 8.3 Evaluator: 评分公式
- **推理深度 (D)**: 模拟器成功识别真相所需的平均步数。
- **不确定性 (U)**: `1 - max(P(Truth))` 的初始值，代表初始迷惑度。
- **总分**: `Score = w1*D + w2*U + w3*DecisionImpact + ...` (权重 w 可根据实验调整)。

---

## 9. Mutator（变异器，可选）

职责：
- 基于优秀设计生成新版本

变异方式：
- 增加/修改证据
- 调整风险概率
- 增加新行动
- 修改胜负条件

目标：
- 在已有基础上提升复杂度与推理深度

---

## 10. 优化循环（核心流程）

初始化：
- 从故事生成多个初始设计

循环过程：
1. 生成候选设计
2. 验证过滤
3. 模拟玩家行为
4. 评分评估
5. 选择最优设计
6. 基于最优设计生成新一轮

终止条件：
- 达到目标评分
- 达到最大迭代次数

---

## 11. 推理质量关键设计点

### 11.1 信息不完全
- 玩家无法直接得出答案

### 11.2 多解释证据
- 每条证据支持多个假设

### 11.3 风险与收益并存
- 每个选择都有代价

### 11.4 推理可被验证
- 行动结果能反向验证假设

### 11.5 推理可被修正
- 错误不会立即结束，而是提供新信息

---

## 12. 最小可行版本（MVP）

建议限制规模：

- 3 个地点
- 3–5 条证据
- 3 个行动
- 简单状态（生命 / 资源）

目标：
- 能跑完整生成 → 模拟 → 评分 → 优化流程

---

## 13. 扩展方向

### 13.1 多结局系统
- 不同策略导向不同结局

### 13.2 推理树结构
- 支持多路径并行探索

### 13.3 玩家模型多样化
- 激进型 / 保守型 / 随机型

### 13.4 长期记忆
- 系统记录优秀设计模式

### 13.5 可解释性增强
- 输出“为什么这是好设计”

---

## 14. 成功标准

系统生成的游戏应满足：

- 玩家需要推理，而非猜测
- 不存在唯一显而易见解
- 行动具有真实影响
- 玩家可以通过失败学习
- 游戏具有可重复体验

---

## 15. 本质总结

该系统本质是：

在“游戏规则空间”中，
搜索最具推理价值的世界结构

而不是简单生成内容。
