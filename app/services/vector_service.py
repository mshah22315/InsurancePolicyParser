from typing import List, Dict, Any, Optional
from flask import current_app
from sqlalchemy import text
from app.db import db
from sklearn.feature_extraction.text import TfidfVectorizer
import json
import numpy as np
from ..models import PolicyChunk
import logging
import re

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self):
        # Initialize TF-IDF vectorizer with fixed vocabulary size
        self.vectorizer = TfidfVectorizer(
            max_features=1000,  # Limit vocabulary size
            stop_words='english',  # Remove common English words
            ngram_range=(1, 2),  # Use both unigrams and bigrams
            min_df=2,  # Minimum document frequency
            max_df=0.95  # Maximum document frequency
        )
        
        # Get database instance
        self.db = db
        
        # Fit vectorizer on existing chunks if any
        self._fit_vectorizer()

    def _fit_vectorizer(self):
        """Fit the TF-IDF vectorizer on existing chunks."""
        try:
            chunks = PolicyChunk.query.all()
            if chunks:
                texts = [chunk.chunk_text for chunk in chunks]
                self.vectorizer.fit(texts)
                current_app.logger.info(f"Fitted vectorizer on {len(texts)} existing chunks")
                
                # Store the vocabulary size for consistency checks
                self.vocab_size = len(self.vectorizer.vocabulary_)
                current_app.logger.info(f"Vocabulary size: {self.vocab_size}")
        except Exception as e:
            current_app.logger.warning(f"Could not fit vectorizer on existing chunks: {str(e)}")
            self.vocab_size = 1000  # Default size if fitting fails

    def get_text_embedding(self, text: str) -> list:
        """Get embedding for text using TF-IDF."""
        try:
            # Handle empty or invalid text
            if not text or not isinstance(text, str):
                current_app.logger.warning("Empty or invalid text provided for embedding")
                return [0.0] * self.vocab_size  # Return zero vector of appropriate size
            
            # If vectorizer is not fitted, fit it with the current text
            if not hasattr(self.vectorizer, 'vocabulary_'):
                self.vectorizer.fit([text])
                self.vocab_size = len(self.vectorizer.vocabulary_)
                current_app.logger.info(f"Fitted vectorizer with single text, vocabulary size: {self.vocab_size}")
            
            # Transform the text to TF-IDF vector
            vector = self.vectorizer.transform([text])
            embedding = vector.toarray()[0].tolist()
            
            # Ensure consistent dimensions
            if len(embedding) != self.vocab_size:
                current_app.logger.warning(f"Embedding dimension mismatch: got {len(embedding)}, expected {self.vocab_size}")
                # Pad or truncate to match vocabulary size
                if len(embedding) < self.vocab_size:
                    embedding.extend([0.0] * (self.vocab_size - len(embedding)))
                else:
                    embedding = embedding[:self.vocab_size]
            
            # Check if we got a zero vector
            if all(x == 0 for x in embedding):
                current_app.logger.warning("Generated zero vector for text")
                # Add a small random noise to prevent zero vector
                embedding = [x + 1e-10 for x in embedding]
            
            return embedding
        except Exception as e:
            current_app.logger.error(f"Error generating embedding: {str(e)}")
            raise

    def add_documents_to_db(self, documents: list) -> None:
        """Add documents with their embeddings to the database."""
        try:
            # Get all texts for fitting the vectorizer
            texts = [doc['chunk_text'] for doc in documents]
            
            # Fit vectorizer on new texts
            self.vectorizer.fit(texts)
            current_app.logger.info(f"Fitted vectorizer on {len(texts)} new documents")
            
            # Generate embeddings for all documents
            for doc in documents:
                embedding = self.get_text_embedding(doc['chunk_text'])
                chunk = PolicyChunk(
                    policy_id=doc['policy_id'],
                    document_source_filename=doc['document_source_filename'],
                    section_type=doc['section_type'],
                    chunk_text=doc['chunk_text'],
                    embedding=embedding
                )
                self.db.session.add(chunk)
            
            self.db.session.commit()
            current_app.logger.info(f"Successfully added {len(documents)} documents to database")
            
        except Exception as e:
            self.db.session.rollback()
            current_app.logger.error(f"Error adding documents to database: {str(e)}")
            raise

    def query_vector_db(self, query_text: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query the vector database using similarity search."""
        try:
            # Generate embedding for query text
            query_embedding = self.get_text_embedding(query_text)
            
            # Build the SQL query
            sql = """
            SELECT 
                id,
                policy_id,
                document_source_filename,
                section_type,
                chunk_text,
                1 - (embedding <=> :query_embedding::vector) as similarity
            FROM policy_chunks
            WHERE 1=1
            """
            
            params = {'query_embedding': json.dumps(query_embedding)}
            
            # Add filters if provided
            if filters:
                for key, value in filters.items():
                    sql += f" AND {key} = :{key}"
                    params[key] = value
            
            # Add ordering and limit
            sql += """
            ORDER BY similarity DESC
            LIMIT :top_k
            """
            params['top_k'] = top_k
            
            # Execute query
            result = self.db.session.execute(text(sql), params)
            
            # Format results
            return [dict(row) for row in result]
            
        except Exception as e:
            current_app.logger.error(f"Error querying vector database: {str(e)}")
            raise

    def search_similar_chunks(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> list:
        """Search for similar chunks using vector similarity and extract specific information."""
        try:
            # Get embedding for the query
            query_embedding = self.get_text_embedding(query)
            
            # Convert embedding to numpy array for similarity calculation
            query_embedding = np.array(query_embedding)
            
            # Normalize query embedding
            query_norm = np.linalg.norm(query_embedding)
            if query_norm < 1e-10:  # If query is a zero vector
                current_app.logger.warning("Query resulted in zero vector")
                return []
            query_embedding = query_embedding / query_norm
            
            # Get chunks with optional filtering
            db_query = PolicyChunk.query
            if filters:
                for key, value in filters.items():
                    db_query = db_query.filter(getattr(PolicyChunk, key) == value)
            chunks = db_query.all()
            
            # Calculate similarities
            similarities = []
            for chunk in chunks:
                chunk_embedding = np.array(chunk.embedding)
                
                # Ensure chunk embedding has correct dimensions
                if len(chunk_embedding) != self.vocab_size:
                    current_app.logger.warning(f"Chunk embedding dimension mismatch: got {len(chunk_embedding)}, expected {self.vocab_size}")
                    # Pad or truncate to match vocabulary size
                    if len(chunk_embedding) < self.vocab_size:
                        chunk_embedding = np.pad(chunk_embedding, (0, self.vocab_size - len(chunk_embedding)))
                    else:
                        chunk_embedding = chunk_embedding[:self.vocab_size]
                
                chunk_norm = np.linalg.norm(chunk_embedding)
                
                if chunk_norm < 1e-10:  # Skip zero vectors
                    continue
                    
                # Normalize chunk embedding
                chunk_embedding = chunk_embedding / chunk_norm
                
                # Calculate cosine similarity
                similarity = np.dot(query_embedding, chunk_embedding)
                
                # Double check that this chunk belongs to the correct policy
                if filters and 'policy_id' in filters and chunk.policy_id != filters['policy_id']:
                    current_app.logger.warning(f"Skipping chunk from wrong policy: {chunk.policy_id} != {filters['policy_id']}")
                    continue
                
                similarities.append((chunk, similarity))
            
            # Sort by similarity and get top k
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_results = similarities[:top_k]
            
            # Extract specific information based on query type
            results = []
            query_lower = query.lower()
            
            # Keep track of coverage types to avoid duplicates
            seen_coverage_types = set()
            
            for chunk, similarity in top_results:
                chunk_text = chunk.chunk_text
                
                # Extract specific information based on query
                extracted_info = None
                
                if "who is the insured" in query_lower or "policyholder" in query_lower:
                    # Look for policyholder name
                    match = re.search(r'policyholder_name:\s*([^\n]+)', chunk_text)
                    if match:
                        extracted_info = match.group(1).strip()
                
                elif "policy number" in query_lower:
                    # Look for policy number
                    match = re.search(r'policy_number:\s*([^\n]+)', chunk_text)
                    if match:
                        extracted_info = match.group(1).strip()
                
                elif "total premium" in query_lower:
                    # Look for total premium
                    match = re.search(r'total_premium:\s*([^\n]+)', chunk_text)
                    if match:
                        premium = match.group(1).strip()
                        # Add dollar sign if not present
                        if not premium.startswith('$'):
                            premium = f"${premium}"
                        extracted_info = premium
                
                elif "coverage limits" in query_lower:
                    # Look for coverage details across all sections
                    coverages = []
                    
                    # Check if this is a coverage section
                    if "coverage_type:" in chunk_text.lower() and "limit:" in chunk_text.lower():
                        coverage_type_match = re.search(r'coverage_type:\s*([^\n]+)', chunk_text)
                        limit_match = re.search(r'limit:\s*([^\n]+)', chunk_text)
                        
                        if coverage_type_match and limit_match:
                            coverage_type = coverage_type_match.group(1).strip()
                            limit = limit_match.group(1).strip()
                            
                            # Only add if we haven't seen this coverage type before
                            if coverage_type not in seen_coverage_types:
                                seen_coverage_types.add(coverage_type)
                                coverages.append(f"{coverage_type}: ${limit}")
                    
                    # Also check for coverage_details in JSON format
                    json_match = re.search(r'coverage_details:\s*({[^}]+})', chunk_text, re.DOTALL)
                    if json_match:
                        try:
                            import json
                            coverage_json = json_match.group(1).replace("'", '"')
                            # Clean up the JSON string by replacing single quotes with double quotes
                            coverage_json = re.sub(r'(\w+):', r'"\1":', coverage_json)
                            coverage_data = json.loads(coverage_json)
                            
                            # Format each coverage type and limit
                            for coverage_type, details in coverage_data.items():
                                if isinstance(details, dict) and 'limit' in details:
                                    limit = details['limit']
                                    # Only add if we haven't seen this coverage type before
                                    if coverage_type not in seen_coverage_types:
                                        seen_coverage_types.add(coverage_type)
                                        coverages.append(f"{coverage_type}: ${limit}")
                        except (json.JSONDecodeError, ValueError) as e:
                            current_app.logger.warning(f"Could not parse coverage JSON: {e}")
                    
                    if coverages:
                        extracted_info = "\n".join(coverages)
                
                elif "deductibles" in query_lower:
                    # Look for deductible information
                    deductibles = []
                    
                    # Check for deductibles in JSON format
                    json_match = re.search(r'deductibles:\s*(\[[^\]]+\])', chunk_text, re.DOTALL)
                    if json_match:
                        try:
                            import json
                            deductibles_json = json_match.group(1).replace("'", '"')
                            # Clean up the JSON string
                            deductibles_json = re.sub(r'(\w+):', r'"\1":', deductibles_json)
                            deductibles_data = json.loads(deductibles_json)
                            
                            # Format each deductible
                            for deductible in deductibles_data:
                                if isinstance(deductible, dict):
                                    coverage_type = deductible.get('coverage_type', 'Unknown')
                                    amount = deductible.get('amount', 'Unknown')
                                    type_info = deductible.get('type', 'Unknown')
                                    deductibles.append(f"{coverage_type}: ${amount} ({type_info})")
                        except (json.JSONDecodeError, ValueError) as e:
                            current_app.logger.warning(f"Could not parse deductibles JSON: {e}")
                    
                    if deductibles:
                        extracted_info = "\n".join(deductibles)
                
                elif "effective date" in query_lower:
                    # Look for effective date
                    match = re.search(r'effective_date:\s*([^\n]+)', chunk_text)
                    if match:
                        extracted_info = match.group(1).strip()
                
                elif "property address" in query_lower:
                    # Look for property address
                    match = re.search(r'property_address:\s*([^\n]+)', chunk_text)
                    if match:
                        extracted_info = match.group(1).strip()
                
                elif "insurer name" in query_lower:
                    # Look for insurer name
                    match = re.search(r'insurer_name:\s*([^\n]+)', chunk_text)
                    if match:
                        extracted_info = match.group(1).strip()
                
                if extracted_info:
                    # Make sure we're only returning the specific answer, not the whole chunk
                    results.append({
                        'policy_id': chunk.policy_id,
                        'section_type': chunk.section_type,
                        'document_source_filename': chunk.document_source_filename,
                        'chunk_text': extracted_info,  # Only include the extracted information
                        'similarity': float(similarity)
                    })
            
            return results
            
        except Exception as e:
            current_app.logger.error(f"Error searching similar chunks: {str(e)}")
            raise 