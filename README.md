# Mini ERP System 🎯

Django + Firestore student ERP with Admissions, Fees, Hostel, Dashboard, PDF receipts, and optional Firestore integration.

This README covers local development. For Render deployment, see README_RENDER.md.

---

## Features

- Admissions: application + approval workflow
- Fees: payments, PDF receipt, history
- Hostel: requests, allocation, occupancy
- Dashboard: summaries and charts

---

## Tech Stack

- Backend: Django (4.2–5.0 compatible)
- Data: Firestore (cloud, via Admin SDK) + SQLite (local dev)
- PDFs/Exports: ReportLab, WeasyPrint, pandas, xlsxwriter, openpyxl
- Static files (prod): WhiteNoise

---

## Local Development (Windows PowerShell)

### Prerequisites
- Python 3.12 recommended (3.10+ works)

### 1) Clone and enter the project
```pwsh path=null start=null
git clone <your-repo-url>
cd mini-erp-test-mvp
```

### 2) Create and activate a virtual environment
```pwsh path=null start=null
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3) Install dependencies
```pwsh path=null start=null
pip install -r requirements.txt
```

### 4) Configure environment
```pwsh path=null start=null
Copy-Item .env.example .env
```
Edit .env and set at minimum:
- DJANGO_SECRET_KEY=your-strong-secret (generate: `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`)
- FIREBASE_ADMIN_SDK_PATH=./firebase-admin-sdk.json (optional for Firestore)

If you use Firestore locally, place your Firebase Admin JSON at the path above.

### 5) Initialize the database
```pwsh path=null start=null
python manage.py migrate
python manage.py createsuperuser  # optional, for admin access
```

### 6) Run the server
```pwsh path=null start=null
python manage.py runserver
```
App is available at http://127.0.0.1:8000/

Optional (collect static for production preview):
```pwsh path=null start=null
python manage.py collectstatic --noinput
```

---

## Project Structure

```text path=null start=null
mini-erp-test-mvp/
├── mini_erp/                # Django project (settings, urls, wsgi)
├── admissions/              # App
├── applications/            # App
├── dashboard/               # App
├── fees/                    # App (includes pdf_generator)
├── hostel/                  # App
├── payments/                # App
├── students/                # App
├── templates/               # HTML templates
├── static/                  # Static assets (collected into staticfiles/)
├── media/                   # User uploads (local dev)
├── manage.py
├── requirements.txt
├── render.yaml              # Render service config
├── runtime.txt              # Python version pin for Render
├── .env / .env.example
└── README_RENDER.md         # Render deployment guide
```

---

## Troubleshooting
- pandas/reportlab/weasyprint install issues: ensure you’re inside the venv and on Python 3.12+.
- Firestore credential errors: set FIREBASE_ADMIN_SDK_PATH to a valid Admin SDK JSON.
- Static files missing in production mode: run `python manage.py collectstatic`.

---

## License
Educational MVP. Use and modify freely.
