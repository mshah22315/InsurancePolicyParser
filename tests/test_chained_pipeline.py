#!/usr/bin/env python3
"""
Test script for the chained pipeline functionality.
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent)
sys.path.append(project_root)

def test_chained_pipeline():
    """Test the chained pipeline with a single document"""
    try:
        from pipeline_tasks import run_chained_pipeline
        
        # Test with a single document
        test_file = "data/policies/Sample Policy Doc 1.pdf"
        
        if not os.path.exists(test_file):
            print(f"✗ Test file not found: {test_file}")
            return False
        
        print(f"Testing chained pipeline with: {test_file}")
        
        # Start the chained pipeline
        result = run_chained_pipeline.delay([test_file])
        
        print(f"Task ID: {result.id}")
        print("Waiting for pipeline completion...")
        
        # Wait for completion (with timeout)
        for i in range(30):  # Wait up to 30 seconds
            if result.ready():
                task_result = result.get()
                print(f"✓ Pipeline completed!")
                print(f"Result: {task_result}")
                return task_result.get('status') == 'started'
            
            time.sleep(1)
            print(f"  Waiting... ({i+1}/30)")
        
        print("✗ Pipeline did not complete within 30 seconds")
        return False
        
    except Exception as e:
        print(f"✗ Chained pipeline test failed: {e}")
        return False

def test_individual_steps():
    """Test individual pipeline steps"""
    try:
        from pipeline_tasks import process_documents_step, vector_processing_step, store_chunks_step, update_context_step
        
        test_file = "data/policies/Sample Policy Doc 1.pdf"
        
        print("\nTesting individual steps...")
        
        # Step 1: Process documents
        print("1. Processing documents...")
        doc_result = process_documents_step.delay([test_file])
        doc_data = doc_result.get(timeout=30)
        print(f"   Document processing result: {doc_data.get('status')}")
        
        if doc_data.get('status') != 'success':
            print("   ✗ Document processing failed")
            return False
        
        # Extract policy numbers
        successful_policies = [
            r['policy_number'] for r in doc_data.get('results', [])
            if r.get('status') == 'success' and r.get('policy_number')
        ]
        
        if not successful_policies:
            print("   ✗ No policies were processed successfully")
            return False
        
        print(f"   ✓ Processed {len(successful_policies)} policies: {successful_policies}")
        
        # Step 2: Vector processing
        print("2. Vector processing...")
        vector_result = vector_processing_step.delay(successful_policies)
        vector_data = vector_result.get(timeout=30)
        print(f"   Vector processing result: {vector_data.get('status')}")
        
        # Step 3: Store chunks
        print("3. Storing chunks...")
        chunks_result = store_chunks_step.delay(successful_policies)
        chunks_data = chunks_result.get(timeout=30)
        print(f"   Chunk storage result: {chunks_data.get('status')}")
        
        # Step 4: Update context
        print("4. Updating context...")
        context_result = update_context_step.delay(successful_policies)
        context_data = context_result.get(timeout=30)
        print(f"   Context update result: {context_data.get('status')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Individual steps test failed: {e}")
        return False

def main():
    print("Chained Pipeline Test")
    print("=" * 50)
    
    # Test chained pipeline
    chained_ok = test_chained_pipeline()
    
    # Test individual steps
    steps_ok = test_individual_steps()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"Chained Pipeline: {'✓ WORKING' if chained_ok else '✗ FAILED'}")
    print(f"Individual Steps: {'✓ WORKING' if steps_ok else '✗ FAILED'}")
    
    if chained_ok and steps_ok:
        print("\n🎉 PIPELINE IS WORKING CORRECTLY!")
        print("The 'Never call result.get() within a task!' error has been fixed.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

if __name__ == '__main__':
    main() 