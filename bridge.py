import os, json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.client.stdio import connect_stdio, StdioServerParameters
from mcp.client.session import ClientSession

# Where server.py lives (repo root)
MCP_DIR = os.environ.get("MCP_DIR", ".")
# We’ll run the MCP server with plain Python (no uv needed)
SERVER_CMD = os.environ.get("SERVER_CMD", "python")
SERVER_ARGS = os.environ.get("SERVER_ARGS", f"{MCP_DIR}/server.py").split()

app = FastAPI()
_session: ClientSession | None = None
_disconnect = None

@app.on_event("startup")
async def startup():
    global _session, _disconnect
    params = StdioServerParameters(command=SERVER_CMD, args=SERVER_ARGS)
    _session, _disconnect = await connect_stdio(params)

@app.on_event("shutdown")
async def shutdown():
    if _disconnect: await _disconnect()

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.post("/rpc")
async def rpc(req: Request):
    try:
        payload = await req.json()
    except Exception:
        return JSONResponse({"error":"invalid_json"}, status_code=400)

    method = payload.get("method")
    params = payload.get("params") or {}
    if not method:
        return JSONResponse({"error":"missing_method"}, status_code=400)

    # JSON-RPC → MCP
    if method == "tools/list":
        tools = await _session.list_tools()
        return JSONResponse({"result":{"tools":[t.model_dump() for t in tools]}})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if not name:
            return JSONResponse({"error":"missing_tool_name"}, status_code=400)
        out = await _session.call_tool(name, args)
        return JSONResponse({"result": out})

    # Convenience: treat any other method name as a tool
    out = await _session.call_tool(method, params)
    return JSONResponse({"result": out})
