import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Google Cloud Storage configuration
    GOOGLE_CLOUD_STORAGE_BUCKET = os.getenv('GOOGLE_CLOUD_STORAGE_BUCKET')
    GCS_ORIGINAL_PDFS_PREFIX = os.getenv('GCS_ORIGINAL_PDFS_PREFIX', 'original/')
    GCS_STRUCTURED_JSONS_PREFIX = os.getenv('GCS_STRUCTURED_JSONS_PREFIX', 'structured/')
    
    # Google AI configuration
    GOOGLE_AI_API_KEY = os.getenv('GOOGLE_AI_API_KEY')
    
    # Vector database configuration
    VECTOR_DB_EMBEDDING_MODEL = os.getenv('VECTOR_DB_EMBEDDING_MODEL', 'gemini-1.5-flash')
    VECTOR_DB_EMBEDDING_DIMENSIONS = int(os.getenv('VECTOR_DB_EMBEDDING_DIMENSIONS', '768'))
    
    # Celery configuration
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False 