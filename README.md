# Blockchain Vulnerability Analyzer MCP Server

An MCP (Model Context Protocol) server for comprehensive blockchain smart contract vulnerability analysis using industry-standard tools Mythril and Slither.

## Features

- **Mythril Integration**: Symbolic execution analysis for security vulnerabilities
- **Slither Integration**: Static analysis framework with comprehensive detectors  
- **Flexible Input**: Analyze contracts from source code or file paths
- **Configurable Analysis**: Multiple analysis modes and detector options
- **Resource Management**: Store and access analysis results through MCP resources
- **Interactive Prompts**: Get analysis recommendations and guidance

## Components

### Resources

The server exposes analysis results as resources:
- Custom `analysis://` URI scheme for accessing individual analysis results
- Each analysis result includes vulnerability findings, tool metadata, and raw output
- JSON format for structured access to analysis data

### Prompts

The server provides analysis guidance prompts:
- `analyze-contract`: Get recommendations for smart contract vulnerability analysis
  - Optional "contract_type" argument (ERC20, ERC721, DeFi, etc.)
  - Optional "focus_area" argument (reentrancy, overflow, access control, etc.)
  - Generates targeted analysis recommendations based on contract type and focus

### Tools

#### mythril-analyze
Analyze Solidity smart contracts using Mythril's symbolic execution engine.

**Parameters:**
- `contract_code` (string): Solidity source code to analyze
- `contract_file` (string): Path to contract file (alternative to contract_code)  
- `analysis_mode` (enum): Analysis depth - "quick", "standard", or "deep"
- `max_depth` (integer): Maximum transaction depth (1-50, default: 12)

**Features:**
- Detects reentrancy vulnerabilities, integer overflows, access control issues
- Configurable analysis depth for speed vs thoroughness trade-offs
- JSON output with structured vulnerability reports

#### slither-analyze  
Analyze Solidity smart contracts using Slither's static analysis framework.

**Parameters:**
- `contract_code` (string): Solidity source code to analyze
- `contract_file` (string): Path to contract file (alternative to contract_code)
- `output_format` (enum): Output format - "text", "json", or "markdown" 
- `exclude_detectors` (array): List of detector names to exclude
- `include_detectors` (array): List of specific detectors to run

**Features:**
- 90+ built-in vulnerability detectors
- Optimization suggestions and code quality checks
- Configurable detector selection for targeted analysis
- Multiple output formats for different use cases

## Prerequisites

Before using this MCP server, ensure you have the following tools installed:

1. **Mythril**: `pip install mythril`
2. **Slither**: `pip install slither-analyzer` 
3. **Solidity Compiler**: Install via `solc-select` for version management

The server will attempt to use these tools via command line, so they must be available in your PATH.

## Installation

### Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd blockchain-vuln-analyzer
```

2. Install dependencies:
```bash
uv sync --dev --all-extras
```

3. The analysis tools should already be installed as dependencies, but you can verify:
```bash
myth version
slither --version
```

### Claude Desktop Configuration

Add the following to your Claude Desktop configuration:

**MacOS**: `~/Library/Application\ Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "blockchain-vuln-analyzer": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/your/blockchain-vuln-analyzer",
        "run",
        "blockchain-vuln-analyzer"
      ]
    }
  }
}
```

## Usage Examples

### Basic Contract Analysis

Analyze a simple ERC20 contract:

```solidity
// Example contract to analyze
pragma solidity ^0.8.0;

contract SimpleToken {
    mapping(address => uint256) public balances;
    
    function transfer(address to, uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
}
```

Use the MCP tools:
1. **mythril-analyze**: Run with "standard" mode for comprehensive analysis
2. **slither-analyze**: Use JSON output for structured results

### Analysis Workflow

1. Use the `analyze-contract` prompt to get targeted recommendations
2. Run both Mythril and Slither analysis for comprehensive coverage  
3. Access detailed results through the analysis resources
4. Compare findings between tools for validation

## Common Vulnerability Detections

This server can help identify:

- **Reentrancy attacks**: Mythril excels at detecting complex reentrancy patterns
- **Integer overflow/underflow**: Both tools detect arithmetic vulnerabilities
- **Access control issues**: Unauthorized function access and privilege escalation
- **Gas optimization**: Slither provides gas usage optimization suggestions
- **Code quality**: Slither detects style and best practice violations
- **Logic errors**: Mythril's symbolic execution finds logical inconsistencies

## Development

### Running the Server

For development and testing:

```bash
# Run the server directly
uv run python -m blockchain_vuln_analyzer.server

# Or use the console script
uv run blockchain-vuln-analyzer
```

### Testing

Test the server with sample contracts:

```bash
# Create a test contract
echo 'pragma solidity ^0.8.0; contract Test { function test() public {} }' > test.sol

# Test mythril integration
myth analyze test.sol

# Test slither integration  
slither test.sol
```

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).


You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /home/siddid/blockchain/mcp run blockchain-vuln-analyzer
```


Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.