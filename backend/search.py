import math
import re
import spacy
import pandas as pd
from preprocessing import tokenize, remove_stopwords, lemmatize_tokens
from index import build_inverted_index
from app import load_dataset, tokenize_all_columns

# ---------------- Load spaCy ---------------- #
nlp = spacy.load("en_core_web_sm")

# ---------------- Preprocess Query ---------------- #
def preprocess_query(query):
    tokens = tokenize(query)
    tokens = remove_stopwords(tokens)
    tokens = lemmatize_tokens(tokens)
    return tokens

# ---------------- BM25 IDF ---------------- #
def compute_idf(inverted_index, N):
    """
    Compute IDF for all tokens.
    Returns: dict {token: idf value}
    """
    idf = {}
    for term, docs in inverted_index.items():
        df = len(set(docs))  # document frequency
        idf[term] = math.log((N - df + 0.5) / (df + 0.5) + 1)
    return idf

# ---------------- BM25 Search ---------------- #
def bm25_search(query_tokens, df, inverted_index, k=1.5, b=0.75, top_n=5):
    N = len(df)  # total documents
    idf = compute_idf(inverted_index, N)

    # Precompute doc lengths
    doc_lengths = [sum(len(col_tokens) for col_tokens in row) for row in df["tokens"]]
    avgdl = sum(doc_lengths) / N

    scores = {}

    for idx, token_lists in enumerate(df["tokens"]):
        doc_tokens = [t for sublist in token_lists for t in sublist]
        doc_len = len(doc_tokens)

        score = 0.0
        for term in query_tokens:
            tf = doc_tokens.count(term)
            if tf == 0 or term not in idf:
                continue

            numerator = tf * (k + 1)
            denominator = tf + k * (1 - b + b * (doc_len / avgdl))
            score += idf[term] * (numerator / denominator)

        if score > 0:
            scores[idx] = score

    # Sort by score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return ranked

# ---------------- Main ---------------- #
if __name__ == "__main__":
    print("🔎 Starting Search Engine...")

    df = load_dataset()
    df = tokenize_all_columns(df)
    inverted_index = build_inverted_index(df)

    while True:
        query = input("\nEnter your query (or 'exit' to quit): ")
        if query.lower() == "exit":
            break

        query_tokens = preprocess_query(query)
        print("Processed Query Tokens:", query_tokens)

        results = bm25_search(query_tokens, df, inverted_index, top_n=5)

        if not results:
            print("No results found ❌")
        else:
            print("\nTop Results:")
            for idx, score in results:
                print(f"Doc {idx} | Score: {score:.4f}")
                print(df.iloc[idx], "\n")
