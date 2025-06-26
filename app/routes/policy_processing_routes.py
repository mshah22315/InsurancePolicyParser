from flask import Blueprint, request, jsonify
from app.services.insurance_document_processor_service import InsuranceDocumentProcessorService
from ..models import ProcessedPolicyData
from ..db import db
from sqlalchemy import or_
from datetime import datetime
from . import main

policy_processing_bp = Blueprint('policy_processing', __name__)

@main.route('/api/v1/policies/process', methods=['POST'])
def process_policy():
    if 'policy_document' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['policy_document']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are allowed'}), 400
    
    try:
        # Read file content
        file_bytes = file.read()
        processor = InsuranceDocumentProcessorService()
        result = processor.process_document(file_bytes, file.filename)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@policy_processing_bp.route('/api/v1/policies', methods=['GET'])
def list_policies():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get query parameters for filtering
    policy_number = request.args.get('policy_number')
    insurer_name = request.args.get('insurer_name')
    policyholder_name = request.args.get('policyholder_name')
    
    # Build query
    query = ProcessedPolicyData.query
    
    if policy_number:
        query = query.filter(ProcessedPolicyData.policy_number.ilike(f'%{policy_number}%'))
    if insurer_name:
        query = query.filter(ProcessedPolicyData.insurer_name.ilike(f'%{insurer_name}%'))
    if policyholder_name:
        query = query.filter(ProcessedPolicyData.policyholder_name.ilike(f'%{policyholder_name}%'))
    
    # Execute paginated query
    pagination = query.order_by(ProcessedPolicyData.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    policies = pagination.items
    
    return jsonify({
        'policies': [{
            'id': policy.id,
            'policy_number': policy.policy_number,
            'insurer_name': policy.insurer_name,
            'policyholder_name': policy.policyholder_name,
            'effective_date': policy.effective_date.isoformat() if policy.effective_date else None,
            'expiration_date': policy.expiration_date.isoformat() if policy.expiration_date else None,
            'total_premium': policy.total_premium,
            'coverage_details': policy.coverage_details,
            'deductibles': policy.deductibles,
            'created_at': policy.created_at.isoformat()
        } for policy in policies],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@policy_processing_bp.route('/api/v1/policies/<int:policy_id>', methods=['GET'])
def get_policy(policy_id):
    policy = ProcessedPolicyData.query.get_or_404(policy_id)
    return jsonify({
        'id': policy.id,
        'policy_number': policy.policy_number,
        'insurer_name': policy.insurer_name,
        'policyholder_name': policy.policyholder_name,
        'property_address': policy.property_address,
        'effective_date': policy.effective_date.isoformat() if policy.effective_date else None,
        'expiration_date': policy.expiration_date.isoformat() if policy.expiration_date else None,
        'total_premium': policy.total_premium,
        'coverage_details': policy.coverage_details,
        'deductibles': policy.deductibles,
        'original_document_gcs_path': policy.original_document_gcs_path,
        'processed_json_gcs_path': policy.processed_json_gcs_path,
        'created_at': policy.created_at.isoformat(),
        'updated_at': policy.updated_at.isoformat()
    })

@policy_processing_bp.route('/api/v1/policies/search', methods=['GET'])
def search_policies():
    search_term = request.args.get('q', '')
    if not search_term:
        return jsonify({'status': 'error', 'message': 'Search term is required'}), 400
    
    policies = ProcessedPolicyData.query.filter(
        or_(
            ProcessedPolicyData.policy_number.ilike(f'%{search_term}%'),
            ProcessedPolicyData.insurer_name.ilike(f'%{search_term}%'),
            ProcessedPolicyData.policyholder_name.ilike(f'%{search_term}%'),
            ProcessedPolicyData.property_address.ilike(f'%{search_term}%')
        )
    ).all()
    
    return jsonify({
        'policies': [{
            'id': policy.id,
            'policy_number': policy.policy_number,
            'insurer_name': policy.insurer_name,
            'policyholder_name': policy.policyholder_name,
            'property_address': policy.property_address,
            'effective_date': policy.effective_date.isoformat() if policy.effective_date else None,
            'expiration_date': policy.expiration_date.isoformat() if policy.expiration_date else None,
            'total_premium': policy.total_premium,
            'coverage_details': policy.coverage_details,
            'deductibles': policy.deductibles
        } for policy in policies]
    })

@policy_processing_bp.route('/api/v1/policies/<int:policy_id>', methods=['DELETE'])
def delete_policy(policy_id):
    policy = ProcessedPolicyData.query.get_or_404(policy_id)
    try:
        db.session.delete(policy)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Policy deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500 