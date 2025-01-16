from enum import Enum, unique
import websockets

@unique
class WsMessageType(Enum):
    AUDIO = 0x1

async def ws_send_audio(websocket: websockets.WebSocketServerProtocol, msg: bytes):
    await ws_send_msg(websocket, WsMessageType.AUDIO, msg)

async def ws_send_audio_end(websocket: websockets.WebSocketServerProtocol):
    await ws_send_msg_end(websocket, WsMessageType.AUDIO)

async def ws_send_msg(websocket: websockets.WebSocketServerProtocol, msg_type: WsMessageType, msg: bytes):
    if len(msg) == 0:
        return
    wrapped_msg = msg_type.value.to_bytes(1, byteorder='little') + msg
    await websocket.send(wrapped_msg)

async def ws_send_msg_end(websocket: websockets.WebSocketServerProtocol, msg_type: WsMessageType):
    wrapped_msg = msg_type.value.to_bytes(1, byteorder='little')
    await websocket.send(wrapped_msg)
