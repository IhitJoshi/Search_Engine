"""
Enhanced BM25 search implementation with better scoring and performance
"""

import math
import logging
from typing import List, Tuple, Dict, Any
from utils.preprocessing import preprocess_text
import pandas as pd

logger = logging.getLogger(__name__)

class BM25Search:
    """
    BM25 search implementation with configurable parameters
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75, epsilon: float = 0.25):
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.inverted_index = None
        self.doc_lengths = None
        self.avg_doc_length = None
        self.idf_cache = {}
        
    def compute_idf(self, term: str, total_docs: int) -> float:
        """
        Compute IDF for a term with smoothing
        """
        if term in self.idf_cache:
            return self.idf_cache[term]
            
        if term not in self.inverted_index:
            return 0.0
            
        doc_freq = len(set(self.inverted_index[term]))
        
        # BM25 IDF formula with smoothing
        idf = math.log(
            (total_docs - doc_freq + 0.5) / 
            (doc_freq + 0.5) + 1.0
        )
        
        self.idf_cache[term] = idf
        return idf
    
    def compute_scores(self, query_tokens: List[str], df: pd.DataFrame) -> List[Tuple[int, float]]:
        """
        Compute BM25 scores for all documents
        """
        if not self.inverted_index or not self.doc_lengths:
            raise ValueError("Index not initialized. Call build_index first.")
        
        total_docs = len(df)
        scores = {}
        
        for doc_idx, doc_length in enumerate(self.doc_lengths):
            score = 0.0
            doc_tokens = df.iloc[doc_idx]["tokens"]
            
            for term in query_tokens:
                if term not in self.inverted_index or doc_idx not in self.inverted_index[term]:
                    continue
                    
                # Term frequency in this document
                tf = doc_tokens.count(term)
                if tf == 0:
                    continue
                
                # IDF
                idf = self.compute_idf(term, total_docs)
                
                # BM25 scoring
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
                
                score += idf * (numerator / denominator)
            
            if score > 0:
                scores[doc_idx] = score
        
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    def build_index(self, df: pd.DataFrame):
        """
        Build search index from DataFrame
        """
        logger.info("Building search index...")
        
        self.inverted_index = {}
        self.doc_lengths = []
        
        # Build inverted index and compute document lengths
        for doc_idx, tokens in enumerate(df["tokens"]):
            self.doc_lengths.append(len(tokens))
            
            for token in set(tokens):  # Use set to avoid duplicate processing
                if token not in self.inverted_index:
                    self.inverted_index[token] = []
                self.inverted_index[token].append(doc_idx)
        
        # Compute average document length
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0
        self.idf_cache = {}  # Clear cache
        
        logger.info(f"Index built with {len(self.inverted_index)} unique terms")
    
    def search(self, query: str, df: pd.DataFrame, top_n: int = 10) -> List[Tuple[int, float]]:
        """
        Search for documents matching the query
        """
        query_tokens = preprocess_text(query)
        logger.info(f"Searching for: '{query}' -> tokens: {query_tokens}")
        
        if not query_tokens:
            return []
        
        results = self.compute_scores(query_tokens, df)
        return results[:top_n]

# Global search instance
search_engine = BM25Search()

def preprocess_query(query: str) -> List[str]:
    """
    Preprocess search query
    """
    return preprocess_text(query)

def bm25_search(query_tokens: List[str], df: pd.DataFrame, inverted_index: Dict, 
                k: float = 1.5, b: float = 0.75, top_n: int = 5) -> List[Tuple[int, float]]:
    """
    Legacy function for backward compatibility
    """
    search_engine.k1 = k
    search_engine.b = b
    search_engine.inverted_index = inverted_index
    search_engine.doc_lengths = [len(tokens) for tokens in df["tokens"]]
    search_engine.avg_doc_length = sum(search_engine.doc_lengths) / len(search_engine.doc_lengths)
    
    query = " ".join(query_tokens)
    return search_engine.search(query, df, top_n)
def search_stocks(filters):
    import sqlite3
    conn = sqlite3.connect("stocks.db")
    cursor = conn.cursor()

    query = "SELECT * FROM stocks WHERE 1=1"
    params = []

    for key, value in filters.items():
        if isinstance(value, dict):
            for op, val in value.items():
                if op == ">":
                    query += f" AND {key} > ?"
                    params.append(val)
                elif op == "<":
                    query += f" AND {key} < ?"
                    params.append(val)
        else:
            query += f" AND {key} = ?"
            params.append(value)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    # Convert rows to dicts (optional)
    return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]

def main():
    """Test the search functionality"""
    from utils.preprocessing import load_dataset, tokenize_all_columns
    
    logging.basicConfig(level=logging.INFO)
    
    print("🔎 Testing Search Engine...")
    
    try:
        df = load_dataset()
        df = tokenize_all_columns(df)
        
        search_engine.build_index(df)
        
        while True:
            query = input("\nEnter your query (or 'exit' to quit): ")
            if query.lower() == 'exit':
                break
                
            results = search_engine.search(query, df, top_n=5)
            
            if not results:
                print("No results found ❌")
            else:
                print(f"\nTop {len(results)} Results:")
                for idx, (doc_idx, score) in enumerate(results, 1):
                    print(f"{idx}. Doc {doc_idx} | Score: {score:.4f}")
                    # Show preview of the document
                    preview = " ".join(str(df.iloc[doc_idx][col]) for col in df.columns if col != 'tokens')
                    print(f"   Preview: {preview[:100]}...\n")
                    
    except Exception as e:
        logger.error(f"Search test failed: {e}")
        raise

if __name__ == "__main__":
    main()