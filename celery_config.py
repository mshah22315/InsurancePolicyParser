import os
from celery import Celery

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND', os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')),
        broker=app.config.get('CELERY_BROKER_URL', os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'))
    )
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Create a placeholder celery instance that will be configured later
celery = Celery('insurance_policy_parser')
celery.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60  # 30 minutes
)

import pipeline_tasks