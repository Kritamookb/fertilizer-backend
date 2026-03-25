from typing import Literal


AGENT_TYPE_GENERAL = "general"
AGENT_TYPE_SUB_CENTER = "sub_center"

AgentType = Literal["general", "sub_center"]

AGENT_TYPE_UNIT_PRICES: dict[AgentType, int] = {
    AGENT_TYPE_GENERAL: 800,
    AGENT_TYPE_SUB_CENTER: 770,
}


def is_valid_agent_type(agent_type: str) -> bool:
    return agent_type in AGENT_TYPE_UNIT_PRICES


def get_agent_unit_price(agent_type: AgentType) -> int:
    return AGENT_TYPE_UNIT_PRICES[agent_type]
