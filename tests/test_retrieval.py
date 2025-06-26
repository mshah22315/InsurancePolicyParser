import sys
from pathlib import Path
import re

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from app import create_app
from app.services.vector_service import VectorService
from app.models import PolicyChunk, Policy, ProcessedPolicyData
import logging
from typing import List, Dict, Any, Optional
from tabulate import tabulate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_policy_reference(query: str) -> Optional[str]:
    """Extract the most specific policy document reference from the query."""
    logger.info(f"extract_policy_reference: raw query: {query}")
    # Very greedy pattern: capture everything from $amount up to 'Policy Doc N', allowing any characters in between
    pattern = r'(\$\d+K[\s\S]*?Policy\s+Doc\s+\d+|Sample Policy Doc \d+|Policy Doc \d+|Document \d+)'
    matches = re.findall(pattern, query, re.IGNORECASE | re.DOTALL)
    logger.info(f"extract_policy_reference: matches found: {matches}")
    if matches:
        # Prefer the match that starts with $ (most specific), else the longest
        dollar_matches = [m for m in matches if m.strip().startswith('$')]
        if dollar_matches:
            policy_ref = max(dollar_matches, key=len).strip()
            logger.info(f"Extracted policy reference: {policy_ref}")
            return policy_ref
        policy_ref = max(matches, key=len).strip()
        logger.info(f"Extracted policy reference: {policy_ref}")
        return policy_ref
    logger.warning(f"No policy reference pattern matched in query: {query}")
    return None

def get_policy_by_reference(policy_ref: str) -> Optional[Policy]:
    """Get the Policy object based on the policy reference, using fuzzy matching."""
    app = create_app()
    with app.app_context():
        logger.info(f"Searching for policy with reference: {policy_ref}")
        all_policies = Policy.query.all()
        logger.info("Available policies in database:")
        for p in all_policies:
            logger.info(f"- {p.document_source_filename}")
        
        # Try exact (case-insensitive) substring match first
        for p in all_policies:
            if policy_ref.lower() in p.document_source_filename.lower():
                logger.info(f"Found exact match: {p.document_source_filename}")
                return p
        
        # If not found, try fuzzy matching: match on doc number and any $ amount/type prefix
        # Extract doc number
        number_match = re.search(r'Policy\s+Doc\s+(\d+)', policy_ref, re.IGNORECASE)
        policy_number = number_match.group(1) if number_match else None
        # Extract $ amount and type
        prefix_match = re.search(r'(\$\d+K\s+[A-Za-z ]+)', policy_ref)
        prefix = prefix_match.group(1).strip() if prefix_match else None
        candidates = []
        for p in all_policies:
            # Match doc number
            filename_number_match = re.search(r'Policy\s+Doc\s+(\d+)', p.document_source_filename)
            filename_number = filename_number_match.group(1) if filename_number_match else None
            if policy_number and filename_number == policy_number:
                if prefix:
                    if prefix.lower() in p.document_source_filename.lower():
                        candidates.append(p)
                else:
                    candidates.append(p)
        if candidates:
            logger.info(f"Found {len(candidates)} candidate(s) for policy reference '{policy_ref}'. Returning the first.")
            return candidates[0]
        logger.warning(f"No policy found for reference: {policy_ref}")
        return None

