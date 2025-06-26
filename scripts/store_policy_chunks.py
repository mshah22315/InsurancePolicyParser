import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

import json
from typing import List, Dict, Any
from flask import Flask
from app import create_app
from app.services.vector_service import VectorService
from google.cloud import storage
import logging
from tqdm import tqdm
from app.models import ProcessedPolicyData, PolicyChunk, Policy
from app.utils.gcs_utils import download_from_gcs
from datetime import datetime
from app.db import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def chunk_policy_json(policy_data: dict, policy_id: int, source_filename: str) -> List[Dict[str, Any]]:
    """Split policy data into chunks for vector storage."""
    chunks = []
    
    # Helper function to create a chunk
    def create_chunk(text: str, section_type: str, chunk_index: int) -> Dict[str, Any]:
        return {
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
    raw_text = policy_data.get('raw_text', '')
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

def store_chunks_in_db(chunks: List[Dict[str, Any]], vector_service: VectorService):
    """Store chunks in the database with their embeddings."""
    current_time = datetime.utcnow()
    
    for chunk in chunks:
        try:
            # Generate embedding for the chunk
            embedding = vector_service.get_text_embedding(chunk['chunk_text'])
            
            # Create new chunk record
            policy_chunk = PolicyChunk(
                policy_id=chunk['policy_id'],
                document_source_filename=chunk['document_source_filename'],
                section_type=chunk['section_type'],
                chunk_text=chunk['chunk_text'],
                embedding=embedding,
                created_at=current_time,
                updated_at=current_time
            )
            
            # Add to database
            db.session.add(policy_chunk)
            db.session.commit()
            
            print(f"Stored chunk for policy {chunk['policy_id']}, section: {chunk['section_type']}")
            
        except Exception as e:
            logger.error(f"Error storing chunk for policy {chunk['policy_id']}: {str(e)}")
            db.session.rollback()
            continue

def get_or_create_policy(processed_policy: ProcessedPolicyData) -> Policy:
    """Get or create a policy record in the policies table."""
    # Try to find existing policy by document source filename
    policy = Policy.query.filter_by(
        document_source_filename=os.path.basename(processed_policy.original_document_gcs_path)
    ).first()
    
    if not policy:
        # Create new policy record
        policy = Policy(
            document_source_filename=os.path.basename(processed_policy.original_document_gcs_path)
        )
        db.session.add(policy)
        db.session.commit()
        print(f"Created new policy record for {processed_policy.policy_number}")
    
    return policy

def main():
    # Initialize Flask app
    app = create_app()
    
    with app.app_context():
        # Initialize services
        storage_client = storage.Client()
        bucket = storage_client.bucket(app.config['GOOGLE_CLOUD_STORAGE_BUCKET'])
        vector_service = VectorService()
        
        # Get all policies from database
        processed_policies = ProcessedPolicyData.query.all()
        
        print(f"Found {len(processed_policies)} policies to process")
        
        # Process each policy
        for processed_policy in tqdm(processed_policies, desc="Processing policies"):
            try:
                # Skip if no raw text
                if not processed_policy.raw_text:
                    print(f"Skipping policy {processed_policy.policy_number} - no raw text")
                    continue
                
                # Get or create policy record
                policy = get_or_create_policy(processed_policy)
                
                # Create policy data dict
                policy_data = {
                    'policy_number': processed_policy.policy_number,
                    'insurer_name': processed_policy.insurer_name,
                    'policyholder_name': processed_policy.policyholder_name,
                    'property_address': processed_policy.property_address,
                    'effective_date': processed_policy.effective_date,
                    'expiration_date': processed_policy.expiration_date,
                    'total_premium': processed_policy.total_premium,
                    'coverage_details': processed_policy.coverage_details,
                    'raw_text': processed_policy.raw_text
                }
                
                # Generate chunks
                chunks = chunk_policy_json(
                    policy_data,
                    policy.id,  # Use the ID from the policies table
                    os.path.basename(processed_policy.original_document_gcs_path)
                )
                
                print(f"Generated {len(chunks)} chunks for policy {processed_policy.policy_number}")
                
                # Store chunks in database
                store_chunks_in_db(chunks, vector_service)
                
                print(f"Successfully processed policy {processed_policy.policy_number}")
                
            except Exception as e:
                print(f"Error processing policy {processed_policy.policy_number}: {str(e)}")
                continue

if __name__ == "__main__":
    main() 