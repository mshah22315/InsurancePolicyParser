#!/usr/bin/env python3
"""
Simple test script to verify the pipeline is working without relying on health checks.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent)
sys.path.append(project_root)

def test_redis_connection():
    """Test Redis connection"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=5)
        result = r.ping()
        print(f"✓ Redis connection: {'SUCCESS' if result else 'FAILED'}")
        return result
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False

def test_celery_task():
    """Test if Celery can queue and process a simple task"""
    try:
        from pipeline_tasks import test_pipeline_health
        
        print("Testing Celery task queue...")
        result = test_pipeline_health.delay()
        
        # Wait for the task to complete
        import time
        for i in range(10):  # Wait up to 10 seconds
            if result.ready():
                task_result = result.get()
                print(f"✓ Celery task completed: {task_result}")
                return True
            time.sleep(1)
            print(f"  Waiting for task completion... ({i+1}/10)")
        
        print("✗ Celery task did not complete within 10 seconds")
        return False
        
    except Exception as e:
        print(f"✗ Celery task failed: {e}")
        return False

def test_flask_app():
    """Test if Flask app can be created"""
    try:
        from app import create_app
        app = create_app()
        print("✓ Flask app created successfully")
        return True
    except Exception as e:
        print(f"✗ Flask app creation failed: {e}")
        return False

def main():
    print("Insurance Policy Pipeline - Component Test")
    print("=" * 50)
    
    # Test Redis
    redis_ok = test_redis_connection()
    
    # Test Flask
    flask_ok = test_flask_app()
    
    # Test Celery
    celery_ok = test_celery_task()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"Redis:     {'✓ WORKING' if redis_ok else '✗ FAILED'}")
    print(f"Flask:     {'✓ WORKING' if flask_ok else '✗ FAILED'}")
    print(f"Celery:    {'✓ WORKING' if celery_ok else '✗ FAILED'}")
    
    if redis_ok and flask_ok and celery_ok:
        print("\n🎉 ALL COMPONENTS WORKING! Your pipeline is ready to use.")
        print("\nYou can now:")
        print("1. Use the API endpoints at http://127.0.0.1:5000/pipeline/*")
        print("2. Use the CLI: python scripts/manage_pipeline.py")
        print("3. Upload and process insurance documents")
    else:
        print("\n⚠️  Some components failed. Check the errors above.")
        
        if not redis_ok:
            print("\nRedis issues:")
            print("- Make sure Redis is running: docker ps")
            print("- If not running: docker start redis-server")
            
        if not celery_ok:
            print("\nCelery issues:")
            print("- Make sure Celery worker is running with: python -m celery -A celery_config worker --loglevel=info")
            print("- Try using --pool=solo for Windows: python -m celery -A celery_config worker --loglevel=info --pool=solo")

if __name__ == '__main__':
    main() 