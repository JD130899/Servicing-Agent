from fastapi import FastAPI
from pydantic import BaseModel, Field

from agent import ask_agent
from tools import get_account, get_ticket_status, create_ticket
from pathlib import Path
from fastapi.responses import FileResponse

app = FastAPI()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class TicketRequest(BaseModel):
    issue: str = Field(min_length=1, max_length=2000)


@app.post("/chat")
async def chat(request: ChatRequest):
    reply = await ask_agent(request.message)
    return {"reply": reply}


@app.get("/account")
def account():
    return get_account()


@app.get("/tickets/{ticket_id}")
def ticket_status(ticket_id: str):
    return get_ticket_status(ticket_id)


@app.post("/tickets")
def new_ticket(request: TicketRequest):
    return create_ticket(request.issue)

@app.get("/")
def home():
    return FileResponse(
        Path(__file__).resolve().parent / "index.html"
    )

@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}


@app.get("/readyz", include_in_schema=False)
async def readyz():
    import asyncio
    from fastapi import HTTPException
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection("127.0.0.1", 8002), timeout=2)
        writer.close()
        await writer.wait_closed()
    except (OSError, asyncio.TimeoutError):
        raise HTTPException(status_code=503, detail="Tools are starting")
    return {"status": "ready"}
