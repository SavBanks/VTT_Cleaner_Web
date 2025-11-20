from flask import Flask, request, send_file, render_template
from clean_vtt import clean_vtt_file
import os
import uuid

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/clean", methods=["POST"])
def clean():
    uploaded_file = request.files["file"]

    # Generate unique filenames
    input_path = f"input_{uuid.uuid4().hex}.vtt"
    output_path = f"cleaned_{uuid.uuid4().hex}.vtt"

    # Save uploaded file
    uploaded_file.save(input_path)

    # Run cleaning function
    clean_vtt_file(input_path, output_path)

    # Return cleaned file
    response = send_file(output_path, as_attachment=True)

    # Delete temporary files
    os.remove(input_path)
    os.remove(output_path)

    return response

if __name__ == "__main__":
    app.run(debug=True)
