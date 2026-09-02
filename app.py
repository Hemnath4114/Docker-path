from flask import Flask, request, send_file
import subprocess
import tempfile
import os

app = Flask(__name__)

MODEL = "en_US-lessac-medium.onnx"


@app.route("/health")
def health():
    return {"status": "ok", "version": "2.0"}


@app.route("/tts", methods=["POST"])
def tts():
    data = request.get_json()

    if not data or "text" not in data:
        return {"error": "text is required"}, 400

    text = data["text"]

    if not text.strip():
        return {"error": "text cannot be empty"}, 400

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
        output_file = temp.name

    try:
        subprocess.run(
            [
                "python",
                "-m",
                "piper",
                "-m",
                MODEL,
                "-f",
                output_file,
            ],
            input=text,
            text=True,
            check=True,
        )

        return send_file(
            output_file,
            mimetype="audio/wav",
            as_attachment=True,
            download_name="speech.wav",
        )

    finally:
        if os.path.exists(output_file):
            os.remove(output_file)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)