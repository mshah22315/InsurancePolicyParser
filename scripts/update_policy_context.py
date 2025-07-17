#!/usr/bin/env python3
"""
Script to update a single policy with realistic context data.

This script:
1. Takes a policy number as user input
2. Extracts renewal date from policy document expiration date
3. Uses InvoiceParser to extract installation date from roofing invoices
4. Allows user input for property features
5. Updates the policy with the collected data

Usage: python scripts/update_policy_context.py
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime, date, timezone
from typing import Optional
from dateutil import parser as dateutil_parser
import argparse

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from app import create_app
from app.models import ProcessedPolicyData
from app.db import db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Available property features
PROPERTY_FEATURES = [
    "monitored_alarm",
    "sprinkler_system", 
    "impact_resistant_roof",
    "new_construction",
    "security_camera",
    "smart_home_system",
    "fire_extinguisher",
    "storm_shutters",
    "backup_generator",
    "water_leak_detector"
]

def find_policy_document(policy_number):
    """
    Find the policy document file for the given policy number.
    
    Args:
        policy_number: The policy number to search for
        
    Returns:
        str: Path to the policy document file, or None if not found
    """
    data_dir = Path(project_root) / "data"
    
    # Search in all subdirectories
    for subdir in data_dir.iterdir():
        if subdir.is_dir():
            for file_path in subdir.rglob("*.pdf"):
                if policy_number.lower() in file_path.name.lower():
                    return str(file_path)
    
    return None

def extract_expiration_date_from_policy(policy_number):
    """
    Extract expiration date from the policy document.
    
    Args:
        policy_number: The policy number
        
    Returns:
        str: Expiration date in YYYY-MM-DD format, or None if not found
    """
    # Find the policy document
    policy_file = find_policy_document(policy_number)
    if not policy_file:
        logger.warning(f"Policy document not found for {policy_number}")
        return None
    
    logger.info(f"Found policy document: {policy_file}")
    
    # For now, we'll use a placeholder approach
    # In a real implementation, you would:
    # 1. Extract text from PDF using PyPDF2 or similar
    # 2. Use regex patterns to find expiration dates
    # 3. Parse various date formats
    
    # Common patterns for expiration dates in insurance documents
    expiration_patterns = [
        r"expiration\s+date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"expires[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"end\s+date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"policy\s+end[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"valid\s+until[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    ]
    
    # For demonstration, we'll ask the user to provide the expiration date
    print(f"\nPolicy document found: {os.path.basename(policy_file)}")
    print("Please extract the expiration date from the policy document.")
    
    while True:
        try:
            expiration_input = input("Enter expiration date (MM/DD/YYYY or YYYY-MM-DD): ").strip()
            
            if not expiration_input:
                return None
            
            # Try to parse the date
            if "/" in expiration_input:
                # MM/DD/YYYY format
                month, day, year = expiration_input.split("/")
                if len(year) == 2:
                    year = "20" + year
                expiration_date = date(int(year), int(month), int(day))
            elif "-" in expiration_input:
                # YYYY-MM-DD format
                expiration_date = datetime.strptime(expiration_input, '%Y-%m-%d').date()
            else:
                print("❌ Invalid date format. Please use MM/DD/YYYY or YYYY-MM-DD")
                continue
            
            return expiration_date.strftime('%Y-%m-%d')
            
        except ValueError:
            print("❌ Invalid date. Please try again.")
        except KeyboardInterrupt:
            return None

def get_roofing_invoice_path(policy_number=None):
    """
    Get the path to a roofing invoice file from user input.
    
    Args:
        policy_number: Optional policy number to filter related invoices
        
    Returns:
        str: Path to the invoice file, or None if user cancels
    """
    print("\n" + "="*50)
    print("ROOFING INVOICE INPUT")
    print("="*50)
    
    # Find available invoice files
    data_dir = str(Path(project_root) / "data")
    invoice_files = find_invoice_files(data_dir, policy_number)
    
    if invoice_files:
        print("Found roofing-related files:")
        for i, file_path in enumerate(invoice_files, 1):
            print(f"  {i:2d}. {os.path.basename(file_path)}")
        print()
    
    print("Options:")
    if invoice_files:
        print("1. Enter the number of an existing file above")
    print("2. Enter the full path to a roofing invoice file")
    print("3. Type 'skip' to enter roof date manually")
    print("4. Type 'none' if no roofing work has been done")
    
    while True:
        try:
            choice = input("\nEnter your choice: ").strip()
            
            if choice.lower() == 'skip':
                return None
            elif choice.lower() == 'none':
                return "none"
            
            # Check if it's a number (existing file)
            try:
                file_index = int(choice) - 1
                if 0 <= file_index < len(invoice_files):
                    return invoice_files[file_index]
                else:
                    print("❌ Invalid file number")
                    continue
            except ValueError:
                # Assume it's a file path
                if os.path.exists(choice):
                    return choice
                else:
                    print(f"❌ File not found: {choice}")
                    continue
                    
        except KeyboardInterrupt:
            return None

def get_user_features():
    """
    Get property features from user input.
    
    Returns:
        list: List of selected feature strings
    """
    print(f"\nAvailable property features:")
    for i, feature in enumerate(PROPERTY_FEATURES, 1):
        print(f"  {i:2d}. {feature}")
    
    print("\nEnter the numbers of features the property has (comma-separated), or 'none' for no features:")
    
    while True:
        try:
            user_input = input("Features: ").strip().lower()
            
            if user_input == 'none' or user_input == '':
                return []
            
            # Parse comma-separated numbers
            feature_indices = [int(x.strip()) for x in user_input.split(',')]
            
            # Validate indices
            selected_features = []
            for idx in feature_indices:
                if 1 <= idx <= len(PROPERTY_FEATURES):
                    selected_features.append(PROPERTY_FEATURES[idx - 1])
                else:
                    print(f"❌ Invalid feature number: {idx}")
                    continue
            
            if selected_features:
                return selected_features
            else:
                print("❌ No valid features selected. Please try again.")
                
        except ValueError:
            print("❌ Invalid input. Please enter numbers separated by commas.")
        except KeyboardInterrupt:
            return []

def get_all_policy_numbers():
    """
    Get all policy numbers from the database.
    
    Returns:
        list: List of policy number strings
    """
    app = create_app()
    
    with app.app_context():
        policies = ProcessedPolicyData.query.with_entities(
            ProcessedPolicyData.policy_number
        ).all()
        
        return [policy.policy_number for policy in policies]

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extract text from PDF file using Gemini Vision model if available, else PyPDF2.
    """
    try:
        import google.generativeai as genai
        from flask import current_app
        genai.configure(api_key=current_app.config['GOOGLE_AI_API_KEY'])
        vision_model = genai.GenerativeModel('gemini-1.5-flash')
        with open(pdf_path, 'rb') as f:
            document_bytes = f.read()
        image_parts = [
            {"mime_type": "application/pdf", "data": document_bytes}
        ]
        vision_response = vision_model.generate_content([
            "Extract all text from this invoice document. Focus on finding dates, especially installation dates, completion dates, issue dates, and due dates. Include all text content that might contain date information.",
            *image_parts
        ])
        extracted_text = vision_response.text
        logging.info(f"Successfully extracted {len(extracted_text)} characters using Gemini Vision")
        return extracted_text
    except Exception as e:
        logging.warning(f"Could not use Gemini Vision: {e}")
        # Fallback to PyPDF2
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e2:
            logging.error(f"Error extracting text from PDF: {e2}")
            return None

