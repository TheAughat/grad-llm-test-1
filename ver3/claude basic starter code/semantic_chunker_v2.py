# Semantic chunker with character counts

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

    
    def find_sentence_positions(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Find sentences and their exact positions in the original text.
        
        Returns:
            List of tuples: (sentence_text, start_char, end_char)
        """
        # Use NLTK to find sentence boundaries
        sentence_spans = list(nltk.tokenize.sent_tokenize(text, realign_boundaries=True))
        
        # Find the actual character positions of each sentence
        positions = []
        search_start = 0
        
        for sentence in sentence_spans:
            # Find this sentence in the original text
            sentence_start = text.find(sentence, search_start)
            if sentence_start == -1:
                # Fallback: try to find a cleaned version
                cleaned_sentence = re.sub(r'\s+', ' ', sentence.strip())
                # Search for the sentence with flexible whitespace
                pattern = re.escape(cleaned_sentence).replace(r'\ ', r'\s+')
                match = re.search(pattern, text[search_start:])
                if match:
                    sentence_start = search_start + match.start()
                    sentence_end = search_start + match.end() - 1
                else:
                    # Skip this sentence if we can't find it
                    continue
            else:
                sentence_end = sentence_start + len(sentence) - 1
            
            positions.append((sentence, sentence_start, sentence_end))
            search_start = sentence_end + 1
        
        return positions
    
    
    def get_clean_sentences_for_embedding(self, sentence_positions: List[Tuple[str, int, int]]) -> List[str]:
        """Extract and clean sentences for embedding generation."""
        sentences = []
        for sentence, start, end in sentence_positions:
            # Clean sentence for embedding
            clean_sentence = re.sub(r'\s+', ' ', sentence.strip())
            if len(clean_sentence) > 10:  # Filter very short sentences
                sentences.append(clean_sentence)
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
    
    
    def chunk_text(self, text: str, window_size: int = 3, min_chunk_size: int = 2) -> List[dict]:
        """
        Main method to chunk text semantically while preserving exact character positions.
        
        Args:
            text: Input text to chunk
            window_size: Size of sliding window for similarity comparison
            min_chunk_size: Minimum number of sentences per chunk
            
        Returns:
            List of dictionaries containing chunk info with exact character indices
        """
        # Find exact sentence positions in original text
        sentence_positions = self.find_sentence_positions(text)
        
        if len(sentence_positions) < min_chunk_size * 2:
            return [{
                'chunk_id': 0,
                'text': text,
                'sentence_count': len(sentence_positions),
                'start_sentence': 0,
                'end_sentence': len(sentence_positions) - 1,
                'start_char': 0,
                'end_char': len(text) - 1
            }]
        
        # Get clean sentences for embedding
        clean_sentences = self.get_clean_sentences_for_embedding(sentence_positions)
        
        # Generate embeddings
        embeddings = self.get_embeddings(clean_sentences)
        
        # Find boundaries
        boundaries = self.find_chunk_boundaries(embeddings, window_size)
        
        # Create chunks using original text positions
        chunks = []
        
        # Add boundaries
        all_boundaries = [0] + boundaries + [len(sentence_positions)]
        
        for i in range(len(all_boundaries) - 1):
            start_sentence_idx = all_boundaries[i]
            end_sentence_idx = all_boundaries[i + 1] - 1
            
            if start_sentence_idx < len(sentence_positions) and end_sentence_idx < len(sentence_positions):
                # Get character range from first sentence start to last sentence end
                start_char = sentence_positions[start_sentence_idx][1]
                end_char = sentence_positions[end_sentence_idx][2]
                
                # Extract exact text from original
                chunk_text = text[start_char:end_char + 1]
                
                chunks.append({
                    'chunk_id': len(chunks),
                    'text': chunk_text,
                    'sentence_count': end_sentence_idx - start_sentence_idx + 1,
                    'start_sentence': start_sentence_idx,
                    'end_sentence': end_sentence_idx,
                    'start_char': start_char,
                    'end_char': end_char
                })
        
        return chunks
    

# Example usage and testing
def example_usage():
    # Sample report text with various formatting
    sample_text = """Artificial intelligence has revolutionized many industries in recent years. Machine learning algorithms can now process vast amounts of data with unprecedented accuracy. Deep learning models have shown remarkable success in image recognition and natural language processing tasks.

However, the automotive industry faces unique challenges when implementing AI solutions. Self-driving cars require real-time decision making capabilities that must prioritize safety above all else. 

The regulatory environment for autonomous vehicles remains complex and varies significantly between countries.

In healthcare, AI applications have shown tremendous promise for diagnostic imaging. Radiologists are increasingly using AI-assisted tools to detect anomalies in medical scans. Early detection of diseases like cancer has improved significantly with these technological advances.

Despite these advances, ethical concerns about AI deployment continue to grow. Issues of bias in algorithmic decision-making affect hiring, lending, and criminal justice systems."""
    
    # Initialize chunker
    chunker = SemanticChunker(similarity_threshold=0.6)
    
    # Chunk the text
    chunks = chunker.chunk_text(sample_text)
    
    print("=== SEMANTIC CHUNKING RESULTS ===")
    print(f"Original text split into {len(chunks)} chunks\n")
    print(f"Original text length: {len(sample_text)} characters\n")
    
    for chunk in chunks:
        print(f"Chunk {chunk['chunk_id']} (Sentences {chunk['start_sentence']}-{chunk['end_sentence']}):")
        print(f"Character range: {chunk['start_char']}-{chunk['end_char']} (length: {len(chunk['text'])})")
        print(f"Sentence count: {chunk['sentence_count']}")
        print(f"Text preview: {repr(chunk['text'][:100])}...")
        print("-" * 70)
    
    # Verify perfect reconstruction
    print("\n=== RECONSTRUCTION VERIFICATION ===")
    reconstructed = ''.join([chunk['text'] for chunk in chunks])
    
    print(f"Original length: {len(sample_text)}")
    print(f"Reconstructed length: {len(reconstructed)}")
    print(f"Perfect match: {sample_text == reconstructed}")
    
    if sample_text != reconstructed:
        print("\nFirst difference found at:")
        for i, (orig, recon) in enumerate(zip(sample_text, reconstructed)):
            if orig != recon:
                print(f"Position {i}: original='{orig}' vs reconstructed='{recon}'")
                break
    else:
        print("✓ Perfect reconstruction achieved!")
    
    # Verify no gaps or overlaps in character ranges
    print("\n=== CHARACTER RANGE VERIFICATION ===")
    for i, chunk in enumerate(chunks):
        if i == 0:
            if chunk['start_char'] != 0:
                print(f"⚠ Gap at beginning: chunk starts at {chunk['start_char']}")
        else:
            prev_end = chunks[i-1]['end_char']
            curr_start = chunk['start_char']
            if curr_start != prev_end + 1:
                print(f"⚠ Gap/Overlap between chunks {i-1} and {i}: {prev_end} -> {curr_start}")
    
    last_chunk = chunks[-1]
    if last_chunk['end_char'] != len(sample_text) - 1:
        print(f"⚠ Gap at end: last chunk ends at {last_chunk['end_char']}, text length is {len(sample_text)}")
    
    print("Character range verification complete!")


if __name__ == "__main__":
    example_usage()
