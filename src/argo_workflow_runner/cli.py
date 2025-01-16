
import click
from argo_workflow_runner.core.server import WorkflowServer, ServerConfig

@click.group()
def cli():
    pass

@cli.command()
@click.option('--host', default='0.0.0.0', help='Server host')
@click.option('--restful-port', default=8000, help='REST API port')
@click.option('--websocket-port', default=8001, help='WebSocket port')
@click.option('--upload-dir', default='./uploads', help='Upload directory')
def serve(host, restful_port, websocket_port, upload_dir):
    """Start the workflow server"""
    config = ServerConfig(
        host=host,
        restful_port=restful_port,
        websocket_port=websocket_port,
        upload_dir=upload_dir
    )
    server = WorkflowServer(config)
    server.run()

if __name__ == '__main__':
    cli()