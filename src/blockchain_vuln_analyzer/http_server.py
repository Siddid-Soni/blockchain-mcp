import asyncio
import json
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from .tools import ALL_TOOLS, TOOL_PROCESSORS
from .server import analysis_results

app = FastAPI(
    title="Blockchain Vulnerability Analyzer",
    description="HTTP API for blockchain smart contract vulnerability analysis",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class AnalysisRequest(BaseModel):
    contract_code: str = None
    contract_file: str = None
    tool: str
    options: Dict[str, Any] = {}

class AnalysisResponse(BaseModel):
    analysis_id: str
    tool: str
    status: str
    result: Dict[str, Any] = None
    error: str = None

class StreamChunk(BaseModel):
    type: str  # "progress", "result", "error", "complete"
    data: Dict[str, Any]

@app.get("/")
async def root():
    return {"message": "Blockchain Vulnerability Analyzer HTTP Server", "version": "0.1.0"}

@app.get("/tools")
async def list_tools():
    """List all available analysis tools."""
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            for tool in ALL_TOOLS
        ]
    }

@app.post("/analyze")
async def analyze_contract(request: AnalysisRequest):
    """Run a single analysis tool on a contract."""
    if request.tool not in TOOL_PROCESSORS:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool}")
    
    try:
        # Prepare arguments
        arguments = {
            "contract_code": request.contract_code,
            "contract_file": request.contract_file,
            **request.options
        }
        
        # Get tool processor
        tool_processor = TOOL_PROCESSORS[request.tool]
        
        # Run analysis
        result, formatter = await tool_processor.process(arguments)
        
        # Store result
        tool_name_prefix = request.tool.split("-")[0]
        analysis_id = f"{tool_name_prefix}_{len(analysis_results)}"
        analysis_results[analysis_id] = result
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            tool=request.tool,
            status="completed" if result.get("success") else "failed",
            result=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/stream")
async def analyze_contract_stream(request: AnalysisRequest):
    """Run analysis with streaming response."""
    if request.tool not in TOOL_PROCESSORS:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool}")
    
    async def generate_stream():
        try:
            # Send initial progress
            yield f"data: {json.dumps({'type': 'progress', 'data': {'status': 'starting', 'tool': request.tool}})}\n\n"
            
            # Prepare arguments
            arguments = {
                "contract_code": request.contract_code,
                "contract_file": request.contract_file,
                **request.options
            }
            
            # Send progress update
            yield f"data: {json.dumps({'type': 'progress', 'data': {'status': 'running', 'message': f'Running {request.tool} analysis...'}})}\n\n"
            
            # Get tool processor and run analysis
            tool_processor = TOOL_PROCESSORS[request.tool]
            result, formatter = await tool_processor.process(arguments)
            
            # Store result
            tool_name_prefix = request.tool.split("-")[0]
            analysis_id = f"{tool_name_prefix}_{len(analysis_results)}"
            analysis_results[analysis_id] = result
            
            # Send result
            yield f"data: {json.dumps({'type': 'result', 'data': {'analysis_id': analysis_id, 'result': result}})}\n\n"
            
            # Send completion
            yield f"data: {json.dumps({'type': 'complete', 'data': {'analysis_id': analysis_id, 'status': 'completed'}})}\n\n"
            
        except Exception as e:
            # Send error
            yield f"data: {json.dumps({'type': 'error', 'data': {'error': str(e)}})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/analyze/batch")
async def analyze_batch(request: Dict[str, Any]):
    """Run multiple analysis tools on a contract."""
    contract_code = request.get("contract_code")
    contract_file = request.get("contract_file")
    tools = request.get("tools", ["slither-analyze", "mythril-analyze"])
    
    results = {}
    
    for tool_name in tools:
        if tool_name not in TOOL_PROCESSORS:
            results[tool_name] = {"error": f"Unknown tool: {tool_name}"}
            continue
            
        try:
            arguments = {
                "contract_code": contract_code,
                "contract_file": contract_file,
                **request.get("options", {}).get(tool_name, {})
            }
            
            tool_processor = TOOL_PROCESSORS[tool_name]
            result, formatter = await tool_processor.process(arguments)
            
            tool_name_prefix = tool_name.split("-")[0]
            analysis_id = f"{tool_name_prefix}_{len(analysis_results)}"
            analysis_results[analysis_id] = result
            
            results[tool_name] = {
                "analysis_id": analysis_id,
                "status": "completed" if result.get("success") else "failed",
                "result": result
            }
            
        except Exception as e:
            results[tool_name] = {"error": str(e)}
    
    return {"results": results}

@app.post("/analyze/batch/stream")
async def analyze_batch_stream(request: Dict[str, Any]):
    """Run multiple analysis tools with streaming response."""
    contract_code = request.get("contract_code")
    contract_file = request.get("contract_file")
    tools = request.get("tools", ["slither-analyze", "mythril-analyze"])
    
    async def generate_batch_stream():
        try:
            yield f"data: {json.dumps({'type': 'progress', 'data': {'status': 'starting', 'total_tools': len(tools)}})}\n\n"
            
            results = {}
            
            for i, tool_name in enumerate(tools):
                yield f"data: {json.dumps({'type': 'progress', 'data': {'status': 'running', 'current_tool': tool_name, 'progress': i + 1, 'total': len(tools)}})}\n\n"
                
                if tool_name not in TOOL_PROCESSORS:
                    results[tool_name] = {"error": f"Unknown tool: {tool_name}"}
                    yield f"data: {json.dumps({'type': 'tool_error', 'data': {'tool': tool_name, 'error': f'Unknown tool: {tool_name}'}})}\n\n"
                    continue
                
                try:
                    arguments = {
                        "contract_code": contract_code,
                        "contract_file": contract_file,
                        **request.get("options", {}).get(tool_name, {})
                    }
                    
                    tool_processor = TOOL_PROCESSORS[tool_name]
                    result, formatter = await tool_processor.process(arguments)
                    
                    tool_name_prefix = tool_name.split("-")[0]
                    analysis_id = f"{tool_name_prefix}_{len(analysis_results)}"
                    analysis_results[analysis_id] = result
                    
                    tool_result = {
                        "analysis_id": analysis_id,
                        "status": "completed" if result.get("success") else "failed",
                        "result": result
                    }
                    results[tool_name] = tool_result
                    
                    yield f"data: {json.dumps({'type': 'tool_result', 'data': {'tool': tool_name, **tool_result}})}\n\n"
                    
                except Exception as e:
                    results[tool_name] = {"error": str(e)}
                    yield f"data: {json.dumps({'type': 'tool_error', 'data': {'tool': tool_name, 'error': str(e)}})}\n\n"
            
            yield f"data: {json.dumps({'type': 'complete', 'data': {'results': results}})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': {'error': str(e)}})}\n\n"
    
    return StreamingResponse(
        generate_batch_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/results/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """Get stored analysis result by ID."""
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    return {
        "analysis_id": analysis_id,
        "result": analysis_results[analysis_id]
    }

@app.get("/results")
async def list_analysis_results():
    """List all stored analysis results."""
    return {
        "results": [
            {
                "analysis_id": aid,
                "tool": result.get("tool", "unknown"),
                "success": result.get("success", False),
                "timestamp": result.get("timestamp")
            }
            for aid, result in analysis_results.items()
        ]
    }

async def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the HTTP server."""
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(start_server())