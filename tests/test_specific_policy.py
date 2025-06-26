#!/usr/bin/env python3
"""
Test script to analyze a specific policy by policy number.
"""

import sys
from pathlib import Path

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

def test_specific_policy(policy_number: str):
    """Test the proactive advisor service with a specific policy."""
    app = create_app()
    
    with app.app_context():
        # Find the policy
        policy = ProcessedPolicyData.query.filter_by(policy_number=policy_number).first()
        
        if not policy:
            logger.error(f"Policy '{policy_number}' not found")
            return
        
        logger.info(f"Testing policy: {policy.policy_number}")
        logger.info(f"Policyholder: {policy.policyholder_name}")
        logger.info(f"Roof Age: {policy.roof_age_years} years")
        logger.info(f"Property Features: {policy.property_features}")
        logger.info(f"Renewal Date: {policy.renewal_date}")
        logger.info("=" * 60)
        
        # Create advisor service
        advisor = ProactiveAdvisorService(policy)
        
        # Run analysis
        insights = advisor.analyze_for_risks_and_opportunities()
        
        if not insights:
            logger.info("No insights found for this policy.")
            return
        
        logger.info(f"Found {len(insights)} insights:")
        logger.info("=" * 60)
        
        for i, insight in enumerate(insights, 1):
            logger.info(f"\n{i}. {insight['title']} ({insight['type'].upper()})")
            logger.info(f"   Finding: {insight['finding']}")
            logger.info(f"   Action: {insight['action']}")
            logger.info(f"   Priority: {insight['priority']}")
            logger.info(f"   Impact: {insight['estimated_impact']}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_specific_policy.py <policy_number>")
        print("Example: python scripts/test_specific_policy.py HMP-IA-001-2025")
        sys.exit(1)
    
    policy_number = sys.argv[1]
    test_specific_policy(policy_number) 