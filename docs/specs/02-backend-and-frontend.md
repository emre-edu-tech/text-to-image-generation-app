# Step 02 — Login, Image Generation Backend, and Frontend UI

## Goal
Build everything needed for a fully working app you can test locally in
a browser before ever touching the VPS: the login gate, the
`/api/generate-image` route calling Cloudflare Workers AI, and the actual
page templates + JS that use them. Nothing here is deferred to Step 03 —
that step is deployment only, with nothing new to test.

## 1. `app/templates/base.html`
Minimal shell pulling in the compiled Tailwind file:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}AI Image Generator{% endblock %}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='dist/output.css') }}">
</head>
<body class="bg-gray-50 min-h-screen">
  {% block content %}{% endblock %}
</body>
</html>
```

## 2. Login gate (`app/main/routes.py`)
```python
import hmac
from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, current_app, send_file,
)
from app.main import main_bp


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
```

## 3. Image generation route (same file, append below)
```python
import base64
import hashlib
from pathlib import Path
import requests

CF_MODEL = "@cf/black-forest-labs/flux-1-schnell"

# Absolute path — deliberately not a relative string. Flask's send_file()
# resolves *relative* paths against current_app.root_path (the app/
# package directory, since Flask(__name__) is created in app/__init__.py),
# not against the process's working directory. A relative "app/static/..."
# string would resolve to app/app/static/... and 404. Building it from
# __file__ sidesteps both that and any cwd assumptions.
CACHE_DIR = Path(__file__).resolve().parent.parent / "static" / "generated_images"


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
```

## 4. `app/templates/login.html`
```html
{% extends "base.html" %}
{% block title %}Log in — AI Image Generator{% endblock %}
{% block content %}
<div class="min-h-screen flex items-center justify-center px-4">
  <div class="w-full max-w-sm bg-white rounded-lg shadow p-6">
    <h1 class="text-xl font-semibold mb-4">AI Image Generator</h1>
    {% if error %}
      <p class="text-red-600 text-sm mb-3">{{ error }}</p>
    {% endif %}
    <form method="post" class="space-y-4">
      <div>
        <label for="username" class="block text-sm font-medium text-gray-700">Username</label>
        <input type="text" id="username" name="username" required
               class="mt-1 w-full rounded border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
      </div>
      <div>
        <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
        <input type="password" id="password" name="password" required
               class="mt-1 w-full rounded border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
      </div>
      <button type="submit"
              class="w-full bg-indigo-600 text-white rounded py-2 font-medium hover:bg-indigo-700">
        Log in
      </button>
    </form>
  </div>
</div>
{% endblock %}
```
(`method="post"` with no `action` submits back to the current URL, `/login`,
matching the route above.)

## 5. `app/templates/index.html`
```html
{% extends "base.html" %}
{% block title %}AI Image Generator{% endblock %}
{% block content %}
<div class="max-w-2xl mx-auto px-4 py-10">
  <div class="flex justify-between items-center mb-6">
    <h1 class="text-xl font-semibold">AI Image Generator</h1>
    <a href="{{ url_for('main.logout') }}" class="text-sm text-gray-500 hover:underline">Logout</a>
  </div>

  <form id="generate-form" class="space-y-3">
    <textarea id="prompt" rows="3" required
      class="w-full rounded border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
      placeholder="Describe the image you want..."></textarea>
    <button type="submit"
      class="bg-indigo-600 text-white rounded px-4 py-2 font-medium hover:bg-indigo-700">
      Generate
    </button>
  </form>

  <div id="loading" class="hidden mt-4 text-gray-500">Generating…</div>
  <div id="error-box" class="hidden mt-4 text-red-600"></div>

  <div class="mt-6">
    <img id="result-img" class="hidden max-w-full rounded shadow">
    <a id="download-link" class="hidden inline-block mt-3 text-indigo-600 hover:underline"
       download="generated-image.png">
      Download image
    </a>
  </div>
</div>
<script src="{{ url_for('static', filename='js/generate.js') }}"></script>
{% endblock %}
```
Every element `id` here matches what `generate.js` (below) looks for —
`generate-form`, `prompt`, `loading`, `error-box`, `result-img`,
`download-link`. If either file is edited later, keep the `id`s in sync.

## 6. `app/static/js/generate.js`
```javascript
const form = document.getElementById("generate-form");
const promptInput = document.getElementById("prompt");
const loading = document.getElementById("loading");
const resultImg = document.getElementById("result-img");
const downloadLink = document.getElementById("download-link");
const errorBox = document.getElementById("error-box");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const prompt = promptInput.value.trim();
  if (!prompt) return;

  errorBox.classList.add("hidden");
  resultImg.classList.add("hidden");
  downloadLink.classList.add("hidden");
  loading.classList.remove("hidden");

  try {
    const res = await fetch("/api/generate-image", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || "Image generation failed");
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    resultImg.src = url;
    resultImg.classList.remove("hidden");
    downloadLink.href = url;
    downloadLink.classList.remove("hidden");
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.remove("hidden");
  } finally {
    loading.classList.add("hidden");
  }
});
```

## Acceptance check — test this locally before starting Step 03
Run `python app.py` (make sure `npm run build:css` has been run at least
once so `output.css` exists), then in a browser:
- Visiting `/` without logging in redirects to `/login`
- Wrong username or password shows an error and stays on `/login`
- Correct username/password redirects to `/`, and the page loads with no
  missing-template errors — prompt box, Generate button, etc. all present
- Typing a prompt and clicking Generate shows the loading state, then
  displays the image and a working Download link
- Submitting the same prompt again is noticeably instant (served from
  the on-disk cache, not a fresh Cloudflare call)
- Visiting `/logout` then `/` redirects back to `/login`
- (Optional, via curl/Postman) `/api/generate-image` without a session
  cookie redirects rather than returning an image

If any of this fails, fix it before starting Step 03 — that step assumes
you already have a fully working app to deploy and adds nothing new to
test locally.
