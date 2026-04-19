# 第一阶段：基础框架 (PHASE 1: MVP)

## 1. 项目目标与核心理念

### 1.1 项目目标
构建一个自动化系统，将“故事输入”转化为“可推理的游戏设计”，并通过循环优化不断提升游戏质量。

系统核心能力：
- 自动生成推理游戏结构（规则、证据、行动）
- 自动验证游戏是否具备推理性
- 模拟玩家行为进行测试
- 基于评估结果迭代优化设计

### 1.2 推理游戏本质
推理游戏的核心结构：
世界真相（Ground Truth） → 证据（Evidence） → 玩家假设（Hypothesis） → 行动（Action） → 反馈（Feedback）

---

## 2. 系统整体架构

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

---

## 3. 项目目录结构与 I/O 规范

### 3.1 目录结构
```text
/
├── stories/                # 输入故事集
│   └── [story_name]/       # 具体故事文件夹
│       ├── story.txt       # 原始故事输入
│       └── runs/           # 运行结果保存（按运行实例划分）
│           └── [run_id]/   # 单次运行结果
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

### 3.2 I/O 规范
- **故事输入**：系统从 `stories/[story_name]/story.txt` 读取原始素材。
- **Prompt 加载**：所有发送给 LLM 的 Prompt 必须通过读取 `prompts/` 目录下的 `.txt` 文件获取。
- **结果持久化**：每次引擎运行必须在对应故事的 `runs/` 目录下创建新文件夹，保存所有产物。

---

## 4. 模块职责设计 (Module Design)

为了实现从故事到推理设计的转化，系统由以下核心模块组成：

### 4.1 Generator (生成器)
- **职责**：根据故事生成多个候选游戏设计。
- **设计原则**：输出必须结构化，且生成的 truth, evidence, actions, outcomes 之间必须具备明确的因果关系，并存在冲突 (risk vs reward)。

### 4.2 Validator (验证器)
- **职责**：过滤不具备推理价值的设计。
- **检查项**：
  - **决策冲突**：不同选择必须带来不同风险/收益。
  - **信息不完全**：玩家无法直接得出唯一答案。
  - **多解释证据**：同一证据不能只支持一个结论。

### 4.3 Simulator (模拟器)
- **职责**：模拟玩家的“假设-行动-反馈”推理过程。
- **关键点**：使用 LLM 扮演玩家，在信息不完全的状态下生成假设（Hypothesis）并选择行动。

### 4.4 Evaluator (评估器)
- **职责**：判断游戏是否“好玩且可推理”。
- **评分维度**：推理深度、不确定性、决策影响、信息增量等。

### 4.5 Selector (选择器)
- **职责**：从候选设计中选择最优方案。
- **策略**：基于评分排名，保留 Top-K 设计。

---

## 5. 核心规范定义 (Data & Interface)

### 5.1 数据结构设计 (Game Design Schema)
一个游戏设计（GameDesign）必须包含以下 JSON 结构的定义：
- **世界真相 (truth)**: `Dict[str, str]` (如：凶手、凶器、动机)
- **证据系统 (evidence)**: `List[EvidenceItem]` (id, content, possible_explanations, reveal_condition)
- **行动集合 (actions)**: `List[ActionItem]` (id, name, cost, pre_condition)
- **结果规则 (outcomes)**: `Dict[str, OutcomeEffect]` (description, state_delta, revealed_evidence_ids, probability)
- **初始状态 (initial_state)**: `Dict[str, Any]`

### 5.2 模块接口设计 (Module I/O)
- **Generator**: 
  - 输入: `story_prompt: str`, `target_complexity: int`
  - 输出: `List[GameDesign]`
- **Validator**: 
  - 输入: `design: GameDesign`
  - 输出: `validation_result: bool`, `errors: List[str]`
- **Simulator**: 
  - 输入: `design: GameDesign`, `strategy: str`
  - 输出: `SimulationLog` (包含 `steps`, `current_hypotheses`, `reasoning_trace`)
- **Evaluator**: 
  - 输入: `design: GameDesign`, `logs: List[SimulationLog]`
  - 输出: `EvaluationReport` (包含 `scores`, `total_score`, `justification`)

---

## 6. 工程化要求 (MVP 阶段强制)

### 5.1 可追溯性 (Traceability)
**目标：** 每一个生成结果、模拟行为和评分结论都必须有据可查。
- **生成溯源：** 记录生成的游戏元素对应的“故事片段”或“推理逻辑路径”。
- **模拟路径记录：** 模拟器在进行决策时，必须记录其 `reasoning_trace`。
- **评分依据：** 评估器必须附带具体的 `justification`。
- **日志持久化：** 全程记录在 `trace.log` 中。

### 5.2 可测试性 (Testability)
**目标：** 确保引擎各组件的逻辑正确且稳定。
- **组件单元测试：** 为各模块编写独立的单元测试。
- **设计回归测试：** 维护“金标准游戏设计集”。
- **Simulator 一致性：** 确保在相同策略和初始条件下决策逻辑可复现。

---

## 6. MVP 成功标准
- 规模：3 个地点、3–5 条证据、3 个行动。
- 目标：跑通完整 生成 → 模拟 → 评分 流程。
- 标准：生成的游戏需要推理而非猜测，行动具有真实影响，过程全可追溯。
