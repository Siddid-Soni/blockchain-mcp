"""
Echidna analysis tool for blockchain property-based testing.
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional, List

import mcp.types as types
from .base import BaseTool


class EchidnaTool(BaseTool):
    """Tool for running Echidna property-based testing on smart contracts."""
    
    def __init__(self):
        super().__init__("echidna-analyze")
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for the Echidna tool."""
        return {
            "name": self.name,
            "description": "Analyze Solidity smart contracts using Echidna property-based testing framework",
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
                    "contract_name": {
                        "type": "string",
                        "description": "Specific contract name to analyze (if multiple contracts in file)"
                    },
                    "test_mode": {
                        "type": "string",
                        "enum": ["property", "assertion", "dapptest", "optimization", "overflow", "exploration"],
                        "description": "Test mode to use for analysis",
                        "default": "assertion"
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["json", "text", "none"],
                        "description": "Output format for analysis results",
                        "default": "text"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds for the analysis",
                        "default": 60,
                        "minimum": 10,
                        "maximum": 3600
                    },
                    "test_limit": {
                        "type": "integer",
                        "description": "Number of sequences of transactions to generate during testing",
                        "default": 50000,
                        "minimum": 100,
                        "maximum": 1000000
                    },
                    "seq_len": {
                        "type": "integer",
                        "description": "Number of transactions to generate during testing",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000
                    },
                    "workers": {
                        "type": "integer",
                        "description": "Number of workers to run",
                        "default": 1,
                        "minimum": 1,
                        "maximum": 8
                    },
                    "seed": {
                        "type": "integer",
                        "description": "Specific seed for reproducible results"
                    },
                    "disable_slither": {
                        "type": "boolean",
                        "description": "Disable running Slither integration",
                        "default": False
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
                     contract_name: Optional[str] = None, test_mode: str = "assertion",
                     output_format: str = "text", timeout: int = 60, test_limit: int = 50000,
                     seq_len: int = 100, workers: int = 1, seed: Optional[int] = None,
                     disable_slither: bool = False) -> Dict[str, Any]:
        """Run Echidna property-based testing on a smart contract."""
        temp_file_path = None
        
        try:
            # Validate input and get contract path
            contract_path = self.validate_input(contract_code, contract_file)
            if contract_code:
                temp_file_path = contract_path

            # Build echidna command
            cmd = ["echidna", contract_path]
            
            # Add contract name if specified
            if contract_name:
                cmd.extend(["--contract", contract_name])
            
            # Add output format
            cmd.extend(["--format", output_format])
            
            # Add test mode
            cmd.extend(["--test-mode", test_mode])
            
            # Add timeout
            cmd.extend(["--timeout", str(timeout)])
            
            # Add test limit
            cmd.extend(["--test-limit", str(test_limit)])
            
            # Add sequence length
            cmd.extend(["--seq-len", str(seq_len)])
            
            # Add workers
            cmd.extend(["--workers", str(workers)])
            
            # Add seed if specified
            if seed is not None:
                cmd.extend(["--seed", str(seed)])
            
            # Disable slither if requested
            if disable_slither:
                cmd.append("--disable-slither")

            # Set up environment to ensure crytic-compile is found
            env = os.environ.copy()
            # Add common paths where crytic-compile might be installed
            additional_paths = [
                "/opt/homebrew/bin",
                "/usr/local/bin",
                "/usr/bin"
            ]
            current_path = env.get("PATH", "")
            for path in additional_paths:
                if path not in current_path:
                    current_path = f"{path}:{current_path}"
            env["PATH"] = current_path

            # Run echidna
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            stdout, stderr = await process.communicate()
            
            # Parse output
            output = stdout.decode() if stdout else ""
            error_output = stderr.decode() if stderr else ""
            
            if output_format == "json" and output:
                try:
                    result = json.loads(output)
                    return {
                        "success": True,
                        "tool": "echidna",
                        "test_mode": test_mode,
                        "output_format": output_format,
                        "timeout": timeout,
                        "test_limit": test_limit,
                        "seq_len": seq_len,
                        "workers": workers,
                        "seed": seed,
                        "results": result,
                        "raw_output": result
                    }
                except json.JSONDecodeError:
                    # If JSON parsing fails, treat as text output
                    pass
            
            # Handle text/non-JSON output or parsing errors
            if process.returncode == 0 or output:
                return {
                    "success": True,
                    "tool": "echidna",
                    "test_mode": test_mode,
                    "output_format": output_format,
                    "timeout": timeout,
                    "test_limit": test_limit,
                    "seq_len": seq_len,
                    "workers": workers,
                    "seed": seed,
                    "raw_output": output,
                    "stderr": error_output if error_output else None
                }
            
            # Handle errors
            return {
                "success": False,
                "error": f"Echidna analysis failed: {error_output or 'Unknown error'}",
                "tool": "echidna",
                "exit_code": process.returncode
            }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Echidna analysis error: {str(e)}",
                "tool": "echidna"
            }
        finally:
            # Clean up temp file if created
            if temp_file_path:
                self.cleanup_temp_file(temp_file_path)
    
    def format_response(self, result: Dict[str, Any], analysis_id: str) -> str:
        """Format the analysis result into a human-readable response."""
        if result["success"]:
            test_mode = result.get("test_mode", "assertion")
            timeout = result.get("timeout", "unknown")
            test_limit = result.get("test_limit", "unknown")
            output_format = result.get("output_format", "text")
            
            summary = f"Echidna {test_mode} testing completed"
            
            response_text = f"{summary}\n\nAnalysis ID: {analysis_id}\n"
            response_text += f"Test Mode: {test_mode}\n"
            response_text += f"Output Format: {output_format}\n"
            response_text += f"Timeout: {timeout}s\n"
            response_text += f"Test Limit: {test_limit}\n"
            
            # Handle text output format (most common for assertion mode)
            if output_format == "text" and "raw_output" in result:
                raw_output = result["raw_output"]
                if isinstance(raw_output, str) and raw_output.strip():
                    response_text += "\nTest Results:\n"
                    # Look for key patterns in text output
                    lines = raw_output.split('\n')
                    failed_assertions = []
                    passed_assertions = []
                    
                    for line in lines:
                        if "failed!" in line.lower() or "falsified!" in line.lower():
                            failed_assertions.append(line.strip())
                        elif "passed" in line.lower() and ("test" in line.lower() or "assertion" in line.lower()):
                            passed_assertions.append(line.strip())
                    
                    if failed_assertions:
                        response_text += f"\n❌ Failed Assertions ({len(failed_assertions)}):\n"
                        for failure in failed_assertions[:3]:  # Show first 3
                            response_text += f"  • {failure}\n"
                        if len(failed_assertions) > 3:
                            response_text += f"  • ... and {len(failed_assertions) - 3} more failures\n"
                    
                    if passed_assertions:
                        response_text += f"\n✅ Passed Assertions ({len(passed_assertions)}):\n"
                        for success in passed_assertions[:3]:  # Show first 3
                            response_text += f"  • {success}\n"
                        if len(passed_assertions) > 3:
                            response_text += f"  • ... and {len(passed_assertions) - 3} more passes\n"
                    
                    if not failed_assertions and not passed_assertions:
                        response_text += "\nRaw Output Preview:\n"
                        preview = raw_output[:500] + "..." if len(raw_output) > 500 else raw_output
                        response_text += f"{preview}\n"
                else:
                    response_text += "\nNo detailed output available.\n"
            
            # Handle JSON output format
            elif output_format == "json" and "results" in result and isinstance(result["results"], dict):
                results_data = result["results"]
                
                # Look for common Echidna result patterns
                if "passed" in results_data:
                    passed = results_data["passed"]
                    response_text += f"\nTests Passed: {passed}\n"
                
                if "failed" in results_data:
                    failed = results_data["failed"]
                    response_text += f"Tests Failed: {failed}\n"
                
                if "coverage" in results_data:
                    coverage = results_data["coverage"]
                    response_text += f"Coverage: {coverage}\n"
                
                if "properties" in results_data:
                    properties = results_data["properties"]
                    response_text += f"\nProperty Results:\n"
                    for prop_name, prop_result in properties.items():
                        status = prop_result.get("status", "unknown")
                        response_text += f"  - {prop_name}: {status}\n"
            
            response_text += "\nSee full results in analysis resource for detailed information."
        else:
            response_text = f"Echidna analysis failed: {result['error']}"
            if "exit_code" in result:
                response_text += f" (exit code: {result['exit_code']})"
            
        return response_text
