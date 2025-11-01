"""Pipelines server for Open WebUI - NL2SQL Agent."""

from __future__ import annotations

from typing import Iterator, Generator, Union
from pydantic import BaseModel

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent import NL2SQLAgent


app = FastAPI(
    title="NL2SQL Pipelines",
    description="Natural Language to SQL Pipelines for Open WebUI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Pipeline:
    """NL2SQL Pipeline for Open WebUI."""

    class Valves(BaseModel):
        """Configuration valves."""
        pass

    def __init__(self):
        self.type = "pipe"
        self.id = "nl2sql_agent"
        self.name = "NL2SQL Database Query Agent"
        self.valves = self.Valves()
        self.agent = NL2SQLAgent()

    async def on_startup(self):
        print(f"on_startup: {__name__}")

    async def on_shutdown(self):
        print(f"on_shutdown: {__name__}")

    def pipe(
        self, user_message: str, model_id: str, messages: list[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """Process natural language query."""
        print(f"pipe: {__name__}")
        print(f"user_message: {user_message}")

        try:
            result = self.agent.process_query(user_message)

            if result["success"]:
                return result["output"]
            else:
                return f"エラー: {result.get('error', '不明なエラー')}"
        except Exception as e:
            return f"エラー: {str(e)}"


# Global pipeline instance
pipeline = Pipeline()

# Pipelines API endpoints
@app.get("/")
@app.get("/v1")
async def get_status():
    """Health check."""
    return {"status": True}


@app.get("/pipelines")
@app.get("/v1/pipelines")
async def list_pipelines():
    """List available pipelines."""
    return {
        "data": [
            {
                "id": pipeline.id,
                "name": pipeline.name,
                "type": pipeline.type,
                "valves": True if hasattr(pipeline, "valves") else False,
            }
        ]
    }


@app.post("/{pipeline_id}/pipe")
@app.post("/v1/{pipeline_id}/pipe")
async def pipe_endpoint(pipeline_id: str, body: dict):
    """Main pipeline endpoint."""
    if pipeline_id != pipeline.id:
        return {"error": f"Pipeline {pipeline_id} not found"}

    user_message = body.get("user_message", "")
    model_id = body.get("model_id", "")
    messages = body.get("messages", [])

    result = pipeline.pipe(user_message, model_id, messages, body)
    return {"response": result}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
