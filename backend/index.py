"""
Stock Indexer - Builds BM25 search index from stock database
"""

import sqlite3
import pickle
import re
from collections import defaultdict
from typing import List, Dict, Tuple
import math

DATABASE_NAME = "stocks.db"
INDEX_FILE = "stock_index.pkl"


def load_stocks_from_db() -> Tuple[List[Dict], List[int]]:
    """
    Load all stocks from SQLite database
    
    Returns:
        Tuple of (list of stock records, list of stock IDs)
    """
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, symbol, company_name, sector, price, summary
        FROM stocks
        ORDER BY id
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    stocks = [dict(row) for row in rows]
    stock_ids = [row['id'] for row in rows]
    
    print(f"✓ Loaded {len(stocks)} stocks from database")
    return stocks, stock_ids


def tokenize_text(text: str) -> List[str]:
    """
    Tokenize and clean text for indexing
    
    Args:
        text: Input text string
    
    Returns:
        List of cleaned, lowercase tokens
    """
    if not text:
        return []
    
    # Convert to lowercase and extract alphanumeric tokens
    text = str(text).lower()
    tokens = re.findall(r'\b[a-z0-9]+\b', text)
    
    # Remove very short tokens (length < 2)
    tokens = [t for t in tokens if len(t) >= 2]
    
    return tokens


def build_inverted_index(stocks: List[Dict]) -> Dict[str, List[int]]:
    """
    Builds an inverted index from stock data.
    Indexes: company_name, sector, and summary fields
    
    Args:
        stocks: List of stock dictionaries from database
    
    Returns:
        dict {token: [stock indices]} - inverted index mapping tokens to stock positions
    """
    inverted_index = defaultdict(list)
    
    # Fields to index for search
    searchable_fields = ['company_name', 'sector', 'summary']
    
    for idx, stock in enumerate(stocks):
        seen_tokens = set()  # Track tokens already indexed for this document
        
        # Tokenize each searchable field
        for field in searchable_fields:
            text = stock.get(field, '')
            tokens = tokenize_text(text)
            
            # Add each unique token to inverted index
            for token in tokens:
                if token not in seen_tokens:
                    inverted_index[token].append(idx)
                    seen_tokens.add(token)
    
    # Convert defaultdict to regular dict for serialization
    inverted_index = dict(inverted_index)
    
    print(f"✓ Built inverted index with {len(inverted_index)} unique tokens")
    return inverted_index


def compute_document_lengths(stocks: List[Dict]) -> List[int]:
    """
    Compute the length (token count) of each document
    
    Args:
        stocks: List of stock dictionaries
    
    Returns:
        List of document lengths (token counts)
    """
    doc_lengths = []
    searchable_fields = ['company_name', 'sector', 'summary']
    
    for stock in stocks:
        total_tokens = 0
        for field in searchable_fields:
            text = stock.get(field, '')
            tokens = tokenize_text(text)
            total_tokens += len(tokens)
        doc_lengths.append(total_tokens)
    
    return doc_lengths


def compute_term_frequencies(stocks: List[Dict]) -> List[Dict[str, int]]:
    """
    Compute term frequency for each document
    
    Args:
        stocks: List of stock dictionaries
    
    Returns:
        List of {token: count} dictionaries for each document
    """
    tf_list = []
    searchable_fields = ['company_name', 'sector', 'summary']
    
    for stock in stocks:
        tf = defaultdict(int)
        for field in searchable_fields:
            text = stock.get(field, '')
            tokens = tokenize_text(text)
            for token in tokens:
                tf[token] += 1
        tf_list.append(dict(tf))
    
    return tf_list


def build_bm25_index(stocks: List[Dict]) -> Dict:
    """
    Build complete BM25 index structure
    
    Args:
        stocks: List of stock dictionaries
    
    Returns:
        Dictionary containing all index components
    """
    print("\n" + "="*60)
    print("🔨 Building BM25 Search Index...")
    print("="*60)
    
    # Build inverted index
    inverted_index = build_inverted_index(stocks)
    
    # Compute document statistics
    doc_lengths = compute_document_lengths(stocks)
    term_frequencies = compute_term_frequencies(stocks)
    
    # Calculate average document length
    avg_doc_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0
    
    # Total number of documents
    num_docs = len(stocks)
    
    index_data = {
        'inverted_index': inverted_index,
        'doc_lengths': doc_lengths,
        'term_frequencies': term_frequencies,
        'avg_doc_length': avg_doc_length,
        'num_docs': num_docs,
        'stocks': stocks  # Store stock data for quick retrieval
    }
    
    print(f"✓ Indexed {num_docs} documents")
    print(f"✓ Average document length: {avg_doc_length:.1f} tokens")
    
    return index_data


def save_index(index_data: Dict, filename: str = INDEX_FILE):
    """
    Save index to disk using pickle
    
    Args:
        index_data: Index dictionary to save
        filename: Output filename
    """
    with open(filename, 'wb') as f:
        pickle.dump(index_data, f)
    print(f"✓ Index saved to '{filename}'")


def load_index(filename: str = INDEX_FILE) -> Dict:
    """
    Load index from disk
    
    Args:
        filename: Input filename
    
    Returns:
        Index dictionary
    """
    with open(filename, 'rb') as f:
        index_data = pickle.load(f)
    print(f"✓ Index loaded from '{filename}'")
    return index_data


def main():
    """Main indexing workflow"""
    print("\n" + "="*60)
    print("📚 Stock Search Indexer")
    print("="*60 + "\n")
    
    # Load stocks from database
    stocks, stock_ids = load_stocks_from_db()
    
    if not stocks:
        print("✗ No stocks found in database. Run stock_fetcher.py first!")
        return
    
    # Build BM25 index
    index_data = build_bm25_index(stocks)
    
    # Save to disk
    save_index(index_data)
    
    print("\n" + "="*60)
    print("✅ Indexing Complete!")
    print("="*60)
    print(f"📊 Total stocks indexed: {len(stocks)}")
    print(f"🔤 Unique tokens: {len(index_data['inverted_index'])}")
    print(f"💾 Index file: {INDEX_FILE}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()