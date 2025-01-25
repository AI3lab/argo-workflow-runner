from typing import Dict
from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

from argo_workflow_runner.configs import logger
from argo_workflow_runner.core.exec_node import ExecNode
from argo_workflow_runner.core.schema import (
    IntentionConfig,
    IntentionBranch,
    ExecResponse,
)
from argo_workflow_runner.utils.llm import get_chat_model
from argo_workflow_runner.configs import logger

SYSTEM_TEMPLATE = """
You are an AI assistant that determines the user's intention based on the user's words. 
The user may have the following intentions:
{content}
If none of the above intent options are relevant to the user's utterance, select branch 'none'.
Please provide the intent branch option that is closest to the user's utterance, without preamble or explaination. 
"""
HUMAN_TEMPLATE = '{text}'

class IntentionNode(ExecNode):
    def __init__(self, info, websocket):
        super().__init__(info, websocket)
        self.config_model = IntentionConfig.model_validate(self.config)

    async def execute(self, state: Dict):
        await super().execute(state)

        chat_model = await get_chat_model(model=self.config_model.model, temperature=0)

        system_message_prompt = SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE)
        human_message_prompt = HumanMessagePromptTemplate.from_template(HUMAN_TEMPLATE)
        chat_prompt = ChatPromptTemplate.from_messages([
            system_message_prompt,
            human_message_prompt,
        ])
        
        chain = chat_prompt | chat_model | StrOutputParser()

        content = '\n'.join(map(lambda x: x.instruction, self.config_model.branches))
        input = {
            'content': content,
            'text': state.get(self.config_model.inputs[0], ''),
        }
        result = await chain.ainvoke(input)
        logger.info(f'selected branch: {result} in {self.id} ')

        self.select_branch_id = 0
        select_branch_name = 'default branch'

        if result != 'none':
            branch_cnt = len(self.config_model.branches)
            for idx in range(branch_cnt):
                branch = self.config_model.branches[idx]
                if branch.title == result:
                    self.select_branch_id = idx
                    select_branch_name = branch.title
                    break
        
        result_data = {
            'select_branch_id': self.select_branch_id,
            'select_branch_name': select_branch_name,
        }
        logger.info(f'selected branch: {result_data} in {self.id}, {self.type}')
        state[self.id] = result_data

        await self.send_response(ExecResponse(
            type='result',
            node_id=self.id,
            node_type=self.type,
            data=result_data,
        ))
