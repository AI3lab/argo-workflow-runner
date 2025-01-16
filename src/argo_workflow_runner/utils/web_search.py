import os
import asyncio
from langchain_community.tools.tavily_search import TavilySearchResults
import serpapi
import time
from argo_workflow_runner.env_settings import settings
from argo_workflow_runner.configs import logger



os.environ['TAVILY_API_KEY'] = settings.TAVILY_API_KEY

async def tavily_search(question: str):
    web_search_tool = TavilySearchResults(k=3)
    try:
        start_tm = time.time()
        docs = await web_search_tool.ainvoke({"query": question})
        logger.info(f'tavily_search cost {time.time() - start_tm:.04} seconds')
        return [d["content"] for d in docs]
    except:
        return []


async def serp_api_search(question: str):
    params = {
        "engine": "google",
        "q": question,
        "location": "Seattle-Tacoma, WA, Washington, United States",
        "hl": "en",
        "gl": "us",
        "google_domain": "google.com",
        "num": "10",
        "safe": "active",
    }

    client = serpapi.Client(api_key=settings.SERP_API_KEY)
    try:
        start_tm = time.time()
        results = await asyncio.to_thread(client.search, params)
        logger.info(f'serp_api_search cost {time.time() - start_tm:.04} seconds')

        return list(map(lambda x: x['snippet'], results['organic_results']))
    except:
        return []
