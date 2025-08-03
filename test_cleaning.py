#!/usr/bin/env python3
"""Test the clean_tool_output function"""

import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, '/home/siddid/blockchain/mcp/src')

from blockchain_vuln_analyzer.server import clean_tool_output

def test_cleaning():
    # Sample output that includes warnings
    sample_output = """/home/siddid/blockchain/mcp/.venv/lib/python3.10/site-packages/slither/utils/output.py:9: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  from pkg_resources import require
'solc --version' running
'solc test_cleaning.sol --combined-json abi,ast,bin,bin-runtime,srcmap,srcmap-runtime,userdoc,devdoc,hashes --allow-paths .,/home/siddid/blockchain/mcp' running

Reentrancy in TestContract.withdraw() (test_cleaning.sol#11-16):
	External calls:
	- (success) = msg.sender.call{value: balance}() (test_cleaning.sol#13)
	State variables written after the call(s):
	- balance = 0 (test_cleaning.sol#15)
	TestContract.balance (test_cleaning.sol#5) can be used in cross function reentrancies:
	- TestContract.deposit() (test_cleaning.sol#7-9)
	- TestContract.withdraw() (test_cleaning.sol#11-16)
Reference: https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities

test_cleaning.sol analyzed (1 contracts with 84 detectors), 4 result(s) found
{
  "success": true,
  "error": null,
  "results": {
    "detectors": [
      {
        "check": "reentrancy-eth",
        "impact": "High",
        "confidence": "Medium"
      }
    ]
  }
}"""

    print("Original output length:", len(sample_output))
    print("Original output first 200 chars:")
    print(repr(sample_output[:200]))
    
    cleaned = clean_tool_output(sample_output)
    print("\nCleaned output length:", len(cleaned))
    print("Cleaned output:")
    print(cleaned)
    
    try:
        parsed = json.loads(cleaned)
        print("\n✅ Successfully parsed as JSON!")
        print("Parsed keys:", list(parsed.keys()))
        return True
    except json.JSONDecodeError as e:
        print(f"\n❌ Failed to parse as JSON: {e}")
        print("Cleaned output for debugging:")
        print(repr(cleaned))
        return False

if __name__ == "__main__":
    success = test_cleaning()
    sys.exit(0 if success else 1)
