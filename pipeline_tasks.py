"""
Pipeline tasks for orchestrating the insurance policy processing workflow.
This orchestrates the services in the following sequence:
1. insurance_document_processor_service + process_policies
2. vector_service + ingest_policies_to_vector_db
3. store_policy_chunks
4. proactive_advisor_service + update_policy_context
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from celery import chain
from celery.utils.log import get_task_logger
import json
from datetime import datetime

# Add the project root directory to Python path
project_root = str(Path(__file__).parent)
sys.path.append(project_root)

# Import celery after path setup
from celery_config import celery
from app import create_app
from app.models import ProcessedPolicyData
from app.db import db

logger = get_task_logger(__name__)

@celery.task(bind=True)
def process_documents_step(self, file_paths: List[str]) -> Dict[str, Any]:
    """
    Step 1: Process documents using insurance_document_processor_service and process_policies
    """
    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': len(file_paths), 'step': 'Processing documents'})
        
        app = create_app()
        with app.app_context():
            from app.services.insurance_document_processor_service import InsuranceDocumentProcessorService
            
            processor = InsuranceDocumentProcessorService()
            results = []
            
            for i, file_path in enumerate(file_paths):
                try:
                    logger.info(f"Processing document {i+1}/{len(file_paths)}: {file_path}")
                    
                    # Read the PDF file
                    with open(file_path, 'rb') as f:
                        document_bytes = f.read()
                    
                    # Process the document
                    result = processor.process_document(document_bytes, os.path.basename(file_path))
                    
                    if result['status'] == 'success':
                        results.append({
                            'file_path': file_path,
                            'status': 'success',
                            'policy_number': result['data'].get('policy_number'),
                            'data': result['data']
                        })
                        logger.info(f"Successfully processed {file_path}")
                    else:
                        results.append({
                            'file_path': file_path,
                            'status': 'error',
                            'error': result['message']
                        })
                        logger.error(f"Failed to process {file_path}: {result['message']}")
                    
                    # Update progress
                    self.update_state(
                        state='PROGRESS', 
                        meta={'current': i+1, 'total': len(file_paths), 'step': 'Processing documents'}
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {str(e)}")
                    results.append({
                        'file_path': file_path,
                        'status': 'error',
                        'error': str(e)
                    })
            
            successful_policies = [r for r in results if r['status'] == 'success']
            logger.info(f"Document processing completed. {len(successful_policies)}/{len(file_paths)} successful")
            
            return {
                'status': 'success',
                'results': results,
                'successful_count': len(successful_policies),
                'total_count': len(file_paths)
            }
            
    except Exception as e:
        logger.error(f"Error in process_documents_step: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@celery.task(bind=True)
def vector_processing_step(self, policy_numbers: List[str]) -> Dict[str, Any]:
    """
    Step 2: Process vectors using vector_service and ingest_policies_to_vector_db
    """
    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': len(policy_numbers), 'step': 'Vector processing'})
        
        app = create_app()
        with app.app_context():
            from app.services.vector_service import VectorService
            from scripts.ingest_policies_to_vector_db import chunk_policy_json
            
            vector_service = VectorService()
            results = []
            
            for i, policy_number in enumerate(policy_numbers):
                try:
                    logger.info(f"Processing vectors for policy {i+1}/{len(policy_numbers)}: {policy_number}")
                    
                    # Get policy from database
                    policy = ProcessedPolicyData.query.filter_by(policy_number=policy_number).first()
                    if not policy:
                        logger.warning(f"Policy {policy_number} not found in database")
                        results.append({
                            'policy_number': policy_number,
                            'status': 'error',
                            'error': 'Policy not found in database'
                        })
                        continue
                    
                    # Create policy data dict
                    policy_data = {
                        'policy_number': policy.policy_number,
                        'insurer_name': policy.insurer_name,
                        'policyholder_name': policy.policyholder_name,
                        'property_address': policy.property_address,
                        'effective_date': policy.effective_date,
                        'expiration_date': policy.expiration_date,
                        'total_premium': policy.total_premium,
                        'coverage_details': policy.coverage_details,
                        'raw_text': policy.raw_text
                    }
                    
                    # Generate chunks
                    chunks = chunk_policy_json(
                        policy_data,
                        str(policy.id),
                        os.path.basename(policy.original_document_gcs_path)
                    )
                    
                    # Generate embeddings and prepare documents
                    documents = []
                    for chunk in chunks:
                        embedding = vector_service.get_text_embedding(chunk['chunk_text'])
                        chunk['embedding'] = embedding
                        documents.append(chunk)
                    
                    # Add to vector database
                    vector_service.add_documents_to_db(documents)
                    
                    results.append({
                        'policy_number': policy_number,
                        'status': 'success',
                        'chunks_count': len(chunks)
                    })
                    
                    logger.info(f"Successfully processed vectors for {policy_number}")
                    
                    # Update progress
                    self.update_state(
                        state='PROGRESS', 
                        meta={'current': i+1, 'total': len(policy_numbers), 'step': 'Vector processing'}
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing vectors for {policy_number}: {str(e)}")
                    results.append({
                        'policy_number': policy_number,
                        'status': 'error',
                        'error': str(e)
                    })
            
            successful_policies = [r for r in results if r['status'] == 'success']
            logger.info(f"Vector processing completed. {len(successful_policies)}/{len(policy_numbers)} successful")
            
            return {
                'status': 'success',
                'results': results,
                'successful_count': len(successful_policies),
                'total_count': len(policy_numbers)
            }
            
    except Exception as e:
        logger.error(f"Error in vector_processing_step: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@celery.task(bind=True)
def store_chunks_step(self, policy_numbers: List[str]) -> Dict[str, Any]:
    """
    Step 3: Store policy chunks using store_policy_chunks
    """
    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': len(policy_numbers), 'step': 'Storing chunks'})
        
        app = create_app()
        with app.app_context():
            from scripts.store_policy_chunks import chunk_policy_json, get_or_create_policy
            
            results = []
            
            for i, policy_number in enumerate(policy_numbers):
                try:
                    logger.info(f"Storing chunks for policy {i+1}/{len(policy_numbers)}: {policy_number}")
                    
                    # Get policy from database
                    processed_policy = ProcessedPolicyData.query.filter_by(policy_number=policy_number).first()
                    if not processed_policy:
                        logger.warning(f"Policy {policy_number} not found in database")
                        results.append({
                            'policy_number': policy_number,
                            'status': 'error',
                            'error': 'Policy not found in database'
                        })
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
                        policy.id,
                        os.path.basename(processed_policy.original_document_gcs_path)
                    )
                    
                    # Generate embeddings for chunks
                    from app.services.vector_service import VectorService
                    vector_service = VectorService()
                    
                    # Store chunks in database
                    from app.models import PolicyChunk
                    for chunk_data in chunks:
                        # Generate embedding for the chunk text
                        embedding = vector_service.get_text_embedding(chunk_data['chunk_text'])
                        
                        chunk = PolicyChunk(
                            policy_id=policy.id,
                            document_source_filename=chunk_data['document_source_filename'],
                            section_type=chunk_data['section_type'],
                            chunk_text=chunk_data['chunk_text'],
                            embedding=embedding
                        )
                        db.session.add(chunk)
                    
                    db.session.commit()
                    
                    results.append({
                        'policy_number': policy_number,
                        'status': 'success',
                        'chunks_count': len(chunks)
                    })
                    
                    logger.info(f"Successfully stored chunks for {policy_number}")
                    
                    # Update progress
                    self.update_state(
                        state='PROGRESS', 
                        meta={'current': i+1, 'total': len(policy_numbers), 'step': 'Storing chunks'}
                    )
                    
                except Exception as e:
                    logger.error(f"Error storing chunks for {policy_number}: {str(e)}")
                    results.append({
                        'policy_number': policy_number,
                        'status': 'error',
                        'error': str(e)
                    })
            
            successful_policies = [r for r in results if r['status'] == 'success']
            logger.info(f"Chunk storage completed. {len(successful_policies)}/{len(policy_numbers)} successful")
            
            return {
                'status': 'success',
                'results': results,
                'successful_count': len(successful_policies),
                'total_count': len(policy_numbers)
            }
            
    except Exception as e:
        logger.error(f"Error in store_chunks_step: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@celery.task(bind=True)
def update_context_step(self, policy_numbers: List[str], invoice_paths: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Step 4: Update policy context (non-interactive version)
    This step updates basic context data without user interaction.
    For full interactive updates, use update_context_interactive_step.
    """
    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': len(policy_numbers), 'step': 'Updating context'})
        
        app = create_app()
        with app.app_context():
            from scripts.update_policy_context import extract_installation_date_from_invoice, calculate_roof_age
            
            results = []
            
            for i, policy_number in enumerate(policy_numbers):
                try:
                    logger.info(f"Updating context for policy {i+1}/{len(policy_numbers)}: {policy_number}")
                    
                    # Get policy from database
                    policy = ProcessedPolicyData.query.filter_by(policy_number=policy_number).first()
                    if not policy:
                        logger.warning(f"Policy {policy_number} not found in database")
                        results.append({
                            'policy_number': policy_number,
                            'status': 'error',
                            'error': 'Policy not found in database'
                        })
                        continue
                    
                    # Set renewal date from expiration date
                    renewal_date = None
                    if policy.expiration_date:
                        renewal_date = policy.expiration_date.strftime('%Y-%m-%d')
                        logger.info(f"Set renewal date from database expiration_date: {renewal_date}")
                    
                    # Calculate roof age from invoice if provided
                    roof_age = None
                    if invoice_paths and policy_number in invoice_paths:
                        invoice_path = invoice_paths[policy_number]
                        if os.path.exists(invoice_path):
                            installation_date = extract_installation_date_from_invoice(invoice_path)
                            if installation_date:
                                roof_age = calculate_roof_age(installation_date)
                                logger.info(f"Calculated roof age: {roof_age} years (from {installation_date})")
                    
                    # Update policy context (non-interactive version)
                    try:
                        # Get or create policy record
                        from scripts.store_policy_chunks import get_or_create_policy
                        policy_record = get_or_create_policy(policy)
                        
                        # Update with available data
                        if roof_age is not None:
                            policy_record.roof_age = roof_age
                        
                        if renewal_date:
                            try:
                                policy_record.renewal_date = datetime.strptime(renewal_date, '%Y-%m-%d').date()
                            except ValueError:
                                logger.warning(f"Invalid renewal date format: {renewal_date}")
                        
                        # Set default features if none provided
                        default_features = ["monitored_alarm"]  # Default feature
                        policy_record.features = json.dumps(default_features)
                        
                        db.session.commit()
                        
                        success = True
                        logger.info(f"Successfully updated context for {policy_number}")
                        
                    except Exception as e:
                        logger.error(f"Error updating policy context: {str(e)}")
                        db.session.rollback()
                        success = False
                    
                    results.append({
                        'policy_number': policy_number,
                        'status': 'success' if success else 'error',
                        'roof_age': roof_age,
                        'renewal_date': renewal_date,
                        'message': 'Basic context updated. Use interactive update for full customization.'
                    })
                    
                    # Update progress
                    self.update_state(
                        state='PROGRESS', 
                        meta={'current': i+1, 'total': len(policy_numbers), 'step': 'Updating context'}
                    )
                    
                except Exception as e:
                    logger.error(f"Error updating context for {policy_number}: {str(e)}")
                    results.append({
                        'policy_number': policy_number,
                        'status': 'error',
                        'error': str(e)
                    })
            
            successful_policies = [r for r in results if r['status'] == 'success']
            logger.info(f"Context update completed. {len(successful_policies)}/{len(policy_numbers)} successful")
            
            return {
                'status': 'success',
                'results': results,
                'successful_count': len(successful_policies),
                'total_count': len(policy_numbers)
            }
            
    except Exception as e:
        logger.error(f"Error in update_context_step: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@celery.task
def update_context_interactive_step(policy_number: str) -> Dict[str, Any]:
    """
    Interactive context update step that allows user input for roofing invoices and features.
    This should be called separately after the main pipeline completes.
    """
    try:
        logger.info(f"Starting interactive context update for policy: {policy_number}")
        
        # This task will return immediately with instructions for the user
        return {
            'status': 'interactive_required',
            'message': f'Interactive context update required for policy {policy_number}',
            'policy_number': policy_number,
            'instructions': [
                '1. Run the interactive context update script:',
                f'   python scripts/update_policy_context.py --policy {policy_number}',
                '2. Or use the CLI command:',
                f'   python scripts/manage_pipeline.py context-interactive --policy {policy_number}',
                '3. Follow the prompts to upload roofing invoices and specify house features'
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in interactive context update: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@celery.task
def extract_policy_numbers_from_docs(result):
    """Extract policy numbers from document processing result"""
    if result.get('status') == 'success':
        successful_policies = [
            r['policy_number'] for r in result.get('results', [])
            if r.get('status') == 'success' and r.get('policy_number')
        ]
        return successful_policies
    return []

@celery.task
def extract_policy_numbers_from_vector(result):
    """Extract policy numbers from vector processing result"""
    if result.get('status') == 'success':
        successful_policies = [
            r['policy_number'] for r in result.get('results', [])
            if r.get('status') == 'success' and r.get('policy_number')
        ]
        return successful_policies
    return []

@celery.task
def extract_policy_numbers_from_chunks(result):
    """Extract policy numbers from chunk storage result"""
    if result.get('status') == 'success':
        successful_policies = [
            r['policy_number'] for r in result.get('results', [])
            if r.get('status') == 'success' and r.get('policy_number')
        ]
        return successful_policies
    return []

@celery.task
def run_chained_pipeline(file_paths: List[str], invoice_paths: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Run the complete pipeline using Celery chains for proper sequencing
    """
    try:
        logger.info(f"Starting chained pipeline for {len(file_paths)} documents")
        
        # Create a chain of tasks that will execute in sequence
        pipeline_chain = chain(
            process_documents_step.s(file_paths),
            extract_policy_numbers_from_docs.s(),
            vector_processing_step.s(),
            extract_policy_numbers_from_vector.s(),
            store_chunks_step.s(),
            extract_policy_numbers_from_chunks.s(),
            update_context_step.s(invoice_paths)
        )
        
        # Execute the chain
        result = pipeline_chain.apply_async()
        
        return {
            'status': 'started',
            'message': f'Chained pipeline started for {len(file_paths)} documents',
            'task_id': result.id,
            'chain_id': result.id
        }
        
    except Exception as e:
        logger.error(f"Error starting chained pipeline: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@celery.task
def run_full_pipeline(file_paths: List[str], invoice_paths: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Run the complete pipeline in sequence:
    1. Process documents
    2. Vector processing
    3. Store chunks
    4. Update context
    """
    try:
        logger.info(f"Starting full pipeline for {len(file_paths)} documents")
        
        # Step 1: Process documents
        doc_result = process_documents_step.delay(file_paths)
        
        # Return the task ID for the first step - the client can check status
        return {
            'status': 'started',
            'message': f'Pipeline started for {len(file_paths)} documents',
            'task_id': doc_result.id,
            'step': 'document_processing',
            'next_steps': ['vector_processing', 'store_chunks', 'update_context']
        }
        
    except Exception as e:
        logger.error(f"Error in full pipeline: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@celery.task
def run_pipeline_step(step_name: str, **kwargs) -> Dict[str, Any]:
    """
    Run a specific pipeline step
    """
    try:
        if step_name == 'process_documents':
            return process_documents_step.delay(kwargs.get('file_paths', [])).get()
        elif step_name == 'vector_processing':
            return vector_processing_step.delay(kwargs.get('policy_numbers', [])).get()
        elif step_name == 'store_chunks':
            return store_chunks_step.delay(kwargs.get('policy_numbers', [])).get()
        elif step_name == 'update_context':
            return update_context_step.delay(
                kwargs.get('policy_numbers', []),
                kwargs.get('invoice_paths')
            ).get()
        else:
            return {'status': 'error', 'error': f'Unknown step: {step_name}'}
    except Exception as e:
        logger.error(f"Error running pipeline step {step_name}: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@celery.task
def test_pipeline_health():
    """
    Simple test task to verify pipeline health
    """
    return {
        'status': 'healthy',
        'message': 'Pipeline is operational',
        'timestamp': '2025-06-25'
    } 