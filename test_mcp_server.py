#!/usr/bin/env python3
"""
Simple test script to validate the MCP server functionality.
"""

import sys
import os
import asyncio
import json

# Add src to path
sys.path.insert(0, 'src')

from blockchain_vuln_analyzer.server import server, analysis_results
from blockchain_vuln_analyzer.tools import ALL_TOOLS, TOOL_PROCESSORS

async def test_server_components():
    """Test basic server components."""
    print("Testing MCP Server Components...")
    
    # Test 1: Check tool definitions
    print(f"✓ Found {len(ALL_TOOLS)} tool definitions:")
    for tool in ALL_TOOLS:
        print(f"  - {tool.name}: {tool.description}")
    
    # Test 2: Check tool processors
    print(f"✓ Found {len(TOOL_PROCESSORS)} tool processors:")
    for name in TOOL_PROCESSORS.keys():
        print(f"  - {name}")
    
    # Test 3: Test resource handling
    print("✓ Testing resource handling...")
    
    # Add a mock analysis result
    analysis_results["test_mythril_1"] = {
        "success": True,
        "tool": "mythril",
        "vulnerabilities": [
            {"title": "Test Vulnerability", "description": "Test description"}
        ]
    }
    
    # Test resource listing (using the handler functions directly)
    from blockchain_vuln_analyzer.server import handle_list_resources, handle_read_resource, handle_list_prompts
    
    resources = await handle_list_resources()
    print(f"  - Found {len(resources)} resources")
    
    # Test resource reading
    from pydantic import AnyUrl
    test_uri = AnyUrl("analysis://internal/test_mythril_1")
    resource_content = await handle_read_resource(test_uri)
    result = json.loads(resource_content)
    print(f"  - Successfully read resource: {result['tool']}")
    
    # Test 4: Test prompt handling
    prompts = await handle_list_prompts()
    print(f"✓ Found {len(prompts)} prompts:")
    for prompt in prompts:
        print(f"  - {prompt.name}: {prompt.description}")
    
    print("\n✅ All basic server components are working correctly!")

async def test_tool_processor():
    """Test a tool processor without actually running the tool."""
    print("\nTesting Tool Processor...")
    
    # Test mythril processor argument extraction
    mythril_processor = TOOL_PROCESSORS["mythril-analyze"]
    test_args = {
        "contract_code": "pragma solidity ^0.8.0; contract Test {}",
        "analysis_mode": "quick"
    }
    
    extracted_args = mythril_processor.argument_extractor(test_args)
    print(f"✓ Mythril argument extraction: {extracted_args}")
    
    # Test slither processor
    slither_processor = TOOL_PROCESSORS["slither-analyze"]
    test_args = {
        "contract_file": "test_contract.sol",
        "output_format": "json"
    }
    
    extracted_args = slither_processor.argument_extractor(test_args)
    print(f"✓ Slither argument extraction: {extracted_args}")
    
    print("✅ Tool processors are working correctly!")

if __name__ == "__main__":
    asyncio.run(test_server_components())
    asyncio.run(test_tool_processor())