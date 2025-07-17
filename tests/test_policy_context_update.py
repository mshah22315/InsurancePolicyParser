import requests
import json
from datetime import date

def test_policy_context_update():
    """Test updating policy context (roof age and property features)"""
    base_url = "http://localhost:5001"
    
    # First, get available policies
    print("Getting available policies...")
    response = requests.get(f"{base_url}/api/policies")
    if response.status_code != 200:
        print(f"Failed to get policies: {response.status_code}")
        return
    
    policies = response.json()
    if not policies:
        print("No policies available for testing")
        return
    
    # Use the first policy for testing
    policy = policies[0]
    policy_id = policy['id']
    print(f"Testing with policy: {policy['policyNumber']} - {policy['policyholderName']}")
    print(f"Policy ID: {policy_id}")
    
    # Test data
    installation_date = "2020-06-15"  # 4 years ago
    property_features = ["monitored_alarm", "sprinkler_system", "smoke_detector"]
    
    # Update policy context
    print(f"\nUpdating policy context...")
    print(f"Installation date: {installation_date}")
    print(f"Property features: {property_features}")
    
    update_data = {
        "installationDate": installation_date,
        "propertyFeatures": property_features
    }
    
    response = requests.patch(
        f"{base_url}/api/policies/{policy_id}/context",
        json=update_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success! Policy context updated")
        print(f"   Roof age: {result.get('roofAgeYears')} years")
        print(f"   Property features: {result.get('propertyFeatures')}")
        
        # Verify the update by getting the policy again
        print(f"\nVerifying update...")
        response = requests.get(f"{base_url}/api/policies/{policy_id}")
        if response.status_code == 200:
            updated_policy = response.json()
            print(f"   Updated roof age: {updated_policy.get('roofAgeYears')} years")
            print(f"   Updated property features: {updated_policy.get('propertyFeatures')}")
            
            # Calculate expected roof age
            install_date = date.fromisoformat(installation_date)
            current_date = date.today()
            expected_age = current_date.year - install_date.year
            if current_date.month < install_date.month or (current_date.month == install_date.month and current_date.day < install_date.day):
                expected_age -= 1
            expected_age = max(0, expected_age)
            
            print(f"   Expected roof age: {expected_age} years")
            print(f"   Age calculation correct: {updated_policy.get('roofAgeYears') == expected_age}")
        else:
            print(f"❌ Failed to verify update: {response.status_code}")
    else:
        print(f"❌ Failed to update policy context: {response.status_code}")
        print(f"   Response: {response.text}")

def test_partial_update():
    """Test updating only roof age or only property features"""
    base_url = "http://localhost:5001"
    
    # Get a policy
    response = requests.get(f"{base_url}/api/policies")
    if response.status_code != 200:
        print("Failed to get policies")
        return
    
    policies = response.json()
    if not policies:
        print("No policies available")
        return
    
    policy_id = policies[0]['id']
    
    # Test updating only roof age
    print(f"\nTesting partial update - roof age only...")
    update_data = {
        "installationDate": "2018-03-20"  # 6 years ago
    }
    
    response = requests.patch(
        f"{base_url}/api/policies/{policy_id}/context",
        json=update_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Roof age only update successful")
        print(f"   Roof age: {result.get('roofAgeYears')} years")
    else:
        print(f"❌ Roof age only update failed: {response.status_code}")
    
    # Test updating only property features
    print(f"\nTesting partial update - property features only...")
    update_data = {
        "propertyFeatures": ["storm_shutters", "impact_windows", "backup_generator"]
    }
    
    response = requests.patch(
        f"{base_url}/api/policies/{policy_id}/context",
        json=update_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Property features only update successful")
        print(f"   Property features: {result.get('propertyFeatures')}")
    else:
        print(f"❌ Property features only update failed: {response.status_code}")

if __name__ == "__main__":
    print("Testing Policy Context Update Functionality")
    print("=" * 50)
    
    test_policy_context_update()
    test_partial_update()
    
    print("\n" + "=" * 50)
    print("Test completed!") 