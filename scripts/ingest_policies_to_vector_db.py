import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

import json
from typing import List, Dict, Any
from app import create_app
from app.services.vector_service import VectorService
from google.cloud import storage
import logging
from tqdm import tqdm
from app.models import ProcessedPolicyData
from app.utils.gcs_utils import download_from_gcs
from app.db import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_raw_text(policy_data: dict) -> str:
    """Extract raw text from policy data, trying different possible fields."""
    # Try different possible fields for raw text
    possible_fields = ['raw_text', 'text', 'content', 'document_text', 'full_text']
    
    for field in possible_fields:
        text = policy_data.get(field)
        if isinstance(text, str) and text.strip():
            return text
    
    # If no raw text found, construct from available data
    text_parts = []
    
    # Add policy details
    for key, value in policy_data.items():
        if key not in ['coverage_details', 'raw_text', 'text', 'content', 'document_text', 'full_text']:
            if value is not None:
                text_parts.append(f"{key}: {value}")
    
    # Add coverage details
    if policy_data.get('coverage_details'):
        for coverage in policy_data['coverage_details']:
            coverage_text = []
            for key, value in coverage.items():
                if value is not None:
                    coverage_text.append(f"{key}: {value}")
            if coverage_text:
                text_parts.append("\n".join(coverage_text))
    
    return "\n\n".join(text_parts)

def chunk_policy_json(policy_data: dict, policy_id: str, source_filename: str) -> List[Dict[str, Any]]:
    """Split policy data into chunks for vector storage."""
    chunks = []
    
    # Helper function to create a chunk
    def create_chunk(text: str, section_type: str, chunk_index: int) -> Dict[str, Any]:
        return {
            'id': f"{policy_id}_chunk{chunk_index}",
            'policy_id': policy_id,
            'document_source_filename': source_filename,
            'section_type': section_type,
            'chunk_text': text
        }
    
    # Process policy details
    policy_details = []
    for key, value in policy_data.items():
        if key not in ['coverage_details', 'raw_text', 'text', 'content', 'document_text', 'full_text']:
            if value is not None:
                policy_details.append(f"{key}: {value}")
    
    if policy_details:
        chunks.append(create_chunk(
            "\n".join(policy_details),
            "policy_details",
            len(chunks)
        ))
    
    # Process coverage details
    if policy_data.get('coverage_details'):
        for i, coverage in enumerate(policy_data['coverage_details']):
            coverage_text = []
            for key, value in coverage.items():
                if value is not None:
                    coverage_text.append(f"{key}: {value}")
            
            if coverage_text:
                chunks.append(create_chunk(
                    "\n".join(coverage_text),
                    f"coverage_{i+1}",
                    len(chunks)
                ))
    
    # Process raw text if available
    raw_text = extract_raw_text(policy_data)
    if raw_text:
        # Split raw text into chunks of approximately 1000 characters
        chunk_size = 1000
        for i in range(0, len(raw_text), chunk_size):
            chunk_text = raw_text[i:i + chunk_size]
            chunks.append(create_chunk(
                chunk_text,
                "raw_text",
                len(chunks)
            ))
    
    return chunks

def create_policy_record(app, json_path: str, policy_data: dict) -> ProcessedPolicyData:
    """Create a new policy record in the database."""
    # Extract policy number from the data
    policy_number = policy_data.get('policy_number')
    if not policy_number:
        raise ValueError(f"No policy number found in JSON data for {json_path}")
    
    # Extract raw text
    raw_text = extract_raw_text(policy_data)
    
    # Create a new policy record
    policy = ProcessedPolicyData(
        policy_number=policy_number,
        insurer_name=policy_data.get('insurer_name'),
        policyholder_name=policy_data.get('policyholder_name'),
        property_address=policy_data.get('property_address'),
        effective_date=policy_data.get('effective_date'),
        expiration_date=policy_data.get('expiration_date'),
        total_premium=policy_data.get('total_premium'),
        coverage_details=policy_data.get('coverage_details'),
        raw_text=raw_text,
        original_document_gcs_path=json_path.replace('structured_jsons', 'original_documents').replace('.json', '.pdf'),
        processed_json_gcs_path=json_path
    )
    
    # Add to database
    db.session.add(policy)
    db.session.commit()
    
    return policy

def find_or_create_policy_record(app, json_path: str) -> ProcessedPolicyData:
    """Find an existing policy record or create a new one."""
    # Try exact match first
    policy = ProcessedPolicyData.query.filter_by(processed_json_gcs_path=json_path).first()
    if policy:
        return policy
    
    # Try matching by filename
    filename = os.path.basename(json_path)
    policy = ProcessedPolicyData.query.filter(
        ProcessedPolicyData.processed_json_gcs_path.like(f'%{filename}')
    ).first()
    if policy:
        return policy
    
    # Try matching by policy number
    try:
        json_content = download_from_gcs(json_path)
        policy_data = json.loads(json_content)
        
        if policy_data.get('policy_number'):
            policy = ProcessedPolicyData.query.filter_by(
                policy_number=policy_data['policy_number']
            ).first()
            if policy:
                # Update the policy record with the correct JSON path and raw text
                policy.processed_json_gcs_path = json_path
                policy.raw_text = extract_raw_text(policy_data)
                db.session.commit()
                return policy
            
            # If no match found, create a new policy record
            return create_policy_record(app, json_path, policy_data)
    except Exception as e:
        logger.error(f"Error reading JSON file {json_path}: {str(e)}")
        raise
    
    raise ValueError(f"Could not find or create policy record for {json_path}")

def main():
    # Initialize Flask app
    app = create_app()
    
    with app.app_context():
        # Initialize services
        storage_client = storage.Client()
        bucket = storage_client.bucket(app.config['GOOGLE_CLOUD_STORAGE_BUCKET'])
        vector_service = VectorService()
        
        # Get all JSON files from GCS
        blobs = bucket.list_blobs(prefix=app.config['GCS_STRUCTURED_JSONS_PREFIX'])
        json_files = [blob for blob in blobs if blob.name.endswith('.json')]
        
        # Process each file
        for blob in tqdm(json_files, desc="Processing files"):
            try:
                # Download and parse JSON first
                json_content = download_from_gcs(blob.name)
                policy_data = json.loads(json_content)
                
                # Find or create policy record
                policy = find_or_create_policy_record(app, blob.name)
                
                # Update raw text if it's not already set
                if not policy.raw_text:
                    policy.raw_text = extract_raw_text(policy_data)
                    db.session.commit()
                
                # Generate chunks
                chunks = chunk_policy_json(policy_data, str(policy.id), os.path.basename(policy.original_document_gcs_path))
                
                # Generate embeddings and prepare documents
                documents = []
                for chunk in chunks:
                    embedding = vector_service.get_text_embedding(chunk['chunk_text'])
                    chunk['embedding'] = embedding
                    documents.append(chunk)
                
                # Add to database
                vector_service.add_documents_to_db(documents)
                
            except Exception as e:
                print(f"Error processing {blob.name}: {str(e)}")
                continue

if __name__ == "__main__":
    main() 