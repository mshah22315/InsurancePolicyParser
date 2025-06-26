"""
API routes for the insurance policy processing pipeline.
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import tempfile
from typing import Dict, List, Any
import uuid

from app import db
from app.models import ProcessedPolicyData

pipeline_bp = Blueprint('pipeline', __name__)

@pipeline_bp.route('/pipeline/upload-and-process', methods=['POST'])
def upload_and_process():
    """
    Upload policy documents and run the full pipeline
    """
    try:
        # Import here to avoid circular imports
        from pipeline_tasks import run_chained_pipeline
        
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': 'No files selected'}), 400
        
        # Check for invoice files
        invoice_files = request.files.getlist('invoice_files') if 'invoice_files' in request.files else []
        
        # Create temporary directory for uploaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = []
            invoice_paths = {}
            
            # Save policy documents
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(temp_dir, filename)
                    file.save(file_path)
                    file_paths.append(file_path)
            
            # Save invoice files and map to policy numbers
            for file in invoice_files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(temp_dir, filename)
                    file.save(file_path)
                    
                    # Extract policy number from filename (assuming format: POLICY_NUMBER_invoice.pdf)
                    parts = filename.split('_')
                    if len(parts) >= 2:
                        policy_number = parts[0]
                        invoice_paths[policy_number] = file_path
            
            # Run the chained pipeline
            task = run_chained_pipeline.delay(file_paths, invoice_paths if invoice_paths else None)
            
            return jsonify({
                'task_id': task.id,
                'status': 'started',
                'message': f'Chained pipeline started for {len(file_paths)} documents',
                'invoice_files': len(invoice_paths)
            }), 202
            
    except Exception as e:
        current_app.logger.error(f"Error in upload_and_process: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/pipeline/status/<task_id>', methods=['GET'])
def get_pipeline_status(task_id):
    """
    Get the status of a pipeline task
    """
    try:
        from celery.result import AsyncResult
        
        task_result = AsyncResult(task_id)
        
        if task_result.ready():
            if task_result.successful():
                result = task_result.result
                return jsonify({
                    'task_id': task_id,
                    'status': 'completed',
                    'result': result
                })
            else:
                return jsonify({
                    'task_id': task_id,
                    'status': 'failed',
                    'error': str(task_result.result)
                })
        else:
            # Get progress information if available
            info = task_result.info
            if info:
                return jsonify({
                    'task_id': task_id,
                    'status': 'running',
                    'progress': info
                })
            else:
                return jsonify({
                    'task_id': task_id,
                    'status': 'running'
                })
                
    except Exception as e:
        current_app.logger.error(f"Error getting task status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/pipeline/run-step', methods=['POST'])
def run_single_step():
    """
    Run a specific pipeline step
    """
    try:
        # Import here to avoid circular imports
        from pipeline_tasks import run_pipeline_step
        
        data = request.get_json()
        step_name = data.get('step_name')
        
        if not step_name:
            return jsonify({'error': 'step_name is required'}), 400
        
        # Validate step name
        valid_steps = ['process_documents', 'vector_processing', 'store_chunks', 'update_context']
        if step_name not in valid_steps:
            return jsonify({'error': f'Invalid step_name. Must be one of: {valid_steps}'}), 400
        
        # Run the step
        task = run_pipeline_step.delay(step_name, **data.get('parameters', {}))
        
        return jsonify({
            'task_id': task.id,
            'status': 'started',
            'step_name': step_name,
            'message': f'Step {step_name} started'
        }), 202
        
    except Exception as e:
        current_app.logger.error(f"Error running pipeline step: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/pipeline/policies', methods=['GET'])
def get_processed_policies():
    """
    Get list of processed policies
    """
    try:
        policies = ProcessedPolicyData.query.all()
        
        policy_list = []
        for policy in policies:
            policy_list.append({
                'id': policy.id,
                'policy_number': policy.policy_number,
                'insurer_name': policy.insurer_name,
                'policyholder_name': policy.policyholder_name,
                'property_address': policy.property_address,
                'effective_date': policy.effective_date.isoformat() if policy.effective_date else None,
                'expiration_date': policy.expiration_date.isoformat() if policy.expiration_date else None,
                'total_premium': float(policy.total_premium) if policy.total_premium else None,
                'created_at': policy.created_at.isoformat() if policy.created_at else None
            })
        
        return jsonify({
            'policies': policy_list,
            'count': len(policy_list)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting processed policies: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/pipeline/policy/<policy_number>', methods=['GET'])
def get_policy_details(policy_number):
    """
    Get detailed information about a specific policy
    """
    try:
        policy = ProcessedPolicyData.query.filter_by(policy_number=policy_number).first()
        
        if not policy:
            return jsonify({'error': 'Policy not found'}), 404
        
        return jsonify({
            'id': policy.id,
            'policy_number': policy.policy_number,
            'insurer_name': policy.insurer_name,
            'policyholder_name': policy.policyholder_name,
            'property_address': policy.property_address,
            'effective_date': policy.effective_date.isoformat() if policy.effective_date else None,
            'expiration_date': policy.expiration_date.isoformat() if policy.expiration_date else None,
            'total_premium': float(policy.total_premium) if policy.total_premium else None,
            'coverage_details': policy.coverage_details,
            'raw_text': policy.raw_text[:1000] + '...' if len(policy.raw_text) > 1000 else policy.raw_text,
            'original_document_gcs_path': policy.original_document_gcs_path,
            'structured_json_gcs_path': policy.structured_json_gcs_path,
            'created_at': policy.created_at.isoformat() if policy.created_at else None,
            'updated_at': policy.updated_at.isoformat() if policy.updated_at else None
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting policy details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/pipeline/health', methods=['GET'])
def pipeline_health():
    """
    Health check for the pipeline
    """
    try:
        # Test Redis connection first
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=5)
        redis_ping = r.ping()
        
        # Test Celery by trying to queue a simple task
        from pipeline_tasks import test_pipeline_health
        
        # Try to queue the task (this tests the connection without network inspection)
        try:
            result = test_pipeline_health.delay()
            # Wait a short time for the task to complete
            import time
            time.sleep(2)
            
            if result.ready():
                task_result = result.get()
                return jsonify({
                    'status': 'healthy',
                    'redis': 'connected',
                    'celery': 'operational',
                    'message': 'Pipeline is fully operational',
                    'task_result': task_result
                })
            else:
                return jsonify({
                    'status': 'warning',
                    'redis': 'connected',
                    'celery': 'task_queued_but_not_completed',
                    'message': 'Pipeline is running but task processing may be slow. This is normal on Windows.',
                    'task_id': result.id
                })
        except Exception as celery_error:
            return jsonify({
                'status': 'warning',
                'redis': 'connected',
                'celery': 'connection_issue',
                'message': f'Redis is working but Celery has issues: {str(celery_error)}',
                'note': 'This may be a Windows firewall issue. Try running a real pipeline task to test functionality.'
            })
            
    except Exception as e:
        current_app.logger.error(f"Pipeline health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@pipeline_bp.route('/pipeline/context-interactive/<policy_number>', methods=['POST'])
def start_interactive_context_update(policy_number):
    """
    Start interactive context update for a specific policy
    """
    try:
        # Import here to avoid circular imports
        from pipeline_tasks import update_context_interactive_step
        
        # Start the interactive context update task
        task = update_context_interactive_step.delay(policy_number)
        
        return jsonify({
            'task_id': task.id,
            'status': 'interactive_required',
            'policy_number': policy_number,
            'message': f'Interactive context update initiated for policy {policy_number}',
            'instructions': [
                '1. Run the interactive context update script:',
                f'   python scripts/update_policy_context.py --policy {policy_number}',
                '2. Or use the CLI command:',
                f'   python scripts/manage_pipeline.py context-interactive --policy {policy_number}',
                '3. Follow the prompts to upload roofing invoices and specify house features'
            ]
        }), 202
        
    except Exception as e:
        current_app.logger.error(f"Error starting interactive context update: {str(e)}")
        return jsonify({'error': str(e)}), 500 