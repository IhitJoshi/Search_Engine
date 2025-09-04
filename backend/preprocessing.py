import pandas as pd
import os
import re
import spacy

# ---------------- Load spaCy model ---------------- #
# Make sure you have installed it first:
# pip install spacy
# python -m spacy download en_core_web_sm
nlp = spacy.load("en_core_web_sm")

# ---------------- Load Dataset ---------------- #
def load_dataset():
    """
    Loads dataset.csv from the data folder.
    Returns: pandas DataFrame
    """
    # Path to the dataset file
    base_dir = os.path.dirname(os.path.abspath(__file__))  
    data_path = os.path.join(base_dir, "..", "data", "dataset.csv")

    # Debug info
    print("Loading dataset from:", data_path)
    print("File size:", os.path.getsize(data_path), "bytes")

    # Try reading with common delimiters
    try:
        df = pd.read_csv(data_path)
    except pd.errors.ParserError:
        print("Default ',' delimiter failed. Trying ';' instead...")
        df = pd.read_csv(data_path, delimiter=";")
    except pd.errors.EmptyDataError:
        raise ValueError("⚠️ dataset.csv is empty!")

    print("✅ Dataset Loaded! Shape:", df.shape)
    return df

# ---------------- Stopwords List ---------------- #
STOPWORDS = {
    "the", "is", "and", "a", "an", "in", "on", "at", "of", "to", "for", 
    "by", "with", "that", "this", "it", "as", "are", "was", "were", 
    "be", "been", "from", "or", "not", "but", "if", "then", "so", 
    "there", "here", "what", "which", "when", "where", "who", "whom"
}

# ---------------- Tokenize Function ---------------- #
def tokenize(text):
    """
    Splits text into lowercase tokens (words) and removes punctuation.
    """
    if not isinstance(text, str):
        return []
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)  # remove punctuation
    tokens = text.split()
    return tokens

# ---------------- Remove Stopwords ---------------- #
def remove_stopwords(tokens):
    """
    Removes common stopwords from a list of tokens.
    """
    return [word for word in tokens if word not in STOPWORDS]

# ---------------- Lemmatize Tokens ---------------- #
def lemmatize_tokens(tokens):
    """
    Converts tokens to their base form (lemma) using spaCy.
    """
    doc = nlp(" ".join(tokens))
    return [token.lemma_ for token in doc]

# ---------------- Tokenize All Columns ---------------- #
def tokenize_all_columns(df):
    """
    Tokenizes all text columns in the DataFrame.
    Returns a new column 'tokens' where each row contains
    a list of sublists (one sublist per column).
    """
    tokenized_rows = []

    for _, row in df.iterrows():
        row_tokens = []
        for col in df.columns:
            tokens = tokenize(row[col])
            tokens = remove_stopwords(tokens)  # remove stopwords here
            row_tokens.append(tokens)
        tokenized_rows.append(row_tokens)

    df["tokens"] = tokenized_rows
    return df
