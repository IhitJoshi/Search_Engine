from preprocessing import load_dataset, tokenize_all_columns
from index import build_inverted_index
if __name__ == "__main__":
    print("Starting Search Engine pipeline...")
    
    df = load_dataset()
    
    print("\nFirst 5 rows of dataset:")

    df = tokenize_all_columns(df)

    print("\nFirst 5 rows with tokens:")
    print(df[["tokens"]].head())
    index = build_inverted_index(df)
    print("\nInverted Index built!")
    print("\nTotal tokens in index:", len(index))
    # Show sample of inverted index
    print("\nSample tokens from index:")
    for word in list(index.keys())[:10]:   # just first 10 tokens
        print(word, ":", index[word])