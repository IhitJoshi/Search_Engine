from preprocessing import load_dataset, tokenize_all_columns

if __name__ == "__main__":
    print("Starting Search Engine pipeline...")
    
    df = load_dataset()
    
    print("\nFirst 5 rows of dataset:")

    df = tokenize_all_columns(df)

    print("\nFirst 5 rows with tokens:")
    print(df[["tokens"]].head())