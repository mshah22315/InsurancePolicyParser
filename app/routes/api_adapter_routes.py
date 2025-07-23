"""
API Adapter Routes - Provides endpoints that match frontend expectations
"""
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import tempfile
import uuid
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_
from app.models import ProcessedPolicyData, Policy, PolicyChunk, Feedback, db
from app import db
from app.utils.text_utils import extract_raw_text
import difflib

api_adapter_bp = Blueprint('api_adapter', __name__)

# Mock data for features and processing tasks (since they don't exist in backend yet)
def get_mock_dashboard_stats():
    """Get dashboard statistics"""
    try:
        total_policies = ProcessedPolicyData.query.count()
        
        # Mock processing queue (would need actual task tracking)
        processing_queue = 0
        
        # Mock completed today
        today = datetime.now().date()
        completed_today = ProcessedPolicyData.query.filter(
            func.date(ProcessedPolicyData.created_at) == today
        ).count()
        
        return {
            'totalPolicies': total_policies,
            'processingQueue': processing_queue,
            'completedToday': completed_today,
            'avgProcessingTime': '2.3m'
        }
    except Exception as e:
        current_app.logger.error(f"Error getting dashboard stats: {str(e)}")
        return {
            'totalPolicies': 0,
            'processingQueue': 0,
            'completedToday': 0,
            'avgProcessingTime': '0m'
        }

@api_adapter_bp.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = get_mock_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': 'Failed to fetch dashboard stats'}), 500

