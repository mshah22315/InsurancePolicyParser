#!/usr/bin/env python3
"""
Celery worker script for the insurance policy processing pipeline.
Run this script to start a Celery worker that will process pipeline tasks.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent)
sys.path.append(project_root)

from celery_config import celery

if __name__ == '__main__':
    # Start the Celery worker
    celery.start() 