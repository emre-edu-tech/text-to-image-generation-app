import base64
import hashlib
import hmac
from functools import wraps
from pathlib import Path

import requests
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, current_app, send_file,
)
from app.main import main_bp

CF_MODEL = "@cf/black-forest-labs/flux-1-schnell"

# Absolute path — deliberately not a relative string. Flask's send_file()
# resolves *relative* paths against current_app.root_path (the app/
# package directory, since Flask(__name__) is created in app/__init__.py),
# not against the process's working directory. A relative "app/static/..."
# string would resolve to app/app/static/... and 404. Building it from
# __file__ sidesteps both that and any cwd assumptions.
CACHE_DIR = Path(__file__).resolve().parent.parent / "static" / "generated_images"


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("main.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username_ok = hmac.compare_digest(
            request.form.get("username", ""), current_app.config["APP_USERNAME"]
        )
        password_ok = hmac.compare_digest(
            request.form.get("password", ""), current_app.config["APP_PASSWORD"]
        )
        if username_ok and password_ok:
            session["authenticated"] = True
            session.permanent = True
            return redirect(request.args.get("next") or url_for("main.index"))
        error = "Incorrect username or password"
    return render_template("login.html", error=error)


@main_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))


@main_bp.route("/")
@login_required
def index():
    return render_template("index.html")


def _cache_path(prompt: str) -> Path:
    digest = hashlib.sha256(f"{CF_MODEL}|{prompt}".encode()).hexdigest()
    return CACHE_DIR / f"{digest}.png"


@main_bp.route("/api/generate-image", methods=["POST"])
@login_required
def generate_image():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()[:2048]
    if not prompt:
        return {"error": "A prompt is required"}, 400

    cache_file = _cache_path(prompt)
    if cache_file.exists():
        return send_file(cache_file, mimetype="image/png")

    account_id = current_app.config["CF_ACCOUNT_ID"]
    token = current_app.config["CF_API_TOKEN"]
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{CF_MODEL}"

    try:
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json={"prompt": prompt},
            timeout=30,
        )
    except requests.RequestException:
        return {"error": "Could not reach the image generation service"}, 502

    if resp.status_code != 200:
        # Cloudflare typically returns 429/403 once the daily free allocation is spent
        status = 429 if resp.status_code in (429, 403) else 502
        return {"error": "Image generation failed"}, status

    if "application/json" in resp.headers.get("Content-Type", ""):
        image_b64 = resp.json().get("result", {}).get("image")
        if not image_b64:
            return {"error": "Unexpected response from image model"}, 502
        image_bytes = base64.b64decode(image_b64)
    else:
        image_bytes = resp.content  # some models return raw binary directly

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(image_bytes)
    return send_file(cache_file, mimetype="image/png")
