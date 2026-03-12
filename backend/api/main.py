import os
import dotenv
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from fastapi import Request
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from uuid import uuid4
from run_analysis import run_analysis


dotenv.load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

class ResetSession(BaseModel):
    session_id: str

@app.get("/analyze")
async def analyze(prompt: str, request: Request):
    session_id = request.session.get("session_id")
    if not session_id:
        session_id = str(uuid4())
        request.session["session_id"] = session_id    
    return StreamingResponse(run_analysis(prompt, session_id), media_type="text/event-stream")

@app.get("/reset")
async def reset(request: Request):
    request.session.clear()
    return {"message": "Session reset successfully"}
