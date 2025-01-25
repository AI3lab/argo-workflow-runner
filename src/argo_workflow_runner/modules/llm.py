from typing import Dict
from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from argo_workflow_runner.configs import logger

from argo_workflow_runner.core.exec_node import ExecNode
from argo_workflow_runner.core.schema import (
    LLMConfig,
    ExecResponse,
)
from argo_workflow_runner.utils.llm import get_chat_model
from argo_workflow_runner.core.llm_memory import llm_memory_mgr

HUMAN_TEMPLATE = '{text}'

class LLMNode(ExecNode):
    def __init__(self, info, websocket):
        super().__init__(info, websocket)
        self.config_model = LLMConfig.model_validate(self.config)

    async def execute(self, state: Dict):
        await super().execute(state)

        session_id = state.get('__session_id', '')

        chat_model = await get_chat_model(model=self.config_model.model, temperature=self.config_model.temperature)

        system_message_prompt = SystemMessagePromptTemplate.from_template(self.config_model.prompt)
        human_message_prompt = HumanMessagePromptTemplate.from_template(HUMAN_TEMPLATE)

        mem_list = []
        if self.config_model.memory_cnt > 0:
            mem_list = await llm_memory_mgr.get_memory(session_id, self.id)

        chat_prompt = ChatPromptTemplate.from_messages([
            system_message_prompt,
            *mem_list,
            human_message_prompt,
        ])
        
        chain = chat_prompt | chat_model | StrOutputParser()

        human_words = state.get(self.config_model.inputs[0], None)
        if human_words is None:
            raise Exception(f'human words should not be empty for {self.id}, {self.type}')
        
        input = {
            'text': human_words,
        }
        for key in self.config_model.prompt_params:
            val = state.get(key, None)
            if val is not None:
                input[key] = val

        result = ''
        async for text_chunk in chain.astream(input):
            await self.send_response(ExecResponse(
                type='text',
                node_id=self.id,
                node_type=self.type,
                data={
                    'text': text_chunk,
                    'is_end': False,
                },
            ))
            result += text_chunk
        await self.send_response(ExecResponse(
            type='text',
            node_id=self.id,
            node_type=self.type,
            data={
                'text': '',
                'is_end': True,
            },
        ))
        
        state[self.id] = result
        logger.info(f'LLM result : {result}')

        await self.send_response(ExecResponse(
            type='result',
            node_id=self.id,
            node_type=self.type,
            data={
                'result': result,
            },
        ))

        if self.config_model.memory_cnt > 0:
            await llm_memory_mgr.set_memory(session_id, self.id, human_words, result, self.config_model.memory_cnt)
