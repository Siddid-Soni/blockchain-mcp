import asyncio
import json
import os
import tempfile
import mcp.types as types

MAIAN_ANALYSIS_TYPES = {
    "suicidal": 0,
    "prodigal": 1,
    "greedy": 2,
}

MAIAN_TOOL_DEFINITION = types.Tool(
    name="maian-analyze",
    description="Detect prodigal, suicidal, and greedy vulnerabilities in Ethereum smart contracts using Maian.",
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
            "contract_name": {
                "type": "string",
                "description": "Main contract name (required for Solidity source analysis)"
            },
            "analysis_type": {
                "type": "string",
                "enum": ["suicidal", "prodigal", "greedy"],
                "description": "Type of vulnerability to check (suicidal, prodigal, greedy)",
                "default": "suicidal"
            },
            "output_format": {
                "type": "string",
                "enum": ["text"],
                "description": "Output format for the analysis results",
                "default": "text"
            }
        },
        "required": ["analysis_type"],
        "anyOf": [
            {"required": ["contract_code", "contract_name"]},
            {"required": ["contract_file", "contract_name"]},
            {"required": ["contract_file"]}
        ]
    },
)

async def run_maian_analysis(
    contract_code: str = None,
    contract_file: str = None,
    contract_name: str = None,
    analysis_type: str = "suicidal",
    output_format: str = "text"
) -> dict:
    """Run Maian analysis on a smart contract."""
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

        # Determine Maian command
        c_flag = MAIAN_ANALYSIS_TYPES.get(analysis_type, 0)
        cmd = ["python3", "maian.py"]
        if contract_path.endswith(".sol"):
            if not contract_name:
                raise ValueError("contract_name is required for Solidity source analysis")
            cmd.extend(["-s", contract_path, contract_name, "-c", str(c_flag)])
        else:
            # Assume bytecode file
            cmd.extend(["-b", contract_path, "-c", str(c_flag)])

        # Run Maian
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
                "error": f"Maian analysis failed: {error_msg}",
                "tool": "maian"
            }

        output = stdout.decode()
        return {
            "success": True,
            "tool": "maian",
            "analysis_type": analysis_type,
            "output": output
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Maian analysis error: {str(e)}",
            "tool": "maian"
        }

def format_maian_response(result: dict, analysis_id: str) -> str:
    if result["success"]:
        summary = f"Maian analysis completed for {result.get('analysis_type', 'unknown')} vulnerability."
        response_text = f"{summary}\n\nAnalysis ID: {analysis_id}\n"
        output = result.get("output", "")
        if output:
            response_text += f"\nResult:\n{output[:1000]}"
            if len(output) > 1000:
                response_text += f"\n... (truncated, see full results in analysis resource)"
        else:
            response_text += "\nNo output from Maian."
    else:
        response_text = f"Maian analysis failed: {result['error']}"
    return response_text

