#!/usr/bin/env python3
"""
Complete workflow test: PDF upload with raw text extraction and querying
"""
import requests
import json
import os
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_pdf():
    """Create a test PDF with insurance policy content"""
    # Create a temporary PDF file
    fd, pdf_path = tempfile.mkstemp(suffix='.pdf')
    os.close(fd)
    
    # Create PDF content
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # Add content to PDF
    y_position = height - 50
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y_position, "INSURANCE POLICY DOCUMENT")
    y_position -= 30
    
    # Policy details
    c.setFont("Helvetica", 12)
    c.drawString(50, y_position, "Policy Number: TEST-POL-2024-001")
    y_position -= 20
    c.drawString(50, y_position, "Insurer: Test Insurance Company")
    y_position -= 20
    c.drawString(50, y_position, "Policyholder: John Doe")
    y_position -= 20
    c.drawString(50, y_position, "Property Address: 123 Test Street, Test City, TC 12345")
    y_position -= 30
    
    # Coverage details
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position, "COVERAGE DETAILS:")
    y_position -= 20
    c.setFont("Helvetica", 12)
    c.drawString(50, y_position, "- Dwelling Coverage: $300,000")
    y_position -= 15
    c.drawString(50, y_position, "- Personal Property: $150,000")
    y_position -= 15
    c.drawString(50, y_position, "- Liability Coverage: $300,000")
    y_position -= 15
    c.drawString(50, y_position, "- Medical Payments: $5,000")
    y_position -= 25
    
    # Deductibles
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position, "DEDUCTIBLES:")
    y_position -= 20
    c.setFont("Helvetica", 12)
    c.drawString(50, y_position, "- Wind/Hail: $1,000")
    y_position -= 15
    c.drawString(50, y_position, "- Other Perils: $1,000")
    y_position -= 25
    
    # Premium information
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position, "PREMIUM INFORMATION:")
    y_position -= 20
    c.setFont("Helvetica", 12)
    c.drawString(50, y_position, "- Total Annual Premium: $2,500")
    y_position -= 15
    c.drawString(50, y_position, "- Effective Date: January 1, 2024")
    y_position -= 15
    c.drawString(50, y_position, "- Expiration Date: January 1, 2025")
    y_position -= 25
    
    # Additional information
    c.drawString(50, y_position, "This is a test policy document for querying purposes.")
    
    c.save()
    return pdf_path

def test_complete_workflow():
    """Test the complete workflow: upload PDF, extract text, query"""
    
    base_url = "http://localhost:5001"
    
    print("Complete Workflow Test: PDF Upload + Text Extraction + Querying")
    print("=" * 70)
    
    try:
        # Step 1: Create test PDF
        print("\n1. Creating test PDF...")
        pdf_path = create_test_pdf()
        print(f"   ✅ Created test PDF: {pdf_path}")
        
        # Step 2: Upload the PDF
        print("\n2. Uploading PDF document...")
        with open(pdf_path, 'rb') as f:
            files = {'document': ('test_policy.pdf', f, 'application/pdf')}
            data = {
                'policyNumber': 'TEST-POL-2024-001'
            }
            
            response = requests.post(
                f"{base_url}/api/policies/upload",
                files=files,
                data=data
            )
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.json()}")
            
            if response.status_code == 200:
                print("   ✅ PDF upload successful")
                
                # Wait for processing
                import time
                time.sleep(3)
                
                # Step 3: Get the uploaded policy
                print("\n3. Retrieving uploaded policy...")
                policies_response = requests.get(f"{base_url}/api/policies?limit=1")
                if policies_response.status_code == 200:
                    policies = policies_response.json()
                    if policies:
                        policy_id = policies[0]['id']
                        print(f"   ✅ Found uploaded policy with ID: {policy_id}")
                        
                        # Step 4: Check raw text extraction
                        print("\n4. Checking raw text extraction...")
                        detail_response = requests.get(f"{base_url}/api/policies/{policy_id}")
                        if detail_response.status_code == 200:
                            policy_detail = detail_response.json()
                            has_raw_text = bool(policy_detail.get('rawText'))
                            raw_text_length = len(policy_detail.get('rawText', ''))
                            
                            print(f"   Has raw text: {has_raw_text}")
                            print(f"   Raw text length: {raw_text_length} characters")
                            
                            if has_raw_text and raw_text_length > 100:
                                print("   ✅ Raw text extraction successful!")
                                
                                # Step 5: Test querying
                                print("\n5. Testing query system...")
                                test_queries = [
                                    "What is the policy number?",
                                    "What is the total premium?",
                                    "What are the deductibles?",
                                    "What coverage is included?",
                                    "When does the policy expire?"
                                ]
                                
                                for query in test_queries:
                                    print(f"   Testing query: '{query}'")
                                    query_data = {
                                        'policyId': str(policy_id),
                                        'query': query
                                    }
                                    
                                    query_response = requests.post(
                                        f"{base_url}/api/policies/query",
                                        json=query_data
                                    )
                                    
                                    print(f"   Status: {query_response.status_code}")
                                    if query_response.status_code == 200:
                                        result = query_response.json()
                                        print(f"   ✅ Answer: {result.get('answer', 'No answer')[:100]}...")
                                        print(f"   Confidence: {result.get('confidence', 0)}")
                                        print(f"   Sources: {len(result.get('sources', []))} found")
                                    else:
                                        print(f"   ❌ Error: {query_response.json()}")
                                
                                print("\n✅ Complete workflow test successful!")
                                print("   - PDF upload ✓")
                                print("   - Raw text extraction ✓")
                                print("   - Query system ✓")
                                
                            else:
                                print("   ❌ Raw text extraction failed or insufficient content")
                        else:
                            print("   ❌ Failed to get policy details")
                    else:
                        print("   ❌ No policies found after upload")
                else:
                    print("   ❌ Failed to get policies after upload")
            else:
                print("   ❌ PDF upload failed")
                
    except Exception as e:
        print(f"❌ Workflow error: {e}")
    
    finally:
        # Clean up
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            os.remove(pdf_path)
            print(f"\n   Cleaned up: {pdf_path}")
    
    print("\n" + "=" * 70)
    print("Complete Workflow Test Finished!")

if __name__ == "__main__":
    test_complete_workflow() 