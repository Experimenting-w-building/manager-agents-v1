# Models for state management
from enum import Enum
import operator
from typing import Annotated, List, Optional, Set, TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage


class AgentType(str, Enum):
    ELIZAOS = "elizaos"
    TRON = "tron"
    GOOSE = "goose"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentTask(BaseModel):
    agent_type: AgentType
    query: str
    status: TaskStatus = TaskStatus.PENDING
    response: Optional[str] = None
    error: Optional[str] = None

class ManagerState(TypedDict):
    original_query: str  # This is set once and never updated
    tasks: List[AgentTask]
    required_agents: Set[AgentType]
    current_agent: Optional[AgentType]
    messages: Annotated[List[BaseMessage], operator.add] # Use append semantics for messages
    final_output: Annotated[str, operator.add] = "" 

# Agent necessity determination schema
class RequiredAgent(BaseModel):
    agent_type: AgentType = Field(description="The type of specialized agent")
    needed: bool = Field(description="Whether this agent is needed to answer the query")
    reason: str = Field(description="Reason why this agent is needed or not needed")

class AgentRequirements(BaseModel):
    agents: List[RequiredAgent] = Field(description="List of agents and whether they're needed")