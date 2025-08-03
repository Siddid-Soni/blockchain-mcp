"""
Slither analysis tool for blockchain vulnerability detection.
"""

import asyncio
import json
from typing import Dict, Any, Optional, List

import mcp.types as types
from .base import BaseTool


class SlitherTool(BaseTool):
    """Tool for running Slither static analysis on smart contracts."""
    
    def __init__(self):
        super().__init__("slither-analyze")
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for the Slither tool."""
        return {
            "name": self.name,
            "description": "Analyze Solidity smart contracts using Slither static analysis framework",
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
            }
        }
    
    async def analyze(self, contract_code: Optional[str] = None, contract_file: Optional[str] = None,
                     output_format: str = "json", exclude_detectors: Optional[List[str]] = None,
                     include_detectors: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run Slither analysis on a smart contract."""
        temp_file_path = None
        
        try:
            # Validate input and get contract path
            contract_path = self.validate_input(contract_code, contract_file)
            if contract_code:
                temp_file_path = contract_path

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
        finally:
            # Clean up temp file if created
            if temp_file_path:
                self.cleanup_temp_file(temp_file_path)
    
    def format_response(self, result: Dict[str, Any], analysis_id: str) -> str:
        """Format the analysis result into a human-readable response."""
        if result["success"]:
            output_format = result.get("output_format", "json")
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
            
        return response_text
