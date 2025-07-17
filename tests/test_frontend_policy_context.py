import requests
import json

def test_frontend_policy_context():
    """Test the frontend policy context functionality"""
    base_url = "http://localhost:5000"  # Frontend with proxy
    
    print("Testing Frontend Policy Context")
    print("=" * 40)
    
    # 1. Test getting policies through frontend proxy
    print("1. Testing policy list retrieval...")
    try:
        response = requests.get(f"{base_url}/api/policies")
        if response.status_code == 200:
            policies = response.json()
            print(f"✅ Successfully retrieved {len(policies)} policies")
            if policies:
                first_policy = policies[0]
                print(f"   First policy: ID={first_policy['id']}, Number={first_policy['policyNumber']}")
                print(f"   Roof age: {first_policy.get('roofAgeYears', 'Not set')}")
                print(f"   Property features: {first_policy.get('propertyFeatures', [])}")
                policy_id = first_policy['id']
            else:
                print("❌ No policies found")
                return
        else:
            print(f"❌ Failed to get policies: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting policies: {e}")
        return
    
    # 2. Test updating policy context through frontend proxy
    print(f"\n2. Testing policy context update for policy {policy_id}...")
    try:
        update_data = {
            "installationDate": "2019-03-15",
            "propertyFeatures": ["sprinkler_system", "smoke_detector", "deadbolt_locks"]
        }
        
        response = requests.patch(
            f"{base_url}/api/policies/{policy_id}/context",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully updated policy context")
            print(f"   Roof age: {result.get('roofAgeYears')} years")
            print(f"   Property features: {result.get('propertyFeatures')}")
        else:
            print(f"❌ Failed to update policy context: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error updating policy context: {e}")
        return
    
    # 3. Verify the update by getting the policy again
    print(f"\n3. Verifying the update...")
    try:
        response = requests.get(f"{base_url}/api/policies/{policy_id}")
        if response.status_code == 200:
            updated_policy = response.json()
            print(f"✅ Policy retrieved successfully")
            print(f"   Roof age: {updated_policy.get('roofAgeYears')} years")
            print(f"   Property features: {updated_policy.get('propertyFeatures')}")
            
            # Check if the data was actually saved
            if updated_policy.get('roofAgeYears') == 6:  # 2019 to 2025 = 6 years
                print("✅ Roof age calculation is correct")
            else:
                print(f"❌ Roof age calculation incorrect: expected 6, got {updated_policy.get('roofAgeYears')}")
            
            if updated_policy.get('propertyFeatures') == ["sprinkler_system", "smoke_detector", "deadbolt_locks"]:
                print("✅ Property features saved correctly")
            else:
                print(f"❌ Property features not saved correctly: {updated_policy.get('propertyFeatures')}")
        else:
            print(f"❌ Failed to verify update: {response.status_code}")
    except Exception as e:
        print(f"❌ Error verifying update: {e}")
    
    print("\n" + "=" * 40)
    print("Frontend Policy Context Test Completed!")

if __name__ == "__main__":
    test_frontend_policy_context() 