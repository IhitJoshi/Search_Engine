import pandas as pd
import os
import re
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
def tokenize(text):
    """
    Splits text into lowercase tokens (words).
    Removes punctuation.
    """
    if not isinstance(text, str):
        return []
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    tokens = text.split()
    return tokens

def tokenize_all_columns(df):
    """
    Tokenizes all text columns in the DataFrame.
    Returns a new column 'tokens' which combines tokens from all columns.
    """
    tokenized_rows = []

    for _, row in df.iterrows():
        row_tokens = []
        for col in df.columns:
            tokens = tokenize(row[col])
            row_tokens.extend(tokens)
        tokenized_rows.append(row_tokens)

    df["tokens"] = tokenized_rows
    return df