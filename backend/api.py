from flask import Flask

app = Flask(__name__)

@app.route("/")
def health():
    return {"status": "ok", "message": "boot test"}
