from preprocessing import load_dataset

if __name__ == "__main__":
    print("Starting Search Engine pipeline...")
    
    df = load_dataset()
    
    print("\nFirst 5 rows of dataset:")
    print(df.head())
