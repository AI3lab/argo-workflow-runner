import asyncio
import uuid
from typing import Dict, Optional, List, Any, Type
import websockets
from langgraph.graph import END, StateGraph

from argo_workflow_runner.configs import logger, COMPOSITE_MODULES
from argo_workflow_runner.core.exec_node import ExecNode, BranchRouter
from argo_workflow_runner.modules import *


class WorkflowManager():
    def __init__(self):
        self._workflow_map: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
        self._exec_node_map: Dict[str, Type[ExecNode]] = {
            'logic_branches': LogicBranchesNode,
            'intention': IntentionNode,
            'llm': LLMNode,
            'code_block': CodeBlockNode,
            'custom_tool': CustomToolNode,
            'sp_app':SpAppNode,
            'agent': AgentNode,
            'knowledge_base': KnowledgeBaseNode,
            'tool/blip': ToolBlipNode,
            'tool/google': ToolGoogleNode,
            'tool/web_reader': ToolWebReaderNode,
            'tts': TTSNode,

        }

    def add_module(self, module_type: str, module_class: Type[ExecNode]) -> None:
        """
        Add a new module type to the workflow manager

        Args:
            module_type: The type identifier for the module
            module_class: The ExecNode class implementation

        Raises:
            ValueError: If module_type already exists
            TypeError: If module_class is not a subclass of ExecNode
        """
        if not issubclass(module_class, ExecNode):
            raise TypeError(f"Module class must be a subclass of ExecNode")

        if module_type in self._exec_node_map:
            raise ValueError(f"Module type '{module_type}' already exists")

        self._exec_node_map[module_type] = module_class

    def get_module(self, module_type: str) -> Optional[Type[ExecNode]]:
        """
        Get module class by type

        Args:
            module_type: The type identifier for the module

        Returns:
            The ExecNode class if found, None otherwise
        """
        return self._exec_node_map.get(module_type)

    def list_modules(self) -> List[str]:
        """
        List all registered module types

        Returns:
            List of module type strings
        """
        return list(self._exec_node_map.keys())

    async def add_workflow(self, workflow: Dict) -> str:
        """
        Add a new workflow

        Args:
            workflow: Workflow configuration dictionary

        Returns:
            Workflow ID string
        """
        async with self._lock:
            while True:
                wf_id = str(uuid.uuid4())
                if wf_id in self._workflow_map:
                    continue
                self._workflow_map[wf_id] = workflow
                return wf_id

    async def get_workflow(self, wf_id: str) -> Optional[Dict]:
        """
        Get workflow by ID

        Args:
            wf_id: Workflow ID

        Returns:
            Workflow configuration if found, None otherwise
        """
        async with self._lock:
            if wf_id not in self._workflow_map:
                return None

            return self._workflow_map[wf_id]

    async def rmv_workflow(self, wf_id: str):
        """
        Remove workflow by ID

        Args:
            wf_id: Workflow ID to remove
        """
        async with self._lock:
            if wf_id not in self._workflow_map:
                return

            del self._workflow_map[wf_id]

    async def add_single_node_workflow(self, node_info: Dict) -> str:
        """
        Create a workflow with a single node

        Args:
            node_info: Node configuration dictionary

        Returns:
            Workflow ID string
        """
        if 'id' in node_info['node']:
            node_id = node_info['node']['id']
        else:
            node_id = 'node_1'
            node_info['node']['id'] = node_id
        workflow = {
            'start': node_info['start'],
            'nodes': [
                node_info['node']
            ],
            'edges': [
                {
                    'to_node': node_id,
                },
                {
                    'from_node': node_id,
                },
            ],
        }
        return await self.add_workflow(workflow)

    async def run_workflow(self, workflow: Dict, websocket: websockets.WebSocketServerProtocol):
        """
        Execute a workflow

        Args:
            workflow: Workflow configuration dictionary
            websocket: WebSocket connection for communication

        Raises:
            Exception: If node type is not found
        """
        graph_builder = StateGraph(dict)

        node_map: Dict[str, ExecNode] = {}
        for node_info in workflow['nodes']:
            node_key = node_info['type']
            if (node_key in COMPOSITE_MODULES) and (node_key != 'custom_tool'):
                name = node_info['config']['name']
                node_key = f'{node_key}/{name}'

            exec_node_cls = self._exec_node_map.get(node_key)
            if exec_node_cls is None:
                raise Exception(f'No such exec node: {node_key}')

            node: ExecNode = exec_node_cls(node_info, websocket)
            graph_builder.add_node(
                node.id,
                node.try_to_execute,
            )
            node_map[node.id] = node

        condition_edges = {}
        for edge in workflow['edges']:
            if 'from_node' not in edge:
                graph_builder.set_entry_point(edge['to_node'])
            elif 'to_node' not in edge:
                graph_builder.add_edge(edge['from_node'], END)
            else:
                if 'from_branch' in edge:
                    if edge['from_node'] not in condition_edges:
                        condition_edges[edge['from_node']] = []
                    condition_edges[edge['from_node']].append(edge)
                else:
                    graph_builder.add_edge(edge['from_node'], edge['to_node'])

        for from_node_id, edges in condition_edges.items():
            from_node = node_map[from_node_id]
            router = BranchRouter(from_node, edges)
            graph_builder.add_conditional_edges(
                from_node_id,
                router.run,
            )

        start_input: Dict = workflow.get('start', {})
        input = {}
        for k, v in start_input.items():
            input[k] = v

        graph = graph_builder.compile()
        logger.info(input)
        try:
            await graph.ainvoke(input)
        except Exception as e:
            logger.error('run_workflow error', exc_info=e)


workflow_manager = WorkflowManager()