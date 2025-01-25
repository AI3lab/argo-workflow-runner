from typing import Dict
import resource
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, TypeAlias, TypeVar, cast, NamedTuple, Set
from dataclasses import dataclass
import asyncio
import traceback
import resource

import asyncio
import logging
import os

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, TypeAlias, TypeVar, cast, NamedTuple, Set
from aiohttp import web
import traceback

import resource


from argo_workflow_runner.core.exec_node import ExecNode
from argo_workflow_runner.core.schema import  (
    CodeBlockConfig,
    ExecResponse,
)

JsonDict: TypeAlias = Dict[str, Any]
T = TypeVar('T')


@dataclass
class ExecutionResult:
    status: str
    result: Any | None = None
    error: str | None = None
    traceback: str | None = None

    def to_dict(self) -> JsonDict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

SAFE_BUILTINS: Set[str] = {
    'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
    'chr', 'complex', 'dict', 'divmod', 'enumerate', 'filter', 'float',
    'format', 'frozenset', 'hash', 'hex', 'int', 'isinstance', 'issubclass',
    'iter', 'len', 'list', 'map', 'max', 'min', 'next', 'oct', 'ord',
    'pow', 'print', 'range', 'repr', 'reversed', 'round', 'set', 'slice',
    'sorted', 'str', 'sum', 'tuple', 'type', 'zip'
}

FORBIDDEN_MODULES: Set[str] = {
    'os', 'sys', 'subprocess', 'socket', 'requests', 'urllib',
    'pathlib', 'pickle', 'shutil', 'importlib', 'builtins'
}
def create_safe_globals() -> Dict[str, Any]:
    import builtins
    safe_globals = {
        '__builtins__': {
            name: getattr(builtins, name)
            for name in SAFE_BUILTINS
            if hasattr(builtins, name)
        },
        'print': lambda *args, **kwargs: None
    }
    return safe_globals

def validate_code(code: str) -> None:

    for module in FORBIDDEN_MODULES:
        if f"import {module}" in code or f"from {module}" in code:
            raise SecurityError(f"Importing module '{module}' is not allowed")

    if 'eval(' in code or 'exec(' in code:
        raise SecurityError("Using eval() or exec() is not allowed")

    if 'open(' in code or 'file(' in code:
        raise SecurityError("File operations are not allowed")

RESOURCE_LIMITS = {
    'CPU_TIME': 1,
    'MEMORY': 100 * 1024 * 1024,  # 30MB
    'FILE_SIZE': 1024 * 1024,  # 1MB
    'PROCESSES': 1,
    'OPEN_FILES': 10
}

def set_resource_limits() -> None:
    """resource limit"""
    try:
        resource.setrlimit(resource.RLIMIT_CPU,
                           (RESOURCE_LIMITS['CPU_TIME'], RESOURCE_LIMITS['CPU_TIME']))

        resource.setrlimit(resource.RLIMIT_AS,
                           (RESOURCE_LIMITS['MEMORY'], RESOURCE_LIMITS['MEMORY']))

        resource.setrlimit(resource.RLIMIT_FSIZE,
                           (RESOURCE_LIMITS['FILE_SIZE'], RESOURCE_LIMITS['FILE_SIZE']))

        resource.setrlimit(resource.RLIMIT_NPROC,
                           (RESOURCE_LIMITS['PROCESSES'], RESOURCE_LIMITS['PROCESSES']))

        resource.setrlimit(resource.RLIMIT_NOFILE,
                           (RESOURCE_LIMITS['OPEN_FILES'], RESOURCE_LIMITS['OPEN_FILES']))

    except Exception as e:
        logger.error(f"Failed to set resource limits: {e}")
        raise
class SecurityError(Exception):
    pass

class CodeBlockNode(ExecNode):
    @staticmethod
    async def execute_code_in_process(code: str, params: JsonDict) -> ExecutionResult:
        loop = asyncio.get_event_loop()
        with ProcessPoolExecutor(max_workers=1) as executor:
            try:
                future = loop.run_in_executor(
                    executor,
                    CodeBlockNode._execute_code_safely,
                    code,
                    params
                )
                result = await asyncio.wait_for(future, timeout=RESOURCE_LIMITS['CPU_TIME'])
                return result
            except asyncio.TimeoutError:
                return ExecutionResult(
                    status='error',
                    error='Execution timeout'
                )
            except Exception as e:
                return ExecutionResult(
                    status='error',
                    error=str(e),
                    traceback=traceback.format_exc()
                )

    @staticmethod
    def _execute_code_safely(code: str, params: JsonDict) -> ExecutionResult:
        try:
            set_resource_limits()

            validate_code(code)

            globals_dict = create_safe_globals()
            globals_dict.update(params)

            compiled_code = compile(code, '<string>', 'exec')

            exec(compiled_code, globals_dict)

            if 'main' not in globals_dict:
                return ExecutionResult(
                    status='error',
                    error="No main function defined"
                )

            result = globals_dict['main'](**params)
            return ExecutionResult(
                status='success',
                result=result
            )

        except SecurityError as e:
            return ExecutionResult(
                status='error',
                error=f"Security violation: {str(e)}"
            )
        except Exception as e:
            return ExecutionResult(
                status='error',
                error=str(e),
                traceback=traceback.format_exc()
            )


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


        res_obj = await self.execute_code_in_process(self.config_model.code, params)
        logging.info(f"CodeBlockNode execute result: {res_obj}")
        if res_obj.status == 'success':

            state[self.id] = res_obj

            await self.send_response(ExecResponse(
                type='result',
                node_id=self.id,
                node_type=self.type,
                data={
                    'result': res_obj.result
                },
            ))
        else:
            await self.send_response(ExecResponse(
                type='error',
                node_id=self.id,
                node_type=self.type,
                data={
                    'msg': str(res_obj),
                },
            ))

#TODO:Put the code_block in docker and standalone  server