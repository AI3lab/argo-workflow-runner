import asyncio
import aiohttp
from typing import Dict

from argo_workflow_runner.core.exec_node import ExecNode
from argo_workflow_runner.core.schema import (
    CustomToolConfig,
    ExecResponse,
)
from argo_workflow_runner.env_settings import settings
from argo_workflow_runner.configs import logger

class CustomToolNode(ExecNode):
    def __init__(self, info, websocket):
        super().__init__(info, websocket)
        self.config_model = CustomToolConfig.model_validate(self.config)

    async def execute(self, state: Dict):
        await super().execute(state)

        text = state.get(self.config_model.inputs[0], None)
        if text is None:
            raise Exception(f'human words should not be empty for {self.id}, {self.type}')


        # param_obj = state.get(self.config_model.inputs[0], None)
        # if param_obj is None:
        #     raise Exception(f'No available input: {self.config_model.inputs[0]}')
        # fields = self.config_model.fields
        #
        # param_obj = {}
        # for field in fields:
        #     param_obj[field] = await param_obj.get(field, None)
        #
        # if isinstance(param_obj, str):
        #     param_obj = {"json": param_obj}  #

        async with aiohttp.ClientSession(
            headers=self.config_model.headers,
        ) as session:
            # if self.config_model.method == 'GET':
            #     kwargs = {
            #         'params': param_obj
            #     }
            # else:
            #     kwargs = {
            #         'json': param_obj
            #     }
            #
            #
            # logger.info(f'param_obj: {param_obj}')
            # logger.info(f'Executing {self.config_model.method} {self.config_model.inputs[0]}')
            # logger.info(f'Params: {kwargs}')
            data = {
                "text": text,
            }

            
            async with session.request(method=self.config_model.method, url=self.config_model.url, json=data) as resp:
                resp.raise_for_status()
                resp_text = await resp.text()

        logger.info(resp_text)

        state[self.id] = resp_text
        logger.info(f'CustomToolNode result resp_text: {resp_text}')

        await self.send_response(ExecResponse(
            type='result',
            node_id=self.id,
            node_type=self.type,
            data={
                'result': resp_text,
            },
        ))
