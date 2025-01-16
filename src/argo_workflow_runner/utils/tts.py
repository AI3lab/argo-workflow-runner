import requests
import aiohttp
from argo_workflow_runner.configs import logger
from argo_workflow_runner.env_settings import settings


async def gpt_sovits_audio_stream_gen(text, voice):
    urlencoded_text = requests.utils.quote(text)
    got_first_chunk = False
    async with aiohttp.ClientSession() as session:
        payload = {
            "cha_name": voice,
            "character_emotion": "default",
            "text": urlencoded_text,
            "text_language": "auto",
            "batch_size": 10,
            "speed": 1,
            "top_k": 6,
            "top_p": 0.8,
            "temperature": 0.8,
            "stream": "True",
            "cut_method": "auto_cut_25",
            "seed": -1,
            "save_temp": "False"
        }
        url = settings.TTS_GPT_SOVITS_URL
        async with session.post(url, json=payload) as resp:
            if resp.status == 200:
                async for data in resp.content.iter_chunked(1024):
                    if not got_first_chunk:
                        logger.info(f'gpt_sovits_audio_stream_gen got first chunk')
                        got_first_chunk = True
                    yield data
            else:
                content = await resp.text()
                logger.error(f'connect to {url} fail: {content}')

async def fetch_audio_stream(text, voice='Emma'):
    async_audio_stream = gpt_sovits_audio_stream_gen

    async for audio_data in async_audio_stream(text, voice):
        yield audio_data
