# Mini ERP for Education – SIH 2025 Pitch

A lightweight, cloud-ready Student ERP that unifies Admissions, Fees, Hostel, and a predictive At‑Risk Dashboard. Built for rapid rollout in government and private institutions with minimal infra and maximum impact.

---

## Why this solution (Problem → Impact)
- Fragmented spreadsheets and paper workflows slow down admissions, fee tracking, and hostel allocation.
- No early-warning system for attendance, fees, and exam risk → higher dropouts.
- High cost and complexity of traditional ERPs hinder adoption in smaller institutes.

Our Mini ERP solves these with a simple, secure, and scalable system that can be deployed in hours, not months.

---

## What’s unique (Key Differentiators)
- Predictive At‑Risk Dashboard
  - Flags students at risk based on attendance, overdue fees, and exam performance.
  - Real-time updates via SSE; optional Firestore listeners to stream only deltas.
- Low-cost, high-efficiency Firestore usage
  - Cursor-based pagination; server-side validation of date ranges.
  - Materialized metrics per student (monthly) to avoid collection scans.
  - Aggregations (count) instead of bulk reads; optional caching on hot endpoints.
- Production-ready now
  - One-click deployment on Render with render.yaml; auto-migrations; WhiteNoise static.
  - Clean .env configuration; Firebase Admin SDK via Secret Files.
- Practical workflows that matter
  - Admissions approval pipeline, hostel allocation, fee receipts (PDF), Excel exports.
- Secure by design
  - RBAC via Django groups, CSRF protection, email/notifications optional.
- Extensible and standards-based
  - Django REST + Firestore; can plug in BigQuery for analytics or a separate React/Flutter frontend.

---

## Functional Highlights
- Admissions:
  - Application creation, review, approve/reject, status tracking.
- Fees:
  - Payments logging, receipt PDF (ReportLab/WeasyPrint), pending/overdue analytics.
- Hostel:
  - Requests, room allocation, occupancy stats.
- Dashboard:
  - At‑Risk students table; distribution analytics; live updates.
- Exports:
  - Excel exports for students/attendance/fees; styled and ready for reporting.

---

## Architecture (High level)
- Backend: Django (Gunicorn) on Render
- Data:
  - Firestore for student operational data (attendance/fees/exams/notifications)
  - PostgreSQL on Render for Django auth/session/admin
- Realtime: SSE endpoints; optional Firestore snapshot listeners
- Static: WhiteNoise (no separate CDN needed for MVP)
- Secrets: Render Environment + Secret Files (Firebase Admin JSON)

This hybrid model balances developer speed, operating cost, and scale.

---

## Security & Governance
- Secrets via environment/secret files; no secrets in repo.
- RBAC with Django groups (admin/teacher/accountant); superuser bypass for ops.
- CSRF protection; secure proxy headers; HTTPS enforced on Render.
- Optional email alerts; configurable SMTP.

---

## Cost & Performance Optimizations
- Avoid full collection scans; enforce filters (student_id, date ranges) and hard limits.
- Cursor-based pagination (no `offset`) to avoid billed skips.
- Aggregation queries (count) where supported to reduce reads.
- Materialized metrics/rollups to serve the dashboard in O(1) reads.
- Optional Redis/short TTL caching on hot endpoints.
- TTL auto-delete for old notifications/logs to control storage.

---

## Deployment Readiness
- render.yaml for web service (build/start/post-deploy migrate)
- runtime.txt (Python 3.12)
- requirements.txt includes dj-database-url, psycopg, Firestore libs, WhiteNoise
- FIREBASE_ADMIN_SDK_PATH to a Secret File on Render

Time-to-live: 30–45 minutes from repo to production.

---

## Demo (Quick Start)
Local (Windows PowerShell):
```pwsh path=null start=null
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# set DJANGO_SECRET_KEY and optional FIREBASE_ADMIN_SDK_PATH in .env
python manage.py migrate
python manage.py runserver
```
Render (hosted): see README_RENDER.md for 5-step deploy.

---

## Impact (KPIs to track in pilots)
- 30–50% reduction in admin time for admissions/hostel workflows
- 10–20% improvement in fee recovery via timely alerts and summaries
- 5–10% reduction in drop‑outs through early at‑risk interventions
- Near‑zero vendor lock-in; runs on commodity infra

---

## Alignment with SIH 2025 Evaluation
- Innovation: Predictive at‑risk + cost‑optimized Firestore patterns
- Feasibility: Working code, instant deployment, minimal infra
- Scalability: Horizontal by design; Firestore + Postgres; stateless app layer
- Sustainability: Low operating cost; documented guardrails to keep bills down
- User‑centric design: Simple flows for students and admins; exports for compliance
- Completion: End‑to‑end flows implemented and deployable now

---

<!-- ## Roadmap (Post‑SIH Enhancements)
- Mobile app (Flutter) for students/faculty
- Role‑based dashboards and multilingual UI (English/Hindi/regional)
- SMS/WhatsApp alerts; parent portal
- BigQuery analytics + scheduled reports to email
- Attendance device integrations (QR/RFID) -->

---

<!-- ## How to Evaluate Quickly (Judge Guide)
- Step 1: Review README_RENDER.md and deploy on Render (10–15 min)
- Step 2: Create superuser, log into /admin, explore groups (RBAC)
- Step 3: Add a few attendance/fees records; watch At‑Risk Dashboard update
- Step 4: Export fees/attendance to Excel; generate receipt PDF
- Step 5: Inspect code structure: clean apps, security controls, and Firestore helpers -->

---

## Contact
- Team: DataWeavers
- Email: chaitanythakar851@gmail.com
- Demo: https://erp-system-mvp.onrender.com/
