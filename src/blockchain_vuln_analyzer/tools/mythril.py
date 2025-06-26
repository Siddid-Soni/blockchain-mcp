import asyncio
import json
import os
import subprocess
import tempfile
import mcp.types as types


MYTHRIL_TOOL_DEFINITION = types.Tool(
    name="mythril-analyze",
    description="Analyze Solidity smart contracts using Mythril for security vulnerabilities",
    inputSchema={
        "type": "object",
        "properties": {
            "contract_code": {
                "type": "string",
                "description": "The Solidity contract source code to analyze",
            },
            "contract_file": {
                "type": "string",
                "description": "Path to the contract file (alternative to contract_code)",
            },
            "analysis_mode": {
                "type": "string",
                "enum": ["quick", "standard", "deep"],
                "description": "Analysis depth mode",
                "default": "standard",
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum transaction depth for analysis (default: 12)",
                "default": 12,
                "minimum": 1,
                "maximum": 50,
            },
        },
        "required": [],
        "anyOf": [{"required": ["contract_code"]}, {"required": ["contract_file"]}],
    },
)


async def run_mythril_analysis(
    contract_code: str = None,
    contract_file: str = None,
    analysis_mode: str = "standard",
    max_depth: int = 12,
) -> dict:
    """Run Mythril analysis on a smart contract."""
    try:
        # Create temporary file if contract_code is provided
        temp_file = None
        if contract_code:
            temp_file = tempfile.NamedTemporaryFile(
                mode="w", suffix=".sol", delete=False
            )
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
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
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
                "tool": "mythril",
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
                "raw_output": result,
            }
        except json.JSONDecodeError:
            # If JSON parsing fails, return raw output
            return {
                "success": True,
                "tool": "mythril",
                "analysis_mode": analysis_mode,
                "max_depth": max_depth,
                "raw_output": stdout.decode(),
                "note": "Could not parse JSON output, showing raw results",
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Mythril analysis error: {str(e)}",
            "tool": "mythril",
        }


def format_mythril_response(result: dict, analysis_id: str) -> str:
    if result["success"]:
        vulnerabilities = result.get("vulnerabilities", [])
        summary = (
            f"Mythril analysis completed. Found {len(vulnerabilities)} potential issues."
        )

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