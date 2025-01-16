# Argo Workflow Runner

workflow runner engine for argo

## Design goals

- Distributed agentic workflow support
- Highly extensible - integrate your own tools
- Web3 Support
- Frameworks have many built-in modules


We are in the process of heavy development

## Quick Start

### Prerequisites
- Python 3.10+
- Redis

1. Install Poetry

We use [poetry](https://python-poetry.org/docs/#installing-with-the-official-installer) to build this project.


```bash
curl -sSL https://install.python-poetry.org | python3 - --version 1.8.4
...
poetry install
```

2. Install redis 

Install them according to different operating systems or use Docker for installation.

3. Configure 

Copy .env.example to .env and modify it to meet your enviroment

4. Start workflow server and use client to test

```bash
:~/train/argo-workflow-runner/examples$ python server.py 
INFO:     Started server process [202004]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
2025-01-16 10:47:03 - server.py[line:715] - INFO: server listening on 127.0.0.1:8004
2025-01-16 10:47:03 - server.py[line:184] - INFO: websocket server started
INFO:     Uvicorn running on http://127.0.0.1:8003 (Press CTRL+C to quit)


~/train/argo-workflow-runner/examples$ python client.py -s data/single_llm.json
ws://127.0.0.1:8004/?workflow_id=e112556a-492a-4aa2-9dc2-c00bc75d7f38
2025-01-16 10:50:19 - client.py[line:56] - INFO: ws connected: ws://127.0.0.1:8004/?workflow_id=e112556a-492a-4aa2-9dc2-c00bc75d7f38
2025-01-16 10:50:19 - client.py[line:95] - INFO: recv msg: {"type":"enter","node_id":"123","node_type":"llm"}
あなたは私に、中国語のテキストを日本語に翻訳してほしいとおっしゃっています。元の意味を保ち、不要な言葉を避けるようにします。
2025-01-16 10:50:20 - client.py[line:95] - INFO: recv msg: {"type":"result","node_id":"123","node_type":"llm","data":{"result":"あなたは私に、中国語のテキストを日本語に翻訳してほしいとおっしゃっています。元の意味を保ち、不要な言葉を避けるようにします。"}}
2025-01-16 10:50:20 - client.py[line:97] - INFO: audio_len: 0

```
