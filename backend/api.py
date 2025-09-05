from flask import Flask, request, jsonify, session
from flask_cors import CORS
import pandas as pd
import sqlite3
import hashlib
from search import preprocess_query, bm25_search
from preprocessing import load_dataset, tokenize_all_columns
from index import build_inverted_index

app = Flask(__name__)
CORS(app, supports_credentials=True)  # allow cookies with frontend
app.secret_key = "supersecretkey"  # Enable CORS for frontend-backend communication
def get_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize DB
init_db()

# ----------------- AUTH ROUTES -----------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, hash_password(password)))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()

    return jsonify({"message": "Signup successful!"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?",
                (username, hash_password(password)))
    user = cur.fetchone()
    conn.close()

    if user:
        session["username"] = username
        return jsonify({"message": "Login successful!"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return jsonify({"message": "Logged out!"}), 200

@app.route("/check", methods=["GET"])
def check():
    if "username" in session:
        return jsonify({"logged_in": True, "username": session["username"]})
    return jsonify({"logged_in": False})

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