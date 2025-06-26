from google.cloud import storage
from flask import current_app
import tempfile

def upload_to_gcs(file_data: bytes, destination_blob_name: str, content_type: str = None) -> str:
    """Upload a file to Google Cloud Storage."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(current_app.config['GOOGLE_CLOUD_STORAGE_BUCKET'])
    blob = bucket.blob(destination_blob_name)
    
    blob.upload_from_string(
        file_data,
        content_type=content_type
    )
    
    return f"gs://{bucket.name}/{destination_blob_name}"

def download_from_gcs(source_blob_name: str) -> bytes:
    """Download a file from Google Cloud Storage."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(current_app.config['GOOGLE_CLOUD_STORAGE_BUCKET'])
    blob = bucket.blob(source_blob_name)
    
    return blob.download_as_bytes() 