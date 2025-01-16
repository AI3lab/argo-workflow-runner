import redis.asyncio as redis
import json
from typing import List, Tuple

from argo_workflow_runner.env_settings import  settings

class LLMMemoryManager():
    def __init__(self):
        self.pool = redis.ConnectionPool.from_url(settings.REDIS_URL)
    
    def get_client(self) -> redis.Redis:
        return redis.Redis(connection_pool=self.pool)
    
    async def close_client(self, client: redis.Redis):
        await client.aclose()

    async def close_pool(self):
        await self.pool.aclose()

    async def set_memory(self, session_id: str, node_id: str, human_words: str, ai_words: str, cnt: int):
        client = self.get_client()

        list_key = f'{session_id}/{node_id}'
        val = [human_words, ai_words]
        await client.rpush(list_key, json.dumps(val))

        await client.ltrim(list_key, 0, cnt)

        await self.close_client(client)
    
    async def get_memory(self, session_id: str, node_id: str) -> List[Tuple[str, str]]:
        client = self.get_client()

        list_key = f'{session_id}/{node_id}'
        values = await client.lrange(list_key, 0, -1)

        mem_list = []
        for val in values:
            arr = json.loads(val)
            mem_list.append(('human', arr[0]))
            mem_list.append(('ai', arr[1]))
        
        await self.close_client(client)
        
        return mem_list

llm_memory_mgr = LLMMemoryManager()
