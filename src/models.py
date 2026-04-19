import json
from enum import Enum
from typing import Dict, List, Any, Optional, Type
from pydantic import BaseModel, Field

def get_model_schema_desc(model_class: Type[BaseModel]) -> str:
    """生成一个对 LLM 友好的字段说明 JSON"""
    schema = model_class.model_json_schema()
    defs = schema.get("$defs", {})
    
    def resolve_type(prop, path=""):
        if "anyOf" in prop:
            types = [resolve_type(t, path) for t in prop["anyOf"] if t.get("type") != "null"]
            return " | ".join(types)
        if "allOf" in prop or "$ref" in prop:
            ref = prop.get("$ref") or prop.get("allOf")[0].get("$ref")
            ref_name = ref.split("/")[-1]
            ref_model = defs.get(ref_name, {})
            return {k: resolve_type(v, f"{path}.{k}") for k, v in ref_model.get("properties", {}).items()}
        if prop.get("type") == "array":
            return [resolve_type(prop.get("items", {}), f"{path}[]")]
        if prop.get("type") == "object":
            if "additionalProperties" in prop:
                # 处理 Dict[str, Type]
                inner_type = resolve_type(prop["additionalProperties"], f"{path}.<Key>")
                # 特殊处理：如果是 Dict[str, Dict]，给出更明确的 Key 示例
                key_name = "DimensionKey" if "current_hypotheses" in path else "ID"
                return {f"<{key_name}>": inner_type}
            return "Dict/Object"
        
        desc = prop.get("description", "")
        type_name = prop.get("type", "any")
        return f"{type_name}, {desc}"

    result = {k: resolve_type(v, k) for k, v in schema.get("properties", {}).items()}
    return json.dumps(result, ensure_ascii=False, indent=2)

class EnrichedStory(BaseModel):
    title: str = Field(..., description="故事标题")
    content: str = Field(..., description="丰富化后的完整故事内容")
    richness_score: float = Field(..., description="故事丰富度评分 0-1")
    key_elements: List[str] = Field(default_factory=list, description="故事核心要素/伏笔")

class Scene(BaseModel):
    id: str = Field(..., description="场景唯一标识符")
    name: str = Field(..., description="场景名称")
    description: str = Field(..., description="场景描述")
    connected_scenes: List[str] = Field(default_factory=list, description="可移动到的其他场景ID列表")

class SourceType(Enum):
    npc = "npc"
    item = "item"

class ClueType(Enum):
    key_clue = "key_clue"
    pre_clue = "pre_clue"
    filler_clue = "filler_clue"

class ActionType(Enum):
    move = "move"
    interact = "interact"

class DeductionLink(BaseModel):
    truth_dimension: str = Field(..., description="指向的真相维度")
    target_value: str = Field(..., description="锁定的值")
    reasoning: str = Field(..., description="推理逻辑说明")

class UnlockCondition(BaseModel):
    required_clues: List[str] = Field(default_factory=list, description="需要先获得的线索ID列表")
    reason: str = Field("", description="解锁条件的原因")

class Source(BaseModel):
    id: str = Field(..., description="来源唯一标识符")
    name: str = Field(..., description="NPC或物品名称")
    type: SourceType = Field(..., description="来源类型：npc或item")
    description: str = Field(..., description="描述")
    scene_id: str = Field(..., description="所属场景ID")
    hidden_clues: List[str] = Field(default_factory=list, description="隐藏的线索ID列表")

class Clue(BaseModel):
    id: str = Field(..., description="线索唯一标识符")
    content: str = Field(..., description="线索内容")
    clue_type: ClueType = Field(..., description="线索类型")
    deduction_link: Optional[DeductionLink] = Field(None, description="推理链接（仅key_clue有）")
    unlock_condition: Optional[UnlockCondition] = Field(None, description="解锁条件")

