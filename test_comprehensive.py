#!/usr/bin/env python3
"""
Comprehensive test of the blockchain vulnerability analyzer
"""

import asyncio
import json

async def test_different_contracts():
    """Test with different types of contracts"""
    from src.blockchain_vuln_analyzer.server import handle_call_tool
    
    # Test 1: Clean contract (should have minimal issues)
    clean_contract = '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract CleanContract {
    uint256 private value;
    address private owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    function setValue(uint256 _value) external onlyOwner {
        value = _value;
    }
    
    function getValue() external view returns (uint256) {
        return value;
    }
}'''

    # Test 2: Vulnerable reentrancy contract
    reentrancy_contract = '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ReentrancyVulnerable {
    mapping(address => uint256) public balances;
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    function withdraw() public {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "No balance");
        
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] = 0;
    }
}'''

    contracts = [
        ("Clean Contract", clean_contract),
        ("Reentrancy Vulnerable Contract", reentrancy_contract)
    ]
    
    for name, contract in contracts:
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"{'='*60}")
        
        # Test Mythril
        print("\n--- Mythril Analysis ---")
        try:
            mythril_result = await handle_call_tool("mythril-analyze", {
                "contract_code": contract,
                "analysis_mode": "standard"
            })
            
            for content in mythril_result:
                if hasattr(content, 'text'):
                    print(content.text)
        except Exception as e:
            print(f"Mythril error: {e}")
        
        # Test Slither
        print("\n--- Slither Analysis ---")
        try:
            slither_result = await handle_call_tool("slither-analyze", {
                "contract_code": contract,
                "output_format": "json"
            })
            
            for content in slither_result:
                if hasattr(content, 'text'):
                    print(content.text)
        except Exception as e:
            print(f"Slither error: {e}")

if __name__ == "__main__":
    asyncio.run(test_different_contracts())
