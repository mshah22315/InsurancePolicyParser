import os
import json
from datetime import datetime, date
from io import BytesIO
from PIL import Image
import fitz  # PyMuPDF
import google.generativeai as genai
from flask import current_app
from ..models import ProcessedPolicyData
from app.utils.gcs_utils import upload_to_gcs, download_from_gcs
from google.cloud import storage
import uuid
from ..db import db

class InsuranceDocumentProcessorService:
    def __init__(self):
        # Initialize Google Cloud Storage client
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(current_app.config['GOOGLE_CLOUD_STORAGE_BUCKET'])
        
        # Initialize Google AI
        genai.configure(api_key=current_app.config['GOOGLE_AI_API_KEY'])
        self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
        self.text_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Get GCS path prefixes
        self.original_pdfs_prefix = current_app.config['GCS_ORIGINAL_PDFS_PREFIX']
        self.structured_jsons_prefix = current_app.config['GCS_STRUCTURED_JSONS_PREFIX']

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
            
            # Save to database
            policy_data = ProcessedPolicyData(
                policy_number=structured_data.get('policy_number'),
                insurer_name=structured_data.get('insurer_name'),
                policyholder_name=structured_data.get('policyholder_name'),
                property_address=structured_data.get('property_address'),
                effective_date=self._convert_date_string(structured_data.get('effective_date')),
                expiration_date=self._convert_date_string(structured_data.get('expiration_date')),
                total_premium=structured_data.get('total_premium'),
                coverage_details=structured_data.get('coverage_details'),
                deductibles=structured_data.get('deductibles'),
                original_document_gcs_path=original_gcs_path,
                processed_json_gcs_path=processed_json_path
            )
            
            db.session.add(policy_data)
            db.session.commit()
            
            return {
                'status': 'success',
                'message': 'Document processed successfully',
                'data': structured_data
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'status': 'error',
                'message': f'Error processing document: {str(e)}'
            }

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