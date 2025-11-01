"""FastAPI application for Open WebUI custom function."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent import NL2SQLAgent

app = FastAPI(
    title="NL2SQL Agent API",
    description="Natural Language to SQL conversion for Open WebUI",
    version="1.0.0",
)

agent = NL2SQLAgent()


class QueryRequest(BaseModel):
    """Request model for NL2SQL query."""
    
    query: str = Field(..., description="Natural language query in Japanese or English")


class QueryResponse(BaseModel):
    """Response model for NL2SQL query."""
    
    success: bool
    output: str | None = None
    error: str | None = None
    input: str


@app.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "nl2sql-agent"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/schema")
async def get_schema() -> dict[str, str]:
    """Get database schema information."""
    try:
        schema = agent.get_schema_info()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest) -> QueryResponse:
    """Process natural language query and return SQL results."""
    result = agent.process_query(request.query)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    
    return QueryResponse(**result)


@app.post("/chat")
async def chat_endpoint(body: dict[str, Any]) -> dict[str, Any]:
    """Open WebUI compatible chat endpoint."""
    messages = body.get("messages", [])
    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    last_message = messages[-1].get("content", "")
    if not last_message:
        raise HTTPException(status_code=400, detail="Empty message")
    
    result = agent.process_query(last_message)
    
    return {
        "type": "message",
        "content": result.get("output", result.get("error", "エラーが発生しました")),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
