# Step 03 — Deployment

## Goal
Ship the already-working local app (from Step 02) to the Plesk VPS.
There's nothing new to build here — just get it running in production
and confirm it behaves the same way it did locally.

## Deployment checklist
1. `npm run build:css` locally (if you haven't already since the last
   template/CSS change); commit `app/static/dist/output.css`.
2. Push to the repo; pull it on the VPS.
3. On the server: create the venv, `pip install -r requirements.txt`.
4. Create the real `.env` on the server (never commit it) with all five
   variables filled in — `CF_ACCOUNT_ID`, `CF_API_TOKEN`, `APP_USERNAME`,
   `APP_PASSWORD`, `SECRET_KEY`.
5. In Plesk: point the Passenger app at `wsgi.py`, set the Python version,
   restart the app.
6. Visit the live site and repeat the same checks from Step 02's
   acceptance check — login redirect, wrong-credential rejection,
   generate → image → download, and the cache hit on a repeated prompt.

## Acceptance check
- Everything that passed locally in Step 02 also passes on the live VPS
- `.env` is present on the server but not committed to git (`git status`
  shows nothing for it)
