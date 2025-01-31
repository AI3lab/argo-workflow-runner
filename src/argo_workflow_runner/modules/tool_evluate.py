import asyncio
import aiohttp
from typing import Dict

from argo_workflow_runner.core.exec_node import ExecNode
from argo_workflow_runner.core.schema  import (
    ToolConfig,
    ExecResponse,
)
from argo_workflow_runner.env_settings import settings
from argo_workflow_runner.configs import logger



lock = asyncio.Lock()

class ToolBlipNode(ExecNode):
    def __init__(self, info, websocket):
        super().__init__(info, websocket)
        self.config_model = ToolConfig.model_validate(self.config)

    async def execute(self, state: Dict):
        await super().execute(state)

        image_name = state.get(self.config_model.inputs[0], None)
        if image_name is None:
            raise Exception(f'No available input: {self.config_model.inputs[0]}')

        transfer_type = state.get('__file_transfer_type', None)
        if transfer_type is None:
            raise Exception('No transfer_type specified.')
        if transfer_type == 'upload':
            image_url = settings.DOWNLOAD_URL_FMT.format(file_name=image_name)
        else:
            image_url = image_name

        async with lock:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'input': image_url,
                }
                url = settings.BLIP_URL
                async with session.post(url, json=payload) as resp:
                    resp.raise_for_status()
                    resp_json = await resp.json()
                    result = resp_json['output']

        state[self.id] = result

        await self.send_response(ExecResponse(
            type='result',
            node_id=self.id,
            node_type=self.type,
            data={
                'result': result,
            },
        ))
