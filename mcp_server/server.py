"""Simple MCP-compatible HTTP server for DuckDB queries."""

from __future__ import annotations

import json
import os
from typing import Any

import duckdb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

DB_PATH = os.getenv("MCP_DB_PATH", "/app/data/ecommerce.db")
READ_ONLY = os.getenv("MCP_READ_ONLY", "true").lower() == "true"


class MCPRequest(BaseModel):
    """MCP JSON-RPC request."""
    jsonrpc: str
    id: int
    method: str
    params: dict[str, Any]


class MCPResponse(BaseModel):
    """MCP JSON-RPC response."""
    jsonrpc: str
    id: int
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest) -> MCPResponse:
    """Handle MCP tool call requests."""
    if request.method != "tools/call":
        return MCPResponse(
            jsonrpc="2.0",
            id=request.id,
            error={"code": -32601, "message": "Method not found"}
        )

    tool_name = request.params.get("name")
    arguments = request.params.get("arguments", {})

    if tool_name == "query":
        return await execute_query(request.id, arguments)

    return MCPResponse(
        jsonrpc="2.0",
        id=request.id,
        error={"code": -32602, "message": f"Unknown tool: {tool_name}"}
    )


async def execute_query(request_id: int, arguments: dict[str, Any]) -> MCPResponse:
    """Execute SQL query against DuckDB."""
    query = arguments.get("query")

    if not query:
        return MCPResponse(
            jsonrpc="2.0",
            id=request_id,
            error={"code": -32602, "message": "Missing 'query' parameter"}
        )

    try:
        conn = duckdb.connect(DB_PATH, read_only=READ_ONLY)
        result = conn.execute(query).fetchall()
        columns = [desc[0] for desc in conn.description] if conn.description else []
        conn.close()

        rows = []
        for row in result:
            row_dict = {}
            for i, col_name in enumerate(columns):
                row_dict[col_name] = row[i]
            rows.append(row_dict)

        result_json = json.dumps(rows)

        return MCPResponse(
            jsonrpc="2.0",
            id=request_id,
            result={
                "content": [
                    {
                        "type": "text",
                        "text": result_json
                    }
                ]
            }
        )

    except Exception as e:
        return MCPResponse(
            jsonrpc="2.0",
            id=request_id,
            error={"code": -32000, "message": f"Query execution failed: {str(e)}"}
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "db_path": DB_PATH, "read_only": READ_ONLY}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
