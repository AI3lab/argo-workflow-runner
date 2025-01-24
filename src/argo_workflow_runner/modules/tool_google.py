from typing import Dict

from argo_workflow_runner.core.exec_node import ExecNode
from argo_workflow_runner.core.schema  import (
    ToolConfig,
    ExecResponse,
)
from argo_workflow_runner.utils.web_search import serp_api_search

class ToolGoogleNode(ExecNode):
    def __init__(self, info, websocket):
        super().__init__(info, websocket)
        self.config_model = ToolConfig.model_validate(self.config)

    async def execute(self, state: Dict):
        await super().execute(state)

        query_info = state.get(self.config_model.inputs[0], None)
        if query_info is None:
            raise Exception(f'No available input: {self.config_model.inputs[0]}')

        result = await serp_api_search(query_info)

        state[self.id] = result

        await self.send_response(ExecResponse(
            type='result',
            node_id=self.id,
            node_type=self.type,
            data={
                'result': result,
            },
        ))
