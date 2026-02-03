"""
Enhanced text preprocessing utilities for stock data
"""

import pandas as pd
import os
import re
try:
    import spacy
    SPACY_AVAILABLE = True
except Exception:
    spacy = None
    SPACY_AVAILABLE = False
import logging
from typing import List, Union

# Setup logging
logger = logging.getLogger(__name__)

# Load spaCy model if available
nlp = None
if SPACY_AVAILABLE:
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        logger.warning("spaCy is installed but model 'en_core_web_sm' not available. Continuing without spaCy.")
        nlp = None

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
    
    if SPACY_AVAILABLE and nlp is not None:
        try:
            doc = nlp(" ".join(tokens))
            lemmas = [token.lemma_.lower() for token in doc if not token.is_punct and not token.is_space]
            return lemmas
        except Exception as e:
            logger.error(f"Error in lemmatization: {e}")
            return tokens
    # Fallback: no spaCy available, return tokens as-is
    return tokens  # Return original tokens if lemmatization not possible

def preprocess_text(text: Union[str, float]) -> List[str]:
    """
    Complete text preprocessing pipeline
    """
    tokens = tokenize(text)
    tokens = remove_stopwords(tokens)
    tokens = lemmatize_tokens(tokens)
    return tokens


def normalize_sector(term: str) -> str:
    """Normalize various sector/category synonyms to canonical sector names."""
    if not term or not isinstance(term, str):
        return ""
    t = term.lower()
    mapping = {
        "tech": "Technology",
        "technology": "Technology",
        "software": "Technology",
        "semiconductor": "Technology",
        "finance": "Financial Services",
        "financials": "Financial Services",
        "financial": "Financial Services",
        "bank": "Financial Services",
        "banks": "Financial Services",
        "investment": "Financial Services",
        "forex": "Financial Services",
        "health": "Healthcare",
        "healthcare": "Healthcare",
        "pharma": "Healthcare",
        "biotech": "Healthcare",
        "pharmaceutical": "Healthcare",
        "hospital": "Healthcare",
        "energy": "Energy",
        "oil": "Energy",
        "renewable": "Energy",
        "power": "Energy",
        "utilities": "Utilities",
        "utility": "Utilities",
        "gas": "Energy",
        "fuel": "Energy",
        "nuclear": "Energy",
        "retail": "Retail",
        "consumer": "Consumer",
        "fmcg": "Consumer",
        "goods": "Consumer",
        "beverage": "Consumer",
        "food": "Consumer",
        "auto": "Automotive",
        "automotive": "Automotive",
        "car": "Automotive",
        "vehicle": "Automotive",
        "automobile": "Automotive",
        "motor": "Automotive",
        "india": "India",
        "indian": "India",
        "nse": "India",
        "bse": "India",
        "industrial": "Industrial",
        "manufacturing": "Industrial",
        "machinery": "Industrial",
        "engineering": "Industrial",
        "construction": "Industrial",
        "telecom": "Telecom",
        "communication": "Telecom",
        "wireless": "Telecom",
        "mobile": "Telecom",
        "realty": "Realty",
        "real": "Realty",
        "estate": "Realty",
        "property": "Realty",
        "metal": "Metals",
        "metals": "Metals",
        "mining": "Metals",
        "mine": "Metals",
        "steel": "Metals",
        "chemical": "Chemicals",
        "chemicals": "Chemicals",
        "infrastructure": "Infrastructure",
        "infra": "Infrastructure",
        "transport": "Infrastructure",
        "logistics": "Infrastructure",
    }
    for k, v in mapping.items():
        if k in t:
            return v
    # fallback: title-case the input
    return term.strip().title()


def extract_trend_intent(query: str) -> str:
    """Detect trend intent from user query: 'up', 'down', or '' (any)."""
    if not query or not isinstance(query, str):
        return ""
    q = query.lower()
    up_keywords = ["up", "increase", "increasing", "growing", "gain", "rising", "inc", "positive"]
    down_keywords = ["down", "decrease", "decreasing", "fall", "falling", "drop", "loss", "decline", "dec","decr", "downward"]
    for kw in up_keywords:
        if kw in q:
            return "up"
    for kw in down_keywords:
        if kw in q:
            return "down"
    return ""


def parse_query_filters(query: str) -> dict:
    """
    Parse a free-text query into structured filters.

    Returns a dict like:
      {
        'raw': <original query>,
        'sector': <canonical sector or ''>,
        'trend': 'up'|'down'|''
      }
    """
    if not query or not isinstance(query, str):
        return {"raw": "", "sector": "", "trend": ""}

    q = query.strip()

    # Try to extract a sector mention by simple token scan
    # Look for common sector words and their related keywords
    sector_candidates = {
        "technology": ["technology", "tech", "software", "semiconductor", "it", "computing", "digital", "it sector", "hi-tech", "hitech"],
        "financial": ["financial", "finance", "bank", "banks", "financials", "banking", "investment", "forex"],
        "healthcare": ["healthcare", "health", "pharma", "biotech", "medical", "medicine", "pharmaceutical", "hospital"],
        "energy": ["energy", "oil", "renewable", "power", "utilities", "gas", "fuel", "nuclear"],
        "retail": ["retail", "consumer", "ecommerce", "shopping", "e-commerce", "commerce"],
        "automotive": ["automotive", "auto", "car", "vehicle", "automobile", "motor"],
        "india": ["india", "indian", "nse", "bse"],
        "consumer": ["consumer", "fmcg", "goods", "beverage", "food"],
        "industrial": ["industrial", "manufacturing", "machinery", "engineering", "construction"],
        "telecom": ["telecom", "communication", "telecom", "wireless", "mobile"],
        "utilities": ["utilities", "utility", "water", "electricity"],
        "realty": ["realty", "real estate", "property", "estate", "real-estate"],
        "metal": ["metal", "metals", "mining", "mine", "steel"],
        "chemical": ["chemical", "chemicals", "pharma"],
        "infrastructure": ["infrastructure", "infra", "transport", "logistics"],
    }

    found_sector = ""
    q_lower = q.lower()
    
    # Check each sector and its related keywords
    for sector, keywords in sector_candidates.items():
        for keyword in keywords:
            if keyword in q_lower:
                found_sector = normalize_sector(sector)
                break
        if found_sector:
            break

    trend = extract_trend_intent(q)

    return {"raw": q, "sector": found_sector, "trend": trend}

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