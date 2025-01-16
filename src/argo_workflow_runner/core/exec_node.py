from typing import Dict, Optional, List, Any
import websockets
from langgraph.graph import END

from argo_workflow_runner.configs import logger, COMPOSITE_MODULES
from argo_workflow_runner.core.schema import ExecResponse
from argo_workflow_runner.utils.llm import llm_chat_stream

class ExecNode():
    def __init__(self, info: Dict[str, Any], websocket: websockets.WebSocketServerProtocol):
        self.id = info['id']
        node_key = info['type']
        if node_key in COMPOSITE_MODULES:
            name = info['config']['name']
            node_key = f'{node_key}/{name}'
        self.type = node_key
        self.config = info['config']

        self.websocket = websocket

        self.select_branch_id = -1

    async def try_to_execute(self, state: Dict):
        try:
            await self.execute(state)
        except Exception as e:
            await self.send_response(ExecResponse(
                type='error',
                node_id=self.id,
                node_type=self.type,
                data={
                    'msg': str(e),
                },
            ))
            async for text_chunk, done in error_report(str(e)):
                await self.send_response(ExecResponse(
                    type='text',
                    node_id=self.id,
                    node_type=self.type,
                    data={
                        'text': text_chunk,
                        'is_end': done,
                    },
                ))
            raise e

    async def execute(self, state: Dict):
        logger.info(f'execute: {self.type}#{self.id}, state: {state.keys()}')
        await self.send_response(ExecResponse(
            type='enter',
            node_id=self.id,
            node_type=self.type,
        ))
    
    def select_branch(self):
        logger.error(f'Not implement select_branch method for node: {self.id}, {self.type}')


    async def send_response(self, rsp: ExecResponse):
        msg = rsp.model_dump_json(exclude_none=True)
        await self.websocket.send(msg)

class BranchRouter():
    def __init__(self, from_node: ExecNode, edges: Dict[str, Any]):
        self.from_node = from_node
        self.edges = edges

    def run(self, state: Dict):
        for edge in self.edges:
            if edge['from_branch'] == self.from_node.select_branch_id:
                if 'to_node' in edge:
                    return edge['to_node']
                else:
                    return END
        
        raise Exception(f'No branch selected for node: {self.from_node.id}, {self.from_node.type}')

ERROR_REPORT_PROMPT = """
<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an assistant named Argo that manages agents running for the user.
But sometimes errors may occur when the agents running.
Here is the error:
'{error}'
You need to politely remind the user this error infomation.
Please generate three sentence maximum to tell the user. 
<|eot_id|><|start_header_id|>user<|end_header_id|>
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

async def error_report(error: str):
    async for result in llm_chat_stream(ERROR_REPORT_PROMPT, {'error': error}):
        yield (result, False)
    yield ('', True)
