import os
import json
from datetime import datetime, date
from io import BytesIO
from PIL import Image
from flask import current_app
from ..models import ProcessedPolicyData
from ..db import db
from app.utils.text_utils import extract_raw_text

class InsuranceDocumentProcessorService:
    def __init__(self):
        # Check if Google services are available
        self.use_google_services = (
            current_app.config.get('GOOGLE_CLOUD_STORAGE_BUCKET') and 
            current_app.config.get('GOOGLE_AI_API_KEY')
        )
        
        # For local development, prefer Google services if available
        if not self.use_google_services:
            current_app.logger.warning("Google services not configured - check your API keys and bucket name")
            current_app.logger.warning("Set GOOGLE_AI_API_KEY and GOOGLE_CLOUD_STORAGE_BUCKET in local.env")
        
        if self.use_google_services:
            # Initialize Google Cloud Storage client
            from google.cloud import storage
            import google.generativeai as genai
            
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(current_app.config['GOOGLE_CLOUD_STORAGE_BUCKET'])
            
            # Initialize Google AI
            genai.configure(api_key=current_app.config['GOOGLE_AI_API_KEY'])
            self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
            self.text_model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Get GCS path prefixes
            self.original_pdfs_prefix = current_app.config['GCS_ORIGINAL_PDFS_PREFIX']
            self.structured_jsons_prefix = current_app.config['GCS_STRUCTURED_JSONS_PREFIX']
        else:
            current_app.logger.warning("Google services not configured - running in local mode")
            self.use_google_services = False

    def _extract_text_from_pdf_bytes(self, document_bytes):
        """Extract text from PDF bytes using PyMuPDF"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=document_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            current_app.logger.error(f"Error extracting text from PDF bytes: {str(e)}")
            return None

    def _extract_raw_text_from_policy_data(self, policy_data):
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

    def _convert_date_string(self, date_str):
        """Convert date string to Python date object."""
        if not date_str:
            return None
            
        try:
            # Try parsing YYYY-MM-DD format
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                # Try parsing Month DD, YYYY format
                return datetime.strptime(date_str, '%B %d, %Y').date()
            except ValueError:
                try:
                    # Try parsing MMM DD, YYYY format
                    return datetime.strptime(date_str, '%b %d, %Y').date()
                except ValueError:
                    print(f"Could not parse date string: {date_str}")
                    return None

    def process_document(self, document_bytes, filename):
        try:
            if self.use_google_services:
                # Use Google services (production mode)
                return self._process_with_google_services(document_bytes, filename)
            else:
                # Use local processing (development mode)
                return self._process_locally(document_bytes, filename)
                
        except Exception as e:
            current_app.logger.error(f"Error processing document: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error processing document: {str(e)}'
            }

    def _process_with_google_services(self, document_bytes, filename):
        """Process document using Google Cloud Storage and AI services"""
        # Upload original PDF to GCS
        original_gcs_path = f"{current_app.config['GCS_ORIGINAL_PDFS_PREFIX']}{filename}"
        blob = self.bucket.blob(original_gcs_path)
        blob.upload_from_string(document_bytes, content_type='application/pdf')
        
        # Extract text using vision model
        image_parts = [
            {
                "mime_type": "application/pdf",
                "data": document_bytes
            }
        ]
        
        vision_response = self.vision_model.generate_content(
            [
                "Extract all text from this insurance policy document. Include policy numbers, dates, coverage details, and any other relevant information.",
                *image_parts
            ]
        )
        
        extracted_text = vision_response.text
        
        # Extract structured data using text model
        structured_data = self._extract_structured_data(extracted_text)
        
        # Save structured data to GCS
        processed_json_path = f"{current_app.config['GCS_STRUCTURED_JSONS_PREFIX']}{os.path.splitext(filename)[0]}.json"
        json_blob = self.bucket.blob(processed_json_path)
        json_blob.upload_from_string(
            json.dumps(structured_data),
            content_type='application/json'
        )
        
        # Note: Database entry will be created by the calling endpoint
        # This service only processes the document and returns structured data
        
        return {
            'status': 'success',
            'message': 'Document processed successfully',
            'data': structured_data
        }

    def _process_locally(self, document_bytes, filename):
        """Process document locally without Google services"""
        try:
            current_app.logger.info(f"Starting local processing for {filename}")
            
            # Extract raw text from PDF
            raw_text = self._extract_text_from_pdf_bytes(document_bytes)
            
            # Quick local processing with basic text extraction
            structured_data = {
                'policy_number': f'LOCAL-{filename.split(".")[0]}',
                'insurer_name': 'Local Processing',
                'policyholder_name': 'Processed Locally',
                'property_address': 'Local Development',
                'effective_date': datetime.now().strftime('%Y-%m-%d'),
                'expiration_date': datetime.now().strftime('%Y-%m-%d'),
                'total_premium': '0.00',
                'coverage_details': [
                    {
                        'coverage_type': 'Local Processing',
                        'limit': '0.00'
                    }
                ],
                'deductibles': [
                    {
                        'coverage_type': 'Local Processing',
                        'amount': '0.00',
                        'type': 'local'
                    }
                ],
                'raw_text': raw_text or f'File {filename} processed locally (no text extraction)'
            }
            
            # If PDF extraction failed, construct text from structured data
            if not raw_text:
                raw_text = extract_raw_text(structured_data)
                structured_data['raw_text'] = raw_text
            
            current_app.logger.info("Created structured data, returning to endpoint for database save...")
            
            # Note: Database entry will be created by the calling endpoint
            # This service only processes the document and returns structured data
            
            return {
                'status': 'success',
                'message': 'Document processed locally (no Google services)',
                'data': structured_data
            }
            
        except Exception as e:
            db.session.rollback()
            raise e

    def _extract_structured_data(self, text):
        prompt = """
        You are an expert at extracting information from insurance policy documents. Extract the following information and return it as a JSON object. If you find multiple values for any field, use the most recent or relevant one.

        Required fields:
        - policy_number: The policy number or identifier (string)
        - insurer_name: The name of the insurance company (string). Look for:
          * Company name at the top of the document
          * Text after "Insured by" or "Underwritten by"
          * Company name followed by "Insurance", "Assurance", or "Group"
          * If multiple names found, use the most prominent one (usually at the top)
        - policyholder_name: The name of the person or entity holding the policy (string)
        - property_address: The address of the insured property (string)
        - effective_date: The start date of the policy (string in YYYY-MM-DD format)
        - expiration_date: The end date of the policy (string in YYYY-MM-DD format)
        - total_premium: The total premium amount (string)
        - coverage_details: An array of objects, each containing:
          - coverage_type: The type of coverage (string)
          - limit: The coverage limit (string)
        - deductibles: An array of objects, each containing:
          - coverage_type: The type of coverage this deductible applies to (string)
          - amount: The deductible amount (string)
          - type: The type of deductible (e.g., "per_occurrence", "per_claim", "annual") (string)

        Example format:
        {
            "policy_number": "HMP-IA-001-2025",
            "insurer_name": "Hawkeye Insurance Group",
            "policyholder_name": "Michael Kline",
            "property_address": "123 Main St, Anytown, IA 50001",
            "effective_date": "2025-06-02",
            "expiration_date": "2026-06-01",
            "total_premium": "1710.00",
            "coverage_details": [
                {
                    "coverage_type": "Coverage A - Dwelling",
                    "limit": "250000.00"
                }
            ],
            "deductibles": [
                {
                    "coverage_type": "Coverage A - Dwelling",
                    "amount": "1000.00",
                    "type": "per_occurrence"
                }
            ]
        }

        Return only the JSON object, no additional text or explanation.
        """
        
        response = self.text_model.generate_content([prompt, text])
        print("\n=== Model Response ===")
        print(response.text)
        print("=== End Model Response ===\n")
        
        try:
            # Try to parse the response as JSON
            data = json.loads(response.text)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from the text
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    raise Exception("Could not parse JSON from model response")
            else:
                raise Exception("No JSON object found in model response")
        
        # Validate and clean up the data
        if not isinstance(data, dict):
            raise Exception("Model response is not a JSON object")
        
        # Clean up insurer name
        if 'insurer_name' in data and data['insurer_name']:
            suffixes = ['Insurance', 'Assurance', 'Group', 'Company', 'Inc.', 'LLC']
            name = data['insurer_name']
            for suffix in suffixes:
                if name and name.endswith(suffix):
                    name = name[:-len(suffix)].strip()
            data['insurer_name'] = name
        
        # Ensure coverage_details is a list
        if 'coverage_details' not in data:
            data['coverage_details'] = []
        elif not isinstance(data['coverage_details'], list):
            data['coverage_details'] = []
            
        # Ensure deductibles is a list
        if 'deductibles' not in data:
            data['deductibles'] = []
        elif not isinstance(data['deductibles'], list):
            data['deductibles'] = []
        
        return data 