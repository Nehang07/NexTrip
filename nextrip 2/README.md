# NexTrip

A full-stack travel booking platform: Flask + SQLite backend, vanilla HTML/CSS/JS frontend. Co-founded by Mr. Nehang.

## What's included

**Booking (new):**
- **Flights** — search real routes across India, Australia, London, France, and Thailand; sort by price/duration/departure; book with a test-mode payment
- **Hotels** — search by city with price/star-rating filters; realistic mock inventory (invented hotel names, real photos) across every NexTrip destination city
- **Buses & Trains** — domestic India routes (Delhi–Jaipur, Mumbai–Goa, Bangalore–Chennai, etc.)
- **Checkout** — a self-contained test-mode payment gateway: Luhn-validated card numbers, realistic test-card outcomes (`4242 4242 4242 4242` succeeds, `4000 0000 0000 0002` declines), a simulated processing sequence, and a real booking record + confirmation on success. No external network calls, no real money — swap `run_mock_gateway()` in `app.py` for a real Stripe/Razorpay server call when you're ready to go live.
- **My Bookings** — every flight/hotel/bus booking in one place, filterable by type, with cancellation

**Planning (existing):**
- **Explorer** — search/filter/sort destinations by category, country, budget; save favorites (backed by real DB queries, not hardcoded arrays)
- **AI Planner** — generates a day-by-day itinerary for any destination based on trip length, budget, and interests, using curated real content (not randomly generated) plus a "hidden gem" tip; itineraries are saved per user
- **Budget Tracker** — log and categorize trip expenses, see totals and a category breakdown, per account
- **Reviews** — browse and post star-rated reviews per destination

**Accounts:** register/login/logout with hashed passwords and server-side sessions (no plaintext passwords, no localStorage auth) shared across every module above.

Everything reads/writes through a real SQLite database (`nextrip.db`, created automatically on first run) via a JSON API — nothing is hardcoded in the frontend JS.

**Countries covered:** India, Australia, London, France, and Thailand — each with must-visit destinations plus hidden gems (e.g. Sydney + Kangaroo Island, London + the Cotswolds, Paris + Annecy, Bangkok + Pai).

## Run it

```bash
cd nextrip
pip install -r requirements.txt
python3 app.py
```

Then open **http://localhost:5000** in your browser. The database and its 25 seed destinations (across India, Australia, United Kingdom, France, and Thailand) are created automatically the first time the app runs.

To reset all data, stop the server and delete `nextrip.db`, then restart.

## Project structure

```
nextrip/
  app.py               # Flask app: all page routes + JSON API + mock payment gateway
  seed_data.py         # Destinations, countries, curated itineraries (loaded into SQLite on first run)
  travel_data.py       # Flights, hotels, buses mock inventory generator
  requirements.txt
  nextrip.db           # created automatically — SQLite database
  public/              # all pages (served by Flask)
    index.html         # homepage with tabbed Flights/Hotels/Buses/Explore search
    flights.html
    hotels.html
    transport.html     # buses & trains
    checkout.html      # shared payment flow for all booking types
    bookings.html      # "My Bookings"
    explorer.html
    planner.html
    budget.html
    reviews.html
    about.html
  static/
    css/style.css      # shared design system + animations
    js/nav.js          # shared auth/session logic, login+register modal, scroll-reveal
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
| `/api/planner/generate` | POST | – (saves trip if logged in) | Generate a curated itinerary |
| `/api/trips` | GET | ✔ | User's saved itineraries |
| `/api/budget` | GET/POST | ✔ | List / add expenses |
| `/api/budget/<id>` | DELETE | ✔ | Delete an expense |
| `/api/cities` | GET | – | City reference list for search forms |
| `/api/flights` | GET | – | Search flights by origin/destination |
| `/api/hotels` | GET | – | Search hotels by city/price/stars |
| `/api/buses` | GET | – | Search buses/trains by origin/destination |
| `/api/checkout/pay` | POST | ✔ | Run mock payment + create booking |
| `/api/bookings` | GET | ✔ | List all of the user's bookings |
| `/api/bookings/<id>/cancel` | POST | ✔ | Cancel a booking |

### Testing payments
The checkout page uses a self-contained mock gateway (no external calls, so it works with no network access at all). Use these card numbers:
- `4242 4242 4242 4242` — succeeds
- `4000 0000 0000 0002` — declined (generic)
- `4000 0000 0000 9995` — declined (insufficient funds)
- Any other number that passes the Luhn check — succeeds

Any future expiry date (`MM/YY`) and any 3-digit CVV work. To go live with real payments later, replace the body of `run_mock_gateway()` in `app.py` with a real Stripe/Razorpay server-side call — the request/response shape is already designed to match.

## Notes on images

I wasn't able to pull images from the reference site (nehang-journey-map.base44.app) directly — it's a client-rendered app that only exposes a login screen to automated fetches, so there was no static markup or image URLs to copy. Destination photos here are curated Unsplash CDN images (same approach your original `explorer.html` used), each with a fallback in case one fails to load.

## Production notes

This runs on Flask's built-in dev server locally, which is fine for local use/demos. `gunicorn` is included in `requirements.txt` and a `Procfile` is provided for real deployment. You'll also want:
- `app.secret_key` set via a real environment variable (`NEXTRIP_SECRET_KEY`) — currently it auto-generates a random one on each restart, which logs out all sessions when the server restarts
- HTTPS, and `SESSION_COOKIE_SECURE=True`

## Publishing to GitHub

1. Create a new repository on [github.com/new](https://github.com/new) — don't initialize it with a README (you already have one).
2. In the `nextrip` folder, run:
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
4. Add an environment variable `NEXTRIP_SECRET_KEY` set to any long random string (so login sessions survive restarts).
5. Deploy — Render gives you a live `https://your-app.onrender.com` URL.

⚠️ Free tiers on Render sleep after inactivity and use **ephemeral disk** — your SQLite database (`nextrip.db`) will reset on redeploys/restarts. Fine for a demo; for anything persistent, upgrade to a paid instance with a persistent disk, or swap SQLite for a managed Postgres database (Render offers a free Postgres tier too — ask me if you want help migrating).

### Option B: Railway.app
Same idea as Render — connect the GitHub repo, it auto-detects the `Procfile`, add the `NEXTRIP_SECRET_KEY` variable, deploy. Railway's free tier also uses ephemeral storage for the same SQLite caveat above.

Want me to walk through either of these deployments live, or help migrate from SQLite to Postgres so your data survives restarts?
