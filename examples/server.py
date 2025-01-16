# examples/client.py

import asyncio
from argo_workflow_runner.core.server import WorkflowServer


async def run_async_server():
    server = WorkflowServer()
    try:
        await server.start()
    except KeyboardInterrupt:
        await server.stop()


if __name__ == "__main__":

    asyncio.run(run_async_server())