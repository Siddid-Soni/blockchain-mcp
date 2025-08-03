import asyncio
import json
from pathlib import Path

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

from .tools import ToolManager

# Store analysis results for resource access
analysis_results: dict[str, dict] = {}

server = Server("blockchain-vuln-analyzer")
tool_manager = ToolManager()

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
                         f"Use the mythril-analyze, slither-analyze, and echidna-analyze tools to perform comprehensive "
                         f"vulnerability analysis. Look for common issues like reentrancy attacks, "
                         f"integer overflow/underflow, access control vulnerabilities, and other "
                         f"security concerns specific to {contract_type} contracts. Use Echidna for "
                         f"property-based testing to find edge cases and test contract invariants.",
                ),
            )
        ],
    )

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available blockchain vulnerability analysis tools.
    """
    return tool_manager.get_tool_schemas()


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests for blockchain vulnerability analysis.
    """
    if not arguments:
        arguments = {}

    try:
        # Run analysis using tool manager
        result = await tool_manager.execute_tool(name, arguments)
        
        # Store result for resource access
        analysis_id = f"{name.replace('-', '_')}_{len(analysis_results)}"
        analysis_results[analysis_id] = result
        
        # Notify clients of new resource (only if server context is available)
        try:
            await server.request_context.session.send_resource_list_changed()
        except:
            pass  # Ignore if not in server context (e.g., during testing)
        
        # Format response using tool manager
        response_text = tool_manager.format_tool_response(name, result, analysis_id)
        
        return [types.TextContent(type="text", text=response_text)]
        
    except Exception as e:
        error_msg = f"Tool execution failed: {str(e)}"
        return [types.TextContent(type="text", text=error_msg)]

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