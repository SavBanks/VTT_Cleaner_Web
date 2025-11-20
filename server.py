from flask import Flask, request, send_file, render_template
from flask_cors import CORS
from clean_vtt import clean_vtt_text
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/clean", methods=["POST"])
def clean():
    if "file" not in request.files:
        return {"status": "error", "message": "No file part"}, 400
    file = request.files["file"]
    if file.filename == "":
        return {"status": "error", "message": "No selected file"}, 400

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_filename = "cleaned_" + file.filename
    output_path = os.path.join(UPLOAD_FOLDER, output_filename)
    file.save(input_path)

    # Run the VTT cleaning
    clean_vtt_file(input_path, output_path)

    return send_file(output_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
