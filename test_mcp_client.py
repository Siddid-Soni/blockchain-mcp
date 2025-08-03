#!/usr/bin/env python3
"""
Simple MCP client to test the blockchain vulnerability analyzer
"""

import asyncio
import json
from pathlib import Path

async def test_mcp_tools():
    """Test the MCP tools via direct function calls"""
    from src.blockchain_vuln_analyzer.server import run_mythril_analysis, run_slither_analysis
    
    # Test contract with vulnerabilities
    contract_code = '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestContract {
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

    print("=== Testing Mythril Analysis ===")
    mythril_result = await run_mythril_analysis(contract_code=contract_code)
    print(f"Success: {mythril_result['success']}")
    if mythril_result['success']:
        vulnerabilities = mythril_result.get('vulnerabilities', [])
        print(f"Found {len(vulnerabilities)} vulnerabilities:")
        for i, vuln in enumerate(vulnerabilities, 1):
            print(f"  {i}. {vuln.get('title', 'Unknown')} ({vuln.get('severity', 'Unknown')})")
            print(f"     {vuln.get('description', 'No description')[:100]}...")
    else:
        print(f"Error: {mythril_result.get('error', 'Unknown error')}")
    
    print("\n=== Testing Slither Analysis ===")
    slither_result = await run_slither_analysis(contract_code=contract_code)
    print(f"Success: {slither_result['success']}")
    if slither_result['success']:
        if 'results' in slither_result:
            detectors = slither_result['results'].get('detectors', [])
            print(f"Found {len(detectors)} detector results:")
            for i, detector in enumerate(detectors, 1):
                check = detector.get('check', 'Unknown')
                impact = detector.get('impact', 'Unknown')
                confidence = detector.get('confidence', 'Unknown')
                print(f"  {i}. {check} (Impact: {impact}, Confidence: {confidence})")
        else:
            print("Raw output received (not JSON format)")
    else:
        print(f"Error: {slither_result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
