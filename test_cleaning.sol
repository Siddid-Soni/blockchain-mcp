// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestContract {
    uint256 private balance;
    
    function deposit() public payable {
        balance += msg.value;
    }
    
    function withdraw() public {
        // Potential reentrancy vulnerability
        (bool success, ) = msg.sender.call{value: balance}("");
        require(success, "Transfer failed");
        balance = 0;
    }
}
