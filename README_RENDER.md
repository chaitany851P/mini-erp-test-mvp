# Deploying Mini ERP on Render

This guide walks through deploying the Django + Firestore app to Render using the included render.yaml.

---

## Overview
- Web service is defined in render.yaml (build/start/migrate steps)
- Static files are served by WhiteNoise
- Database: use Render PostgreSQL (DATABASE_URL)
- Firestore: use Firebase Admin SDK (set as a Secret File on Render)

---

## 1) Prerequisites
- A Git repo containing this project
- Render account (https://render.com)

Optional (recommended locally):
- Python 3.12 to generate a strong DJANGO_SECRET_KEY

Generate a secret key locally:
```pwsh path=null start=null
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

---

## 2) Provision a PostgreSQL instance on Render
- In Render: New → PostgreSQL → Create
- Copy the internal DATABASE_URL (you will paste it into the Web Service env vars)

---

## 3) Create a Web Service
- In Render: New → Web Service → Connect your repo
- Render will detect render.yaml and use it automatically
- The build step will:
  - pip install -r requirements.txt
  - python manage.py collectstatic --noinput
- The start command launches gunicorn
- A postDeployCommand runs `python manage.py migrate --noinput`

---

## 4) Configure environment variables (Render → your service → Environment)
Required:
- DJANGO_SECRET_KEY = <your-strong-secret>
- DJANGO_DEBUG = false
- DJANGO_ALLOWED_HOSTS = *.onrender.com (or your exact host)
- DATABASE_URL = <from your Render PostgreSQL>

Firestore (Admin SDK):
- Create a Secret File in Render → Secret Files
  - Path: /etc/secrets/firebase-admin.json
  - Content: paste your Firebase Admin SDK JSON
- Add env var:
  - FIREBASE_ADMIN_SDK_PATH = /etc/secrets/firebase-admin.json

Optional email/Cashfree vars:
- EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS, DEFAULT_FROM_EMAIL
- CASHFREE_ENV, CASHFREE_APP_ID, CASHFREE_SECRET_KEY, CASHFREE_WEBHOOK_SECRET

---

## 5) First deploy
- Click Deploy. You should see dependencies install, static collected, and migrations run
- Visit https://<your-service>.onrender.com

Create a superuser (one-time):
- Open a one-off shell in Render → your service → Shell → run:
```bash path=null start=null
python manage.py createsuperuser
```

---

## 6) Notes & tips
- Static files: Served by WhiteNoise (no extra CDN needed for MVP)
- SSE/endpoints: gunicorn timeout is 180s; ensure your SSE endpoint sends periodic keep-alives
- CORS: If your frontend is on a different domain, enable django-cors-headers and set CORS_ALLOWED_ORIGINS in env
- Health checks: To manage migrations manually, remove postDeployCommand from render.yaml and run them via a shell

---

## 7) Troubleshooting
- App crashes on start: verify DJANGO_SECRET_KEY, DATABASE_URL, and FIREBASE_ADMIN_SDK_PATH
- 500 errors on pages that read Firestore: ensure Admin SDK JSON is valid and path is correct
- Missing static assets: ensure collectstatic runs and STATIC_URL paths are correct
- DisallowedHost: add your exact onrender.com domain to DJANGO_ALLOWED_HOSTS
