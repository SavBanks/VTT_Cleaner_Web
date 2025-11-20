from flask import Flask, request, send_file, render_template
from clean_vtt import clean_vtt_file
import os

app = Flask(__name__)

# Route for the upload page
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# Route to handle file uploads and cleaning
@app.route("/upload", methods=["POST"])
def upload_file():
    uploaded_file = request.files.get("file")
    if not uploaded_file or uploaded_file.filename == "":
        return "No file uploaded", 400

    input_filename = uploaded_file.filename
    input_path = os.path.join("/tmp", input_filename)
    uploaded_file.save(input_path)

    # Create output filename
    output_filename = "cleaned_" + input_filename
    output_path = os.path.join("/tmp", output_filename)

    # Run your cleaning script
    clean_vtt_file(input_path, output_path)

    # Send the cleaned file back to the user
    return send_file(output_path, as_attachment=True)

# Ensure Flask binds to Render's assigned port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
