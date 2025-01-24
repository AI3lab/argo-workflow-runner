from typing import Dict

from argo_workflow_runner.core.exec_node import ExecNode
from argo_workflow_runner.core.schema import (
    SpAppConfig,
    ExecResponse,
)

class SpAppNode(ExecNode):
    def __init__(self, info, websocket):
        super().__init__(info, websocket)
        self.config_model = SpAppConfig.model_validate(self.config)

    async def execute(self, state: Dict):
        await super().execute(state)

        params = {}
        for key in self.config_model.inputs:
            val = state.get(key, None)
            if val is not None:
                params[key] = val

        await self.send_response(ExecResponse(
            type='app',
            node_id=self.id,
            node_type=self.type,
            data={
                'name': self.config_model.name,
                'params': params,
            },
        ))
