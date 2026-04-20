import json
from enum import Enum
from typing import Dict, List, Optional, Type
from pydantic import BaseModel, Field


def get_model_schema_desc(model_class: Type[BaseModel]) -> str:
    """生成 JSON Schema 描述（用于 LLM 提示词）"""
    schema = model_class.model_json_schema(mode='validation')
    return json.dumps(schema, ensure_ascii=False, indent=2)


class Character(BaseModel):
    name: str = Field(..., description="角色名称")
    role: str = Field(..., description="角色身份")
    description: str = Field(..., description="角色外观和性格描述")
    relationship: str = Field(..., description="与死者/事件的关系")


class SceneDraft(BaseModel):
    name: str = Field(..., description="场景名称")
    description: str = Field(..., description="场景详细描述")


class EventDetail(BaseModel):
    what: str = Field(..., description="发生了什么事件")
    when: str = Field(..., description="事件发生时间")
    where: str = Field(..., description="事件发生地点")
    details: str = Field(..., description="事件细节描述")


class TruthDraft(BaseModel):
    culprit: str = Field(..., description="真相：谁做的")
    method: str = Field(..., description="真相：怎么做的")
    motive: str = Field(..., description="真相：为什么")


class EnrichedStory(BaseModel):
    title: str = Field(..., description="故事标题")
    background: str = Field(..., description="故事背景设定")
    characters: List[Character] = Field(default_factory=list, description="角色列表")
    scenes: List[SceneDraft] = Field(default_factory=list, description="场景列表")
    event: EventDetail = Field(..., description="事件详情")
    truth: TruthDraft = Field(..., description="真相")
    red_herrings: List[str] = Field(default_factory=list, description="误导性线索")
    atmosphere: str = Field(..., description="整体氛围")


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