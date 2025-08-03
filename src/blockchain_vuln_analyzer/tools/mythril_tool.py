"""
Mythril analysis tool for blockchain vulnerability detection.
"""

import asyncio
import json
from typing import Dict, Any, Optional

import mcp.types as types
from .base import BaseTool


class MythrilTool(BaseTool):
    """Tool for running Mythril security analysis on smart contracts."""
    
    def __init__(self):
        super().__init__("mythril-analyze")
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for the Mythril tool."""
        return {
            "name": self.name,
            "description": "Analyze Solidity smart contracts using Mythril for security vulnerabilities",
            "inputSchema": {
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
            }
        }
    
    async def analyze(self, contract_code: Optional[str] = None, contract_file: Optional[str] = None, 
                     analysis_mode: str = "standard", max_depth: int = 12) -> Dict[str, Any]:
        """Run Mythril analysis on a smart contract."""
        temp_file_path = None
        
        try:
            # Validate input and get contract path
            contract_path = self.validate_input(contract_code, contract_file)
            if contract_code:
                temp_file_path = contract_path

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
            
            # Parse JSON output - Mythril returns non-zero exit code even on successful analysis
            stdout_text = stdout.decode() if stdout else ""
            stderr_text = stderr.decode() if stderr else ""
            
            if stdout_text:
                try:
                    result = json.loads(stdout_text)
                    return {
                        "success": True,
                        "tool": "mythril",
                        "analysis_mode": analysis_mode,
                        "max_depth": max_depth,
                        "vulnerabilities": result.get("issues", []),
                        "raw_output": result
                    }
                except json.JSONDecodeError:
                    # If JSON parsing fails but we have output, return it as raw
                    return {
                        "success": True,
                        "tool": "mythril", 
                        "analysis_mode": analysis_mode,
                        "max_depth": max_depth,
                        "raw_output": stdout_text,
                        "note": "Could not parse JSON output, showing raw results"
                    }
            
            # Only treat as error if no stdout and non-zero return code
            if process.returncode != 0:
                error_msg = stderr_text if stderr_text else "Unknown error"
                return {
                    "success": False,
                    "error": f"Mythril analysis failed: {error_msg}",
                    "tool": "mythril"
                }
                
        except Exception as e:
            print(f"Error running Mythril analysis: {e}")
            return {
                "success": False,
                "error": f"Mythril analysis error: {str(e)}",
                "tool": "mythril"
            }
        finally:
            # Clean up temp file if created
            if temp_file_path:
                self.cleanup_temp_file(temp_file_path)
    
    def format_response(self, result: Dict[str, Any], analysis_id: str) -> str:
        """Format the analysis result into a human-readable response."""
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
        
        return response_text
