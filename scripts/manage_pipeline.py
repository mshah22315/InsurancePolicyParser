#!/usr/bin/env python3
"""
Pipeline management script for the insurance policy processing system.
This script provides command-line tools to manage the pipeline.
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from app import create_app
from pipeline_tasks import (
    run_pipeline_step,
    run_chained_pipeline
)
from celery.result import AsyncResult

def run_full_pipeline_cli(file_paths: List[str], invoice_paths: Dict[str, str] = None):
    """
    Run the full pipeline from command line
    """
    print(f"Starting full pipeline for {len(file_paths)} documents...")
    
    # Validate file paths
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            return False
    
    if invoice_paths:
        for policy_number, invoice_path in invoice_paths.items():
            if not os.path.exists(invoice_path):
                print(f"Error: Invoice file not found for policy {policy_number}: {invoice_path}")
                return False
    
    # Run the pipeline
    task = run_chained_pipeline.delay(file_paths, invoice_paths)
    
    print(f"Pipeline task started with ID: {task.id}")
    print("You can monitor progress using: python scripts/manage_pipeline.py status <task_id>")
    
    return True

def run_single_step_cli(step_name: str, parameters: Dict[str, Any]):
    """
    Run a single pipeline step from command line
    """
    print(f"Running pipeline step: {step_name}")
    
    # Validate step name
    valid_steps = ['process_documents', 'vector_processing', 'store_chunks', 'update_context']
    if step_name not in valid_steps:
        print(f"Error: Invalid step name. Must be one of: {valid_steps}")
        return False
    
    # Run the step
    task = run_pipeline_step.delay(step_name, **parameters)
    
    print(f"Step task started with ID: {task.id}")
    print("You can monitor progress using: python scripts/manage_pipeline.py status <task_id>")
    
    return True

def get_task_status(task_id: str):
    """
    Get the status of a task
    """
    task_result = AsyncResult(task_id)
    
    if task_result.ready():
        if task_result.successful():
            result = task_result.result
            print(f"Task {task_id} completed successfully!")
            print("Result:")
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"Task {task_id} failed!")
            print(f"Error: {task_result.result}")
    else:
        info = task_result.info
        if info:
            print(f"Task {task_id} is running...")
            print("Progress:")
            print(json.dumps(info, indent=2, default=str))
        else:
            print(f"Task {task_id} is running...")

def list_policies():
    """
    List all processed policies
    """
    app = create_app()
    with app.app_context():
        from app.models import ProcessedPolicyData
        
        policies = ProcessedPolicyData.query.all()
        
        if not policies:
            print("No policies found in database.")
            return
        
        print(f"Found {len(policies)} processed policies:")
        print("-" * 80)
        
        for policy in policies:
            print(f"Policy Number: {policy.policy_number}")
            print(f"Insurer: {policy.insurer_name}")
            print(f"Policyholder: {policy.policyholder_name}")
            print(f"Property Address: {policy.property_address}")
            print(f"Effective Date: {policy.effective_date}")
            print(f"Expiration Date: {policy.expiration_date}")
            print(f"Total Premium: ${policy.total_premium}" if policy.total_premium else "Total Premium: Not specified")
            print(f"Created: {policy.created_at}")
            print("-" * 80)

def run_interactive_context_update(policy_number: str):
    """
    Run interactive context update for a specific policy
    """
    print(f"Starting interactive context update for policy: {policy_number}")
    print("This will open the interactive update script where you can:")
    
    print("- Specify house features")
    print("- Set renewal dates")
    print()
    
    # Import and run the interactive script
    try:
        from scripts.update_policy_context import main as update_main
        
        # Set up the policy number for the interactive script
        import sys
        sys.argv = ['update_policy_context.py', '--policy', policy_number]
        
        # Run the interactive update
        update_main()
        
    except ImportError:
        print("Error: Could not import update_policy_context script")
        print("Please ensure the script exists and is properly configured")
        return False
    except Exception as e:
        print(f"Error running interactive update: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Insurance Policy Processing Pipeline Management')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Full pipeline command
    pipeline_parser = subparsers.add_parser('pipeline', help='Run the full pipeline')
    pipeline_parser.add_argument('files', nargs='+', help='Policy document file paths')
    pipeline_parser.add_argument('--invoices', nargs='*', help='Invoice file paths (format: policy_number:file_path)')
    
    # Single step command
    step_parser = subparsers.add_parser('step', help='Run a single pipeline step')
    step_parser.add_argument('step_name', choices=['process_documents', 'vector_processing', 'store_chunks', 'update_context'], 
                           help='Name of the step to run')
    step_parser.add_argument('--file-paths', nargs='*', help='File paths for process_documents step')
    step_parser.add_argument('--policy-numbers', nargs='*', help='Policy numbers for other steps')
    step_parser.add_argument('--invoice-paths', nargs='*', help='Invoice paths for update_context step (format: policy_number:file_path)')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get task status')
    status_parser.add_argument('task_id', help='Task ID to check')
    
    # List policies command
    subparsers.add_parser('list-policies', help='List all processed policies')
    
    # Interactive context update command
    context_parser = subparsers.add_parser('context-interactive', help='Run interactive context update for a policy')
    context_parser.add_argument('--policy', required=True, help='Policy number to update')
    
    args = parser.parse_args()
    
    if args.command == 'pipeline':
        # Parse invoice paths
        invoice_paths = {}
        if args.invoices:
            for invoice_arg in args.invoices:
                if ':' in invoice_arg:
                    policy_number, file_path = invoice_arg.split(':', 1)
                    invoice_paths[policy_number] = file_path
                else:
                    print(f"Warning: Invalid invoice format: {invoice_arg}. Expected format: policy_number:file_path")
        
        run_full_pipeline_cli(args.files, invoice_paths if invoice_paths else None)
    
    elif args.command == 'step':
        parameters = {}
        
        if args.step_name == 'process_documents':
            if not args.file_paths:
                print("Error: file-paths required for process_documents step")
                return
            parameters['file_paths'] = args.file_paths
        else:
            if not args.policy_numbers:
                print("Error: policy-numbers required for this step")
                return
            parameters['policy_numbers'] = args.policy_numbers
            
            if args.step_name == 'update_context' and args.invoice_paths:
                invoice_paths = {}
                for invoice_arg in args.invoice_paths:
                    if ':' in invoice_arg:
                        policy_number, file_path = invoice_arg.split(':', 1)
                        invoice_paths[policy_number] = file_path
                    else:
                        print(f"Warning: Invalid invoice format: {invoice_arg}. Expected format: policy_number:file_path")
                parameters['invoice_paths'] = invoice_paths
        
        run_single_step_cli(args.step_name, parameters)
    
    elif args.command == 'status':
        get_task_status(args.task_id)
    
    elif args.command == 'list-policies':
        list_policies()
    
    elif args.command == 'context-interactive':
        run_interactive_context_update(args.policy)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 