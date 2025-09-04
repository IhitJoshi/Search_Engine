from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from search import preprocess_query, bm25_search
from preprocessing import load_dataset, tokenize_all_columns
from index import build_inverted_index

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# Load and prepare data once at startup
print("Loading dataset and building index...")
df = load_dataset()
df = tokenize_all_columns(df)
inverted_index = build_inverted_index(df)
print("Dataset loaded and index built!")

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    # Preprocess query
    query_tokens = preprocess_query(query)
    
    # Perform search
    results = bm25_search(query_tokens, df, inverted_index, top_n=10)
    
    # Format results
    formatted_results = []
    for idx, score in results:
        # Create a preview of the document content
        preview = ""
        for col in df.columns:
            if col != 'tokens' and pd.notna(df.iloc[idx][col]):
                preview += str(df.iloc[idx][col]) + " "
                if len(preview) > 150:  # Limit preview length
                    preview = preview[:150] + "..."
                    break
        
        formatted_results.append({
            'doc_id': int(idx),
            'score': float(score),
            'preview': preview.strip()
        })
    
    return jsonify({'results': formatted_results})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'documents': len(df)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)