# AI Image Generator — Project Overview

## Purpose
A small, standalone Flask web app with its own UI that generates images on
demand from a text prompt, using Cloudflare Workers AI (free tier) as the
image-generation backend — no paid image-generation subscription needed.

## Scope (deliberately minimal)
- One page: type a prompt, click Generate, see the image, download it.
- No accounts, no database, no gallery or history.
- A single shared username/password pair gates the whole app (env-var
  secrets, no accounts/DB). This matters because Cloudflare's free daily allocation
  (250 image-generation "steps", resetting at 00:00 UTC) is shared across
  your *entire* Cloudflare account — an unprotected public URL could burn
  through it and starve any other app using the same account.

## Tech stack (matches the other apps in this project)
- Backend: Python Flask, app factory + Blueprint pattern
- Frontend: Tailwind CSS v3 (npm build), vanilla JS for the AJAX call
- No database — nothing needs to persist
- Deployment: Plesk-managed VPS, Nginx + Phusion Passenger
- Secrets: `.env` file + `python-dotenv` (gitignored; `.env.example` committed)
- Runs inside a Python virtual environment, as usual

## Image generation
- Provider: Cloudflare Workers AI, model `@cf/black-forest-labs/flux-1-schnell`
- Free tier: roughly 30-60 images/day (4-8 steps each, out of a 250
  steps/day account-wide allocation)
- Called via a plain REST POST from Flask — no Workers/JS code needed
- Identical prompts are served from an on-disk cache instead of hitting
  the API again, to stretch the daily quota

## Deployment constraint
The production server does not run an npm build step, so the compiled
Tailwind output (`app/static/dist/output.css`) must be committed to
version control — it is **not** gitignored, even though it's a build
artifact. Whenever `input.css` or the Tailwind config changes, re-run
`npm run build:css` and commit the updated `output.css` before deploying.

## Environment variables (`.env`)
| Variable | Purpose |
|---|---|
| `CF_ACCOUNT_ID` | Your Cloudflare account ID |
| `CF_API_TOKEN` | Cloudflare API token (Workers AI: Read) |
| `APP_USERNAME` | The shared username for the login gate |
| `APP_PASSWORD` | The shared password for the login gate |
| `SECRET_KEY` | Flask session-signing key — generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `FLASK_ENV` | `development` locally, unset (or `production`) on the server |

## File structure
```
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── main/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   └── index.html
│   └── static/
│       ├── src/input.css
│       ├── dist/output.css      (compiled, committed to git)
│       ├── js/generate.js
│       └── generated_images/    (runtime cache, gitignored)
├── .env.example
├── .gitignore
├── requirements.txt
├── package.json
├── tailwind.config.js
├── app.py                       (local dev entry point)
└── wsgi.py                      (Passenger entry point)
```

## Build order (step files)
1. `01-project-scaffolding.md` — app factory, folder layout, Tailwind
   build, env config, entry points
2. `02-image-generation-backend.md` — password gate + the
   `/api/generate-image` route calling Cloudflare
3. `03-frontend-and-deployment.md` — the single-page UI, vanilla JS, and
   the deployment checklist

Each step file is sized for one Opencode session — feed them in order,
and don't regenerate `wsgi.py` in a later step once Step 01 has created it.
