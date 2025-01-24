import aiohttp
from typing import Dict

from argo_workflow_runner.core.exec_node import ExecNode
from argo_workflow_runner.core.schema import (
    KnowledgeBaseConfig,
    ExecResponse,
)
from argo_workflow_runner.env_settings import settings

class KnowledgeBaseNode(ExecNode):
    def __init__(self, info, websocket):
        super().__init__(info, websocket)
        self.config_model = KnowledgeBaseConfig.model_validate(self.config)

    async def execute(self, state: Dict):
        await super().execute(state)

        user_id = state.get('__user_id', 'workflow_runner')
        query_info = state.get(self.config_model.inputs[0], None)
        if query_info is None:
            raise Exception(f'No available input: {self.config_model.inputs[0]}')

        async with aiohttp.ClientSession() as session:
            payload = {
                "knowledge_base_id": self.config_model.kb_name,
                "user_id": user_id,
                "q": query_info,
                "similarity": self.config_model.similarity,
                "top_k": self.config_model.cnt,
                "search_mode": self.config_model.search_type,
            }
            url = settings.KB_URL
            async with session.post(url, json=payload) as resp:
                resp.raise_for_status()
                resp_json = await resp.json()
                result = resp_json['data']
        
        state[self.id] = result

        await self.send_response(ExecResponse(
            type='app',
            node_id=self.id,
            node_type=self.type,
            data={
                'result': result,
            },
        ))
