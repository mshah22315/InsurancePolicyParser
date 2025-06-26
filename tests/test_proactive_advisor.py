#!/usr/bin/env python3
"""
Test script for the Proactive Advisor Service.

This script demonstrates how to use the ProactiveAdvisorService to analyze
policies for risks and opportunities.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from app import create_app
from app.models import ProcessedPolicyData
from app.services.proactive_advisor_service import ProactiveAdvisorService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_proactive_advisor():
    """Test the proactive advisor service with sample data."""
    app = create_app()
    
    with app.app_context():
        # Get all policies from the database
        policies = ProcessedPolicyData.query.all()
        
        if not policies:
            logger.warning("No policies found in database. Please process some policies first.")
            return
        
        logger.info(f"Found {len(policies)} policies to analyze")
        
        # Test with the first few policies
        for i, policy in enumerate(policies[:3]):  # Test first 3 policies
            logger.info(f"\n{'='*60}")
            logger.info(f"Analyzing Policy {i+1}: {policy.policy_number}")
            logger.info(f"Policyholder: {policy.policyholder_name}")
            logger.info(f"{'='*60}")
            
            # Create advisor service
            advisor = ProactiveAdvisorService(policy)
            
            # Run analysis
            insights = advisor.analyze_for_risks_and_opportunities()
            
            if not insights:
                logger.info("No insights found for this policy.")
                continue
            
            # Display insights by type
            for insight_type in ['risk', 'opportunity', 'alert']:
                type_insights = advisor.get_insights_by_type(insight_type)
                if type_insights:
                    logger.info(f"\n{insight_type.upper()} INSIGHTS:")
                    for insight in type_insights:
                        logger.info(f"  • {insight['title']}")
                        logger.info(f"    Finding: {insight['finding']}")
                        logger.info(f"    Action: {insight['action']}")
                        logger.info(f"    Priority: {insight['priority']}")
                        logger.info(f"    Impact: {insight['estimated_impact']}")
                        logger.info("")

def test_with_sample_data():
    """Test with manually created sample data."""
    app = create_app()
    
    with app.app_context():
        # Create a sample policy for testing
        sample_policy = ProcessedPolicyData(
            policy_number="TEST-001",
            policyholder_name="John Smith",
            insurer_name="Sample Insurance Co",
            total_premium=2500.00,
            roof_age_years=18,  # Aging roof
            property_features=["monitored_alarm", "sprinkler_system"],  # Features for discounts
            renewal_date=datetime.strptime("2025-01-15", "%Y-%m-%d").date(),  # Near renewal
            coverage_details=[
                {
                    "coverage_type": "Coverage A - Dwelling",
                    "limit": "150000.00"  # Low limit
                }
            ],
            deductibles=[
                {
                    "coverage_type": "All Coverages",
                    "amount": "500.00",  # Low deductible
                    "type": "per_occurrence"
                }
            ],
            original_document_gcs_path="test_path.pdf",
            processed_json_gcs_path="test_path.json"
        )
        
        logger.info("Testing with sample policy data...")
        logger.info(f"Policy: {sample_policy.policy_number}")
        logger.info(f"Roof Age: {sample_policy.roof_age_years} years")
        logger.info(f"Property Features: {sample_policy.property_features}")
        logger.info(f"Renewal Date: {sample_policy.renewal_date}")
        
        # Create advisor service
        advisor = ProactiveAdvisorService(sample_policy)
        
        # Run analysis
        insights = advisor.analyze_for_risks_and_opportunities()
        
        logger.info(f"\nFound {len(insights)} insights:")
        for i, insight in enumerate(insights, 1):
            logger.info(f"\n{i}. {insight['title']} ({insight['type'].upper()})")
            logger.info(f"   Finding: {insight['finding']}")
            logger.info(f"   Action: {insight['action']}")
            logger.info(f"   Priority: {insight['priority']}")
            logger.info(f"   Impact: {insight['estimated_impact']}")

def main():
    """Main function to run tests."""
    print("Proactive Advisor Service Test")
    print("=" * 40)
    
    # Test with real data first
    try:
        test_proactive_advisor()
    except Exception as e:
        logger.error(f"Error testing with real data: {e}")
    
    # Test with sample data
    try:
        test_with_sample_data()
    except Exception as e:
        logger.error(f"Error testing with sample data: {e}")

if __name__ == "__main__":
    main() 