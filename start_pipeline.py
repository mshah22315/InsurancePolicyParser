#!/usr/bin/env python3
"""
Startup script for the insurance policy processing pipeline.
This script starts both the Flask application and Celery worker.
"""

import sys
import subprocess
import time
import threading

def start_flask_app():
    """Start the Flask application"""
    print("Starting Flask application...")
    try:
        subprocess.run([sys.executable, "run.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting Flask app: {e}")
    except KeyboardInterrupt:
        print("Flask app stopped by user")

def start_celery_worker():
    """Start the Celery worker"""
    print("Starting Celery worker...")
    try:
        subprocess.run([sys.executable, "-m", "celery", "-A", "celery_config", "worker", "--loglevel=info"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting Celery worker: {e}")
    except KeyboardInterrupt:
        print("Celery worker stopped by user")

def check_redis():
    """Check if Redis server is running"""
    print("Checking Redis server...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=5)
        r.ping()
        print("✓ Redis server is running.")
        return True
    except Exception as e:
        print("✗ Redis server is not running.")
        print("Please start Redis manually:")
        print("  Windows: Download and run Redis server")
        print("  Linux/Mac: redis-server")
        print("  Docker: docker run -d -p 6379:6379 redis:alpine")
        print(f"  Error: {e}")
        return False

def main():
    print("Insurance Policy Processing Pipeline")
    print("=" * 50)
    
    # Check if Redis is running
    if not check_redis():
        print("\nCannot start pipeline without Redis. Please start Redis first.")
        return
    
    print("\nStarting pipeline components...")
    
    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=start_flask_app, daemon=True)
    flask_thread.start()
    
    # Give Flask a moment to start
    time.sleep(3)
    
    # Start Celery worker
    try:
        start_celery_worker()
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)

if __name__ == '__main__':
    main() 