class GameAction(BaseModel):
    id: str = Field(..., description="行动唯一标识符")
    name: str = Field(..., description="行动名称")
    action_type: ActionType = Field(..., description="行动类型")
    target_source_id: Optional[str] = Field(None, description="交互目标来源ID（interact类型）")
    target_scene_id: Optional[str] = Field(None, description="目标场景ID（move类型）")
    cost: Dict[str, int] = Field(default_factory=dict, description="行动代价")
    unlock_condition: Optional[UnlockCondition] = Field(None, description="解锁条件")

class GameWorld(BaseModel):
    truth: Dict[str, str] = Field(..., description="真相字典")
    scenes: List[Scene] = Field(default_factory=list, description="场景列表")
    sources: List[Source] = Field(default_factory=list, description="来源列表（NPC/物品）")
    clues: List[Clue] = Field(default_factory=list, description="线索列表")
    actions: List[GameAction] = Field(default_factory=list, description="行动列表")

class ExplanationItem(BaseModel):
    truth_dim: str = Field(..., description="对应真相中的维度Key")
    truth_val: str = Field(..., description="该维度下的某个可能取值")
    reason: str = Field(..., description="为什么这个真相能解释这条证据")

class EvidenceItem(BaseModel):
    id: str = Field(..., description="唯一标识符，如 E1, E2")
    content: str = Field(..., description="证据的具体描述文字")
    possible_explanations: List[ExplanationItem] = Field(..., description="该证据可能的解释，必须包含至少两个不同的真相推导")
    reveal_condition: Optional[str] = Field(None, description="触发该证据显示的条件或行动ID")

class ActionItem(BaseModel):
    id: str = Field(..., description="唯一标识符，如 A1, A2")
    name: str = Field(..., description="行动的名称，如 '检查书架'")
    cost: Dict[str, int] = Field(default_factory=dict, description="执行该行动的代价，如 {'stamina': 10}")
    pre_condition: Optional[str] = Field(None, description="执行该行动的前提条件描述")

class OutcomeEffect(BaseModel):
    description: str = Field("", description="行动执行后的结果描述")
    state_delta: Dict[str, int] = Field(default_factory=dict, description="状态变化，如 {'health': -5}")
    revealed_evidence_ids: List[str] = Field(default_factory=list, description="该行动揭露的证据ID列表")
    probability: float = Field(1.0, description="该结果发生的概率 0-1，同一行动下的所有概率和应为1")

class GameDesign(BaseModel):
    truth: Dict[str, str] = Field(..., description="世界真相字典，必须是唯一的最终答案。Key是维度，Value是真相。例如: {'murderer': 'Butler'}")
    evidence: List[EvidenceItem] = Field(..., description="证据系统")
    actions: List[ActionItem] = Field(..., description="可选行动列表")
    outcomes: Dict[str, List[OutcomeEffect]] = Field(..., description="行动结果映射。Key是Action ID，Value是该行动可能导致的后果列表(支持多概率结果)")
    initial_state: Dict[str, Any] = Field(default_factory=dict, description="游戏的初始状态字典")

class SimulationStep(BaseModel):
    step_index: int
    current_hypotheses: Dict[str, Dict[str, float]] = Field(..., description="对真相各维度可能性的概率估计")
    chosen_action_id: Optional[str] = None
    reasoning_trace: str = Field(..., description="为什么选择这个行动")
    outcome_result: Optional[OutcomeEffect] = None

class SimulationLog(BaseModel):
    steps: List[SimulationStep] = Field(default_factory=list)

class EvaluationReport(BaseModel):
    scores: Dict[str, float] = Field(..., description="各项指标 0-1 评分")
    total_score: float
    justification: str = Field(..., description="评分理由")

# --- LLM 响应专用模型 (用于 Schema 注入) ---

class GeneratorResponse(BaseModel):
    designs: List[GameDesign] = Field(..., description="生成的推理游戏设计列表")

class SimulatorResponse(BaseModel):
    current_hypotheses: Dict[str, Dict[str, float]] = Field(..., description="真相维度到取值及其概率的映射。例如: {'murderer': {'Butler': 0.7, 'Maid': 0.3}}")
    chosen_action_id: str = Field(..., description="选择执行的行动ID")
    reasoning_trace: str = Field(..., description="详细的逻辑推理过程")

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
