import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from flask import Flask
from app.services.insurance_document_processor_service import InsuranceDocumentProcessorService
from config import Config
from app.db import db
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def process_file(file_path):
    """Process a single PDF file."""
    app = create_app()
    
    with app.app_context():
        processor = InsuranceDocumentProcessorService()
        
        try:
            logger.info(f"Processing {file_path.name}...")
            
            # Read the PDF file
            with open(file_path, 'rb') as f:
                document_bytes = f.read()
            
            # Process the document
            result = processor.process_document(document_bytes, file_path.name)
            
            if result['status'] == 'success':
                logger.info(f"Successfully processed {file_path.name}")
                logger.info(f"Policy Number: {result['data'].get('policy_number', 'N/A')}")
                logger.info(f"Insurer: {result['data'].get('insurer_name', 'N/A')}")
                logger.info(f"Policyholder: {result['data'].get('policyholder_name', 'N/A')}")
                
                # Log coverage details
                if result['data'].get('coverage_details'):
                    logger.info("Coverage Details:")
                    for coverage in result['data']['coverage_details']:
                        logger.info(f"  - {coverage['coverage_type']}: ${coverage['limit']}")
                
                # Log deductibles
                if result['data'].get('deductibles'):
                    logger.info("Deductibles:")
                    for deductible in result['data']['deductibles']:
                        logger.info(f"  - {deductible['coverage_type']}: ${deductible['amount']} ({deductible['type']})")
            else:
                logger.error(f"Failed to process {file_path.name}: {result['message']}")
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {str(e)}")

def process_directory(directory_path):
    """Process all PDF files in the given directory."""
    app = create_app()
    
    with app.app_context():
        processor = InsuranceDocumentProcessorService()
        
        # Get all PDF files in the directory
        pdf_files = list(Path(directory_path).glob('**/*.pdf'))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {directory_path}")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process each file
        for pdf_file in pdf_files:
            process_file(pdf_file)

def main():
    if len(sys.argv) != 2:
        print("Usage: python process_policies.py <path>")
        print("  <path> can be either a directory or a single PDF file")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    
    if not path.exists():
        print(f"Error: {path} does not exist")
        sys.exit(1)
    
    if path.is_file():
        if path.suffix.lower() != '.pdf':
            print(f"Error: {path} is not a PDF file")
            sys.exit(1)
        process_file(path)
    elif path.is_dir():
        process_directory(path)
    else:
        print(f"Error: {path} is neither a file nor a directory")
        sys.exit(1)

if __name__ == '__main__':
    main() 