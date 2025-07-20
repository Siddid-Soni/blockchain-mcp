from .mythril import (
    MYTHRIL_TOOL_DEFINITION,
    run_mythril_analysis,
    format_mythril_response,
)
from .slither import (
    SLITHER_TOOL_DEFINITION,
    run_slither_analysis,
    format_slither_response,
)
from .echidna import (
    ECHIDNA_TOOL_DEFINITION,
    run_echidna_analysis,
    format_echidna_response,
)
from .maian import (
    MAIAN_TOOL_DEFINITION,
    run_maian_analysis,
    format_maian_response,
)
from .smartcheck import (
    SMARTCHECK_TOOL_DEFINITION,
    run_smartcheck_analysis,
    format_smartcheck_response,
)
from .manticore import (
    MANTICORE_TOOL_DEFINITION,
    run_manticore_analysis,
    format_manticore_response,
)
from .main import ToolProcessor

# A list of all tool definitions
ALL_TOOLS = [
    MYTHRIL_TOOL_DEFINITION,
    SLITHER_TOOL_DEFINITION,
    ECHIDNA_TOOL_DEFINITION,
    MAIAN_TOOL_DEFINITION,
    SMARTCHECK_TOOL_DEFINITION,
    MANTICORE_TOOL_DEFINITION,
]

# A map of tool processors
TOOL_PROCESSORS = {
    "mythril-analyze": ToolProcessor(
        runner=run_mythril_analysis,
        formatter=format_mythril_response,
        argument_extractor=lambda args: {
            "contract_code": args.get("contract_code"),
            "contract_file": args.get("contract_file"),
            "analysis_mode": args.get("analysis_mode", "standard"),
            "max_depth": args.get("max_depth", 12),
        },
    ),
    "slither-analyze": ToolProcessor(
        runner=run_slither_analysis,
        formatter=format_slither_response,
        argument_extractor=lambda args: {
            "contract_code": args.get("contract_code"),
            "contract_file": args.get("contract_file"),
            "output_format": args.get("output_format", "json"),
            "exclude_detectors": args.get("exclude_detectors", []),
            "include_detectors": args.get("include_detectors", []),
        },
    ),
    "echidna-analyze": ToolProcessor(
        runner=run_echidna_analysis,
        formatter=format_echidna_response,
        argument_extractor=lambda args: {
            "contract_code": args.get("contract_code"),
            "contract_file": args.get("contract_file"),
            "config_file": args.get("config_file"),
            "testMode": args.get("testMode", "property"),
            "testLimit": args.get("testLimit", 50000),
            "timeout": args.get("timeout"),
            "output_format": args.get("output_format", "json"),
        },
    ),
    "maian-analyze": ToolProcessor(
        runner=run_maian_analysis,
        formatter=format_maian_response,
        argument_extractor=lambda args: {
            "contract_code": args.get("contract_code"),
            "contract_file": args.get("contract_file"),
            "contract_name": args.get("contract_name"),
            "analysis_type": args.get("analysis_type", "suicidal"),
            "output_format": args.get("output_format", "text"),
        },
    ),
    "smartcheck-analyze": ToolProcessor(
        runner=run_smartcheck_analysis,
        formatter=format_smartcheck_response,
        argument_extractor=lambda args: {
            "contract_code": args.get("contract_code"),
            "contract_file": args.get("contract_file"),
            "rules_file": args.get("rules_file"),
            "output_format": args.get("output_format", "text"),
        },
    ),
    "manticore-analyze": ToolProcessor(
        runner=run_manticore_analysis,
        formatter=format_manticore_response,
        argument_extractor=lambda args: {
            "contract_code": args.get("contract_code"),
            "contract_file": args.get("contract_file"),
            "output_dir": args.get("output_dir"),
            "output_format": args.get("output_format", "text"),
        },
    ),
} 