"""
Orchestrator - A2A client.

Discovers the Research Agent and Writer Agent via their Agent Cards, then
delegates sequentially:
    user request -> Research Agent (find facts) -> Writer Agent (write it up) -> user

Run with:  python main.py "your request here"
Requires the research_agent and writer_agent servers to already be running
(see README.md for start-up instructions).
"""

import asyncio
import sys
import uuid

import httpx

import a2a.types as t
from a2a.client import A2ACardResolver, ClientConfig, create_client

RESEARCH_AGENT_URL = "http://localhost:9001"
WRITER_AGENT_URL = "http://localhost:9002"


def build_user_message(text: str) -> t.SendMessageRequest:
    return t.SendMessageRequest(
        message=t.Message(
            message_id=str(uuid.uuid4()),
            role=t.Role.ROLE_USER,
            parts=[t.Part(text=text)],
        )
    )


def extract_text(stream_response: t.StreamResponse) -> str | None:
    """Pull plain text out of whichever event type came back."""
    if stream_response.HasField("message"):
        return "".join(p.text for p in stream_response.message.parts if p.text)
    if stream_response.HasField("task"):
        task = stream_response.task
        # Look at the task's status message and/or artifacts for text
        texts = []
        if task.status.HasField("message"):
            texts += [p.text for p in task.status.message.parts if p.text]
        for artifact in task.artifacts:
            texts += [p.text for p in artifact.parts if p.text]
        return "".join(texts) if texts else None
    return None


async def discover(httpx_client: httpx.AsyncClient, base_url: str):
    resolver = A2ACardResolver(httpx_client, base_url)
    card = await resolver.get_agent_card()
    print(f"  Discovered: {card.name} ({base_url})")
    return card


async def delegate(httpx_client: httpx.AsyncClient, card: t.AgentCard, text: str) -> str:
    """Send a task to an agent and collect its final text response."""
    config = ClientConfig(httpx_client=httpx_client, streaming=False)
    client = await create_client(card, client_config=config)
    request = build_user_message(text)

    collected = []
    async for response in client.send_message(request):
        piece = extract_text(response)
        if piece:
            collected.append(piece)
    return "\n".join(collected).strip()


async def run(user_request: str) -> None:
    async with httpx.AsyncClient(timeout=60.0) as httpx_client:
        print("Discovering agents...")
        research_card = await discover(httpx_client, RESEARCH_AGENT_URL)
        writer_card = await discover(httpx_client, WRITER_AGENT_URL)

        print("\nStep 1: delegating research task...")
        findings = await delegate(httpx_client, research_card, user_request)
        print(f"  Findings received ({len(findings)} chars)")

        print("\nStep 2: delegating writing task...")
        writing_instruction = (
            f"Original request: {user_request}\n\n"
            f"Research findings:\n{findings}\n\n"
            "Write this up clearly for the reader."
        )
        final_output = await delegate(httpx_client, writer_card, writing_instruction)

        print("\n=== FINAL OUTPUT ===\n")
        print(final_output)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python main.py "your request here"')
        sys.exit(1)
    asyncio.run(run(" ".join(sys.argv[1:])))