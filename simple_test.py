#!/usr/bin/env python3
"""
Simple test script to validate MCP server functionality without external dependencies.
"""

import asyncio
import json
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from blockchain_vuln_analyzer.server import handle_call_tool, handle_list_tools

async def test_direct_tool_calls():
    """Test the MCP server tools directly."""
    print("🔍 Testing Blockchain Vulnerability Analyzer MCP Server")
    print("=" * 60)
    
    # Test contract code
    test_contract = """pragma solidity ^0.8.13;

contract Exceptions {
    uint256[8] myarray;
    uint counter = 0;
    function assert1() public pure {
        uint256 i = 1;
        assert(i == 0);
    }
    function counter_increase() public {
        counter+=1;
    }
    function assert5(uint input_x) public view{
        require(counter>2);
        assert(input_x > 10);
    }
    function assert2() public pure {
        uint256 i = 1;
        assert(i > 0);
    }
    function assert3(uint256 input) public pure {
        assert(input != 23);
    }
    function require_is_fine(uint256 input) public pure {
        require(input != 23);
    }
    function this_is_fine(uint256 input) public pure {
        if (input > 0) {
            uint256 i = 1/input;
        }
    }
    function this_is_find_2(uint256 index) public view {
        if (index < 8) {
            uint256 i = myarray[index];
        }
    }
}"""

    # Test 1: List available tools
    print("1. Listing available tools...")
    try:
        tools = await handle_list_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
    except Exception as e:
        print(f"❌ Error listing tools: {e}")
        return
    
    print("\n" + "=" * 60)
    
    # Test 2: Run Slither analysis
    print("2. Testing Slither analysis...")
    try:
        slither_args = {
            "contract_code": test_contract,
            "output_format": "json"
        }
        
        result = await handle_call_tool("slither-analyze", slither_args)
        print("✅ Slither analysis completed:")
        for content in result:
            if hasattr(content, 'text'):
                print(f"   {content.text}")
            else:
                print(f"   {content}")
    except Exception as e:
        print(f"❌ Slither analysis failed: {e}")
    
    print("\n" + "=" * 60)
    
    # Test 3: Run Mythril analysis
    print("3. Testing Mythril analysis...")
    try:
        mythril_args = {
            "contract_code": test_contract,
            "analysis_mode": "quick"
        }
        
        result = await handle_call_tool("mythril-analyze", mythril_args)
        print("✅ Mythril analysis completed:")
        for content in result:
            if hasattr(content, 'text'):
                print(f"   {content.text}")
            else:
                print(f"   {content}")
    except Exception as e:
        print(f"❌ Mythril analysis failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Analysis Summary:")
    print("The test contract contains several vulnerabilities:")
    print("   - Always-failing assertion in assert1() function")
    print("   - Inappropriate use of assert() for input validation")
    print("   - Potential gas inefficiencies")
    print("\n✅ MCP Server testing completed!")

if __name__ == "__main__":
    asyncio.run(test_direct_tool_calls())