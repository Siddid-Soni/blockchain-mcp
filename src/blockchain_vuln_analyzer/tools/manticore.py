import asyncio
import os
import tempfile
import mcp.types as types

MANTICORE_TOOL_DEFINITION = types.Tool(
    name="manticore-analyze",
    description="Symbolically execute smart contracts using Manticore to find vulnerabilities.",
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
            "output_dir": {
                "type": "string",
                "description": "Directory to store Manticore results (optional)"
            },
            "output_format": {
                "type": "string",
                "enum": ["text"],
                "description": "Output format for the analysis results",
                "default": "text"
            }
        },
        "required": [],
        "anyOf": [
            {"required": ["contract_code"]},
            {"required": ["contract_file"]}
        ]
    },
)

async def run_manticore_analysis(
    contract_code: str = None,
    contract_file: str = None,
    output_dir: str = None,
    output_format: str = "text"
) -> dict:
    """Run Manticore symbolic execution on a smart contract."""
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

        # Build Manticore command
        cmd = ["manticore", contract_path]
        if output_dir:
            cmd.extend(["--workspace", output_dir])

        # Run Manticore
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        # Clean up temp file
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

        output = stdout.decode(errors="replace")
        error_output = stderr.decode(errors="replace")

        # Manticore prints info/warnings to stderr but still may succeed
        if process.returncode != 0:
            # If output is empty, treat as error
            if not output.strip():
                return {
                    "success": False,
                    "error": f"Manticore analysis failed: {error_output.strip()}",
                    "tool": "manticore"
                }
            # Otherwise, treat as partial success with warnings
            return {
                "success": True,
                "tool": "manticore",
                "output": output,
                "warnings": error_output.strip()
            }

        return {
            "success": True,
            "tool": "manticore",
            "output": output,
            "warnings": error_output.strip() if error_output.strip() else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Manticore analysis error: {str(e)}",
            "tool": "manticore"
        }

def format_manticore_response(result: dict, analysis_id: str) -> str:
    if result["success"]:
        response_text = f"Manticore analysis completed.\n\nAnalysis ID: {analysis_id}\n"
        if result.get("warnings"):
            response_text += f"\nWarnings:\n{result['warnings']}\n"
        output = result.get("output", "")
        if output:
            response_text += f"\nResults (first 1000 chars):\n{output[:1000]}"
            if len(output) > 1000:
                response_text += f"\n... (truncated, see full results in analysis resource)"
        else:
            response_text += "\nNo output from Manticore."
    else:
        response_text = f"Manticore analysis failed: {result['error']}"
    return response_text 