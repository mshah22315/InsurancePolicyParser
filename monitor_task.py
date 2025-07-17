#!/usr/bin/env python3
"""
Task monitoring script for the insurance policy processing pipeline.
This script provides detailed information about task status and progress.
"""

import sys
import json
from datetime import datetime

def monitor_task(task_id):
    """Monitor a specific task and provide detailed status"""
    try:
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id)
        
        print(f"Task ID: {task_id}")
        print(f"Status: {result.status}")
        print(f"Ready: {result.ready()}")
        print(f"Successful: {result.successful()}")
        print(f"Failed: {result.failed()}")
        
        if result.info:
            print(f"\nTask Info:")
            if isinstance(result.info, dict):
                for key, value in result.info.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {result.info}")
        
        if result.result:
            print(f"\nTask Result:")
            if isinstance(result.result, dict):
                print(json.dumps(result.result, indent=2, default=str))
            else:
                print(f"  {result.result}")
        
        if result.traceback:
            print(f"\nError Traceback:")
            print(result.traceback)
        
        # Check if task is taking too long
        if result.date_done:
            duration = result.date_done - result.date_start
            print(f"\nTask Duration: {duration}")
        elif result.date_start:
            current_time = datetime.now()
            duration = current_time - result.date_start
            print(f"\nTask Running For: {duration}")
            
            # Warning if task is running for more than 30 minutes
            if duration.total_seconds() > 1800:  # 30 minutes
                print("⚠️  WARNING: Task has been running for more than 30 minutes!")
                print("   This might indicate an issue. Consider checking:")
                print("   - Redis server status")
                print("   - Celery worker logs")
                print("   - Database connectivity")
        
        return result
        
    except Exception as e:
        print(f"Error monitoring task: {e}")
        return None

def check_redis_status():
    """Check if Redis is running"""
    try:
        import redis
        r = redis.Redis()
        r.ping()
        print("✓ Redis is running")
        return True
    except Exception as e:
        print(f"✗ Redis is not running: {e}")
        return False

def check_celery_workers():
    """Check if Celery workers are active"""
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print("✓ Celery workers are active:")
            for worker, tasks in active_workers.items():
                print(f"  - {worker}: {len(tasks)} active tasks")
        else:
            print("✗ No active Celery workers found")
            
        return bool(active_workers)
    except Exception as e:
        print(f"✗ Error checking Celery workers: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python monitor_task.py <task_id>")
        print("\nExample: python monitor_task.py 67a621ac-0777-4ced-a91c-00c4254f1086")
        sys.exit(1)
    
    task_id = sys.argv[1]
    
    print("Insurance Policy Pipeline - Task Monitor")
    print("=" * 50)
    
    # Check system status
    print("\nSystem Status:")
    print("-" * 20)
    redis_ok = check_redis_status()
    workers_ok = check_celery_workers()
    
    print(f"\nTask Details:")
    print("-" * 20)
    result = monitor_task(task_id)
    
    # Provide recommendations
    print(f"\nRecommendations:")
    print("-" * 20)
    
    if not redis_ok:
        print("• Start Redis server")
        print("• Check if Redis is running on localhost:6379")
    
    if not workers_ok:
        print("• Start Celery worker: celery -A celery_config worker --loglevel=info --pool=solo")
    
    if result and result.status == 'PENDING':
        print("• Task is pending - check if Celery workers are running")
    
    if result and result.status == 'RUNNING':
        print("• Task is running - this is normal for large documents")
        print("• Check Celery worker logs for detailed progress")
    
    if result and result.status == 'FAILURE':
        print("• Task failed - check the error traceback above")
        print("• Review Celery worker logs for more details")

if __name__ == '__main__':
    main() 