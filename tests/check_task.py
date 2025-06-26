#!/usr/bin/env python3
"""
Check task status and provide timing information
"""

import sys
from celery.result import AsyncResult
from celery_config import celery

def check_task(task_id):
    """Check the status of a specific task"""
    result = AsyncResult(task_id, app=celery)
    
    print(f"Task ID: {task_id}")
    print(f"State: {result.state}")
    print(f"Ready: {result.ready()}")
    
    if result.ready():
        print(f"Success: {result.successful()}")
        if result.successful():
            print("✅ Task completed successfully!")
            print("Result:")
            print(result.result)
        else:
            print("❌ Task failed!")
            print(f"Error: {result.result}")
    else:
        print("⏳ Task is still running...")
        
        # Try to get progress info
        info = result.info
        if info:
            print("Progress info:")
            print(info)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_task.py <task_id>")
        sys.exit(1)
    
    task_id = sys.argv[1]
    check_task(task_id) 