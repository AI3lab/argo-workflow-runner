import asyncio
from typing import Optional
from dataclasses import dataclass
import asyncio
from urllib.parse import urlparse
import uvicorn
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse
import websockets
import signal
import os
import uuid
import aiofiles
from pydantic import BaseModel, Field
import uvicorn
from typing import Dict
from argo_workflow_runner.core.schema import RspUpload
from argo_workflow_runner.env_settings import settings
from argo_workflow_runner.core.llm_memory import llm_memory_mgr
from argo_workflow_runner.configs import logger
from argo_workflow_runner.core.workflow_manager import workflow_manager


class RestfulServer(uvicorn.Server):
    def install_signal_handlers(self) -> None:
        pass

class ServerManager():
    def __init__(self):
        self._restful_servers = []
        self._ws_servers = []
        self._is_running = True
        signal.signal(signal.SIGINT, lambda _, __: self.terminate_all())

    def reg_ws_server(self, server):
        self._ws_servers.append(server)

    def create_restful_server(self, config: uvicorn.Config):
        server = RestfulServer(config)
        self._restful_servers.append(server)
        return server

    def is_running(self):
        return self._is_running

    def terminate_all(self):
        for svr in self._ws_servers:
            svr.close()
        for svr in self._restful_servers:
            svr.should_exit = True

        self._is_running = False

        logger.info('Require to terminate all servers.')


async def on_connected(websocket: websockets.WebSocketServerProtocol):
    try:
        logger.info('connected.')
        path = websocket.path
        parse_result = urlparse(path)
        query = parse_result.query
        prefix = 'workflow_id='
        if not query.startswith(prefix):
            logger.error('No workflow_id in query')
            await websocket.close(1000, "No workflow_id provided")
            return

        workflow_id = query[len(prefix):]
        logger.info(f'Received workflow_id: {workflow_id}')

        workflow = await workflow_manager.get_workflow(workflow_id)
        if not workflow:
            logger.error(f'No workflow found for id: {workflow_id}')
            await websocket.close(1000, "Workflow not found")
            return

        logger.info(f'run_workflow: {workflow_id}')
        await workflow_manager.run_workflow(workflow, websocket)
        await workflow_manager.rmv_workflow(workflow_id)

    except Exception as e:
        logger.error(f"Error in websocket connection: {str(e)}", exc_info=True)
        try:
            await websocket.close(1011, f"Internal server error: {str(e)}")
        except:
            pass  #





app = FastAPI()


@app.post('/send_workflow')
async def send_workflow(workflow: Dict):
    wf_id = await workflow_manager.add_workflow(workflow)
    return {
        'workflow_id': wf_id,
    }


@app.post('/test_single_node')
async def test_single_node(node: Dict):
    wf_id = await workflow_manager.add_single_node_workflow(node)
    return {
        'workflow_id': wf_id,
    }


@app.get("/file/{file_name}")
async def api_get_file(file_name: str):
    UPLOAD_DIR = os.path.join(settings.WORKING_DIR, "upload")

    file_path = os.path.join(UPLOAD_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=file_name)
    else:
        return {
            'error': f'No file named {file_name}',
        }



@app.post("/upload")
async def api_upload(file: UploadFile) -> RspUpload:
    _, file_extension = os.path.splitext(file.filename)
    file_name = str(uuid.uuid4()) + file_extension
    UPLOAD_DIR = os.path.join(settings.WORKING_DIR, "upload")

    file_path = os.path.join(UPLOAD_DIR, file_name)

    try:
        contents = file.file.read()
        async with aiofiles.open(file_path, 'wb') as fp:
            await fp.write(contents)
    except Exception:
        return {"error": "There was an error uploading the file"}
    finally:
        file.file.close()

    return RspUpload(
        name=file_name,
    )




class WorkflowServer:
    def __init__(self):
        self.server_manager = ServerManager()

    async def start(self):
        """Start both REST and WebSocket servers"""
        tasks = [
            self._start_restful_server(),
            self._start_ws_server()
        ]
        await asyncio.gather(*tasks)

    def run(self):
        """Synchronous method to start the server"""
        asyncio.run(self.start())

    async def stop(self):
        """Stop all servers"""
        self.server_manager.terminate_all()

    async def _start_restful_server(self):
        # Move restful server logic here
        config = uvicorn.Config("argo_workflow_runner.core.server:app", host=settings.RESTFUL_SERVER_HOST, port=settings.RESTFUL_SERVER_PORT, log_level="info")
        server = self.server_manager.create_restful_server(config)
        await server.serve()
        logger.info('restful server exit')
    async def _start_ws_server(self):
        server = await websockets.serve(
            on_connected,
            settings.WS_SERVER_HOST, settings.WS_SERVER_PORT,
            max_size=settings.WS_MAX_SIZE,
            start_serving=True,
        )
        self.server_manager.reg_ws_server(server)
        logger.info('websocket server started')

        await server.wait_closed()

        logger.info('websocket server exit')

        await llm_memory_mgr.close_pool()
        logger.info('llm_memory_mgr closed')