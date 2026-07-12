# A2A Multi-Agent Demo: Research + Writer + Orchestrator

Three agents that talk to each other over the official **Agent2Agent (A2A) Protocol v1.0**,
using the official `a2a-sdk` Python package.

```
User request
     │
     ▼
Orchestrator (A2A client)
     │
     ├──► Research Agent  (A2A server, :9001) — web search, returns raw findings
     │
     └──► Writer Agent    (A2A server, :9002) — turns findings into polished prose
     │
     ▼
Final output
```

## Project layout

```
a2a-demo/
├── requirements.txt
├── research_agent/
│   ├── agent.py            # LLM logic (web search via Claude's web_search tool)
│   ├── agent_executor.py    # Bridges A2A protocol <-> agent.py
│   └── main.py              # FastAPI server, runs on :9001
├── writer_agent/
│   ├── agent.py             # LLM logic (writing/summarizing)
│   ├── agent_executor.py
│   └── main.py               # FastAPI server, runs on :9002
└── orchestrator/
    └── main.py               # A2A client: discovers + delegates to both agents
```

## Setup

```bash
cd a2a-demo
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt

export ANTHROPIC_API_KEY=sk-ant-...   # on Windows (PowerShell): $env:ANTHROPIC_API_KEY="sk-ant-..."
```

## Running it

Open **three terminals** (all with the venv activated and `ANTHROPIC_API_KEY` set):

**Terminal 1 — Research Agent:**
```bash
cd research_agent
python main.py
# Serves Agent Card at http://localhost:9001/.well-known/agent-card.json
```

**Terminal 2 — Writer Agent:**
```bash
cd writer_agent
python main.py
# Serves Agent Card at http://localhost:9002/.well-known/agent-card.json
```

**Terminal 3 — Orchestrator (run whenever you want a result):**
```bash
cd orchestrator
python main.py "What's new in solid-state batteries in 2026?"
```

You'll see:
1. Discovery of both Agent Cards
2. Task delegated to the Research Agent → raw findings returned
3. Task delegated to the Writer Agent (with those findings) → polished write-up returned
4. Final output printed to the console

## How the A2A protocol pieces map to the code

| A2A concept | Where it lives |
|---|---|
| **Agent Card** (`/.well-known/agent-card.json`) | Built in each agent's `main.py` (`AgentCard(...)`), served automatically by `create_agent_card_routes` |
| **Agent Skill** | `AgentSkill(...)` in each `main.py` — declares what the agent can do |
| **A2A Server** | `DefaultRequestHandler` + `add_a2a_routes_to_fastapi` in each `main.py` |
| **Agent Executor** | `agent_executor.py` in each agent — receives a `RequestContext`, calls the agent's own logic, emits a `Message` event |
| **A2A Client** | `orchestrator/main.py` — `A2ACardResolver` (discovery) + `create_client` / `send_message` (delegation) |
| **Transport** | JSON-RPC 2.0 over HTTP (the `protocol_binding="JSONRPC"` in each Agent Card) |

## Notes / things worth knowing

- This SDK version (`a2a-sdk==1.1.0`) implements **A2A Protocol v1.0**. Requests must include the header `A2A-Version: 1.0` — the official `a2a-sdk` client sets this for you automatically, so you only need to worry about it if you call the JSON-RPC endpoint directly (e.g. with `curl`).
- The demo currently runs everything **sequentially** and **without streaming** (`streaming=False` in `ClientConfig`) to keep the first version simple. Real A2A supports SSE streaming so a client can watch a task's status change live (`submitted` → `working` → `completed`) — that's a natural next upgrade.
- The Research Agent uses Claude's built-in `web_search` tool via the Anthropic API for real, live web research — no separate search API key needed, just `ANTHROPIC_API_KEY`.
- Task/state management here uses `InMemoryTaskStore`, fine for a demo; a production system would swap in a persistent task store.

## Suggested next steps (once this is working for you)

1. **Streaming** — switch `ClientConfig(streaming=True)` and consume `status_update` / `artifact_update` events as they arrive, so you can print live progress.
2. **Parallel delegation** — if you add a 3rd worker agent, have the orchestrator delegate to multiple agents concurrently with `asyncio.gather`.
3. **Smarter orchestrator routing** — right now the orchestrator always does research → write, in that fixed order. You could have it use an LLM call itself to decide which agent(s) a request needs.
4. **Auth** — A2A supports OAuth2/JWT natively; useful once these agents aren't just running on localhost.