def search_policy_chunks(query: str, top_n: int = 3) -> List[Dict[str, Any]]:
    """Search policy chunks using vector similarity with policy document filtering."""
    app = create_app()
    
    with app.app_context():
        vector_service = VectorService()
        
        # Extract policy reference from query
        policy_ref = extract_policy_reference(query)
        if not policy_ref:
            logger.warning(f"No policy reference found in query: {query}")
            return []
            
        logger.info(f"Extracted policy reference: {policy_ref}")
        
        # Get the specific policy
        policy = get_policy_by_reference(policy_ref)
        if not policy:
            logger.warning(f"No policy found for reference: {policy_ref}")
            return []
        
        logger.info(f"Found policy with ID: {policy.id} for reference: {policy_ref}")
        logger.info(f"Policy filename: {policy.document_source_filename}")
        
        # Check if there are any chunks for this policy
        chunks = PolicyChunk.query.filter_by(policy_id=policy.id).all()
        logger.info(f"Found {len(chunks)} chunks for policy {policy.id}")
        
        if not chunks:
            logger.warning(f"No chunks found for policy {policy.id}")
            return []
        
        # Special handling for coverage limits
        if "coverage limits" in query.lower():
            logger.info("Processing coverage limits query...")
            coverage_chunks = [c for c in chunks if c.section_type.startswith('coverage_')]
            
            if coverage_chunks:
                results = []
                coverage_info = []
                seen_coverage_types = set()  # Track seen coverage types to avoid duplicates
                
                # Extract coverage information from each coverage chunk
                for chunk in coverage_chunks:
                    coverage_type_match = re.search(r'coverage_type:\s*([^\n]+)', chunk.chunk_text)
                    limit_match = re.search(r'limit:\s*([^\n]+)', chunk.chunk_text)
                    
                    if coverage_type_match and limit_match:
                        coverage_type = coverage_type_match.group(1).strip()
                        limit = limit_match.group(1).strip()
                        
                        # Only add if we haven't seen this coverage type before
                        if coverage_type not in seen_coverage_types:
                            seen_coverage_types.add(coverage_type)
                            coverage_info.append(f"{coverage_type}: ${limit}")
                
                if coverage_info:
                    # Create a result with all coverage information
                    results.append({
                        'policy_number': 'Unknown',  # Will be updated later
                        'document_source_filename': policy.document_source_filename,
                        'section_type': 'coverage',
                        'similarity': 1.0,
                        'chunk_text': "\n".join(coverage_info)
                    })
                    
                    # Update policy number if available
                    try:
                        processed_policy = ProcessedPolicyData.query.filter_by(
                            original_document_gcs_path=policy.document_source_filename
                        ).first()
                        
                        if processed_policy and processed_policy.policy_number:
                            results[0]['policy_number'] = processed_policy.policy_number
                    except Exception as e:
                        logger.warning(f"Error getting policy number: {str(e)}")
                    
                    return results

        # Special handling for deductibles
        if "deductibles" in query.lower():
            logger.info("Processing deductibles query...")
            # Get the processed policy data which contains the deductibles in JSON format
            from sqlalchemy import or_
            processed_policy = ProcessedPolicyData.query.filter(
                ProcessedPolicyData.original_document_gcs_path.ilike(f"%{policy.document_source_filename}")
            ).first()
            
            logger.info(f"Found processed policy: {processed_policy is not None}")
            if processed_policy:
                logger.info(f"Processed policy deductibles: {processed_policy.deductibles}")
            
            if processed_policy and processed_policy.deductibles:
                results = []
                deductible_info = []
                
                # Format each deductible
                for deductible in processed_policy.deductibles:
                    coverage_type = deductible.get('coverage_type', 'Unknown')
                    amount = deductible.get('amount', 'Unknown')
                    type_info = deductible.get('type', 'Unknown')
                    deductible_info.append(f"{coverage_type}: ${amount} ({type_info})")
                
                if deductible_info:
                    results.append({
                        'policy_number': processed_policy.policy_number or 'Unknown',
                        'document_source_filename': policy.document_source_filename,
                        'section_type': 'deductibles',
                        'similarity': 1.0,
                        'chunk_text': "\n".join(deductible_info)
                    })
                    return results
            else:
                logger.warning("No deductibles found in processed policy data")
                
                # Try to find deductibles in chunks as fallback
                deductible_chunks = [c for c in chunks if "deductible" in c.chunk_text.lower()]
                if deductible_chunks:
                    results = []
                    deductible_info = []
                    
                    for chunk in deductible_chunks:
                        logger.info(f"Found chunk with deductible info: {chunk.chunk_text[:200]}...")
                        deductible_info.append(chunk.chunk_text)
                    
                    if deductible_info:
                        results.append({
                            'policy_number': 'Unknown',
                            'document_source_filename': policy.document_source_filename,
                            'section_type': 'deductibles',
                            'similarity': 1.0,
                            'chunk_text': "\n".join(deductible_info)
                        })
                        return results
        
        # For specific data fields, try to extract directly from policy chunks
        query_lower = query.lower()
        if any(term in query_lower for term in ["who is the insured", "policyholder", "policy number", 
                                               "total premium", "effective date", "property address", 
                                               "insurer name"]):
            # Get the policy details chunk
            policy_details = next((c for c in chunks if c.section_type == 'policy_details'), None)
            if policy_details:
                extracted_info = None
                section_type = "policy_details"
                
                if "who is the insured" in query_lower or "policyholder" in query_lower:
                    match = re.search(r'policyholder_name:\s*([^\n]+)', policy_details.chunk_text)
                    if match:
                        extracted_info = match.group(1).strip()
                        section_type = "policyholder"
                
                elif "policy number" in query_lower:
                    match = re.search(r'policy_number:\s*([^\n]+)', policy_details.chunk_text)
                    if match:
                        extracted_info = match.group(1).strip()
                        section_type = "policy_number"
                
                elif "total premium" in query_lower:
                    match = re.search(r'total_premium:\s*([^\n]+)', policy_details.chunk_text)
                    if match:
                        premium = match.group(1).strip()
                        # Add dollar sign if not present
                        if not premium.startswith('$'):
                            premium = f"${premium}"
                        extracted_info = premium
                        section_type = "total_premium"
                
                elif "effective date" in query_lower:
                    match = re.search(r'effective_date:\s*([^\n]+)', policy_details.chunk_text)
                    if match:
                        extracted_info = match.group(1).strip()
                        section_type = "effective_date"
                
                elif "property address" in query_lower:
                    match = re.search(r'property_address:\s*([^\n]+)', policy_details.chunk_text)
                    if match:
                        extracted_info = match.group(1).strip()
                        section_type = "property_address"
                
                elif "insurer name" in query_lower:
                    match = re.search(r'insurer_name:\s*([^\n]+)', policy_details.chunk_text)
                    if match:
                        extracted_info = match.group(1).strip()
                        section_type = "insurer_name"
                
                if extracted_info:
                    # Get policy number if available
                    policy_number = 'Unknown'
                    match = re.search(r'policy_number:\s*([^\n]+)', policy_details.chunk_text)
                    if match:
                        policy_number = match.group(1).strip()
                    
                    return [{
                        'policy_number': policy_number,
                        'document_source_filename': policy.document_source_filename,
                        'section_type': section_type,
                        'similarity': 1.0,
                        'chunk_text': extracted_info
                    }]
        
        # If direct extraction fails, fall back to vector search
        logger.info("Using vector search for the query")
        similar_chunks = vector_service.search_similar_chunks(
            query, 
            top_k=top_n,
            filters={'policy_id': policy.id}
        )
        
        logger.info(f"Found {len(similar_chunks)} similar chunks")
        
        # Format results
        results = []
        for chunk_data in similar_chunks:
            # Get policy details
            chunk_policy = Policy.query.get(chunk_data['policy_id'])
            if not chunk_policy:
                logger.warning(f"Could not find policy for chunk with policy_id: {chunk_data['policy_id']}")
                continue
                
            processed_policy = ProcessedPolicyData.query.filter_by(
                original_document_gcs_path=chunk_policy.document_source_filename
            ).first()
            
            # Extract policy number from the chunk text if available
            policy_number = None
            if processed_policy and processed_policy.policy_number:
                policy_number = processed_policy.policy_number
            else:
                # Try to extract from chunk text
                policy_match = re.search(r'policy_number:\s*([^\n]+)', chunk_data['chunk_text'], re.IGNORECASE)
                if policy_match:
                    policy_number = policy_match.group(1).strip()
            
            results.append({
                'policy_number': policy_number or 'Unknown',
                'document_source_filename': chunk_policy.document_source_filename,
                'section_type': chunk_data['section_type'],
                'similarity': chunk_data['similarity'],
                'chunk_text': chunk_data['chunk_text']
            })
        
        # Sort results by similarity score in descending order
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results

