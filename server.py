from flask import Flask, request, jsonify
from flask_cors import CORS
from clean_vtt import clean_vtt_text

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "VTT Cleaner Running"

@app.route("/clean", methods=["POST"])
def clean():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    content = file.read().decode("utf-8", errors="replace")

    cleaned = clean_vtt_text(content)

    return cleaned, 200, {
        "Content-Type": "text/plain; charset=utf-8",
        "Content-Disposition": "attachment; filename=cleaned.vtt"
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
