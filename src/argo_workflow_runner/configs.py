import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from argo_workflow_runner.env_settings import settings

USING_FILE_HANDLER = False

def init_logger():
    try:
        import langchain
        langchain.verbose = False
    except:
        pass

    # log format
    LOG_FORMAT = "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
    logger = logging.getLogger('0xbot')
    logger.setLevel(logging.INFO)

    handlers = None
    if USING_FILE_HANDLER:
        # log dir
        LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        if not os.path.exists(LOG_PATH):
            os.mkdir(LOG_PATH)

        proc_name = os.path.basename(sys.argv[0])
        proc_name = proc_name[0:-3]
        log_file = LOG_PATH + os.sep + f'{proc_name}.log'
        file_handler = RotatingFileHandler(
            filename=log_file, 
            mode='a', 
            maxBytes=(100*1024*1024),
            backupCount=10,
            encoding="utf-8",
        )
        handlers = [file_handler]

    logging.basicConfig(
        level=logging.INFO,
        handlers=handlers,
        format=LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.INFO)

    return logger

logger = init_logger()


UPLOAD_DIR = os.path.join(settings.WORKING_DIR, "upload")
if not os.path.exists(UPLOAD_DIR):
    os.mkdir(UPLOAD_DIR)

COMPOSITE_MODULES = {'tool', 'custom_tool'}
