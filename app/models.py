from .db import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class ProcessedPolicyData(db.Model):
    __tablename__ = 'processed_policy_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    original_document_gcs_path = db.Column(db.String(255), nullable=False)
    processed_json_gcs_path = db.Column(db.String(255), nullable=False)
    policy_number = db.Column(db.String(50), nullable=True, index=True)
    insurer_name = db.Column(db.String(100), nullable=True)
    policyholder_name = db.Column(db.String(100), nullable=True)
    property_address = db.Column(db.String(255), nullable=True)
    effective_date = db.Column(db.Date, nullable=True)
    expiration_date = db.Column(db.Date, nullable=True)
    total_premium = db.Column(db.Float, nullable=True)
    coverage_details = db.Column(db.JSON, nullable=True)
    deductibles = db.Column(db.JSON, nullable=True)
    raw_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # --- NEW PROACTIVE FIELDS ---
    renewal_date = db.Column(db.Date, nullable=True)  # Essential for timing alerts
    roof_age_years = db.Column(db.Integer, nullable=True)  # For Scenario 1
    property_features = db.Column(JSONB, nullable=True)  # For Scenario 2 (e.g., ["monitored_alarm"])
    last_proactive_analysis = db.Column(db.DateTime, nullable=True)

class Policy(db.Model):
    __tablename__ = 'policies'
    
    id = db.Column(db.Integer, primary_key=True)
    document_source_filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chunks = db.relationship('PolicyChunk', backref='policy', lazy=True)

class PolicyChunk(db.Model):
    __tablename__ = 'policy_chunks'

    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer, db.ForeignKey('policies.id'), nullable=False)
    document_source_filename = db.Column(db.String(255), nullable=False)
    section_type = db.Column(db.String(50), nullable=False)
    chunk_text = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.ARRAY(db.Float), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Note: The embedding column is not defined here as it will be handled via raw SQL
    # The actual column will be created in the migration as: embedding vector(768)


class RoofingInvoice(db.Model):
    __tablename__ = 'roofing_invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    policy_id = db.Column(db.Integer, db.ForeignKey('processed_policy_data.id'), nullable=True)
    installation_date = db.Column(db.Date, nullable=True)
    roof_age_years = db.Column(db.Integer, nullable=True)
    work_description = db.Column(db.Text, nullable=True)
    processing_status = db.Column(db.String(50), default='uploaded')
    original_document_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    policy = db.relationship('ProcessedPolicyData', backref='roofing_invoices')
    
    def __repr__(self):
        return f'<RoofingInvoice {self.filename}>'

class ProcessingTask(db.Model):
    __tablename__ = 'processing_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(100), unique=True, nullable=False)
    celery_task_id = db.Column(db.String(100), nullable=True)
    task_type = db.Column(db.String(50), nullable=False)  # 'policy_processing', 'invoice_processing', etc.
    status = db.Column(db.String(50), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    filename = db.Column(db.String(255), nullable=True)
    progress = db.Column(db.Integer, default=0)  # 0-100
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProcessingTask {self.task_id}: {self.status}>' 