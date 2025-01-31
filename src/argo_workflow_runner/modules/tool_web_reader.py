import aiohttp
from typing import Dict

from argo_workflow_runner.core.exec_node import ExecNode
from argo_workflow_runner.core.schema  import (
    ToolConfig,
    ExecResponse,
)
from argo_workflow_runner.configs import logger

class ToolWebReaderNode(ExecNode):
    def __init__(self, info, websocket):
        super().__init__(info, websocket)
        self.config_model = ToolConfig.model_validate(self.config)

    async def execute(self, state: Dict):
        await super().execute(state)

        url = state.get(self.config_model.inputs[0], None)
        if url is None:
            raise Exception(f'No available input: {self.config_model.inputs[0]}')

        result = ''
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()

                result = await resp.text()

        state[self.id] = result

        await self.send_response(ExecResponse(
            type='result',
            node_id=self.id,
            node_type=self.type,
            data={
                'result': result,
            },
        ))
