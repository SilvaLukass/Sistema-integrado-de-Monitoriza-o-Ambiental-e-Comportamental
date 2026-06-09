"""Small Flask service for on-demand PlayStation camera captures.

Run this on the Raspberry Pi. The backend calls POST /capture only when a
caregiver explicitly requests a frame, keeping the image transient.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from flask import Flask, send_file

app = Flask(__name__)
PHOTO_PATH = Path("/tmp/foto_atual.jpg")


@app.route("/capture", methods=["POST"])
def capture():
    subprocess.run(
        ["fswebcam", "-r", "640x480", "--no-banner", str(PHOTO_PATH)],
        check=True,
    )
    return send_file(PHOTO_PATH, mimetype="image/jpeg")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
