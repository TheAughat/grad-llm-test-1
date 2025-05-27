import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple
import nltk
from nltk.tokenize import sent_tokenize
import re

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class SemanticChunker:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', similarity_threshold: float = 0.7):
        """
        Initialize the semantic chunker.
        
        Args:
            model_name: Name of the sentence transformer model to use
            similarity_threshold: Cosine similarity threshold below which to split chunks
        """
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold
    
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK."""
        sentences = sent_tokenize(text)
        # Filter out very short sentences (likely artifacts)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        return sentences
    
    def get_embeddings(self, sentences: List[str]) -> np.ndarray:
        """Generate embeddings for all sentences."""
        return self.model.encode(sentences)
    
    def find_chunk_boundaries(self, embeddings: np.ndarray, window_size: int = 3) -> List[int]:
        """
        Find chunk boundaries using sliding window cosine similarity.
        
        Args:
            embeddings: Sentence embeddings
            window_size: Size of the sliding window for comparison
            
        Returns:
            List of indices where chunks should be split
        """
        if len(embeddings) <= window_size * 2:
            return []
        
        boundaries = []
        
        for i in range(window_size, len(embeddings) - window_size):
            # Get windows before and after current position
            window_before = embeddings[i-window_size:i]
            window_after = embeddings[i:i+window_size]
            
            # Calculate average embeddings for each window
            avg_before = np.mean(window_before, axis=0).reshape(1, -1)
            avg_after = np.mean(window_after, axis=0).reshape(1, -1)
            
            # Calculate cosine similarity between windows
            similarity = cosine_similarity(avg_before, avg_after)[0][0]
            
            # If similarity drops below threshold, mark as boundary
            if similarity < self.similarity_threshold:
                boundaries.append(i)
        
        return boundaries
    
    def create_chunks(self, sentences: List[str], boundaries: List[int]) -> List[str]:
        """Create text chunks based on identified boundaries."""
        if not boundaries:
            return [' '.join(sentences)]
        
        chunks = []
        start_idx = 0
        
        for boundary in boundaries:
            chunk_sentences = sentences[start_idx:boundary]
            if chunk_sentences:  # Only add non-empty chunks
                chunks.append(' '.join(chunk_sentences))
            start_idx = boundary
        
        # Add the final chunk
        final_chunk_sentences = sentences[start_idx:]
        if final_chunk_sentences:
            chunks.append(' '.join(final_chunk_sentences))
        
        return chunks
    
    def chunk_text(self, text: str, window_size: int = 3, min_chunk_size: int = 2) -> List[dict]:
        """
        Main method to chunk text semantically.
        
        Args:
            text: Input text to chunk
            window_size: Size of sliding window for similarity comparison
            min_chunk_size: Minimum number of sentences per chunk
            
        Returns:
            List of dictionaries containing chunk info
        """
        # Preprocess text
        clean_text = self.preprocess_text(text)
        
        # Split into sentences
        sentences = self.split_into_sentences(clean_text)
        
        if len(sentences) < min_chunk_size * 2:
            return [{
                'chunk_id': 0,
                'text': clean_text,
                'sentence_count': len(sentences),
                'start_sentence': 0,
                'end_sentence': len(sentences) - 1
            }]
        
        # Generate embeddings
        embeddings = self.get_embeddings(sentences)
        
        # Find boundaries
        boundaries = self.find_chunk_boundaries(embeddings, window_size)
        
        # Create chunks
        chunks = self.create_chunks(sentences, boundaries)
        
        # Format output with metadata
        result = []
        sentence_idx = 0
        
        for i, chunk in enumerate(chunks):
            chunk_sentences = chunk.split('. ')
            # Rejoin with periods (they were split during processing)
            chunk_sentences = [s + '.' if not s.endswith('.') else s for s in chunk_sentences[:-1]] + [chunk_sentences[-1]]
            chunk_sentence_count = len([s for s in chunk_sentences if s.strip()])
            
            result.append({
                'chunk_id': i,
                'text': chunk.strip(),
                'sentence_count': chunk_sentence_count,
                'start_sentence': sentence_idx,
                'end_sentence': sentence_idx + chunk_sentence_count - 1
            })
            
            sentence_idx += chunk_sentence_count
        
        return result

# Enhanced chunker with additional features
class AdvancedSemanticChunker(SemanticChunker):
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', similarity_threshold: float = 0.7):
        super().__init__(model_name, similarity_threshold)
    
    def adaptive_threshold_chunking(self, text: str, percentile: float = 25) -> List[dict]:
        """
        Use adaptive thresholding based on similarity distribution.
        
        Args:
            text: Input text to chunk
            percentile: Percentile of similarities to use as threshold
        """
        clean_text = self.preprocess_text(text)
        sentences = self.split_into_sentences(clean_text)
        
        if len(sentences) < 6:
            return self.chunk_text(text)
        
        embeddings = self.get_embeddings(sentences)
        
        # Calculate all similarities
        similarities = []
        window_size = 3
        
        for i in range(window_size, len(embeddings) - window_size):
            window_before = embeddings[i-window_size:i]
            window_after = embeddings[i:i+window_size]
            
            avg_before = np.mean(window_before, axis=0).reshape(1, -1)
            avg_after = np.mean(window_after, axis=0).reshape(1, -1)
            
            similarity = cosine_similarity(avg_before, avg_after)[0][0]
            similarities.append(similarity)
        
        # Use percentile as adaptive threshold
        adaptive_threshold = np.percentile(similarities, percentile)
        
        # Find boundaries with adaptive threshold
        boundaries = []
        for i, similarity in enumerate(similarities):
            if similarity < adaptive_threshold:
                boundaries.append(i + window_size)
        
        chunks = self.create_chunks(sentences, boundaries)
        
        # Format output
        result = []
        sentence_idx = 0
        
        for i, chunk in enumerate(chunks):
            chunk_sentences = chunk.split('. ')
            chunk_sentences = [s + '.' if not s.endswith('.') else s for s in chunk_sentences[:-1]] + [chunk_sentences[-1]]
            chunk_sentence_count = len([s for s in chunk_sentences if s.strip()])
            
            result.append({
                'chunk_id': i,
                'text': chunk.strip(),
                'sentence_count': chunk_sentence_count,
                'start_sentence': sentence_idx,
                'end_sentence': sentence_idx + chunk_sentence_count - 1,
                'adaptive_threshold_used': adaptive_threshold
            })
            
            sentence_idx += chunk_sentence_count
        
        return result

# Example usage and testing
def example_usage():
    # Sample report text
    sample_text = """
    Artificial intelligence has revolutionized many industries in recent years. Machine learning algorithms 
    can now process vast amounts of data with unprecedented accuracy. Deep learning models have shown 
    remarkable success in image recognition and natural language processing tasks.
    
    However, the automotive industry faces unique challenges when implementing AI solutions. Self-driving 
    cars require real-time decision making capabilities that must prioritize safety above all else. 
    The regulatory environment for autonomous vehicles remains complex and varies significantly between countries.
    
    In healthcare, AI applications have shown tremendous promise for diagnostic imaging. Radiologists are 
    increasingly using AI-assisted tools to detect anomalies in medical scans. Early detection of diseases 
    like cancer has improved significantly with these technological advances.
    
    Despite these advances, ethical concerns about AI deployment continue to grow. Issues of bias in 
    algorithmic decision-making affect hiring, lending, and criminal justice systems. Transparency and 
    accountability in AI systems remain ongoing challenges for developers and regulators alike.
    """
    
    # Initialize chunker
    chunker = SemanticChunker(similarity_threshold=0.6)
    
    # Chunk the text
    chunks = chunker.chunk_text(sample_text)
    
    print("=== SEMANTIC CHUNKING RESULTS ===")
    print(f"Original text split into {len(chunks)} chunks\n")
    
    for chunk in chunks:
        print(f"Chunk {chunk['chunk_id']} (Sentences {chunk['start_sentence']}-{chunk['end_sentence']}):")
        print(f"Sentence count: {chunk['sentence_count']}")
        print(f"Text: {chunk['text'][:100]}...")
        print("-" * 50)
    
    # Test adaptive chunking
    print("\n=== ADAPTIVE CHUNKING RESULTS ===")
    advanced_chunker = AdvancedSemanticChunker()
    adaptive_chunks = advanced_chunker.adaptive_threshold_chunking(sample_text)
    
    print(f"Adaptive chunking produced {len(adaptive_chunks)} chunks\n")
    
    for chunk in adaptive_chunks:
        print(f"Chunk {chunk['chunk_id']}:")
        print(f"Adaptive threshold: {chunk['adaptive_threshold_used']:.3f}")
        print(f"Text: {chunk['text'][:100]}...")
        print("-" * 50)

if __name__ == "__main__":
    example_usage()
