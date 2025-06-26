import asyncio
import json
import os
import subprocess
import tempfile
import mcp.types as types

SLITHER_TOOL_DEFINITION = types.Tool(
    name="slither-analyze",
    description="Analyze Solidity smart contracts using Slither static analysis framework",
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
            "output_format": {
                "type": "string",
                "enum": ["text", "json", "markdown"],
                "description": "Output format for the analysis results",
                "default": "json",
            },
            "exclude_detectors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of detector names to exclude from analysis",
            },
            "include_detectors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of specific detectors to run (if not specified, runs all)",
            },
        },
        "required": [],
        "anyOf": [{"required": ["contract_code"]}, {"required": ["contract_file"]}],
    },
)


async def run_slither_analysis(
    contract_code: str = None,
    contract_file: str = None,
    output_format: str = "json",
    exclude_detectors: list = None,
    include_detectors: list = None,
) -> dict:
    """Run Slither analysis on a smart contract."""
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
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
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
                    "raw_output": result,
                }
            except json.JSONDecodeError:
                pass

        # Return text output or handle errors
        if not output and error_output:
            return {
                "success": False,
                "error": f"Slither analysis failed: {error_output}",
                "tool": "slither",
            }

        return {
            "success": True,
            "tool": "slither",
            "output_format": output_format,
            "raw_output": output,
            "stderr": error_output if error_output else None,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Slither analysis error: {str(e)}",
            "tool": "slither",
        }


def format_slither_response(result: dict, analysis_id: str) -> str:
    if result["success"]:
        if result.get("output_format") == "json" and "results" in result:
            detectors = result.get("results", {}).get("detectors", [])
            summary = (
                f"Slither analysis completed. Found {len(detectors)} detector results."
            )

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