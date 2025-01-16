from typing import Optional, Union, List
from pydantic import AnyHttpUrl, field_validator, BaseModel
from dotenv import load_dotenv
from decouple import config, Csv

load_dotenv()


class EnvSettings(BaseModel):

    LLM_MODEL: str = config("LLM_MODEL", default="gpt-3.5-turbo", cast=str)
    LLM_BASE_URL: str = config("LLM_BASE_URL", default="", cast=str)
    LLM_KEY: str = config("LLM_KEY", default="", cast=str)
    WORKING_DIR : str = config("WORKING_DIR", default="", cast=str)

    TTS_GPT_SOVITS_URL: str = config("TTS_GPT_SOVITS_URL", default="", cast=str)

    TAVILY_API_KEY : str = config("TAVILY_API_KEY", default="", cast=str)
    SERP_API_KEY :  str = config("SERP_API_KEY", default="", cast=str)

    DOWNLOAD_URL_FMT : str = config("DOWNLOAD_URL_FMT", default="", cast=str)
    BLIP_URL :  str = config("BLIP_URL", default="", cast=str)
    KB_URL : str = config("KB_URL", default="", cast=str)

    REDIS_URL :  str = config("REDIS_URL", default="redis://localhost", cast=str)

    RESTFUL_SERVER_HOST:  str = config("RESTFUL_SERVER_HOST", default="127.0.0.1", cast=str)
    RESTFUL_SERVER_PORT:  int = config("RESTFUL_SERVER_PORT", default=8003, cast=int)
    WS_SERVER_HOST:  str = config("WS_SERVER_HOST", default="127.0.0.1", cast=str)
    WS_SERVER_PORT:  int = config("WS_SERVER_PORT", default=8004, cast=int)
    WS_MAX_SIZE:  int = config("WS_SERVER_PORT", default=1*1024*1024, cast=int)
    WORKING_DIR:  str = config("WORKING_DIR", default=".", cast=str)

settings = EnvSettings()