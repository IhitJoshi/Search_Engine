"""
Enhanced text preprocessing utilities for stock data
"""

import pandas as pd
import os
import re
import spacy
import logging
from typing import List, Union

# Setup logging
logger = logging.getLogger(__name__)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.error("spaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm")
    raise

# Enhanced stopwords list
STOPWORDS = {
    "the", "is", "and", "a", "an", "in", "on", "at", "of", "to", "for", 
    "by", "with", "that", "this", "it", "as", "are", "was", "were", 
    "be", "been", "from", "or", "not", "but", "if", "then", "so", 
    "there", "here", "what", "which", "when", "where", "who", "whom",
    "you", "your", "we", "our", "they", "their", "this", "that",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "can"
}

def load_dataset(file_path: str = None) -> pd.DataFrame:
    """
    Load dataset with enhanced error handling and validation
    
    Args:
        file_path: Path to the dataset file
    
    Returns:
        pandas DataFrame
    """
    if file_path is None:
        # Try multiple possible locations
        base_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(base_dir, "data", "dataset.csv"),
            os.path.join(base_dir, "..", "data", "dataset.csv"),
            os.path.join(base_dir, "dataset.csv"),
            os.path.join(base_dir, "sample_dataset.csv"),
            "data/dataset.csv",
            "../data/dataset.csv",
            "dataset.csv",
            "sample_dataset.csv"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                logger.info(f"Found dataset at: {file_path}")
                break
        else:
            raise FileNotFoundError(f"Could not find dataset file. Tried: {possible_paths}")
    
    logger.info(f"Loading dataset from: {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    try:
        # Try different delimiters and encodings
        for delimiter in [',', ';', '\t']:
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(file_path, delimiter=delimiter, encoding=encoding)
                    if not df.empty:
                        logger.info(f"Successfully loaded dataset with delimiter '{delimiter}' and encoding '{encoding}'")
                        return df
                except (pd.errors.ParserError, UnicodeDecodeError):
                    continue
        
        raise ValueError("Could not parse dataset with common delimiters and encodings")
        
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise

def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing
    """
    if not isinstance(text, str):
        return ""
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def tokenize(text: Union[str, float]) -> List[str]:
    """
    Enhanced tokenization with better text cleaning
    
    Args:
        text: Input text to tokenize
    
    Returns:
        List of cleaned tokens
    """
    if not isinstance(text, str) or pd.isna(text):
        return []
    
    text = clean_text(text)
    text = text.lower()
    
    # Remove punctuation but keep important symbols like $, %
    text = re.sub(r'[^\w\s$%]', ' ', text)
    
    # Extract tokens
    tokens = re.findall(r'\b[a-z0-9$%]+\b', text)
    
    # Filter tokens
    tokens = [token for token in tokens if len(token) >= 2 and token not in STOPWORDS]
    
    return tokens

def remove_stopwords(tokens: List[str]) -> List[str]:
    """
    Remove stopwords from token list
    """
    return [token for token in tokens if token not in STOPWORDS]

def lemmatize_tokens(tokens: List[str]) -> List[str]:
    """
    Lemmatize tokens using spaCy with error handling
    """
    if not tokens:
        return []
    
    try:
        doc = nlp(" ".join(tokens))
        lemmas = [token.lemma_.lower() for token in doc if not token.is_punct and not token.is_space]
        return lemmas
    except Exception as e:
        logger.error(f"Error in lemmatization: {e}")
        return tokens  # Return original tokens if lemmatization fails

def preprocess_text(text: Union[str, float]) -> List[str]:
    """
    Complete text preprocessing pipeline
    """
    tokens = tokenize(text)
    tokens = remove_stopwords(tokens)
    tokens = lemmatize_tokens(tokens)
    return tokens

def tokenize_all_columns(df: pd.DataFrame, text_columns: List[str] = None) -> pd.DataFrame:
    """
    Tokenize specified text columns in the DataFrame
    
    Args:
        df: Input DataFrame
        text_columns: List of column names to tokenize. If None, tokenize all columns.
    
    Returns:
        DataFrame with added 'tokens' column
    """
    if text_columns is None:
        text_columns = [col for col in df.columns if df[col].dtype == 'object']
    
    logger.info(f"Tokenizing columns: {text_columns}")
    
    tokenized_rows = []
    
    for _, row in df.iterrows():
        row_tokens = []
        for col in text_columns:
            if col in df.columns:
                tokens = preprocess_text(row[col])
                row_tokens.extend(tokens)  # Flatten across columns for search
        
        tokenized_rows.append(row_tokens)
    
    df = df.copy()
    df["tokens"] = tokenized_rows
    logger.info("Tokenization completed successfully")
    
    return df