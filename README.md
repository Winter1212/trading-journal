# Trading Journal

Flask + Firestore journal. Log each trade with **why you took it**, then review the result and lesson later.

## 1. Firebase (Firestore)
1. https://console.firebase.google.com → create project → **Build → Firestore Database → Create database**.
2. **Project settings → Service accounts → Generate new private key** → downloads a `.json` file. Keep it secret, never commit it.

## 2. Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export FIREBASE_CREDENTIALS_FILE=/path/to/serviceAccount.json
python app.py          # http://localhost:5000
```

## 3. GitHub
```bash
git init && git add . && git commit -m "Trading journal"
git branch -M main
git remote add origin https://github.com/<you>/trading-journal.git
git push -u origin main
```

## 4. Deploy on Render
1. Render → **New → Blueprint** (or Web Service) → pick your GitHub repo.
2. Build: `pip install -r requirements.txt`  Start: `gunicorn app:app`
3. Environment variables:
   - `FIREBASE_CREDENTIALS` = paste the **entire contents** of the service-account JSON
   - `APP_PASSWORD` = your login password (username defaults to `trader`)
4. Deploy. Open the URL and log in.

Note: Render free plan sleeps after inactivity; first load can take ~30s. Data is safe in Firestore.
