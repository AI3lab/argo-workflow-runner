import json
import asyncio
import aiohttp
import websockets
import subprocess
import shlex
import argparse
from typing import Dict

from argo_workflow_runner.configs import logger
from argo_workflow_runner.env_settings import settings
from argo_workflow_runner.utils.ws_messager import WsMessageType

class AudioPlayer():
    def __init__(self) -> None:
        self._player = None

    def recv_audio_bytes(self, audio_bytes):
        if self._player is None:
            ffplay_process = "ffplay -autoexit -nodisp -hide_banner -loglevel error -i pipe:0"
            self._player = subprocess.Popen(
                shlex.split(ffplay_process), 
                stdin=subprocess.PIPE,
                bufsize=10*1024*1024,
            )
            logger.info('Audio player opened.')
        
        self._player.stdin.write(audio_bytes)

    def close(self):
        if self._player is None:
            return
        self._player.stdin.close()
        self._player.wait()
        self._player = None
        logger.info('Audio player closed.')

async def send_executing_data(data: Dict, is_test=False):
    url = f'http://{settings.RESTFUL_SERVER_HOST}:{settings.RESTFUL_SERVER_PORT}/{"test_single_node" if is_test else "send_workflow"}'
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as resp:
            resp.raise_for_status()

            resp_json = await resp.json()
            return resp_json['workflow_id']

async def main(data: Dict, is_test=False):
    workflow_id = await send_executing_data(data, is_test)


    url = f'ws://{settings.WS_SERVER_HOST}:{settings.WS_SERVER_PORT}/?workflow_id={workflow_id}'
    print(url)
    async with websockets.connect(
        url, max_size=settings.WS_MAX_SIZE,
    ) as websocket:
        logger.info(f'ws connected: {url}')
        audio_len = 0
        text_appending = False
        _fp = None
        async for message in websocket:
            if type(message) == bytes:
                msg_type = int(message[0])
                message = message[1:]
                if msg_type == WsMessageType.AUDIO.value:
                    if len(message) > 0:
                        if _fp is None:
                            _fp = open('output.wav', 'wb')
                        _fp.write(message)
                        audio_len += len(message)
                        # audio_player.recv_audio_bytes(message)
                    else:
                        logger.info('recv audio end.')
                        if _fp is not None:
                            chunk_size = audio_len - 44
                            _fp.seek(40, 0)
                            _fp.write(chunk_size.to_bytes(4, byteorder='little'))

                            _fp.close()
                            _fp = None
                continue
            
            msg = json.loads(message)
            if msg['type'] == 'text':
                data = msg['data']
                if not data['is_end']:
                    print(data['text'], end='')
                    text_appending = True
                else:
                    if text_appending:
                        print(data['text'])
                    else:
                        logger.info(f'recv msg: {message}')
                    text_appending = False
            else:
                logger.info(f'recv msg: {message}')
        
        logger.info(f'audio_len: {audio_len}')
    
    # audio_player.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="terminal for testing workflow runner.")

    parser.add_argument(
        '-w', 
        '--workflow',
        help=("workflow file path")
    )
    parser.add_argument(
        '-s', 
        '--single',
        help=("single node file path")
    )

    args = parser.parse_args()

    if args.workflow:
        with open(args.workflow, 'rb') as fp:
            workflow_info = json.load(fp)
        asyncio.run(main(workflow_info))
    elif args.single:
        with open(args.single, 'rb') as fp:
            single_node_info = json.load(fp)
        asyncio.run(main(single_node_info, True))
