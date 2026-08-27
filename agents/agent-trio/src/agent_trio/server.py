"""FastAPI server exposing the three agents over HTTP. Suitable for ECS Fargate."""
from __future__ import annotations

from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Header
from pydantic import BaseModel
from agents import Runner, SQLiteSession, InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered

from .agents.second_brain_agent import build_second_brain_agent
from .agents.trading_agent import build_trading_agent
from .agents.research_agent import build_research_agent
from .common.config import settings
from .common.logging import get_logger

log = get_logger(__name__)

app = FastAPI(title="Agent Trio", version="0.1.0")

# Build agents once at startup (cheap; tools are functions, model calls are lazy).
AGENTS = {
    "atlas": build_second_brain_agent(),
    "trading": build_trading_agent(),
    "research": build_research_agent(),
}


def auth(authorization: str = Header(default="")) -> None:
    if settings.api_auth_token and settings.api_auth_token != "change-me":
        if authorization != f"Bearer {settings.api_auth_token}":
            raise HTTPException(status_code=401, detail="unauthorized")


class ChatIn(BaseModel):
    agent: Literal["atlas", "trading", "research"] = "atlas"
    message: str
    session_id: str | None = None


class ChatOut(BaseModel):
    agent: str
    final_agent: str
    output: str
    blocked: bool = False
    block_reason: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatOut, dependencies=[Depends(auth)])
async def chat(payload: ChatIn) -> ChatOut:
    agent = AGENTS[payload.agent]
    session = SQLiteSession(payload.session_id) if payload.session_id else None
    try:
        result = await Runner.run(agent, payload.message, session=session)
        return ChatOut(
            agent=payload.agent,
            final_agent=result.last_agent.name,
            output=str(result.final_output),
        )
    except InputGuardrailTripwireTriggered as e:
        return ChatOut(agent=payload.agent, final_agent=agent.name, output="", blocked=True, block_reason=f"input: {e}")
    except OutputGuardrailTripwireTriggered as e:
        return ChatOut(agent=payload.agent, final_agent=agent.name, output="", blocked=True, block_reason=f"output: {e}")


def serve() -> None:
    import uvicorn

    uvicorn.run("agent_trio.server:app", host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    serve()
