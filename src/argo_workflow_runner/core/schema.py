from pydantic import BaseModel, Field
from typing import Literal, Dict, Optional, List, Any

class RspUpload(BaseModel):
    name: str = Field(description='Uploaded file name')

class CommonModule(BaseModel):
    inputs: List[str]

class StartNodeConfig(BaseModel):
    text: Optional[str] = None
    file: Optional[str] = None
    file_transfer_type: Optional[Literal['upload', 'url']] = 'url'

class LogicBranchCondition(BaseModel):
    cond_param: str
    compare_type: Literal['include', 'not_include', 'equal', 'not_equal', 'empty', 'not_empty', 'start_with', 'end_with']
    cond_val: Optional[str] = None
    logic_relation: Optional[Literal['and', 'or']] = 'and'

class LogicBranch(BaseModel):
    name: str
    conditions: List[LogicBranchCondition]

class LogicBranchesConfig(BaseModel):
    branches: List[LogicBranch]

class IntentionBranch(BaseModel):
    title: str
    instruction: str

class IntentionConfig(CommonModule):
    model: str
    memory_cnt: Optional[int] = 0
    branches: List[IntentionBranch]

class ToolConfig(CommonModule):
    name: str



class CustomToolConfig(ToolConfig):
    url: str
    method: str
    headers: Dict[str, str]

class TTSConfig(ToolConfig):
    voice: str

class SpAppConfig(CommonModule):
    name: str
    memory_cnt: Optional[int] = 0

class LLMConfig(CommonModule):
    prompt: str
    prompt_params: List[str]
    temperature: float = 0.0
    model: str
    memory_cnt: Optional[int] = 0

class AgentConfig(CommonModule):
    name: str
    agent_id: str = None

class CodeBlockConfig(BaseModel):
    args: Dict[str, str]
    code: str

class KnowledgeBaseConfig(CommonModule):
    kb_name: str
    search_type: Literal['vector', 'enhance'] = 'vector'
    similarity: float = 0.75
    cnt: int = 3

class EdgeConfig(BaseModel):
    from_node_id: Optional[str] = None
    from_branch_id: Optional[int] = None
    to_node_id: Optional[str] = None

class ExecResponse(BaseModel):
    type: Literal['enter', 'result', 'error', 'text', 'json', 'images', 'billing', 'app']
    node_id: Optional[str] = None
    node_type: Optional[str] = None
    data: Optional[Dict] = None
