#!/usr/bin/env python3
"""
Script to identify and remove duplicate records from the processed_policy_data table.

This script helps clean up duplicate policy records by:
1. Identifying duplicates based on policy_number
2. Showing details of duplicates for review
3. Providing options to preview, dry-run, or actually delete duplicates
4. Keeping the most recent record when duplicates are found
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from app import create_app
from app.models import ProcessedPolicyData
from app.db import db
from sqlalchemy import func, desc
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DuplicateCleaner:
    """Class to handle duplicate cleanup operations."""
    
    def __init__(self):
        self.app = create_app()
        self.duplicates_found = []
        self.records_to_delete = []
        
    def find_duplicates(self) -> List[Tuple[str, int]]:
        """
        Find all policy numbers that have duplicate records.
        
        Returns:
            List of tuples (policy_number, count)
        """
        with self.app.app_context():
            duplicates = db.session.query(
                ProcessedPolicyData.policy_number,
                func.count(ProcessedPolicyData.id)
            ).group_by(ProcessedPolicyData.policy_number).having(
                func.count(ProcessedPolicyData.id) > 1
            ).all()
            
            self.duplicates_found = duplicates
            return duplicates
    
    def get_duplicate_details(self, policy_number: str) -> List[ProcessedPolicyData]:
        """
        Get detailed information about duplicate records for a specific policy.
        
        Args:
            policy_number: The policy number to get details for
            
        Returns:
            List of ProcessedPolicyData records for this policy
        """
        with self.app.app_context():
            records = ProcessedPolicyData.query.filter_by(
                policy_number=policy_number
            ).order_by(desc(ProcessedPolicyData.created_at)).all()
            
            return records
    
    def preview_duplicates(self, limit: int = 5) -> None:
        """
        Preview duplicate records with detailed information.
        
        Args:
            limit: Maximum number of duplicate policies to show details for
        """
        if not self.duplicates_found:
            logger.info("No duplicates found.")
            return
        
        logger.info(f"Found {len(self.duplicates_found)} policy numbers with duplicates:")
        
        for i, (policy_number, count) in enumerate(self.duplicates_found[:limit]):
            logger.info(f"\n{i+1}. Policy: {policy_number} ({count} records)")
            
            records = self.get_duplicate_details(policy_number)
            for j, record in enumerate(records):
                logger.info(f"   Record {j+1}:")
                logger.info(f"     ID: {record.id}")
                logger.info(f"     Created: {record.created_at}")
                logger.info(f"     Updated: {record.updated_at}")
                logger.info(f"     Policyholder: {record.policyholder_name}")
                logger.info(f"     Insurer: {record.insurer_name}")
                logger.info(f"     Document Path: {record.original_document_gcs_path}")
                logger.info(f"     Has Deductibles: {bool(record.deductibles)}")
                logger.info(f"     Has Coverage Details: {bool(record.coverage_details)}")
        
        if len(self.duplicates_found) > limit:
            logger.info(f"\n... and {len(self.duplicates_found) - limit} more duplicate policies")
    
    def identify_records_to_delete(self) -> List[ProcessedPolicyData]:
        """
        Identify which duplicate records should be deleted.
        Keeps the most recent record (by created_at) and marks others for deletion.
        
        Returns:
            List of ProcessedPolicyData records to delete
        """
        records_to_delete = []
        
        with self.app.app_context():
            for policy_number, count in self.duplicates_found:
                records = self.get_duplicate_details(policy_number)
                
                # Keep the most recent record (first in the list due to desc ordering)
                # Delete all others
                for record in records[1:]:
                    records_to_delete.append(record)
        
        self.records_to_delete = records_to_delete
        return records_to_delete
    
    def dry_run_deletion(self) -> None:
        """
        Perform a dry run of the deletion process.
        Shows what would be deleted without actually deleting anything.
        """
        if not self.duplicates_found:
            logger.info("No duplicates found to delete.")
            return
        
        records_to_delete = self.identify_records_to_delete()
        
        logger.info(f"\nDRY RUN - Would delete {len(records_to_delete)} duplicate records:")
        logger.info("=" * 60)
        
        # Group by policy number for better display
        by_policy = {}
        for record in records_to_delete:
            if record.policy_number not in by_policy:
                by_policy[record.policy_number] = []
            by_policy[record.policy_number].append(record)
        
        for policy_number, records in by_policy.items():
            logger.info(f"\nPolicy: {policy_number}")
            for record in records:
                logger.info(f"  - ID: {record.id}, Created: {record.created_at}, Policyholder: {record.policyholder_name}")
        
        logger.info(f"\nTotal records that would be deleted: {len(records_to_delete)}")
        logger.info("Run with --execute to actually perform the deletion.")
    
    def execute_deletion(self, confirm: bool = False) -> bool:
        """
        Actually delete the duplicate records.
        
        Args:
            confirm: If True, skip confirmation prompt
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.duplicates_found:
            logger.info("No duplicates found to delete.")
            return True
        
        records_to_delete = self.identify_records_to_delete()
        
        if not records_to_delete:
            logger.info("No records identified for deletion.")
            return True
        
        logger.info(f"About to delete {len(records_to_delete)} duplicate records.")
        
        if not confirm:
            response = input("Are you sure you want to proceed? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                logger.info("Deletion cancelled.")
                return False
        
        try:
            with self.app.app_context():
                # Delete records
                for record in records_to_delete:
                    logger.info(f"Deleting record ID {record.id} (Policy: {record.policy_number})")
                    db.session.delete(record)
                
                # Commit the changes
                db.session.commit()
                logger.info(f"Successfully deleted {len(records_to_delete)} duplicate records.")
                return True
                
        except Exception as e:
            logger.error(f"Error during deletion: {str(e)}")
            db.session.rollback()
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the duplicate situation.
        
        Returns:
            Dictionary with summary information
        """
        total_duplicates = len(self.duplicates_found)
        total_records_to_delete = len(self.records_to_delete) if self.records_to_delete else 0
        
        # Count total records
        with self.app.app_context():
            total_records = ProcessedPolicyData.query.count()
        
        return {
            'total_records': total_records,
            'duplicate_policies': total_duplicates,
            'records_to_delete': total_records_to_delete,
            'records_after_cleanup': total_records - total_records_to_delete
        }

def main():
    """Main function to handle command line arguments and execute cleanup."""
    parser = argparse.ArgumentParser(
        description="Clean up duplicate records in processed_policy_data table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/cleanup_duplicates.py --preview
  python scripts/cleanup_duplicates.py --dry-run
  python scripts/cleanup_duplicates.py --execute
  python scripts/cleanup_duplicates.py --execute --confirm
        """
    )
    
    parser.add_argument('--preview', action='store_true', 
                       help='Preview duplicate records with details')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without actually deleting')
    parser.add_argument('--execute', action='store_true',
                       help='Actually delete duplicate records')
    parser.add_argument('--confirm', action='store_true',
                       help='Skip confirmation prompt when executing deletion')
    parser.add_argument('--limit', type=int, default=5,
                       help='Limit number of duplicate policies to show in preview (default: 5)')
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any([args.preview, args.dry_run, args.execute]):
        parser.print_help()
        return
    
    cleaner = DuplicateCleaner()
    
    # Find duplicates
    duplicates = cleaner.find_duplicates()
    
    if not duplicates:
        logger.info("No duplicate records found in the database.")
        return
    
    # Show summary
    summary = cleaner.get_summary()
    logger.info(f"Database Summary:")
    logger.info(f"  Total records: {summary['total_records']}")
    logger.info(f"  Duplicate policies: {summary['duplicate_policies']}")
    logger.info(f"  Records to delete: {summary['records_to_delete']}")
    logger.info(f"  Records after cleanup: {summary['records_after_cleanup']}")
    
    # Execute requested actions
    if args.preview:
        cleaner.preview_duplicates(limit=args.limit)
    
    if args.dry_run:
        cleaner.dry_run_deletion()
    
    if args.execute:
        success = cleaner.execute_deletion(confirm=args.confirm)
        if success:
            # Show final summary
            final_summary = cleaner.get_summary()
            logger.info(f"\nCleanup completed successfully!")
            logger.info(f"Final record count: {final_summary['total_records']}")
        else:
            logger.error("Cleanup failed!")
            sys.exit(1)

if __name__ == "__main__":
    main() 