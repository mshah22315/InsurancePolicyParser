def extract_raw_text(policy_data: dict) -> str:
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