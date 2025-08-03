import asyncio
import subprocess
import tempfile
import os
import json
from pathlib import Path

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
from .tools import ALL_TOOLS, TOOL_PROCESSORS

# Store analysis results for resource access
analysis_results: dict[str, dict] = {}

server = Server("blockchain-vuln-analyzer")

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available analysis results as resources.
    Each analysis result is exposed as a resource with a custom analysis:// URI scheme.
    """
    return [
        types.Resource(
            uri=AnyUrl(f"analysis://internal/{analysis_id}"),
            name=f"Analysis: {analysis_id}",
            description=f"Vulnerability analysis result for {analysis_id}",
            mimeType="application/json",
        )
        for analysis_id in analysis_results
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific analysis result by its URI.
    The analysis ID is extracted from the URI path component.
    """
    if uri.scheme != "analysis":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    analysis_id = uri.path
    if analysis_id is not None:
        analysis_id = analysis_id.lstrip("/")
        if analysis_id in analysis_results:
            return json.dumps(analysis_results[analysis_id], indent=2)
    raise ValueError(f"Analysis result not found: {analysis_id}")

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts for blockchain vulnerability analysis.
    """
    return [
        types.Prompt(
            name="analyze-contract",
            description="Get analysis recommendations for a smart contract",
            arguments=[
                types.PromptArgument(
                    name="contract_type",
                    description="Type of contract (ERC20, ERC721, DeFi, etc.)",
                    required=False,
                ),
                types.PromptArgument(
                    name="focus_area",
                    description="Specific vulnerability focus (reentrancy, overflow, access control, etc.)",
                    required=False,
                )
            ],
        )
    ]

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate a prompt for blockchain vulnerability analysis.
    """
    if name != "analyze-contract":
        raise ValueError(f"Unknown prompt: {name}")

    contract_type = (arguments or {}).get("contract_type", "generic")
    focus_area = (arguments or {}).get("focus_area", "all vulnerabilities")

    return types.GetPromptResult(
        description="Analyze smart contract for vulnerabilities",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Please analyze this {contract_type} smart contract focusing on {focus_area}. "
                         f"Use the mythril-analyze and slither-analyze tools to perform comprehensive "
                         f"vulnerability analysis. Look for common issues like reentrancy attacks, "
                         f"integer overflow/underflow, access control vulnerabilities, and other "
                         f"security concerns specific to {contract_type} contracts.",
                ),
            )
        ],
    )

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available blockchain vulnerability analysis tools.
    """
    return [
        types.Tool(
            name="mythril-analyze",
            description="Analyze Solidity smart contracts using Mythril for security vulnerabilities",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_code": {
                        "type": "string",
                        "description": "The Solidity contract source code to analyze"
                    },
                    "contract_file": {
                        "type": "string", 
                        "description": "Path to the contract file (alternative to contract_code)"
                    },
                    "analysis_mode": {
                        "type": "string",
                        "enum": ["quick", "standard", "deep"],
                        "description": "Analysis depth mode",
                        "default": "standard"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum transaction depth for analysis (default: 12)",
                        "default": 12,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": [],
                "anyOf": [
                    {"required": ["contract_code"]},
                    {"required": ["contract_file"]}
                ]
            },
        ),
        types.Tool(
            name="slither-analyze", 
            description="Analyze Solidity smart contracts using Slither static analysis framework",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_code": {
                        "type": "string",
                        "description": "The Solidity contract source code to analyze"
                    },
                    "contract_file": {
                        "type": "string",
                        "description": "Path to the contract file (alternative to contract_code)"
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["text", "json", "markdown"],
                        "description": "Output format for the analysis results",
                        "default": "json"
                    },
                    "exclude_detectors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of detector names to exclude from analysis"
                    },
                    "include_detectors": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "List of specific detectors to run (if not specified, runs all)"
                    }
                },
                "required": [],
                "anyOf": [
                    {"required": ["contract_code"]},
                    {"required": ["contract_file"]}
                ]
            },
        )
    ]

async def run_mythril_analysis(contract_code: str = None, contract_file: str = None, 
                             analysis_mode: str = "standard", max_depth: int = 12) -> dict:
    """Run Mythril analysis on a smart contract."""
    try:
        # Create temporary file if contract_code is provided
        temp_file = None
        if contract_code:
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False)
            temp_file.write(contract_code)
            temp_file.close()
            contract_path = temp_file.name
        elif contract_file:
            contract_path = contract_file
            if not os.path.exists(contract_path):
                raise ValueError(f"Contract file not found: {contract_path}")
        else:
            raise ValueError("Either contract_code or contract_file must be provided")

        # Build mythril command
        cmd = ["myth", "analyze", contract_path, "-o", "json"]
        
        # Add analysis mode settings
        if analysis_mode == "quick":
            cmd.extend(["--max-depth", "3"])
        elif analysis_mode == "deep":
            cmd.extend(["--max-depth", str(min(max_depth * 2, 50))])
        else:  # standard
            cmd.extend(["--max-depth", str(max_depth)])

        # Run mythril
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # Clean up temp file
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            return {
                "success": False,
                "error": f"Mythril analysis failed: {error_msg}",
                "tool": "mythril"
            }
        
        # Parse JSON output
        try:
            result = json.loads(stdout.decode())
            return {
                "success": True,
                "tool": "mythril",
                "analysis_mode": analysis_mode,
                "max_depth": max_depth,
                "vulnerabilities": result.get("issues", []),
                "raw_output": result
            }
        except json.JSONDecodeError:
            # If JSON parsing fails, return raw output
            return {
                "success": True,
                "tool": "mythril", 
                "analysis_mode": analysis_mode,
                "max_depth": max_depth,
                "raw_output": stdout.decode(),
                "note": "Could not parse JSON output, showing raw results"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Mythril analysis error: {str(e)}",
            "tool": "mythril"
        }


async def run_slither_analysis(contract_code: str = None, contract_file: str = None,
                             output_format: str = "json", exclude_detectors: list = None,
                             include_detectors: list = None) -> dict:
    """Run Slither analysis on a smart contract."""
    try:
        # Create temporary file if contract_code is provided
        temp_file = None
        if contract_code:
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False)
            temp_file.write(contract_code)
            temp_file.close()
            contract_path = temp_file.name
        elif contract_file:
            contract_path = contract_file
            if not os.path.exists(contract_path):
                raise ValueError(f"Contract file not found: {contract_path}")
        else:
            raise ValueError("Either contract_code or contract_file must be provided")

        # Build slither command
        cmd = ["slither", contract_path]
        
        # Add output format
        if output_format == "json":
            cmd.extend(["--json", "-"])
        
        # Add detector filters
        if exclude_detectors:
            cmd.extend(["--exclude", ",".join(exclude_detectors)])
        if include_detectors:
            cmd.extend(["--include", ",".join(include_detectors)])

        # Run slither
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # Clean up temp file
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        
        # Slither may return non-zero exit code even on successful analysis with findings
        output = stdout.decode() if stdout else ""
        error_output = stderr.decode() if stderr else ""
        
        if output_format == "json" and output:
            try:
                result = json.loads(output)
                return {
                    "success": True,
                    "tool": "slither",
                    "output_format": output_format,
                    "results": result.get("results", {}),
                    "detector_info": result.get("detectors", []),
                    "raw_output": result
                }
            except json.JSONDecodeError:
                pass
        
        # Return text output or handle errors
        if not output and error_output:
            return {
                "success": False,
                "error": f"Slither analysis failed: {error_output}",
                "tool": "slither"
            }
        
        return {
            "success": True,
            "tool": "slither",
            "output_format": output_format,
            "raw_output": output,
            "stderr": error_output if error_output else None
        }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Slither analysis error: {str(e)}",
            "tool": "slither"
        }


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests for blockchain vulnerability analysis.
    """
    if not arguments:
        arguments = {}

    if name == "mythril-analyze":
        # Extract arguments
        contract_code = arguments.get("contract_code")
        contract_file = arguments.get("contract_file") 
        analysis_mode = arguments.get("analysis_mode", "standard")
        max_depth = arguments.get("max_depth", 12)
        
        # Run analysis
        result = await run_mythril_analysis(
            contract_code=contract_code,
            contract_file=contract_file,
            analysis_mode=analysis_mode,
            max_depth=max_depth
        )
        
        # Store result for resource access
        analysis_id = f"mythril_{len(analysis_results)}"
        analysis_results[analysis_id] = result
        
        # Notify clients of new resource
        await server.request_context.session.send_resource_list_changed()
        
        # Format response
        if result["success"]:
            vulnerabilities = result.get("vulnerabilities", [])
            summary = f"Mythril analysis completed. Found {len(vulnerabilities)} potential issues."
            
            response_text = f"{summary}\n\nAnalysis ID: {analysis_id}\n"
            if vulnerabilities:
                response_text += "\nVulnerabilities found:\n"
                for i, vuln in enumerate(vulnerabilities[:5]):  # Show first 5
                    response_text += f"{i+1}. {vuln.get('title', 'Unknown')}: {vuln.get('description', 'No description')}\n"
                if len(vulnerabilities) > 5:
                    response_text += f"... and {len(vulnerabilities) - 5} more. See full results in analysis resource."
            else:
                response_text += "\nNo vulnerabilities detected."
        else:
            response_text = f"Mythril analysis failed: {result['error']}"
        
        return [types.TextContent(type="text", text=response_text)]
        
    elif name == "slither-analyze":
        # Extract arguments
        contract_code = arguments.get("contract_code")
        contract_file = arguments.get("contract_file")
        output_format = arguments.get("output_format", "json")
        exclude_detectors = arguments.get("exclude_detectors", [])
        include_detectors = arguments.get("include_detectors", [])
        
        # Run analysis
        result = await run_slither_analysis(
            contract_code=contract_code,
            contract_file=contract_file,
            output_format=output_format,
            exclude_detectors=exclude_detectors,
            include_detectors=include_detectors
        )
        
        # Store result for resource access  
        analysis_id = f"slither_{len(analysis_results)}"
        analysis_results[analysis_id] = result
        
        # Notify clients of new resource
        await server.request_context.session.send_resource_list_changed()
        
        # Format response
        if result["success"]:
            if output_format == "json" and "results" in result:
                detectors = result.get("results", {}).get("detectors", [])
                summary = f"Slither analysis completed. Found {len(detectors)} detector results."
                
                response_text = f"{summary}\n\nAnalysis ID: {analysis_id}\n"
                if detectors:
                    response_text += "\nDetector results:\n"
                    for i, detector in enumerate(detectors[:5]):  # Show first 5
                        response_text += f"{i+1}. {detector.get('check', 'Unknown')}: {len(detector.get('elements', []))} issues\n"
                    if len(detectors) > 5:
                        response_text += f"... and {len(detectors) - 5} more detectors. See full results in analysis resource."
                else:
                    response_text += "\nNo issues detected."
            else:
                response_text = f"Slither analysis completed.\n\nAnalysis ID: {analysis_id}\nSee full results in analysis resource."
        else:
            response_text = f"Slither analysis failed: {result['error']}"
            
        return [types.TextContent(type="text", text=response_text)]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="blockchain-vuln-analyzer",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())