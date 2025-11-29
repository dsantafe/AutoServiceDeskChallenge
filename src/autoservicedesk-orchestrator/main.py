"""
API FastAPI para TechDesk Copilot
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import traceback

from orchestrator import process_request

app = FastAPI(
    title="TechDesk Copilot API",
    description="API de soporte TI multiagente",
    version="1.0.0",
)


class SupportRequest(BaseModel):
    user_request: str
    user_email: str
    thread_id: Optional[str] = None


@app.post("/support")
async def support_endpoint(payload: SupportRequest):
    """Endpoint principal de soporte"""
    try:
        result = process_request(
            user_request=payload.user_request,
            user_email=payload.user_email,
            thread_id=payload.thread_id,
        )
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