def extract_relevant_preview(text: str, query: str, max_length: int = 100) -> str:
    """Extract the most relevant part of the text based on the query."""
    # Split text into sentences
    sentences = text.split('.')
    
    # Find the most relevant sentence based on query terms
    query_terms = set(query.lower().split())
    best_sentence = None
    best_score = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Calculate relevance score based on query term matches
        sentence_terms = set(sentence.lower().split())
        score = len(query_terms.intersection(sentence_terms))
        
        if score > best_score:
            best_score = score
            best_sentence = sentence
    
    # If no good match found, just take the first sentence
    if not best_sentence:
        best_sentence = sentences[0].strip() if sentences else text
    
    # Truncate if too long
    if len(best_sentence) > max_length:
        best_sentence = best_sentence[:max_length] + "..."
    
    return best_sentence

def evaluate_search_results(query: str, results: list):
    """Evaluate and display search results."""
    print(f"\nQuery: {query}")
    print("\nResults:")
    
    if not results:
        print("No results found.")
        return
    
    # Format results for display
    table_data = []
    for i, result in enumerate(results, 1):
        # Clean up the document source filename for display
        doc_name = result['document_source_filename']
        if doc_name.startswith('timestamp_uuid_structured.pdf'):
            doc_name = doc_name.replace('timestamp_uuid_structured.pdf', '')
        
        # Format multi-line text for display
        answer_text = result['chunk_text']
        if '\n' in answer_text:
            # For multi-line text (like coverage limits), preserve the formatting
            lines = answer_text.split('\n')
            formatted_text = lines[0]
            for line in lines[1:]:
                formatted_text += f"\n{line}"
        else:
            formatted_text = answer_text
        
        table_data.append([
            i,
            doc_name,
            result['section_type'],
            f"{result['similarity']:.4f}",
            formatted_text
        ])
    
    print(tabulate(
        table_data,
        headers=['Rank', 'Document', 'Section', 'Score', 'Answer'],
        tablefmt='grid'
    ))

def main():
    # Test queries
    test_queries = [
        "What are the deductibles in $200K High Tornado Risk Policy Doc 1?",
        "What is the policy number for Sample Policy Doc 2?",
        "What is the total premium for Sample Policy Doc 2?",
        "What are the coverage limits for Sample Policy Doc 2?",
        "What is the effective date for Sample Policy Doc 2?",
        "What is the property address for Sample Policy Doc 2?",
        "What is the insurer name for Sample Policy Doc 2?"
    ]
    
    print("Testing Policy Document Retrieval")
    print("=================================")
    
    for query in test_queries:
        results = search_policy_chunks(query, top_n=3)
        evaluate_search_results(query, results)
        
        # Add a pause between queries
        input("\nPress Enter to continue to next query...")

if __name__ == "__main__":
    main() 