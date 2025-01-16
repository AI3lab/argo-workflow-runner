import asyncio
import aiohttp
from typing import Dict

from argo_workflow_runner.core.exec_node import ExecNode
from argo_workflow_runner.core.schema import (
    CustomToolConfig,
    ExecResponse,
)

class CustomToolNode(ExecNode):
    def __init__(self, info, websocket):
        super().__init__(info, websocket)
        self.config_model = CustomToolConfig.model_validate(self.config)

    async def execute(self, state: Dict):
        await super().execute(state)

        param_obj = state.get(self.config_model.inputs[0], None)
        if param_obj is None:
            raise Exception(f'No available input: {self.config_model.inputs[0]}')

        async with aiohttp.ClientSession(
            headers=self.config_model.headers,
        ) as session:
            if self.config_model.method == 'GET':
                kwargs = {
                    'params': param_obj
                }
            else:
                kwargs = {
                    'json': param_obj
                }
            
            async with session.request(method=self.config_model.method, url=self.config_model.url, **kwargs) as resp:
                resp.raise_for_status()
                resp_text = await resp.text()

        state[self.id] = resp_text

        await self.send_response(ExecResponse(
            type='result',
            node_id=self.id,
            node_type=self.type,
            data={
                'result': resp_text,
            },
        ))
