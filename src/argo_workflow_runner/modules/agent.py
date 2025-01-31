from typing import Dict

from argo_workflow_runner.core.exec_node import ExecNode
from argo_workflow_runner.core.schema  import (
    AgentConfig,
    ExecResponse,
)
from argo_workflow_runner.configs import logger
from argo_workflow_runner.configs import logger

class AgentNode(ExecNode):
    def __init__(self, info, websocket):
        super().__init__(info, websocket)
        self.config_model = AgentConfig.model_validate(self.config)

    async def execute(self, state: Dict):
        await super().execute(state)
        param_obj = state.get(self.config_model.inputs[0], None)
        if param_obj is None:
            raise Exception(f'No available input: {self.config_model.inputs[0]}')
        params = {}
        for key in self.config_model.inputs:
            val = state.get(key, None)
            if val is not None:
                params[key] = val

        async with aiohttp.ClientSession(
                headers=self.config_model.headers,
        ) as session:

            kwargs = {
                'text': param_obj,
            }

            async with session.request(method="POST", url=self.config_model.url, **kwargs) as resp:
                resp.raise_for_status()
                resp_text = await resp.text()
        logger.info(resp_text)

        state[self.id] = resp_text

        await self.send_response(ExecResponse(
            type='result',
            node_id=self.id,
            node_type=self.type,
            data={
                'result': resp_text,
            },
        ))

