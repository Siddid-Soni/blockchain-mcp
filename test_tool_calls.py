#!/usr/bin/env python3
"""
Test the MCP server tool calls like they would be called via the MCP protocol
"""

import asyncio
import json

async def test_mcp_tool_calls():
    """Test the tool call handlers directly"""
    from src.blockchain_vuln_analyzer.server import handle_call_tool
    import mcp.types as types
    
    # Test contract
    contract_code = '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VulnerableContract {
    mapping(address => uint256) public balances;
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        // Vulnerable to reentrancy
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] -= amount;
    }
}'''

    print("=== Testing Mythril via MCP Tool Call ===")
    try:
        mythril_args = {
            "contract_code": contract_code,
            "analysis_mode": "standard",
            "max_depth": 12
        }
        
        mythril_result = await handle_call_tool("mythril-analyze", mythril_args)
        
        print("Mythril tool call result:")
        for content in mythril_result:
            if hasattr(content, 'text'):
                print(content.text)
            else:
                print(content)
    
    except Exception as e:
        print(f"Error testing Mythril: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Testing Slither via MCP Tool Call ===")
    try:
        slither_args = {
            "contract_code": contract_code,
            "output_format": "json"
        }
        
        slither_result = await handle_call_tool("slither-analyze", slither_args)
        
        print("Slither tool call result:")
        for content in slither_result:
            if hasattr(content, 'text'):
                print(content.text)
            else:
                print(content)
    
    except Exception as e:
        print(f"Error testing Slither: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_tool_calls())