def extract_labeled_dates_from_text(text: str) -> dict:
    """
    Extract dates with their labels from text using regex patterns.
    Returns: dict mapping label to parsed date
    """
    text = re.sub(r'\s+', ' ', text)
    labeled_dates = {}
    pattern_labels = [
        (r"\*\s*\*\*Date of Issue:\*\*\s*([A-Za-z]+ \d{1,2}, \d{4})", "Date of Issue"),
        (r"\*\s*\*\*Project Completion Date:\*\*\s*([A-Za-z]+ \d{1,2}, \d{4})", "Project Completion Date"),
        (r"\*\s*\*\*Due Date:\*\*\s*([A-Za-z]+ \d{1,2}, \d{4})", "Due Date"),
        (r"\*\s*\*\*Invoice Date:\*\*\s*([A-Za-z]+ \d{1,2}, \d{4})", "Invoice Date"),
        (r"\*\s*\*\*Installation Date:\*\*\s*([A-Za-z]+ \d{1,2}, \d{4})", "Installation Date"),
        (r"\*\s*\*\*Work Date:\*\*\s*([A-Za-z]+ \d{1,2}, \d{4})", "Work Date"),
        (r"\*\s*\*\*Service Date:\*\*\s*([A-Za-z]+ \d{1,2}, \d{4})", "Service Date"),
        (r"\*\s*\*\*Completion Date:\*\*\s*([A-Za-z]+ \d{1,2}, \d{4})", "Completion Date"),
        (r"date\s+of\s+issue[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Date of Issue"),
        (r"issue\s+date[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Issue Date"),
        (r"invoice\s+date[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Invoice Date"),
        (r"completion\s+date[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Completion Date"),
        (r"installation\s+date[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Installation Date"),
        (r"work\s+date[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Work Date"),
        (r"service\s+date[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Service Date"),
        (r"due\s+date[:\s]*([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})", "Due Date"),
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

def extract_installation_date_from_invoice(file_path: str) -> Optional[str]:
    """
    Extract the most relevant installation date from an invoice PDF file.
    Returns: date string in YYYY-MM-DD or None
    """
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return None
    text = extract_text_from_pdf(file_path)
    if not text:
        logging.error(f"Could not extract text from file: {file_path}")
        return None
    labeled_dates = extract_labeled_dates_from_text(text)
    if not labeled_dates:
        logging.warning("No dates found in invoice text")
        return None
    preferred_labels = [
        "Installation Date",
        "Work Date",
        "Service Date",
        "Completion Date",
        "Project Completion Date",
        "Date of Issue",
        "Invoice Date"
    ]
    for label in preferred_labels:
        if label in labeled_dates:
            selected_date = labeled_dates[label]
            logging.info(f"Using {label} as installation date: {selected_date}")
            return selected_date.strftime('%Y-%m-%d')
    # Fallback: use earliest date
    earliest_date = min(labeled_dates.values())
    return earliest_date.strftime('%Y-%m-%d')

def calculate_roof_age(installation_date: str) -> Optional[int]:
    """
    Calculate roof age from installation date.
    Args:
        installation_date: Installation date in YYYY-MM-DD format
    Returns:
        Roof age in years or None if invalid
    """
    try:
        install_date = datetime.strptime(installation_date, '%Y-%m-%d').date()
        today = date.today()
        years = today.year - install_date.year
        if today.month < install_date.month or (today.month == install_date.month and today.day < install_date.day):
            years -= 1
        return max(0, years)
    except Exception:
        return None

def update_policy_context(policy_number, roof_age=None, features=None, renewal_date=None):
    """
    Update a ProcessedPolicyData record with contextual information.
    
    Args:
        policy_number: The policy number to update
        roof_age: Age of the roof in years (if None, will calculate from invoice)
        features: List of property features (if None, will ask user)
        renewal_date: Renewal date in YYYY-MM-DD format (if None, will extract from policy)
    """
    app = create_app()
    
    with app.app_context():
        # Find the policy by policy number
        policy = ProcessedPolicyData.query.filter_by(policy_number=policy_number).first()
        if not policy:
            logger.error(f"Policy with number '{policy_number}' not found")
            return False
        
        logger.info(f"Found policy: {policy.policy_number} ({policy.policyholder_name})")
        
        # Extract renewal date from policy document if not provided
        if renewal_date is None:
            # Use expiration date from the database
            if policy.expiration_date:
                renewal_date = policy.expiration_date.strftime('%Y-%m-%d')
                logger.info(f"Set renewal date from database expiration_date: {renewal_date}")
            else:
                logger.warning("No expiration date found in database for this policy")
        
        # Calculate roof age from invoice if not provided
        if roof_age is None:
            # Get roofing invoice path from user
            invoice_path = get_roofing_invoice_path(policy_number)
            
            if invoice_path == "none":
                logger.info("No roofing work has been done")
                roof_age = None
            elif invoice_path:
                # Use InvoiceParser to extract date from invoice
                invoice_date = extract_installation_date_from_invoice(invoice_path)
                
                if invoice_date:
                    roof_age = calculate_roof_age(invoice_date)
                    logger.info(f"Calculated roof age: {roof_age} years (from {invoice_date})")
                else:
                    logger.warning("Could not extract roof date from invoice")
                    # Fallback to manual input
                    print("\nCould not automatically extract date from invoice.")
                    print("Please enter the roof installation date manually:")
                    
                    while True:
                        try:
                            manual_date = input("Installation date (MM/DD/YYYY or YYYY-MM-DD): ").strip()
                            if not manual_date:
                                break
                            
                            # Try to parse the date
                            if "/" in manual_date:
                                month, day, year = manual_date.split("/")
                                if len(year) == 2:
                                    year = "20" + year
                                roof_installation_date = date(int(year), int(month), int(day))
                            elif "-" in manual_date:
                                roof_installation_date = datetime.strptime(manual_date, '%Y-%m-%d').date()
                            else:
                                print("❌ Invalid date format. Please use MM/DD/YYYY or YYYY-MM-DD")
                                continue
                            
                            roof_age = calculate_roof_age(roof_installation_date.strftime('%Y-%m-%d'))
                            logger.info(f"Manual input - Calculated roof age: {roof_age} years")
                            break
                            
                        except ValueError:
                            print("❌ Invalid date. Please try again.")
                        except KeyboardInterrupt:
                            break
            else:
                # Prompt for manual input if skipped
                print("\nNo invoice provided. Please enter the roof installation date manually.")
                while True:
                    try:
                        manual_date = input("Installation date (MM/DD/YYYY or YYYY-MM-DD): ").strip()
                        if not manual_date:
                            break
                        # Try to parse the date
                        if "/" in manual_date:
                            month, day, year = manual_date.split("/")
                            if len(year) == 2:
                                year = "20" + year
                            roof_installation_date = date(int(year), int(month), int(day))
                        elif "-" in manual_date:
                            roof_installation_date = datetime.strptime(manual_date, '%Y-%m-%d').date()
                        else:
                            print("❌ Invalid date format. Please use MM/DD/YYYY or YYYY-MM-DD")
                            continue
                        roof_age = calculate_roof_age(roof_installation_date.strftime('%Y-%m-%d'))
                        logger.info(f"Manual input - Calculated roof age: {roof_age} years")
                        break
                    except ValueError:
                        print("❌ Invalid date. Please try again.")
                    except KeyboardInterrupt:
                        break
        
        # Get features from user if not provided
        if features is None:
            features = get_user_features()
            if features:
                logger.info(f"User selected features: {features}")
            else:
                logger.info("No features selected by user")
        
        # Update fields
        if roof_age is not None:
            policy.roof_age_years = roof_age
        
        if features is not None:
            policy.property_features = features
        
        if renewal_date is not None:
            policy.renewal_date = datetime.strptime(renewal_date, '%Y-%m-%d').date()
        
        # Always update the last proactive analysis timestamp
        policy.last_proactive_analysis = datetime.now(timezone.utc)
        
        # Commit changes
        db.session.commit()
        logger.info("Successfully updated policy context data")
        return True

def display_policy_summary(policy_number):
    """
    Display a summary of the policy after update.
    
    Args:
        policy_number: The policy number to display
    """
    app = create_app()
    
    with app.app_context():
        policy = ProcessedPolicyData.query.filter_by(policy_number=policy_number).first()
        if not policy:
            logger.error(f"Policy with number '{policy_number}' not found")
            return
        
        logger.info("\n" + "="*60)
        logger.info("POLICY CONTEXT SUMMARY")
        logger.info("="*60)
        logger.info(f"Policy Number: {policy.policy_number}")
        logger.info(f"Policyholder: {policy.policyholder_name}")
        logger.info(f"Roof Age: {policy.roof_age_years} years")
        logger.info(f"Property Features: {policy.property_features}")
        logger.info(f"Renewal Date: {policy.renewal_date}")
        logger.info(f"Last Analysis: {policy.last_proactive_analysis}")
        
        # Calculate days until renewal
        if policy.renewal_date:
            days_until_renewal = (policy.renewal_date - date.today()).days
            logger.info(f"Days until renewal: {days_until_renewal}")
            
            if days_until_renewal <= 30:
                logger.warning("⚠️  POLICY DUE FOR RENEWAL SOON!")
            elif days_until_renewal <= 90:
                logger.info("📅 Policy renewal approaching")
        
        # Roof age analysis
        if policy.roof_age_years:
            if policy.roof_age_years > 20:
                logger.warning("⚠️  AGING ROOF - Consider replacement")
            elif policy.roof_age_years > 15:
                logger.info("🏠 Roof approaching end of life")
            elif policy.roof_age_years <= 5:
                logger.info("🆕 New roof - Good condition")
        
        logger.info("="*60)

def find_invoice_files(data_dir: str, policy_number: str = None) -> list:
    """
    Find invoice files in the data directory.
    Args:
        data_dir: Path to data directory
        policy_number: Optional policy number to filter by
    Returns:
        List of invoice file paths
    """
    invoice_files = []
    data_path = Path(data_dir)
    if not data_path.exists():
        return invoice_files
    invoice_keywords = ["roof", "roofing", "shingle", "gutter", "siding", "invoice"]
    for subdir in data_path.iterdir():
        if subdir.is_dir():
            for file_path in subdir.rglob("*"):
                if file_path.is_file():
                    filename_lower = file_path.name.lower()
                    if any(keyword in filename_lower for keyword in invoice_keywords):
                        if policy_number and policy_number.lower() in filename_lower:
                            invoice_files.append(str(file_path))
                        elif not policy_number:
                            invoice_files.append(str(file_path))
    return invoice_files

def main():
    """Main function to handle user input and execute policy update."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Update policy context with interactive input')
    parser.add_argument('--policy', help='Policy number to update (if not provided, will prompt for selection)')
    args = parser.parse_args()
    
    print("="*60)
    print("POLICY CONTEXT UPDATE TOOL")
    print("="*60)
    print("This tool will update a policy with realistic context data from documents.")
    print()
    
    # Get all available policy numbers
    policy_numbers = get_all_policy_numbers()
    
    if not policy_numbers:
        logger.error("No policies found in database.")
        return
    
    # Determine policy number
    if args.policy:
        # Use command line argument
        policy_number = args.policy
        if policy_number not in policy_numbers:
            logger.error(f"Policy number '{policy_number}' not found in database.")
            print("Available policy numbers:")
            for policy_num in policy_numbers:
                print(f"  - {policy_num}")
            return
    else:
        # Interactive mode - display available policies
        print(f"Found {len(policy_numbers)} policies in database.")
        print("Available policy numbers:")
        for i, policy_num in enumerate(policy_numbers, 1):
            print(f"  {i:2d}. {policy_num}")
        
        print()
        
        # Get user input
        while True:
            try:
                choice = input("Enter policy number or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    print("Exiting...")
                    return
                
                # Check if it's a valid policy number
                if choice in policy_numbers:
                    policy_number = choice
                    break
                else:
                    print(f"❌ Policy number '{choice}' not found. Please try again.")
            except KeyboardInterrupt:
                print("\nExiting...")
                return
            except Exception as e:
                print(f"❌ Error: {e}. Please try again.")
    
    print()
    print(f"Updating policy: {policy_number}")
    print()
    
    # Update the policy
    success = update_policy_context(policy_number)
    
    if success:
        print()
        print("✅ Policy updated successfully!")
        print()
        
        # Display summary
        display_policy_summary(policy_number)
    else:
        print()
        print("❌ Failed to update policy.")

if __name__ == "__main__":
    main() 