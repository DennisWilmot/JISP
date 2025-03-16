import requests
import json

# Base URL of your API (use localhost for testing)
BASE_URL = "http://localhost:8000"  # Change port if needed

# Test the allocation endpoint
def test_allocation_endpoint():
    response = requests.post(f"{BASE_URL}/api/v1/parishes/allocate-resources")
    
    if response.status_code == 200:
        result = response.json()
        
        # Check if both recommendations and allocations are returned
        assert "recommendations" in result, "Recommendations not found in response"
        assert "allocations" in result, "Allocations not found in response"
        
        # Verify the total officer counts
        rec_total = sum(result["recommendations"].values())
        alloc_total = sum(result["allocations"].values())
        
        print(f"Total in recommendations: {rec_total}")
        print(f"Total in allocations: {alloc_total}")
        
        # Both should be 1000 (or your configured total)
        assert rec_total == 1000, f"Total recommendations should be 1000, got {rec_total}"
        assert alloc_total == 1000, f"Total allocations should be 1000, got {alloc_total}"
        
        print("Test passed! Both recommendations and allocations sum to 1000.")
        print("Full response:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_allocation_endpoint()