# 第二阶段：核心算法与推理逻辑 (PHASE 2: LOGIC & ALGORITHMS)

## 1. 模块算法逻辑

### 1.1 Generator: 提示词工程与结构约束
- **Few-shot Prompting**: 在 `generator.txt` 模板中提供 2-3 个高质量推理游戏设计案例，引导 LLM 理解因果链。
- **Schema Enforcement**: 结合 Pydantic 模型，利用 LLM 的 JSON Mode 或输出解析器强制生成结构化数据。
- **Truth-Evidence 强绑定**: 在 Prompt 中明确要求每条证据必须在生成的逻辑中至少支撑两个不同的假设维度。

### 1.2 Validator: 静态校验与逻辑过滤
- **结构连通性检查**: 确保所有 `evidence` 都有对应的 `action` 可以触发，所有 `outcome` 都指向存在的 `state` 变化。
- **信息不完全性验证**: 检查是否可以通过初始信息直接推导出唯一的 `truth`。如果可以，该设计将被判定为“非推理”而过滤。
- **证据歧义性校验**: 遍历 `evidence.possible_explanations`，确保每条证据对应的解释集合大小 $\ge 2$，且这些解释之间存在逻辑互斥。
- **决策价值评估**: 如果所有 `action` 的 `outcome` 在 `state_delta` 和 `revealed_evidence_ids` 上完全一致，说明玩家无论选什么都一样，该设计将被视为“无效设计”。

### 1.3 Simulator: 决策逻辑
- **贝叶斯更新 (推荐方案)**: 
  - 模拟器维护一个对真相的概率分布 `P(Truth)`。
  - 获得证据后，根据 `P(Truth | Evidence) ∝ P(Evidence | Truth) * P(Truth)` 进行更新。
- **信息熵最小化**: 
  - 模拟器评估每个 Action 的预期信息增量。
  - 优先选择能最大程度降低假设分布熵（Entropy）的 Action，模拟“寻找真相”的直觉。

### 1.4 Evaluator: 评分公式
- **推理深度 (D)**: 模拟器识别出真相所需的平均步数。步数过少（一眼看出）或过长（纯靠运气）得分较低。
- **迷惑度 (Confusion Index)**: 初始状态下各真相分支的概率分布均匀程度。
- **决策影响 (Decision Impact)**: 关键行动对最终胜负概率的影响显著度。
- **综合评分**: `Score = w1*D + w2*C + w3*Impact`。

---

## 2. 推理质量控制点

### 2.1 信息的非对称性
- 确保 Simulator 无法直接访问 `truth`，只能通过执行 `action` 获得 `evidence`。

### 2.2 证据的多义性
- 每一条证据在逻辑上必须能被解释为至少两种 `truth` 的产物。

### 2.3 因果的严密性
- `action` 触发 `outcome` 的逻辑必须在 `story.txt` 的背景框架内自洽。
