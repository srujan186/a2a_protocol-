"""
Research Agent - A2A server entrypoint.

Run with:  python main.py
Exposes:
  GET  /.well-known/agent-card.json   (Agent Card - discovery)
  POST /                              (JSON-RPC endpoint - task delegation)
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

from agent_executor import ResearchAgentExecutor

HOST = "localhost"
PORT = 9001
URL = f"http://{HOST}:{PORT}/"

skill = AgentSkill(
    id="web_research",
    name="Web Research",
    description="Searches the web and returns key findings on a topic or question",
    tags=["research", "search"],
    examples=["Research recent developments in solid-state batteries"],
)

agent_card = AgentCard(
    name="Research Agent",
    description="Finds and summarizes information on a given topic via web search",
    version="1.0.0",
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[skill],
    supported_interfaces=[AgentInterface(url=URL, protocol_binding="JSONRPC")],
)

request_handler = DefaultRequestHandler(
    agent_executor=ResearchAgentExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=agent_card,
)

app = FastAPI(title="Research Agent (A2A)")

add_a2a_routes_to_fastapi(
    app,
    agent_card_routes=create_agent_card_routes(agent_card),
    jsonrpc_routes=create_jsonrpc_routes(request_handler, rpc_url="/"),
)

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)