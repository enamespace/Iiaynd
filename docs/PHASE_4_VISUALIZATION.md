# 第四阶段：可视化与界面展示 (PHASE 4: VISUALIZATION)

## 1. 可视化目标
直观展示游戏逻辑，辅助开发者调试和优化设计，并向用户展示生成成果。

---

## 2. 核心功能规划

### 2.1 游戏逻辑图谱 (Logic Graph)
- **目标**: 展示 truth -> evidence -> action 的因果链。
- **技术实现**: 使用 `NetworkX` 生成图结构，并利用 `Matplotlib` 或导出为 `Mermaid` 格式。
- **展示内容**: 
  - 核心 Truth 的维度。
  - 每个 Evidence 指向的 Truth 集合。
  - Action 触发的 Outcome 与 Evidence 揭示路径。

### 2.2 模拟过程可视化 (Simulation Flow)
- **目标**: 展示模拟器如何逐步修正假设。
- **展示方式**:
  - **概率热力图**: 展示各真相选项在不同 Step 的 `P(Truth)` 变化。
  - **决策树/时间轴**: 展示模拟器执行的行动序列及其背后的 `reasoning_trace`。

### 2.3 评估雷达图 (Evaluation Radar)
- **目标**: 综合评价一个设计的优劣。
- **技术实现**: 使用 `Plotly` 或 `Matplotlib`。
- **维度**: 推理深度、决策影响、信息增量、非平凡性等。

### 2.4 实时流程监控
- **目标**: 监控 `Generator -> Validator -> Simulator -> Evaluator -> Selector` 的流水线状态。
- **展示方式**: 终端控制台进度条 (如使用 `rich` 库)。

---

## 3. 验收标准
1. 开发者能通过逻辑图快速识别出孤立节点或逻辑断点。
2. 模拟器的“学习过程”（假设修正）能直观展现。
3. 多个候选设计的优劣能通过雷达图一目了然。
