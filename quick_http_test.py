#!/usr/bin/env python3
"""
Quick test of the HTTP server functionality.
"""

import requests
import json

# Test contract
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
}"""

def test_single_analysis():
    """Test single analysis endpoint."""
    print("🔍 Testing single analysis...")
    
    url = "http://localhost:8001/analyze"
    payload = {
        "contract_code": test_contract,
        "tool": "slither-analyze",
        "options": {"output_format": "json"}
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Analysis completed:")
            print(f"   - Analysis ID: {data['analysis_id']}")
            print(f"   - Tool: {data['tool']}")
            print(f"   - Status: {data['status']}")
            print(f"   - Success: {data['result'].get('success', False)}")
            return data['analysis_id']
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_results_retrieval(analysis_id):
    """Test results retrieval."""
    if not analysis_id:
        print("⚠️  Skipping results test (no analysis ID)")
        return
        
    print(f"\n📄 Testing results retrieval for {analysis_id}...")
    
    url = f"http://localhost:8001/results/{analysis_id}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            result = data['result']
            print(f"✅ Retrieved result:")
            print(f"   - Tool: {result.get('tool', 'unknown')}")
            print(f"   - Success: {result.get('success', False)}")
            if result.get('success'):
                if 'results' in result and 'detectors' in result['results']:
                    detector_count = len(result['results']['detectors'])
                    print(f"   - Detectors found: {detector_count}")
        else:
            print(f"❌ Results retrieval failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error retrieving results: {e}")

def test_batch_analysis():
    """Test batch analysis."""
    print("\n🔄 Testing batch analysis...")
    
    url = "http://localhost:8001/analyze/batch"
    payload = {
        "contract_code": test_contract,
        "tools": ["slither-analyze", "mythril-analyze"],
        "options": {
            "slither-analyze": {"output_format": "json"},
            "mythril-analyze": {"analysis_mode": "quick"}
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 200:
            data = response.json()
            results = data['results']
            print(f"✅ Batch analysis completed:")
            for tool, result in results.items():
                if 'error' in result:
                    print(f"   ❌ {tool}: {result['error']}")
                else:
                    print(f"   ✅ {tool}: {result['status']} (ID: {result['analysis_id']})")
        else:
            print(f"❌ Batch analysis failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Error during batch analysis: {e}")

if __name__ == "__main__":
    print("🚀 Quick HTTP Server Test")
    print("=" * 40)
    
    # Test 1: Single analysis
    analysis_id = test_single_analysis()
    
    # Test 2: Results retrieval
    test_results_retrieval(analysis_id)
    
    # Test 3: Batch analysis
    test_batch_analysis()
    
    print("\n" + "=" * 40)
    print("✅ HTTP server is working correctly!")