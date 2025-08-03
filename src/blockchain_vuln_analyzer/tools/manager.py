"""
Tool manager for coordinating blockchain vulnerability analysis tools.
"""

from typing import Dict, Any, List
import mcp.types as types

from .mythril_tool import MythrilTool
from .slither_tool import SlitherTool
from .echidna_tool import EchidnaTool


class ToolManager:
    """Manages all blockchain vulnerability analysis tools."""
    
    def __init__(self):
        self.tools = {
            "mythril-analyze": MythrilTool(),
            "slither-analyze": SlitherTool(),
            "echidna-analyze": EchidnaTool()
        }
    
    def get_tool_schemas(self) -> List[types.Tool]:
        """Get all tool schemas for MCP server registration."""
        tool_schemas = []
        
        for tool in self.tools.values():
            schema = tool.get_tool_schema()
            tool_schemas.append(
                types.Tool(
                    name=schema["name"],
                    description=schema["description"],
                    inputSchema=schema["inputSchema"]
                )
            )
        
        return tool_schemas
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with the given arguments."""
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        
        tool = self.tools[name]
        return await tool.analyze(**arguments)
    
    def format_tool_response(self, name: str, result: Dict[str, Any], analysis_id: str) -> str:
        """Format tool response for display."""
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        
        tool = self.tools[name]
        return tool.format_response(result, analysis_id)