@api_adapter_bp.route('/api/policies', methods=['GET'])
def get_policies():
    """Get policies with pagination"""
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        policies = ProcessedPolicyData.query.order_by(
            ProcessedPolicyData.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        result = []
        for policy in policies:
            result.append({
                'id': policy.id,
                'policyNumber': policy.policy_number,
                'insurerName': policy.insurer_name,
                'policyholderName': policy.policyholder_name,
                'propertyAddress': policy.property_address,
                'totalPremium': policy.total_premium,
                'effectiveDate': policy.effective_date.isoformat() if policy.effective_date else None,
                'expirationDate': policy.expiration_date.isoformat() if policy.expiration_date else None,
                'coverageDetails': policy.coverage_details,
                'deductibles': policy.deductibles,
                'roofAgeYears': policy.roof_age_years,
                'propertyFeatures': policy.property_features,
                'documentSourceFilename': policy.original_document_gcs_path,
                'processingStatus': 'completed',  # Mock status
                'processedAt': policy.created_at.isoformat(),
                'createdAt': policy.created_at.isoformat(),
                'updatedAt': policy.updated_at.isoformat()
            })
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error fetching policies: {str(e)}")
        return jsonify({'error': 'Failed to fetch policies'}), 500

@api_adapter_bp.route('/api/policies/search', methods=['GET'])
def search_policies():
    """Search policies"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        from sqlalchemy import or_
        policies = ProcessedPolicyData.query.filter(
            or_(
                ProcessedPolicyData.policy_number.ilike(f'%{query}%'),
                ProcessedPolicyData.insurer_name.ilike(f'%{query}%'),
                ProcessedPolicyData.policyholder_name.ilike(f'%{query}%'),
                ProcessedPolicyData.property_address.ilike(f'%{query}%')
            )
        ).all()
        
        result = []
        for policy in policies:
            result.append({
                'id': policy.id,
                'policyNumber': policy.policy_number,
                'insurerName': policy.insurer_name,
                'policyholderName': policy.policyholder_name,
                'propertyAddress': policy.property_address,
                'totalPremium': policy.total_premium,
                'effectiveDate': policy.effective_date.isoformat() if policy.effective_date else None,
                'expirationDate': policy.expiration_date.isoformat() if policy.expiration_date else None,
                'coverageDetails': policy.coverage_details,
                'deductibles': policy.deductibles
            })
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error searching policies: {str(e)}")
        return jsonify({'error': 'Failed to search policies'}), 500

@api_adapter_bp.route('/api/policies/<int:policy_id>', methods=['GET'])
def get_policy_by_id(policy_id):
    """Get policy by ID"""
    try:
        policy = ProcessedPolicyData.query.get(policy_id)
        if not policy:
            return jsonify({'error': 'Policy not found'}), 404
        
        return jsonify({
            'id': policy.id,
            'policyNumber': policy.policy_number,
            'insurerName': policy.insurer_name,
            'policyholderName': policy.policyholder_name,
            'propertyAddress': policy.property_address,
            'totalPremium': policy.total_premium,
            'effectiveDate': policy.effective_date.isoformat() if policy.effective_date else None,
            'expirationDate': policy.expiration_date.isoformat() if policy.expiration_date else None,
            'coverageDetails': policy.coverage_details,
            'deductibles': policy.deductibles,
            'rawText': policy.raw_text,
            'roofAgeYears': policy.roof_age_years,
            'propertyFeatures': policy.property_features,
            'documentSourceFilename': policy.original_document_gcs_path,
            'processingStatus': 'completed',
            'processedAt': policy.created_at.isoformat(),
            'createdAt': policy.created_at.isoformat(),
            'updatedAt': policy.updated_at.isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching policy {policy_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch policy'}), 500

@api_adapter_bp.route('/api/policies', methods=['POST'])
def create_policy():
    """Create a new policy (mock implementation)"""
    try:
        data = request.get_json()
        
        # This would need to be implemented based on your business logic
        # For now, return a mock response
        return jsonify({
            'id': 999,
            'policyNumber': data.get('policyNumber', 'MOCK-001'),
            'insurerName': data.get('insurerName', 'Mock Insurer'),
            'policyholderName': data.get('policyholderName', 'Mock Holder'),
            'propertyAddress': data.get('propertyAddress', 'Mock Address'),
            'totalPremium': data.get('totalPremium', 0),
            'effectiveDate': data.get('effectiveDate'),
            'expirationDate': data.get('expirationDate'),
            'coverageDetails': data.get('coverageDetails', []),
            'deductibles': data.get('deductibles', []),
            'processingStatus': 'completed',
            'createdAt': datetime.now().isoformat(),
            'updatedAt': datetime.now().isoformat()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating policy: {str(e)}")
        return jsonify({'error': 'Failed to create policy'}), 500

@api_adapter_bp.route('/api/policies/<int:policy_id>', methods=['PATCH'])
def update_policy(policy_id):
    """Update a policy (mock implementation)"""
    try:
        policy = ProcessedPolicyData.query.get(policy_id)
        if not policy:
            return jsonify({'error': 'Policy not found'}), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'policyNumber' in data:
            policy.policy_number = data['policyNumber']
        if 'insurerName' in data:
            policy.insurer_name = data['insurerName']
        if 'policyholderName' in data:
            policy.policyholder_name = data['policyholderName']
        if 'propertyAddress' in data:
            policy.property_address = data['propertyAddress']
        if 'totalPremium' in data:
            policy.total_premium = data['totalPremium']
        
        policy.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'id': policy.id,
            'policyNumber': policy.policy_number,
            'insurerName': policy.insurer_name,
            'policyholderName': policy.policyholder_name,
            'propertyAddress': policy.property_address,
            'totalPremium': policy.total_premium,
            'effectiveDate': policy.effective_date.isoformat() if policy.effective_date else None,
            'expirationDate': policy.expiration_date.isoformat() if policy.expiration_date else None,
            'coverageDetails': policy.coverage_details,
            'deductibles': policy.deductibles,
            'processingStatus': 'completed',
            'createdAt': policy.created_at.isoformat(),
            'updatedAt': policy.updated_at.isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"Error updating policy {policy_id}: {str(e)}")
        return jsonify({'error': 'Failed to update policy'}), 500

@api_adapter_bp.route('/api/policies/<int:policy_id>/context', methods=['PATCH'])
def update_policy_context(policy_id):
    """Update policy context (roof age and property features)"""
    try:
        policy = ProcessedPolicyData.query.get(policy_id)
        if not policy:
            return jsonify({'error': 'Policy not found'}), 404
        
        data = request.get_json()
        installation_date = data.get('installationDate')
        property_features = data.get('propertyFeatures', [])
        renewal_date = data.get('renewalDate')
        
        # Calculate roof age from installation date
        if installation_date:
            try:
                install_date = datetime.strptime(installation_date, '%Y-%m-%d').date()
                current_date = date.today()
                roof_age_years = current_date.year - install_date.year
                
                # Adjust for partial years
                if current_date.month < install_date.month or (current_date.month == install_date.month and current_date.day < install_date.day):
                    roof_age_years -= 1
                
                roof_age_years = max(0, roof_age_years)  # Ensure non-negative
                policy.roof_age_years = roof_age_years
                current_app.logger.info(f"Updated policy {policy_id} with roof age: {roof_age_years} years")
            except Exception as e:
                current_app.logger.error(f"Error calculating roof age: {str(e)}")
                return jsonify({'error': 'Invalid installation date format'}), 400
        
        # Update property features
        if property_features:
            policy.property_features = property_features
            current_app.logger.info(f"Updated policy {policy_id} with property features: {property_features}")
        
        # Update renewal date
        if renewal_date:
            try:
                renewal_date_obj = datetime.strptime(renewal_date, '%Y-%m-%d').date()
                policy.renewal_date = renewal_date_obj
                current_app.logger.info(f"Updated policy {policy_id} with renewal date: {renewal_date}")
            except Exception as e:
                current_app.logger.error(f"Error setting renewal date: {str(e)}")
                return jsonify({'error': 'Invalid renewal date format'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'Policy context updated successfully',
            'policyId': policy_id,
            'roofAgeYears': policy.roof_age_years,
            'propertyFeatures': policy.property_features,
            'renewalDate': policy.renewal_date.isoformat() if policy.renewal_date else None
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating policy context: {str(e)}")
        return jsonify({'error': 'Failed to update policy context'}), 500

def _extract_raw_text_from_pdf(file_path):
    """Extract raw text from PDF file using PyMuPDF"""
    try:
        import fitz  # PyMuPDF
        current_app.logger.info(f"Opening PDF file: {file_path}")
        doc = fitz.open(file_path)
        current_app.logger.info(f"PDF has {len(doc)} pages")
        text = ""
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            current_app.logger.info(f"Page {page_num + 1}: {len(page_text)} characters")
            text += page_text
        doc.close()
        extracted_text = text.strip()
        current_app.logger.info(f"Total extracted text: {len(extracted_text)} characters")
        return extracted_text
    except Exception as e:
        current_app.logger.error(f"Error extracting text from PDF: {str(e)}")
        return None

def _extract_raw_text_from_policy_data(policy_data):
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

@api_adapter_bp.route('/api/policies/upload', methods=['POST'])
def upload_policy():
    """Upload and process policy document using the pipeline"""
    try:
        if 'document' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['document']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get form data for policy linking
        policy_number = request.form.get('policyNumber')
        property_features = request.form.getlist('propertyFeatures')
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        try:
            # For now, process the document synchronously without Celery
            # This avoids the Redis dependency while still providing pipeline processing
            
            # Import the document processor service
            from app.services.insurance_document_processor_service import InsuranceDocumentProcessorService
            
            # Process the document
            processor = InsuranceDocumentProcessorService()
            
            # Read the file
            with open(file_path, 'rb') as f:
                document_bytes = f.read()
            
            # Process the document
            result = processor.process_document(document_bytes, filename)
            
            if result['status'] == 'success':
                # Create a policy record with the processed data
                from app.models import ProcessedPolicyData
                
                policy_data = result['data']
                
                # Extract raw text from the PDF file for querying
                current_app.logger.info(f"Extracting raw text from: {file_path}")
                raw_text = _extract_raw_text_from_pdf(file_path)
                current_app.logger.info(f"Raw text extracted: {len(raw_text) if raw_text else 0} characters")
                
                # If PDF extraction failed, construct text from policy data
                if not raw_text:
                    current_app.logger.info("PDF extraction failed, constructing text from policy data using extract_raw_text util")
                    current_app.logger.info(f"Policy data keys: {list(policy_data.keys())}")
                    current_app.logger.info(f"Policy data sample: {str(policy_data)[:200]}...")
                    raw_text = extract_raw_text(policy_data)
                    current_app.logger.info(f"Constructed text: {len(raw_text) if raw_text else 0} characters")
                    if raw_text:
                        current_app.logger.info(f"Text preview: {raw_text[:200]}...")
                
                processed_policy = ProcessedPolicyData(
                    policy_number=policy_number or policy_data.get('policy_number', f'UPLOAD-{task_id[:8]}'),
                    insurer_name=policy_data.get('insurer_name', 'Processed Document'),
                    policyholder_name=policy_data.get('policyholder_name', 'Extracted from Document'),
                    property_address=policy_data.get('property_address', 'Address from Document'),
                    total_premium=policy_data.get('total_premium', 0.0),
                    effective_date=policy_data.get('effective_date'),
                    expiration_date=policy_data.get('expiration_date'),
                    renewal_date=policy_data.get('expiration_date'),  # Set renewal date to expiration date
                    coverage_details=policy_data.get('coverage_details'),
                    deductibles=policy_data.get('deductibles'),
                    raw_text=raw_text or 'No text extracted',
                    original_document_gcs_path=filename,
                    processed_json_gcs_path=f'{filename}.json'
                )
                
                db.session.add(processed_policy)
                db.session.commit()
                
                # Handle property features if provided
                if property_features:
                    current_app.logger.info(f"Property features for policy {processed_policy.id}: {property_features}")
                    # In a real implementation, you would save these features to a separate table
                
                # Create a processing task record for tracking
                from app.models import ProcessingTask
                processing_task = ProcessingTask(
                    task_id=task_id,
                    celery_task_id=None,  # No Celery task for now
                    task_type='policy_processing',
                    status='completed',
                    filename=filename,
                    progress=100,
                    created_at=datetime.now()
                )
                
                db.session.add(processing_task)
                db.session.commit()
                
                current_app.logger.info(f"Document processed successfully: {filename}")
                
                return jsonify({
                    'taskId': task_id,
                    'message': 'Upload successful, document processed',
                    'status': 'completed',
                    'policyId': processed_policy.id
                })
            else:
                # Processing failed
                from app.models import ProcessingTask
                processing_task = ProcessingTask(
                    task_id=task_id,
                    celery_task_id=None,
                    task_type='policy_processing',
                    status='failed',
                    filename=filename,
                    progress=0,
                    error_message=result.get('message', 'Processing failed'),
                    created_at=datetime.now()
                )
                
                db.session.add(processing_task)
                db.session.commit()
                
                return jsonify({
                    'taskId': task_id,
                    'message': 'Upload successful, but processing failed',
                    'error': result.get('message', 'Processing failed'),
                    'status': 'failed'
                }), 500
            
            # Clean up temp file after processing
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            
        except Exception as processing_error:
            # Clean up temp file
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            
            current_app.logger.error(f"Document processing error: {str(processing_error)}")
            return jsonify({
                'taskId': task_id,
                'message': 'Upload successful, but processing failed',
                'error': str(processing_error)
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error uploading policy: {str(e)}")
        return jsonify({'error': 'Failed to upload document'}), 500

@api_adapter_bp.route('/api/roofing-invoices/upload', methods=['POST'])
def upload_roofing_invoice():
    """Upload roofing invoice for processing with policy linking"""
    try:
        if 'document' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['document']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Get form data
        policy_number = request.form.get('policyNumber')
        installation_date = request.form.get('installationDate')
        work_description = request.form.get('WorkDescription') or request.form.get('workDescription')
        property_features = request.form.getlist('propertyFeatures')
        
        # Find policy by policy number
        policy = None
        if policy_number:
            policy = ProcessedPolicyData.query.filter_by(policy_number=policy_number).first()
            if not policy:
                # Try to find by policyholder name if policy number not found
                policy = ProcessedPolicyData.query.filter_by(policyholder_name=policy_number).order_by(
                    ProcessedPolicyData.created_at.desc()
                ).first()
        
        # Generate unique task ID
        task_id = f"invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Create temp directory
        temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], task_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        # Extract installation date from PDF if not provided
        extracted_installation_date = None
        if not installation_date:
            try:
                import re
                from dateutil import parser as dateutil_parser
                def extract_text_from_pdf(pdf_path: str):
                    try:
                        import fitz  # PyMuPDF
                        doc = fitz.open(pdf_path)
                        text = ""
                        for page in doc:
                            text += page.get_text()
                        doc.close()
                        return text.strip()
                    except Exception as e:
                        current_app.logger.error(f"Error extracting text from PDF: {str(e)}")
                        return None
                def extract_labeled_dates_from_text(text: str):
                    text = re.sub(r'\s+', ' ', text)
                    labeled_dates = {}
                    # Enhanced pattern labels with ISO and US/General formats
                    pattern_labels = [
                        (r"installation\s+date[:\s]*(\d{4}-\d{1,2}-\d{1,2})", "Installation Date ISO"),
                        (r"installation\s+date[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Installation Date"),
                        (r"work\s+date[:\s]*(\d{4}-\d{1,2}-\d{1,2})", "Work Date ISO"),
                        (r"work\s+date[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Work Date"),
                        (r"service\s+date[:\s]*(\d{4}-\d{1,2}-\d{1,2})", "Service Date ISO"),
                        (r"service\s+date[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Service Date"),
                        (r"completion\s+date[:\s]*(\d{4}-\d{1,2}-\d{1,2})", "Completion Date ISO"),
                        (r"completion\s+date[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Completion Date"),
                        (r"project\s+completion\s+date[:\s]*(\d{4}-\d{1,2}-\d{1,2})", "Project Completion Date ISO"),
                        (r"project\s+completion\s+date[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Project Completion Date"),
                        (r"date\s+of\s+issue[:\s]*(\d{4}-\d{1,2}-\d{1,2})", "Date of Issue ISO"),
                        (r"date\s+of\s+issue[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Date of Issue"),
                        (r"issue\s+date[:\s]*(\d{4}-\d{1,2}-\d{1,2})", "Issue Date ISO"),
                        (r"issue\s+date[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Issue Date"),
                        (r"invoice\s+date[:\s]*(\d{4}-\d{1,2}-\d{1,2})", "Invoice Date ISO"),
                        (r"invoice\s+date[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Invoice Date"),
                        (r"due\s+date[:\s]*(\d{4}-\d{1,2}-\d{1,2})", "Due Date ISO"),
                        (r"due\s+date[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Due Date"),
                        # General date patterns
                        (r"(\d{1,2}/\d{1,2}/\d{4})", "General Date"),
                        (r"(\d{4}-\d{1,2}-\d{1,2})", "ISO Date"),
                        (r"(\d{1,2}-\d{1,2}-\d{4})", "US Date"),
                    ]
                    for pattern, label in pattern_labels:
                        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                        for match in matches:
                            try:
                                parsed_date = dateutil_parser.parse(match).date()
                                labeled_dates[label] = parsed_date
                            except Exception:
                                continue
                    return labeled_dates
                def extract_installation_date_from_invoice(file_path: str):
                    if not os.path.exists(file_path):
                        current_app.logger.error(f"File not found: {file_path}")
                        return None
                    text = extract_text_from_pdf(file_path)
                    if not text:
                        current_app.logger.error(f"Could not extract text from file: {file_path}")
                        return None
                    labeled_dates = extract_labeled_dates_from_text(text)
                    if not labeled_dates:
                        current_app.logger.warning("No dates found in invoice text")
                        return None
                    preferred_labels = [
                        "Installation Date",
                        "Installation Date ISO",
                        "Work Date",
                        "Work Date ISO",
                        "Service Date",
                        "Service Date ISO",
                        "Completion Date",
                        "Completion Date ISO",
                        "Project Completion Date",
                        "Project Completion Date ISO",
                        "Date of Issue",
                        "Date of Issue ISO",
                        "Issue Date",
                        "Issue Date ISO",
                        "Invoice Date",
                        "Invoice Date ISO",
                        "Due Date",
                        "Due Date ISO"
                    ]
                    for label in preferred_labels:
                        if label in labeled_dates:
                            selected_date = labeled_dates[label]
                            current_app.logger.info(f"Using {label} as installation date: {selected_date}")
                            return selected_date.strftime('%Y-%m-%d')
                    if labeled_dates:
                        earliest_date = min(labeled_dates.values())
                        current_app.logger.info(f"Using earliest date as fallback: {earliest_date}")
                        return earliest_date.strftime('%Y-%m-%d')
                    return None
                extracted_installation_date = extract_installation_date_from_invoice(file_path)
                if extracted_installation_date:
                    current_app.logger.info(f"Extracted installation date from PDF: {extracted_installation_date}")
                    installation_date = extracted_installation_date
                else:
                    current_app.logger.warning("Could not extract installation date from PDF")
            except Exception as e:
                current_app.logger.error(f"Error extracting date from PDF: {str(e)}")
        # Create invoice record
        from app.models import RoofingInvoice
        invoice_data = RoofingInvoice(
            filename=filename,
            policy_id=policy.id if policy else None,
            installation_date=datetime.strptime(installation_date, '%Y-%m-%d').date() if installation_date else None,
            roof_age_years=None,  # Will be calculated during processing
            work_description=work_description or "Pending processing",
            processing_status="uploaded",
            original_document_path=file_path
        )
        db.session.add(invoice_data)
        db.session.commit()
        # Process the invoice to extract roof age
        try:
            if installation_date:
                from datetime import date
                install_date = datetime.strptime(installation_date, '%Y-%m-%d').date()
                current_date = date.today()
                roof_age_years = current_date.year - install_date.year
                if current_date.month < install_date.month or (current_date.month == install_date.month and current_date.day < install_date.day):
                    roof_age_years -= 1
                roof_age_years = max(0, roof_age_years)  # Ensure non-negative
                invoice_data.roof_age_years = roof_age_years
                invoice_data.processing_status = "processed"
                if policy:
                    policy.roof_age_years = roof_age_years
                    current_app.logger.info(f"Updated policy {policy.id} with roof age: {roof_age_years} years")
                db.session.commit()
                current_app.logger.info(f"Processed invoice {invoice_data.id} with roof age: {roof_age_years} years")
            else:
                estimated_roof_age = 5  # Default estimate
                invoice_data.roof_age_years = estimated_roof_age
                invoice_data.processing_status = "processed"
                if policy:
                    policy.roof_age_years = estimated_roof_age
                db.session.commit()
                current_app.logger.info(f"Estimated roof age for invoice {invoice_data.id}: {estimated_roof_age} years")
        except Exception as processing_error:
            current_app.logger.error(f"Error processing invoice: {str(processing_error)}")
        if policy and property_features:
            # Convert property features to a list and save to policy
            if isinstance(property_features, list):
                features_list = property_features
            else:
                # Handle case where property_features might be a single string
                features_list = [property_features] if property_features else []
            
            # Update the policy with property features
            policy.property_features = features_list
            db.session.commit()
            current_app.logger.info(f"Updated policy {policy.id} with property features: {features_list}")
        return jsonify({
            'taskId': task_id,
            'message': 'Invoice upload successful, document processed',
            'invoiceId': invoice_data.id,
            'policyLinked': policy is not None,
            'policyId': policy.id if policy else None,
            'roofAgeYears': invoice_data.roof_age_years,
            'processingStatus': invoice_data.processing_status,
            'extractedInstallationDate': extracted_installation_date,
            'usedInstallationDate': installation_date
        })
    except Exception as e:
        current_app.logger.error(f"Error uploading invoice: {str(e)}")
        return jsonify({'error': 'Failed to upload invoice'}), 500

@api_adapter_bp.route('/api/policies/<int:policy_id>/download', methods=['GET'])
def download_policy_document(policy_id):
    """Download policy document"""
    try:
        policy = ProcessedPolicyData.query.get(policy_id)
        if not policy:
            return jsonify({'error': 'Policy not found'}), 404
        
        if not policy.original_document_gcs_path:
            return jsonify({'error': 'No document available for download'}), 404
        
        # For now, return the GCS path as a download link
        # In a real implementation, you would stream the file from GCS
        return jsonify({
            'downloadUrl': policy.original_document_gcs_path,
            'filename': policy.original_document_gcs_path.split('/')[-1] if policy.original_document_gcs_path else 'document.pdf'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error downloading policy document {policy_id}: {str(e)}")
        return jsonify({'error': 'Failed to download document'}), 500

# Mock endpoints for features and processing tasks
@api_adapter_bp.route('/api/policies/<int:policy_id>/features', methods=['GET'])
def get_policy_features(policy_id):
    """Get property features for a policy (mock implementation)"""
    try:
        # Mock features - in real implementation, this would query a features table
        features = [
            {
                'id': 1,
                'policyId': policy_id,
                'featureName': 'Monitored Alarm',
                'featureDescription': '24/7 monitoring security system',
                'discountPercentage': 5.0,
                'isActive': True,
                'createdAt': datetime.now().isoformat()
            }
        ]
        return jsonify(features)
    except Exception as e:
        return jsonify({'error': 'Failed to fetch property features'}), 500

@api_adapter_bp.route('/api/processing-tasks', methods=['GET'])
def get_processing_tasks():
    """Get processing tasks from database"""
    try:
        limit = int(request.args.get('limit', 50))
        
        from app.models import ProcessingTask
        
        tasks = ProcessingTask.query.order_by(
            ProcessingTask.created_at.desc()
        ).limit(limit).all()
        
        result = []
        for task in tasks:
            result.append({
                'id': task.id,
                'taskId': task.task_id,
                'celeryTaskId': task.celery_task_id,
                'taskType': task.task_type,
                'status': task.status,
                'filename': task.filename,
                'progress': task.progress,
                'errorMessage': task.error_message,
                'createdAt': task.created_at.isoformat(),
                'updatedAt': task.updated_at.isoformat()
            })
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error fetching processing tasks: {str(e)}")
        return jsonify({'error': 'Failed to fetch processing tasks'}), 500

@api_adapter_bp.route('/api/processing-tasks/<task_id>', methods=['GET'])
def get_processing_task(task_id):
    """Get specific processing task from database"""
    try:
        from app.models import ProcessingTask
        
        task = ProcessingTask.query.filter_by(task_id=task_id).first()
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # If there's a Celery task ID, check its status
        if task.celery_task_id:
            from celery.result import AsyncResult
            celery_result = AsyncResult(task.celery_task_id)
            
            if celery_result.ready():
                if celery_result.successful():
                    task.status = 'completed'
                    task.progress = 100
                else:
                    task.status = 'failed'
                    task.error_message = str(celery_result.result)
            elif celery_result.state == 'PROGRESS':
                task.status = 'processing'
                if celery_result.info:
                    task.progress = celery_result.info.get('current', 0)
            
            db.session.commit()
        
        return jsonify({
            'id': task.id,
            'taskId': task.task_id,
            'celeryTaskId': task.celery_task_id,
            'taskType': task.task_type,
            'status': task.status,
            'filename': task.filename,
            'progress': task.progress,
            'errorMessage': task.error_message,
            'createdAt': task.created_at.isoformat(),
            'updatedAt': task.updated_at.isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching task {task_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch task'}), 500

# Roofing invoices endpoints
@api_adapter_bp.route('/api/roofing-invoices', methods=['GET'])
def get_roofing_invoices():
    """Get roofing invoices"""
    try:
        from app.models import RoofingInvoice
        
        policy_id = request.args.get('policyId')
        
        if policy_id:
            invoices = RoofingInvoice.query.filter_by(policy_id=int(policy_id)).all()
        else:
            invoices = RoofingInvoice.query.all()
        
        return jsonify([{
            'id': invoice.id,
            'policyId': invoice.policy_id,
            'filename': invoice.filename,
            'installationDate': invoice.installation_date.isoformat() if invoice.installation_date else None,
            'workDescription': invoice.work_description,
            'roofAgeYears': invoice.roof_age_years,
            'processingStatus': invoice.processing_status,
            'createdAt': invoice.created_at.isoformat() if invoice.created_at else None,
            'updatedAt': invoice.updated_at.isoformat() if invoice.updated_at else None
        } for invoice in invoices])
    except Exception as e:
        current_app.logger.error(f"Error fetching roofing invoices: {str(e)}")
        return jsonify({'error': 'Failed to fetch roofing invoices'}), 500

@api_adapter_bp.route('/api/policies/query', methods=['POST'])
def query_policy():
    """Query policy documents using vector search"""
    try:
        data = request.get_json()
        policy_id = data.get('policyId')
        query = data.get('query')
        
        if not policy_id or not query:
            return jsonify({'error': 'Policy ID and query are required'}), 400
        
        # Get policy chunks for the specified policy
        # First, find the policy in the processed_policy_data table
        policy = ProcessedPolicyData.query.get(int(policy_id))
        if not policy:
            return jsonify({'error': 'Policy not found'}), 404
        
        # For now, we'll search in the raw_text of the processed policy
        # In a real implementation, you would have proper chunks stored
        if not policy.raw_text:
            return jsonify({'error': 'No policy content available for querying'}), 404
        
        # Improved text search with keyword matching
        query_lower = query.lower()
        raw_text_lower = policy.raw_text.lower()
        
        # Define keyword mappings for common queries
        keyword_mappings = {
            'policy number': ['policy number', 'policy_number'],
            'premium': ['premium', 'total annual premium', 'annual premium'],
            'deductible': ['deductible', 'deductibles'],
            'coverage': ['coverage', 'coverage details', 'dwelling coverage', 'personal property', 'liability'],
            'expire': ['expiration', 'expire', 'expiration date'],
            'effective': ['effective', 'effective date'],
            'insurer': ['insurer', 'insurance company'],
            'policyholder': ['policyholder', 'insured'],
            'address': ['address', 'property address']
        }
        
        # Find matching keywords
        matched_keywords = []
        for query_key, keywords in keyword_mappings.items():
            if query_key in query_lower:
                matched_keywords.extend(keywords)
        
        # If no specific keywords found, try direct search
        if not matched_keywords:
            matched_keywords = [query_lower]
        
        # Find content in raw_text that matches any of the matched_keywords
        lines = policy.raw_text.splitlines()
        found_content = [
            line for line in lines
            if any(keyword in line.lower() for keyword in matched_keywords)
        ]
        
        # Check for specific query types first, before doing generic content search
        if 'coverage' in query_lower:
            # Enhanced table-aware coverage extraction
            coverage_info = []
            lines = policy.raw_text.split('\n')
            
            # First, try to find the coverage table section
            table_start = -1
            for i, line in enumerate(lines):
                if 'coverage type' in line.lower():
                    # Check if the next line contains "limit"
                    if i + 1 < len(lines) and 'limit' in lines[i + 1].lower():
                        table_start = i
                        break
            
            if table_start != -1:
                # Parse the table structure
                for i in range(table_start + 1, len(lines)):
                    line = lines[i].strip()
                    if not line or 'deductibles' in line.lower() or 'endorsements' in line.lower():
                        break
                    
                    line_lower = line.lower()
                    # Look for coverage lines (A, B, C, D, E, F)
                    if any(word in line_lower for word in ['coverage a', 'coverage b', 'coverage c', 'coverage d', 'coverage e', 'coverage f']):
                        coverage_type = line
                        # Look for the limit amount in the next few lines
                        limit_found = False
                        for j in range(i + 1, min(i + 5, len(lines))):
                            next_line = lines[j].strip()
                            if not next_line:
                                continue
                            # Check if this line contains a dollar amount
                            if '$' in next_line:
                                # Extract just the dollar amount
                                import re
                                dollar_match = re.search(r'\$[\d,]+(?:\.\d{2})?', next_line)
                                if dollar_match:
                                    limit_amount = dollar_match.group()
                                    coverage_info.append(f"{coverage_type}: {limit_amount}")
                                    limit_found = True
                                    break
                        if not limit_found:
                            # If no dollar amount found, include the coverage type anyway
                            coverage_info.append(coverage_type)
            
            # If no table found, try the old method
            if not coverage_info:
                for i, line in enumerate(lines):
                    line_lower = line.lower().strip()
                    if any(word in line_lower for word in ['coverage a', 'coverage b', 'coverage c', 'coverage d', 'coverage e', 'coverage f']):
                        coverage_type = line.strip()
                        # Look ahead for the next line with a $ or a number
                        for j in range(i+1, min(i+4, len(lines))):
                            next_line = lines[j].strip()
                            if ('$' in next_line or (next_line.replace(',', '').replace('.', '').replace('(', '').replace(')', '').replace('%','').replace('of','').replace('A','').strip().isdigit() and len(next_line) > 2)):
                                coverage_info.append(f"{coverage_type}: {next_line}")
                                break
                        else:
                            coverage_info.append(coverage_type)
            
            if coverage_info:
                answer = f"Coverage information: {'; '.join(coverage_info)}"
                sources = [f"Policy {policy.policy_number} - {policy.original_document_gcs_path}"]
                confidence = 0.9
                return jsonify({
                    'answer': answer,
                    'sources': sources,
                    'confidence': confidence
                })
            else:
                answer = "I could not find specific coverage information in the policy documents."
                sources = [f"Policy {policy.policy_number} - {policy.original_document_gcs_path}"]
                confidence = 0.0
                return jsonify({
                    'answer': answer,
                    'sources': sources,
                    'confidence': confidence
                })
        
        elif 'premium' in query_lower:
            # Extract premium information
            premium_info = []
            for content in found_content:
                lines = content.split('\n')
                for line in lines:
                    line_lower = line.lower()
                    if 'total annual premium' in line_lower or ('premium' in line_lower and '$' in line):
                        # Extract just the premium amount
                        line = line.strip()
                        if 'total annual premium' in line_lower:
                            # Find the amount after "TOTAL ANNUAL PREMIUM:"
                            if ':' in line:
                                amount = line.split(':', 1)[1].strip()
                                premium_info.append(f"Total Annual Premium: {amount}")
                        elif '$' in line and 'premium' in line_lower:
                            premium_info.append(line)
            if premium_info:
                answer = f"Premium information: {'; '.join(premium_info)}"
            elif found_content:
                answer = f"Based on the policy documents, I found the premium information: {found_content[0]}"
            else:
                answer = "I could not find specific premium information in the policy documents."
                
        elif 'effective' in query_lower:
            # Find lines with 'effective'
            import re
            effective_lines = [line for line in lines if 'effective' in line.lower()]
            date_match = None
            for line in effective_lines:
                # Try to extract the effective date using regex
                match = re.search(r'effective[^:]*:\s*([0-9/\.-]+)', line, re.IGNORECASE)
                if match:
                    date_match = match.group(1)
                    break
            if date_match:
                answer = f"Effective date: {date_match}"
            elif effective_lines:
                answer = f"Effective date information: {effective_lines[0]}"
            else:
                answer = "I could not find specific effective date information in the policy documents."
            sources = [f"Policy {policy.policy_number} - {policy.original_document_gcs_path}"]
            confidence = 0.9 if date_match else 0.5
            return jsonify({
                'answer': answer,
                'sources': sources,
                'confidence': confidence
            })

        elif 'expire' in query_lower or 'expiration' in query_lower:
            # Find lines with 'expiration'
            import re
            expiration_lines = [line for line in lines if 'expiration' in line.lower() or 'expire' in line.lower()]
            date_match = None
            for line in expiration_lines:
                # Try to extract the expiration date using regex
                match = re.search(r'expir\w*[^:]*:\s*([0-9/\.-]+)', line, re.IGNORECASE)
                if match:
                    date_match = match.group(1)
                    break
            if date_match:
                answer = f"Expiration date: {date_match}"
            elif expiration_lines:
                answer = f"Expiration date information: {expiration_lines[0]}"
            else:
                answer = "I could not find specific expiration date information in the policy documents."
            sources = [f"Policy {policy.policy_number} - {policy.original_document_gcs_path}"]
            confidence = 0.9 if date_match else 0.5
            return jsonify({
                'answer': answer,
                'sources': sources,
                'confidence': confidence
            })
        
        elif 'address' in query_lower or 'location' in query_lower:
            # Search for address/location information
            address_lines = []
            for line in lines:
                line_lower = line.lower()
                if any(term in line_lower for term in ['address', 'location', 'property', 'residence', 'dwelling']):
                    address_lines.append(line.strip())
            if address_lines:
                answer = f"Address/Location information: {address_lines[0]}"
                sources = [f"Policy {policy.policy_number} - {policy.original_document_gcs_path}"]
                confidence = 0.8
                return jsonify({
                    'answer': answer,
                    'sources': sources,
                    'confidence': confidence
                })
            else:
                answer = "I could not find specific address/location information in the policy documents."
                sources = [f"Policy {policy.policy_number} - {policy.original_document_gcs_path}"]
                confidence = 0.0
                return jsonify({
                    'answer': answer,
                    'sources': sources,
                    'confidence': confidence
                })
        
        elif 'deductible' in query_lower:
            # Improved deductible extraction
            deductible_info = []
            lines = policy.raw_text.split('\n')
            header_phrases = [
                'deductible annual premium',
                'deductibles',
                'coverage type',
                'limit'
            ]
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                # Skip header lines
                if any(line_lower == header for header in header_phrases):
                    continue
                # Only include lines with deductible info
                if (
                    'deductible' in line_lower and
                    (
                        '$' in line_lower or
                        '%' in line_lower or
                        'per occurrence' in line_lower or
                        'wind/hail' in line_lower
                    )
                ):
                    clean_line = line.strip()
                    if clean_line:
                        deductible_info.append(clean_line)
            if deductible_info:
                answer = f"Deductible information: {'; '.join(deductible_info)}"
                sources = [f"Policy {policy.policy_number} - {policy.original_document_gcs_path}"]
                confidence = 0.9
                return jsonify({
                    'answer': answer,
                    'sources': sources,
                    'confidence': confidence
                })
            else:
                answer = "I could not find specific deductible information in the policy documents."
                sources = [f"Policy {policy.policy_number} - {policy.original_document_gcs_path}"]
                confidence = 0.0
                return jsonify({
                    'answer': answer,
                    'sources': sources,
                    'confidence': confidence
                })
        
        else:
            # For other queries, provide the most relevant content
            if found_content:
                answer = f"Based on the policy documents, I found: {found_content[0]}"
            else:
                answer = "I could not find specific information about that in the policy documents."
        
        # If not found_content, try fuzzy matching on lines
        if not found_content:
            lines = policy.raw_text.splitlines()
            # Try to find the closest line to the query or keywords
            candidates = []
            for keyword in matched_keywords:
                matches = difflib.get_close_matches(keyword, [line.lower() for line in lines], n=1, cutoff=0.6)
                if matches:
                    idx = [line.lower() for line in lines].index(matches[0])
                    candidates.append(lines[idx].strip())
            if candidates:
                answer = f"Closest match: {'; '.join(candidates)}"
                sources = [f"Policy {policy.policy_number} - {policy.original_document_gcs_path}"]
                confidence = 0.6
                return jsonify({
                    'answer': answer,
                    'sources': sources,
                    'confidence': confidence
                })
            else:
                # Try fuzzy match on the whole query
                matches = difflib.get_close_matches(query_lower, [line.lower() for line in lines], n=1, cutoff=0.5)
                if matches:
                    idx = [line.lower() for line in lines].index(matches[0])
                    answer = f"Closest match: {lines[idx].strip()}"
                    sources = [f"Policy {policy.policy_number} - {policy.original_document_gcs_path}"]
                    confidence = 0.5
                    return jsonify({
                        'answer': answer,
                        'sources': sources,
                        'confidence': confidence
                    })
                return jsonify({
                    'answer': 'I could not find specific information about that in the policy documents.',
                    'sources': [],
                    'confidence': 0.0
                })
        
        sources = [f"Policy {policy.policy_number} - {policy.original_document_gcs_path}"]
        confidence = 0.8  # Simple confidence calculation
        
        return jsonify({
            'answer': answer,
            'sources': sources,
            'confidence': confidence
        })
        
    except Exception as e:
        current_app.logger.error(f"Error querying policy: {str(e)}")
        return jsonify({'error': 'Failed to query policy documents'}), 500 

@api_adapter_bp.route('/api/risk-factors/analyze', methods=['POST'])
def analyze_iowa_risk_factors():
    """Analyze Iowa-specific risk factors for a property"""
    try:
        data = request.get_json()
        policy_id = data.get('policyId')
        zip_code = data.get('zipCode')
        user_query = data.get('userQuery', '')
        policy_context = None

        import re
        # If policyId is provided, use it to extract ZIP code and context
        if policy_id:
            policy = ProcessedPolicyData.query.get(int(policy_id))
            if not policy:
                return jsonify({'error': 'Policy not found'}), 404
            # Extract ZIP code from property address
            zip_code = None
            if policy.property_address:
                zip_match = re.search(r'\b(\d{5})\b', policy.property_address)
                if zip_match:
                    zip_code = zip_match.group(1)
            if not zip_code:
                return jsonify({'error': 'Could not extract ZIP code from property address'}), 400
            # Build policy context
            policy_context = {
                'policyNumber': policy.policy_number,
                'policyholderName': policy.policyholder_name,
                'propertyAddress': policy.property_address,
                'effectiveDate': policy.effective_date.isoformat() if policy.effective_date else None,
                'expirationDate': policy.expiration_date.isoformat() if policy.expiration_date else None,
                'totalPremium': policy.total_premium,
                'coverageDetails': policy.coverage_details,
                'deductibles': policy.deductibles,
                'roofAgeYears': policy.roof_age_years,
                'propertyFeatures': policy.property_features
            }
        elif zip_code:
            # Use zipCode directly, build minimal or provided context
            policy_context = data.get('policyContext', {})
            # Optionally, add more context fields if provided
            policy_context.setdefault('policyNumber', None)
            policy_context.setdefault('policyholderName', None)
            policy_context.setdefault('propertyAddress', None)
            policy_context.setdefault('effectiveDate', None)
            policy_context.setdefault('expirationDate', None)
            policy_context.setdefault('totalPremium', None)
            policy_context.setdefault('coverageDetails', [])
            policy_context.setdefault('deductibles', [])
            policy_context.setdefault('roofAgeYears', None)
            policy_context.setdefault('propertyFeatures', [])
        else:
            return jsonify({'error': 'Either policyId or zipCode is required'}), 400

        # Iowa-specific risk assessment based on ZIP code
        risk_factors = get_iowa_risk_factors(zip_code, policy_context)
        # Generate recommendations using Gemini
        recommendations = generate_iowa_recommendations(zip_code, risk_factors, policy_context, user_query)
        return jsonify({
            'zipCode': zip_code,
            'riskFactors': risk_factors,
            'recommendations': recommendations,
            'policyContext': policy_context,
            'iowaSpecific': True
        })
    except Exception as e:
        current_app.logger.error(f"Error analyzing Iowa risk factors: {str(e)}")
        return jsonify({'error': 'Failed to analyze risk factors'}), 500

def get_iowa_risk_factors(zip_code, policy_context):
    """Get Iowa-specific risk factors based on ZIP code (pattern-based, covers all ZIPs)"""
    # Determine region and base risks by ZIP code prefix
    region = 'Iowa'
    base_risks = {'flood': 'medium', 'tornado': 'medium', 'hail': 'medium', 'winter': 'medium', 'agricultural': 'medium'}
    if zip_code.startswith('52'):
        region = 'Eastern Iowa (Mississippi River)'
        base_risks = {'flood': 'high', 'tornado': 'medium', 'hail': 'medium', 'winter': 'medium', 'agricultural': 'high'}
    elif zip_code.startswith('50'):
        region = 'Central Iowa (Des Moines Area)'
        base_risks = {'flood': 'medium', 'tornado': 'high', 'hail': 'high', 'winter': 'medium', 'agricultural': 'medium'}
    elif zip_code.startswith('51'):
        region = 'Western Iowa (Missouri River)'
        base_risks = {'flood': 'high', 'tornado': 'medium', 'hail': 'medium', 'winter': 'medium', 'agricultural': 'high'}
    elif zip_code.startswith('506'):
        region = 'Northern Iowa'
        base_risks = {'flood': 'medium', 'tornado': 'medium', 'hail': 'medium', 'winter': 'high', 'agricultural': 'high'}
    elif zip_code.startswith('525'):
        region = 'Southern Iowa'
        base_risks = {'flood': 'medium', 'tornado': 'high', 'hail': 'high', 'winter': 'medium', 'agricultural': 'high'}

    # Adjust risks based on policy context
    adjusted_risks = base_risks.copy()
    roof_age = policy_context.get('roofAgeYears')
    if roof_age:
        if roof_age > 20:
            adjusted_risks['hail'] = 'high'
            adjusted_risks['winter'] = 'high'
    features = policy_context.get('propertyFeatures', [])
    if features:
        if 'impact_resistant_roof' in features:
            adjusted_risks['hail'] = 'low'
        if 'storm_shutters' in features:
            adjusted_risks['tornado'] = 'low'
        if 'backup_generator' in features:
            adjusted_risks['winter'] = 'low'
    return {
        'floodRisk': adjusted_risks['flood'],
        'tornadoRisk': adjusted_risks['tornado'],
        'hailRisk': adjusted_risks['hail'],
        'winterRisk': adjusted_risks['winter'],
        'agriculturalRisk': adjusted_risks['agricultural'],
        'zipCode': zip_code,
        'region': region
    }

def get_iowa_region(zip_code):
    """Get Iowa region based on ZIP code"""
    if zip_code.startswith('52'):
        return 'Eastern Iowa (Mississippi River)'
    elif zip_code.startswith('50'):
        return 'Central Iowa (Des Moines Area)'
    elif zip_code.startswith('51'):
        return 'Western Iowa (Missouri River)'
    elif zip_code.startswith('50'):
        return 'Northern Iowa'
    elif zip_code.startswith('52'):
        return 'Southern Iowa'
    else:
        return 'Iowa'

def generate_iowa_recommendations(zip_code, risk_factors, policy_context, user_query):
    """Generate Iowa-specific recommendations using Gemini"""
    try:
        import google.generativeai as genai
        
        # Configure Gemini
        genai.configure(api_key=current_app.config.get('GOOGLE_AI_API_KEY'))
        model = genai.GenerativeModel('models/gemini-2.5-pro')
        
        # Build context for Gemini
        context = f"""
        As an Iowa insurance expert, analyze this property's risk factors and provide recommendations.

        ZIP Code: {zip_code}
        Region: {risk_factors.get('region', 'Iowa')}

        Risk Factors:
        - Flood Risk: {risk_factors.get('floodRisk', 'medium')}
        - Tornado Risk: {risk_factors.get('tornadoRisk', 'medium')}
        - Hail Risk: {risk_factors.get('hailRisk', 'medium')}
        - Winter Risk: {risk_factors.get('winterRisk', 'medium')}
        - Agricultural Risk: {risk_factors.get('agriculturalRisk', 'medium')}

        Policy Context: {policy_context}

        User Question: {user_query if user_query else 'General risk assessment and recommendations'}

        IMPORTANT: If the user requests a specific order or focus for the recommendations, follow their instructions exactly. If the user asks for coverage recommendations first, list those first in your response. Always prioritize the user's explicit instructions in the User Question.

        Respond ONLY with valid JSON in this format. Do not include any explanation, markdown, or text outside the JSON object:
        {{
            "riskMitigation": ["..."],
            "coverageRecommendations": ["..."],
            "homeImprovements": ["..."],
            "emergencyPreparedness": ["..."],
            "iowaSpecificNotes": ["..."]
        }}
        """
        
        response = model.generate_content(context)
        current_app.logger.info(f"Gemini response: {response}")

        # Try to extract the text from the response
        response_text = None
        if hasattr(response, 'text') and response.text:
            response_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            try:
                response_text = response.candidates[0].content.parts[0].text
            except Exception as e:
                current_app.logger.error(f"Error extracting text from candidates: {str(e)}")

        current_app.logger.info(f"Gemini response_text: {response_text!r}")

        if response_text:
            try:
                import re
                import json
                # Try to extract JSON object from the response text
                json_match = re.search(r'({[\s\S]*})', response_text)
                if json_match:
                    recommendations = json.loads(json_match.group(1))
                else:
                    recommendations = json.loads(response_text)  # fallback, may still fail
            except Exception as e:
                current_app.logger.error(f"Error parsing Gemini JSON: {str(e)}")
                recommendations = {
                    "riskMitigation": ["Install sump pump for flood protection", "Consider storm shelter for tornado protection"],
                    "coverageRecommendations": ["Add flood insurance", "Consider hail damage coverage"],
                    "homeImprovements": ["Upgrade to impact-resistant roofing", "Install backup generator"],
                    "emergencyPreparedness": ["Create emergency kit", "Develop evacuation plan"],
                    "iowaSpecificNotes": ["Located in Tornado Alley", "Consider agricultural chemical exposure"]
                }
        else:
            recommendations = {
                "riskMitigation": ["Install sump pump for flood protection", "Consider storm shelter for tornado protection"],
                "coverageRecommendations": ["Add flood insurance", "Consider hail damage coverage"],
                "homeImprovements": ["Upgrade to impact-resistant roofing", "Install backup generator"],
                "emergencyPreparedness": ["Create emergency kit", "Develop evacuation plan"],
                "iowaSpecificNotes": ["Located in Tornado Alley", "Consider agricultural chemical exposure"]
            }

        return recommendations
        
    except Exception as e:
        current_app.logger.error(f"Error generating recommendations: {str(e)}")
        # Return default recommendations if Gemini fails
        return {
            "riskMitigation": ["Install sump pump for flood protection", "Consider storm shelter for tornado protection"],
            "coverageRecommendations": ["Add flood insurance", "Consider hail damage coverage"],
            "homeImprovements": ["Upgrade to impact-resistant roofing", "Install backup generator"],
            "emergencyPreparedness": ["Create emergency kit", "Develop evacuation plan"],
            "iowaSpecificNotes": ["Located in Tornado Alley", "Consider agricultural chemical exposure"]
        } 

@api_adapter_bp.route('/api/feedback/risk-analysis', methods=['POST'])
def risk_analysis_feedback():
    """Accept user feedback (upvote/downvote) for risk analysis recommendations"""
    try:
        data = request.get_json()
        zip_code = data.get('zipCode')
        policy_id = data.get('policyId')
        user_feedback = data.get('userFeedback')  # boolean
        user_query = data.get('userQuery')
        policy_context = data.get('policyContext')
        feedback_comment = data.get('feedbackComment')
        current_app.logger.info(f"Risk analysis feedback: zip={zip_code}, policyId={policy_id}, feedback={user_feedback}, userQuery={user_query}, policyContext={policy_context}, comment={feedback_comment}")
        feedback = Feedback(
            zip_code=zip_code,
            policy_id=policy_id,
            user_feedback=user_feedback,
            user_query=user_query,
            policy_context=policy_context,
            feedback_comment=feedback_comment
        )
        db.session.add(feedback)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Feedback received'})
    except Exception as e:
        current_app.logger.error(f"Error receiving risk analysis feedback: {str(e)}")
        return jsonify({'error': 'Failed to receive feedback'}), 500 

@api_adapter_bp.route('/api/feedback/risk-analysis/history', methods=['GET'])
def risk_analysis_feedback_history():
    """Return the most recent feedback entries for risk analysis (limit 20, newest first)"""
    try:
        feedback_entries = Feedback.query.order_by(Feedback.created_at.desc()).limit(20).all()
        result = [
            {
                'id': f.id,
                'created_at': f.created_at.isoformat(),
                'updated_at': f.updated_at.isoformat(),
                'zip_code': f.zip_code,
                'policy_id': f.policy_id,
                'user_feedback': f.user_feedback,
                'user_query': f.user_query,
                'policy_context': f.policy_context,
                'feedback_comment': f.feedback_comment
            }
            for f in feedback_entries
        ]
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error fetching feedback history: {str(e)}")
        return jsonify({'error': 'Failed to fetch feedback history'}), 500 