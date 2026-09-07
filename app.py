from flask import Flask, request, send_file
import subprocess
import os
import redis


SECRET_PATH = "/run/secrets/api_key"

def load_api_key():
    try:
        with open(SECRET_PATH, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "No secret found"


APP_VERSION = os.getenv("APP_VERSION", "3.1")
app = Flask(__name__)

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True,
)


MODEL = "/app/models/en_US-lessac-medium.onnx"


@app.route("/secret-status")
def secret_status():
    api_key = load_api_key()

    return {
        "secret_loaded": api_key != "No secret found",
        "secret_length": len(api_key) if api_key != "No secret found" else 0
    }


@app.route("/health")
def health():
    return {"status": "ok", "version": APP_VERSION}

@app.route("/stats")
def stats():
    total_requests = redis_client.get("tts_requests")
    return {
        "total_requests": int(total_requests or 0)
    }

@app.route("/tts", methods=["POST"])
def tts():
    data = request.get_json()

    if not data or "text" not in data:
        return {"error": "text is required"}, 400

    text = data["text"]

    if not text.strip():
        return {"error": "text cannot be empty"}, 400

    # Increment the total number of TTS requests
    redis_client.incr("tts_requests")

    output_dir = "/app/output"
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "speech.wav")

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)