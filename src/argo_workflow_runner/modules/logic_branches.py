from typing import Dict

from argo_workflow_runner.core.exec_node import ExecNode
from argo_workflow_runner.core.schema import (
    LogicBranchesConfig,
    LogicBranchCondition,
    ExecResponse,
)

class LogicBranchesNode(ExecNode):
    def __init__(self, info, websocket):
        super().__init__(info, websocket)
        self.config_model = LogicBranchesConfig.model_validate(self.config)

    async def execute(self, state: Dict):
        await super().execute(state)

        self.select_branch_id = -1
        select_branch_name = 'default'

        branch_cnt = len(self.config_model.branches)
        for idx in range(branch_cnt):
            branch = self.config_model.branches[idx]
            matched = True
            for cond in branch.conditions:
                if cond.logic_relation == 'and':
                    matched = (matched and self.logic_calculate(state, cond))
                else:
                    matched = (matched or self.logic_calculate(state, cond))
            
            if matched:
                self.select_branch_id = idx
                select_branch_name = branch.name
                break
        
        result_data = {
            'select_branch_id': self.select_branch_id,
            'select_branch_name': select_branch_name,
        }
        state[self.id] = result_data

        await self.send_response(ExecResponse(
            type='result',
            node_id=self.id,
            node_type=self.type,
            data=result_data,
        ))


    def logic_calculate(self, state: Dict, cond: LogicBranchCondition) -> bool:
        state_val = str(state.get(cond.cond_param, ''))
        if cond.cond_val is None:
            cond_val = ''
        else:
            cond_val = str(cond.cond_val)

        compare_type = cond.compare_type
        if compare_type == 'include':
            return state_val.find(cond_val) != -1
        
        elif compare_type == 'not_include':
            return state_val.find(cond_val) == -1
        
        elif compare_type == 'equal':
            return state_val == cond_val
        
        elif compare_type == 'not_equal':
            return state_val != cond_val

        elif compare_type == 'empty':
            return state_val == ''

        elif compare_type == 'not_empty':
            return state_val != ''

        elif compare_type == 'start_with':
            return state_val.startswith(cond_val)

        elif compare_type == 'end_with':
            return state_val.endswith(cond_val)
        
        raise Exception(f'Invalid compare_type({compare_type}) for node: {self.id}')
