#!/usr/bin/env python3
"""
Debug script to examine pipeline results structure.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent)
sys.path.append(project_root)

def debug_document_processing():
    """Debug the document processing step"""
    try:
        from pipeline_tasks import process_documents_step
        
        test_file = "data/policies/Sample Policy Doc 1.pdf"
        
        print(f"Debugging document processing with: {test_file}")
        
        # Process document
        result = process_documents_step.delay([test_file])
        doc_data = result.get(timeout=30)
        
        print(f"Raw result: {doc_data}")
        print(f"Status: {doc_data.get('status')}")
        print(f"Results type: {type(doc_data.get('results'))}")
        print(f"Results: {doc_data.get('results')}")
        
        if doc_data.get('results'):
            for i, r in enumerate(doc_data.get('results')):
                print(f"  Result {i}: {r}")
                print(f"    Status: {r.get('status')}")
                print(f"    Policy Number: {r.get('policy_number')}")
        
        # Try to extract policy numbers
        successful_policies = []
        for r in doc_data.get('results', []):
            if r.get('status') == 'success' and r.get('policy_number'):
                successful_policies.append(r['policy_number'])
        
        print(f"Successful policies: {successful_policies}")
        
    except Exception as e:
        print(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_document_processing() 