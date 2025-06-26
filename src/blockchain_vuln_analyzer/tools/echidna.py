import asyncio
import json
import os
import tempfile
import mcp.types as types

ECHIDNA_TOOL_DEFINITION = types.Tool(
    name="echidna-analyze",
    description="Fuzz smart contracts for property violations using Echidna",
    inputSchema={
        "type": "object",
        "properties": {
            "contract_code": {
                "type": "string",
                "description": "The Solidity contract source code to fuzz"
            },
            "contract_file": {
                "type": "string",
                "description": "Path to the contract file (alternative to contract_code)"
            },
            "config_file": {
                "type": "string",
                "description": "Path to an Echidna YAML config file (optional)"
            },
            "testMode": {
                "type": "string",
                "enum": ["property", "assertion", "optimization", "overflow", "exploration"],
                "description": "Echidna test mode (property, assertion, etc.)",
                "default": "property"
            },
            "testLimit": {
                "type": "integer",
                "description": "Number of transactions to generate during testing (default: 50000)",
                "default": 50000
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout for the fuzzing campaign in seconds (optional)"
            },
            "output_format": {
                "type": "string",
                "enum": ["json", "text"],
                "description": "Output format for the analysis results",
                "default": "json"
            }
        },
        "required": [],
        "anyOf": [
            {"required": ["contract_code"]},
            {"required": ["contract_file"]}
        ]
    },
)

async def run_echidna_analysis(
    contract_code: str = None,
    contract_file: str = None,
    config_file: str = None,
    testMode: str = "property",
    testLimit: int = 50000,
    timeout: int = None,
    output_format: str = "json"
) -> dict:
    """Run Echidna fuzzing analysis on a smart contract."""
    try:
        temp_file = None
        contract_path = None
        if contract_code:
            temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".sol", delete=False)
            temp_file.write(contract_code)
            temp_file.close()
            contract_path = temp_file.name
        elif contract_file:
            contract_path = contract_file
            if not os.path.exists(contract_path):
                raise ValueError(f"Contract file not found: {contract_path}")
        else:
            raise ValueError("Either contract_code or contract_file must be provided")

        # Build Echidna command
        cmd = ["echidna", contract_path]
        if config_file:
            cmd.extend(["--config", config_file])
        if testMode:
            cmd.extend(["--test-mode", testMode])
        if testLimit:
            cmd.extend(["--test-limit", str(testLimit)])
        if timeout:
            cmd.extend(["--timeout", str(timeout)])
        if output_format:
            cmd.extend(["--format", output_format])
        else:
            cmd.extend(["--format", "json"])

        # Run Echidna
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
                "error": f"Echidna analysis failed: {error_msg}",
                "tool": "echidna"
            }

        # Parse output
        if output_format == "json":
            try:
                result = json.loads(stdout.decode())
                return {
                    "success": True,
                    "tool": "echidna",
                    "testMode": testMode,
                    "testLimit": testLimit,
                    "timeout": timeout,
                    "results": result,
                    "raw_output": result
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "tool": "echidna",
                    "testMode": testMode,
                    "testLimit": testLimit,
                    "timeout": timeout,
                    "raw_output": stdout.decode(),
                    "note": "Could not parse JSON output, showing raw results"
                }
        else:
            return {
                "success": True,
                "tool": "echidna",
                "testMode": testMode,
                "testLimit": testLimit,
                "timeout": timeout,
                "raw_output": stdout.decode()
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Echidna analysis error: {str(e)}",
            "tool": "echidna"
        }

def format_echidna_response(result: dict, analysis_id: str) -> str:
    if result["success"]:
        if "results" in result and isinstance(result["results"], dict):
            tests = result["results"].get("tests", [])
            failed = [t for t in tests if t.get("status") == "error"]
            summary = f"Echidna fuzzing completed. {len(failed)} property violations found." if failed else "Echidna fuzzing completed. No property violations found."
            response_text = f"{summary}\n\nAnalysis ID: {analysis_id}\n"
            if failed:
                response_text += "\nFailed properties:\n"
                for i, test in enumerate(failed[:5]):
                    response_text += f"{i+1}. {test.get('name', 'Unknown')}: {test.get('error', 'No error message')}\n"
                if len(failed) > 5:
                    response_text += f"... and {len(failed) - 5} more. See full results in analysis resource."
            else:
                response_text += "\nNo property violations detected."
        else:
            response_text = f"Echidna fuzzing completed.\n\nAnalysis ID: {analysis_id}\nSee full results in analysis resource."
    else:
        response_text = f"Echidna analysis failed: {result['error']}"
    return response_text
