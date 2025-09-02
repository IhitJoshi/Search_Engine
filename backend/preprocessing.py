import pandas as pd
import os

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
