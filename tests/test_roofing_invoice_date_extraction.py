#!/usr/bin/env python3
"""
Test roofing invoice upload with automatic date extraction from PDF
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
    doc.save("test_roofing_invoice_with_date.pdf")
    doc.close()
    
    print("✅ Created test roofing invoice PDF with installation date")

def test_roofing_invoice_date_extraction():
    """Test roofing invoice upload with automatic date extraction"""
    
    base_url = "http://localhost:5001"
    
    print("Testing Roofing Invoice Upload with Date Extraction")
    print("=" * 60)
    
    # Create test invoice PDF
    create_test_invoice_pdf()
    
    # Test 1: Upload without providing installation date (should extract from PDF)
    print("\n1. Testing roofing invoice upload with automatic date extraction...")
    try:
        with open('test_roofing_invoice_with_date.pdf', 'rb') as f:
            files = {'document': ('test_invoice_auto_date.pdf', f, 'application/pdf')}
            data = {
                'policyNumber': 'TEST-POL-2024-001',
                'workDescription': 'Complete roof replacement with impact-resistant shingles',
                'propertyFeatures': ['impact_windows', 'storm_shutters']
            }
            
            response = requests.post(
                f"{base_url}/api/roofing-invoices/upload",
                files=files,
                data=data
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Roofing invoice upload successful")
                print(f"   Invoice ID: {result.get('invoiceId')}")
                print(f"   Extracted Installation Date: {result.get('extractedInstallationDate')}")
                print(f"   Used Installation Date: {result.get('usedInstallationDate')}")
                print(f"   Roof Age: {result.get('roofAgeYears')} years")
                print(f"   Processing Status: {result.get('processingStatus')}")
                print(f"   Policy Linked: {result.get('policyLinked')}")
                
                # Calculate expected roof age
                if result.get('usedInstallationDate'):
                    install_date = datetime.strptime(result.get('usedInstallationDate'), '%Y-%m-%d').date()
                    current_date = date.today()
                    expected_age = current_date.year - install_date.year
                    
                    # Adjust for partial years
                    if current_date.month < install_date.month or (current_date.month == install_date.month and current_date.day < install_date.day):
                        expected_age -= 1
                    
                    expected_age = max(0, expected_age)
                    print(f"   Expected Age: {expected_age} years")
                    
                    if result.get('roofAgeYears') == expected_age:
                        print("✅ Roof age calculation correct!")
                    else:
                        print("❌ Roof age calculation incorrect")
                        
                    if result.get('extractedInstallationDate'):
                        print("✅ Date extraction from PDF successful!")
                    else:
                        print("❌ Date extraction from PDF failed")
                else:
                    print("❌ No installation date found or extracted")
            else:
                print("❌ Roofing invoice upload failed")
                
    except Exception as e:
        print(f"❌ Roofing invoice upload error: {e}")
    
    # Test 2: Upload with manual installation date (should use provided date)
    print("\n2. Testing roofing invoice upload with manual installation date...")
    try:
        with open('test_roofing_invoice_with_date.pdf', 'rb') as f:
            files = {'document': ('test_invoice_manual_date.pdf', f, 'application/pdf')}
            data = {
                'policyNumber': 'TEST-POL-2024-002',
                'installationDate': '2018-03-10',  # Different date than in PDF
                'workDescription': 'Roof repair and maintenance',
                'propertyFeatures': ['monitored_alarm']
            }
            
            response = requests.post(
                f"{base_url}/api/roofing-invoices/upload",
                files=files,
                data=data
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Roofing invoice upload successful (manual date)")
                print(f"   Invoice ID: {result.get('invoiceId')}")
                print(f"   Extracted Installation Date: {result.get('extractedInstallationDate')}")
                print(f"   Used Installation Date: {result.get('usedInstallationDate')}")
                print(f"   Roof Age: {result.get('roofAgeYears')} years")
                
                # Should use manual date (2018-03-10) instead of PDF date (2020-06-15)
                if result.get('usedInstallationDate') == '2018-03-10':
                    print("✅ Manual installation date used correctly!")
                else:
                    print("❌ Manual installation date not used correctly")
                    
                # Calculate expected roof age for manual date
                install_date = datetime.strptime('2018-03-10', '%Y-%m-%d').date()
                current_date = date.today()
                expected_age = current_date.year - install_date.year
                
                # Adjust for partial years
                if current_date.month < install_date.month or (current_date.month == install_date.month and current_date.day < install_date.day):
                    expected_age -= 1
                
                expected_age = max(0, expected_age)
                
                if result.get('roofAgeYears') == expected_age:
                    print("✅ Roof age calculation correct for manual date!")
                else:
                    print("❌ Roof age calculation incorrect for manual date")
            else:
                print("❌ Roofing invoice upload failed")
                
    except Exception as e:
        print(f"❌ Roofing invoice upload error: {e}")
    
    # Test 3: Upload without any date (should use default estimate)
    print("\n3. Testing roofing invoice upload without any date...")
    try:
        # Create a PDF without installation date
        doc = fitz.open()
        page = doc.new_page()
        
        text_content = """
        ROOFING INVOICE
        
        Customer: Jane Smith
        Property: 456 Oak Street, Test City, TC 12345
        
        Invoice Date: 2023-12-01
        
        Work Description: Minor roof repairs
        
        SERVICES:
        - Repair damaged shingles
        - Seal roof penetrations
        
        Total Amount: $2,500
        """
        
        page.insert_text((50, 50), text_content, fontsize=12)
        doc.save("test_roofing_invoice_no_date.pdf")
        doc.close()
        
        with open('test_roofing_invoice_no_date.pdf', 'rb') as f:
            files = {'document': ('test_invoice_no_date.pdf', f, 'application/pdf')}
            data = {
                'policyNumber': 'TEST-POL-2024-003',
                'workDescription': 'Minor roof repairs',
                'propertyFeatures': ['security_camera']
            }
            
            response = requests.post(
                f"{base_url}/api/roofing-invoices/upload",
                files=files,
                data=data
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Roofing invoice upload successful (no date)")
                print(f"   Invoice ID: {result.get('invoiceId')}")
                print(f"   Extracted Installation Date: {result.get('extractedInstallationDate')}")
                print(f"   Used Installation Date: {result.get('usedInstallationDate')}")
                print(f"   Roof Age: {result.get('roofAgeYears')} years")
                
                if result.get('roofAgeYears') == 5:  # Default estimate
                    print("✅ Default roof age applied correctly!")
                else:
                    print("❌ Default roof age not applied correctly")
                    
                if not result.get('extractedInstallationDate'):
                    print("✅ Correctly handled missing installation date")
                else:
                    print("❌ Unexpectedly extracted date when none should exist")
            else:
                print("❌ Roofing invoice upload failed")
                
    except Exception as e:
        print(f"❌ Roofing invoice upload error: {e}")
    
    # Test 4: Check roofing invoices endpoint
    print("\n4. Testing roofing invoices endpoint...")
    try:
        response = requests.get(f"{base_url}/api/roofing-invoices")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            invoices = response.json()
            print(f"✅ Found {len(invoices)} roofing invoices")
            
            for i, invoice in enumerate(invoices[-3:]):  # Show last 3 invoices
                print(f"   Invoice {i+1}:")
                print(f"     ID: {invoice.get('id')}")
                print(f"     Filename: {invoice.get('filename')}")
                print(f"     Installation Date: {invoice.get('installationDate')}")
                print(f"     Roof Age: {invoice.get('roofAgeYears')} years")
                print(f"     Status: {invoice.get('processingStatus')}")
        else:
            print("❌ Failed to get roofing invoices")
            
    except Exception as e:
        print(f"❌ Roofing invoices endpoint error: {e}")
    
    # Clean up
    for filename in ['test_roofing_invoice_with_date.pdf', 'test_roofing_invoice_no_date.pdf']:
        if os.path.exists(filename):
            os.remove(filename)
    
    print("\n" + "=" * 60)
    print("Roofing Invoice Date Extraction Test Complete!")

if __name__ == "__main__":
    test_roofing_invoice_date_extraction() 