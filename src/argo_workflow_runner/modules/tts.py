import asyncio
import aiohttp
from typing import Dict

from argo_workflow_runner.core.exec_node import ExecNode
from argo_workflow_runner.core.schema  import (
    TTSConfig,
    ExecResponse,
)
import argo_workflow_runner.utils.tts as tts
import argo_workflow_runner.utils.ws_messager as ws_messager

class TTSNode(ExecNode):
    def __init__(self, info, websocket):
        super().__init__(info, websocket)
        self.config_model = TTSConfig.model_validate(self.config)

    async def execute(self, state: Dict):
        await super().execute(state)

        text = state.get(self.config_model.inputs[0], None)
        if text is None:
            raise Exception(f'No available input: {self.config_model.inputs[0]}, in {self.id}#{self.type}#{self.config_model.name}')
        
        async for audio in tts.fetch_audio_stream(text, self.config_model.voice):
            await ws_messager.ws_send_audio(self.websocket, audio)
        
        await ws_messager.ws_send_audio_end(self.websocket)
