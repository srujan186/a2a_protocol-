"""
Writer Agent - A2A server entrypoint.

Run with:  python main.py
Exposes:
  GET  /.well-known/agent-card.json
  POST /
"""

import uvicorn
from fastapi import FastAPI

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

from agent_executor import WriterAgentExecutor

HOST = "localhost"
PORT = 9002
URL = f"http://{HOST}:{PORT}/"

skill = AgentSkill(
    id="summarize_and_write",
    name="Summarize and Write",
    description="Turns raw research findings into a polished piece of writing",
    tags=["writing", "summarization"],
    examples=["Turn these bullet-point findings into a short article"],
)

agent_card = AgentCard(
    name="Writer Agent",
    description="Turns raw research findings into clear, polished prose",
    version="1.0.0",
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[skill],
    supported_interfaces=[AgentInterface(url=URL, protocol_binding="JSONRPC")],
)

request_handler = DefaultRequestHandler(
    agent_executor=WriterAgentExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=agent_card,
)

app = FastAPI(title="Writer Agent (A2A)")

add_a2a_routes_to_fastapi(
    app,
    agent_card_routes=create_agent_card_routes(agent_card),
    jsonrpc_routes=create_jsonrpc_routes(request_handler, rpc_url="/"),
)

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)