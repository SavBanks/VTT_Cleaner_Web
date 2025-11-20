from flask import Flask, request, send_file, render_template, make_response
from clean_vtt import clean_vtt_text
import tempfile

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/clean", methods=["POST"])
def clean():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]
    original_text = file.read().decode("utf-8")

    cleaned = clean_vtt_text(original_text)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".vtt")
    with open(tmp.name, "w", encoding="utf-8") as f:
        f.write(cleaned)

    response = make_response(send_file(
        tmp.name,
        as_attachment=True,
        download_name="cleaned.vtt",
        mimetype="text/vtt"
    ))

    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
