# NexTrip

A full-stack travel planning site: Flask + SQLite backend, vanilla HTML/CSS/JS frontend.

## What's included

- **Explorer** — search/filter/sort destinations by category, country, budget; save favorites (backed by real DB queries, not hardcoded arrays)
- **AI Planner** — generates a day-by-day itinerary for any destination based on trip length, budget, and interests, and surfaces a "hidden gem" insider tip alongside popular destinations; itineraries are saved per user
- **Budget Tracker** — log and categorize trip expenses, see totals and a category breakdown, per account
- **Reviews** — browse and post star-rated reviews per destination
- **Accounts** — register/login/logout with hashed passwords and server-side sessions (no plaintext passwords, no localStorage auth)

Everything reads/writes through a real SQLite database (`nehang.db`, created automatically on first run) via a JSON API — nothing is hardcoded in the frontend JS anymore.

**Countries covered:** India, Australia, United Kingdom, France, and Thailand — each with must-visit destinations plus hidden gems (e.g. Sydney + Kangaroo Island, London + the Cotswolds, Paris + Annecy, Bangkok + Pai).

## Run it

```bash
cd nehang-planner
pip install -r requirements.txt
python3 app.py
```

Then open **http://localhost:5000** in your browser. The database and its 25 seed destinations (across India, Australia, United Kingdom, France, and Thailand) are created automatically the first time the app runs.

To reset all data, stop the server and delete `nehang.db`, then restart.

## Project structure

```
nehang-planner/
  app.py              # Flask app: all page routes + JSON API
  seed_data.py         # Initial destinations & countries (loaded into SQLite on first run)
  requirements.txt
  nehang.db            # created automatically — SQLite database
  public/               # the 5 pages (served by Flask)
    index.html
    explorer.html
    planner.html
    budget.html
    reviews.html
  static/
    css/style.css       # shared design system
    js/nav.js           # shared auth/session logic, login+register modal
```

## API overview

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/api/auth/register` | POST | – | Create account |
| `/api/auth/login` | POST | – | Sign in |
| `/api/auth/logout` | POST | – | Sign out |
| `/api/auth/me` | GET | – | Current session user |
| `/api/destinations` | GET | – | Search/filter/sort destinations |
| `/api/destinations/<id>` | GET | – | Single destination |
| `/api/countries` | GET | – | Country list with counts |
| `/api/favorites` | GET/POST | ✔ | List / toggle saved destinations |
| `/api/reviews` | GET/POST | POST ✔ | List / post reviews |
| `/api/planner/generate` | POST | – (saves trip if logged in) | Generate an itinerary |
| `/api/trips` | GET | ✔ | User's saved itineraries |
| `/api/budget` | GET/POST | ✔ | List / add expenses |
| `/api/budget/<id>` | DELETE | ✔ | Delete an expense |

## Notes on images

I wasn't able to pull images from the reference site (nehang-journey-map.base44.app) directly — it's a client-rendered app that only exposes a login screen to automated fetches, so there was no static markup or image URLs to copy. Destination photos here are curated Unsplash CDN images (same approach your original `explorer.html` used), each with a fallback in case one fails to load.

## Production notes

This runs on Flask's built-in dev server locally, which is fine for local use/demos. `gunicorn` is included in `requirements.txt` and a `Procfile` is provided for real deployment. You'll also want:
- `app.secret_key` set via a real environment variable (`NEHANG_SECRET_KEY`) — currently it auto-generates a random one on each restart, which logs out all sessions when the server restarts
- HTTPS, and `SESSION_COOKIE_SECURE=True`

## Publishing to GitHub

1. Create a new repository on [github.com/new](https://github.com/new) — don't initialize it with a README (you already have one).
2. In the `nehang-planner` folder, run:
   ```bash
   git init
   git add -A
   git commit -m "Initial commit: NexTrip"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```
   (If you already ran `git init` — this project comes with a git repo pre-initialized and committed — just add the remote and push: `git remote add origin ...` then `git push -u origin main`.)
3. Refresh the GitHub page — your code is now public (or private, if you chose that when creating the repo).

## Putting the live site online

**GitHub itself only hosts static files — it can't run a Flask/Python server.** GitHub Pages (GitHub's free static hosting) won't work here because this app needs a backend process and a database. You have two good free/cheap options:

### Option A: Render.com (easiest)
1. Push your code to GitHub (above).
2. Go to [render.com](https://render.com) → New → Web Service → connect your GitHub repo.
3. Settings:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
4. Add an environment variable `NEHANG_SECRET_KEY` set to any long random string (so login sessions survive restarts).
5. Deploy — Render gives you a live `https://your-app.onrender.com` URL.

⚠️ Free tiers on Render sleep after inactivity and use **ephemeral disk** — your SQLite database (`nehang.db`) will reset on redeploys/restarts. Fine for a demo; for anything persistent, upgrade to a paid instance with a persistent disk, or swap SQLite for a managed Postgres database (Render offers a free Postgres tier too — ask me if you want help migrating).

### Option B: Railway.app
Same idea as Render — connect the GitHub repo, it auto-detects the `Procfile`, add the `NEHANG_SECRET_KEY` variable, deploy. Railway's free tier also uses ephemeral storage for the same SQLite caveat above.

Want me to walk through either of these deployments live, or help migrate from SQLite to Postgres so your data survives restarts?
