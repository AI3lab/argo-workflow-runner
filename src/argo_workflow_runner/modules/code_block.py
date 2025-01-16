from typing import Dict

from argo_workflow_runner.core.exec_node import ExecNode
from argo_workflow_runner.core.schema import  (
    CodeBlockConfig,
    ExecResponse,
)

class CodeBlockNode(ExecNode):
    def __init__(self, info, websocket):
        super().__init__(info, websocket)
        self.config_model = CodeBlockConfig.model_validate(self.config)

    async def execute(self, state: Dict):
        await super().execute(state)

        params = {}
        for arg_key, key in self.config_model.args.items():
            val = state.get(key, None)
            if val is None:
                raise Exception(f'No available input: {key} in {self.id}#{self.type}')
            params[arg_key] = val
        
        compiled_code = compile(self.config_model.code, '<string>', 'exec')
        exec(compiled_code)
        func = eval('main')
        res_obj = func(**params)

        state[self.id] = res_obj

        await self.send_response(ExecResponse(
            type='app',
            node_id=self.id,
            node_type=self.type,
            data={
                'result': res_obj['result'],
            },
        ))
