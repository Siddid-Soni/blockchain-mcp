pragma solidity ^0.8.0;

contract VulnerableContract {
    mapping(address => uint256) public balances;
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    // Vulnerable to reentrancy
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        // External call before state change - vulnerable!
        (bool success,) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] -= amount;
    }
    
    // Missing access control
    function emergencyWithdraw() public {
        payable(msg.sender).transfer(address(this).balance);
    }
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
}
