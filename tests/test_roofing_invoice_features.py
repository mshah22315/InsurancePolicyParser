#!/usr/bin/env python3
"""
Test roofing invoice upload with property features
"""
import requests
import json
import os
from datetime import datetime, date
import fitz  # PyMuPDF

def create_test_invoice_pdf():
    """Create a test roofing invoice PDF with installation date"""
    print("Creating test roofing invoice PDF...")
    
    # Create a simple PDF with installation date
    doc = fitz.open()
    page = doc.new_page()
    
    # Add text content with installation date
    text_content = """
    ROOFING INVOICE
    
    Customer: John Doe
    Property: 123 Test Street, Test City, TC 12345
    
    Installation Date: 2020-06-15
    Project Completion Date: 2020-06-20
    Invoice Date: 2020-06-25
    
    Work Description: Complete roof replacement with impact-resistant shingles
    
    SERVICES:
    - Remove old roofing materials
    - Install new impact-resistant shingles
    - Install new underlayment
    - Install new flashing
    
    Total Amount: $15,000
    """
    
    page.insert_text((50, 50), text_content, fontsize=12)
    doc.save("test_roofing_invoice_features.pdf")
    doc.close()
    
    print("✅ Created test roofing invoice PDF")

def test_roofing_invoice_with_features():
    """Test roofing invoice upload with property features"""
    
    base_url = "http://localhost:5001"
    
    print("Testing Roofing Invoice Upload with Property Features")
    print("=" * 60)
    
    # Create test invoice PDF
    create_test_invoice_pdf()
    
    # Test 1: Upload with property features
    print("\n1. Testing roofing invoice upload with property features...")
    try:
        # Add property features as individual form fields
        property_features = ['monitored_alarm', 'sprinkler_system', 'storm_shutters']
        
        # Create form data with multiple propertyFeatures fields
        form_data = []
        with open('test_roofing_invoice_features.pdf', 'rb') as f:
            form_data.append(('document', ('test_invoice_features.pdf', f.read(), 'application/pdf')))
        form_data.append(('policyNumber', 'HMP-IA-001-3056'))
        form_data.append(('installationDate', '2020-06-15'))
        form_data.append(('workDescription', 'Complete roof replacement with impact-resistant shingles'))
        
        # Add each property feature as a separate field
        for feature in property_features:
            form_data.append(('propertyFeatures', feature))
        
        response = requests.post(
            f"{base_url}/api/roofing-invoices/upload",
            files=form_data
        )
            
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
            
        if response.status_code == 200:
            result = response.json()
            print("✅ Roofing invoice upload successful")
            print(f"   Invoice ID: {result.get('invoiceId')}")
            print(f"   Roof Age: {result.get('roofAgeYears')} years")
            print(f"   Processing Status: {result.get('processingStatus')}")
            print(f"   Policy Linked: {result.get('policyLinked')}")
            print(f"   Policy ID: {result.get('policyId')}")
                
            # Check if policy was updated with features
            if result.get('policyId'):
                print("\n2. Checking if policy was updated with features...")
                policy_response = requests.get(f"{base_url}/api/policies/{result.get('policyId')}")
                    
                if policy_response.status_code == 200:
                    policy_data = policy_response.json()
                    print(f"✅ Policy retrieved successfully")
                    print(f"   Policy Number: {policy_data.get('policyNumber')}")
                    print(f"   Roof Age: {policy_data.get('roofAgeYears')} years")
                        
                    # Check property features
                    property_features = policy_data.get('propertyFeatures', [])
                    print(f"   Property Features: {property_features}")
                        
                    expected_features = ['monitored_alarm', 'sprinkler_system', 'storm_shutters']
                    if all(feature in property_features for feature in expected_features):
                        print("✅ Property features saved correctly!")
                    else:
                        print("❌ Property features not saved correctly")
                        print(f"   Expected: {expected_features}")
                        print(f"   Found: {property_features}")
                else:
                    print("❌ Failed to retrieve policy")
            else:
                print("❌ Roofing invoice upload failed")
                
    except Exception as e:
        print(f"❌ Roofing invoice upload error: {e}")
    
    # Test 3: Check roofing invoices endpoint
    print("\n3. Testing roofing invoices endpoint...")
    try:
        response = requests.get(f"{base_url}/api/roofing-invoices")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            invoices = response.json()
            print(f"✅ Found {len(invoices)} roofing invoices")
            
            # Show the most recent invoice
            if invoices:
                latest_invoice = invoices[-1]
                print(f"   Latest Invoice:")
                print(f"     ID: {latest_invoice.get('id')}")
                print(f"     Filename: {latest_invoice.get('filename')}")
                print(f"     Installation Date: {latest_invoice.get('installationDate')}")
                print(f"     Roof Age: {latest_invoice.get('roofAgeYears')} years")
                print(f"     Status: {latest_invoice.get('processingStatus')}")
        else:
            print("❌ Failed to get roofing invoices")
            
    except Exception as e:
        print(f"❌ Roofing invoices endpoint error: {e}")
    
    # Clean up
    if os.path.exists('test_roofing_invoice_features.pdf'):
        os.remove('test_roofing_invoice_features.pdf')
    
    print("\n" + "=" * 60)
    print("Roofing Invoice Features Test Complete!")

if __name__ == "__main__":
    test_roofing_invoice_with_features() 