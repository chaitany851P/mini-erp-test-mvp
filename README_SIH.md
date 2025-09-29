# Mini ERP for Education – SIH 2025 Pitch

A lightweight, cloud-ready Student ERP that unifies Admissions, Fees, Hostel, and a predictive At-Risk Dashboard. Built for rapid rollout in government and private institutions with minimal infrastructure and maximum impact.

---

## Why this Solution? (Problem → Impact)

* **Problem:** Fragmented spreadsheets and paper workflows slow down admissions, fee tracking, and hostel allocation.
* **Problem:** The lack of an early-warning system for attendance, fees, and exam risk leads to higher dropout rates.
* **Problem:** The high cost and complexity of traditional ERPs hinder adoption in smaller institutes.

**Our Mini ERP solves these challenges with a simple, secure, and scalable system that can be deployed in hours, not months.**

---

## What’s Unique? (Key Differentiators)

* **Predictive At-Risk Dashboard:**

  * Flags students at risk based on attendance, overdue fees, and exam performance.
  * Uses real-time updates via SSE; optional Firestore listeners stream only deltas.
* **Low-Cost, High-Efficiency Firestore Usage:**

  * Employs cursor-based pagination and server-side validation to reduce costs.
  * Uses materialized metrics per student to avoid expensive collection scans for the dashboard.
  * Aggregations (`count`) reduce reads; optional caching is available on hot endpoints.
* **Production-Ready (Cloud Deployment in Progress):**

  * System designed for easy deployment on managed cloud services.
  * Includes automated migrations and static file serving with WhiteNoise.
  * Secure configuration using `.env` files and Firebase Admin SDK via environment/secret files.
* **Practical Workflows that Matter:**

  * Admissions approval pipeline, hostel allocation, PDF fee receipts, and Excel exports.
* **Secure by Design:**

  * Implements Role-Based Access Control (RBAC) via Django groups.
  * Includes CSRF protection, HTTPS-only cookies, and SSL redirects.
* **Extensible and Standards-Based:**

  * The architecture (Django REST + Firestore) allows easy integration with other services like BigQuery for advanced analytics or a separate frontend framework (e.g., React/Flutter).

---

## Functional Highlights

* **Admissions:** Application creation, review, approve/reject, and status tracking.
* **Fees:** Payments logging, receipt PDF generation (ReportLab/WeasyPrint), and pending/overdue analytics.
* **Hostel:** Requests, room allocation, and occupancy stats.
* **Dashboard:** At-Risk students table with distribution analytics and live updates.
* **Exports:** Excel exports for students, attendance, and fees, styled for easy reporting.

---

## Architecture (High-Level)

* **Backend:** Django (Gunicorn) on local/dev environment.
* **Data:**

  * **Firestore** for student operational data (attendance, fees, exams, notifications).
* **Realtime:** SSE endpoints with optional Firestore snapshot listeners.
* **Static Assets:** WhiteNoise (no separate CDN needed for MVP).
* **Secrets:** Managed securely via environment/secret files.

This hybrid model balances developer speed, operating cost, and scalability.

---

## Security & Governance

* **Secrets:** Stored securely via environment/secret files, never in the repository.
* **RBAC:** Implemented with Django groups for distinct roles (admin, teacher, accountant).
* **Protection:** Includes CSRF protection, secure proxy headers, and HTTPS enforcement.
* **Alerts:** Optional email alerts via a configurable SMTP server.

---

## Cost & Performance Optimizations

* **Data Reads:** Avoid full collection scans by enforcing filters (`student_id`, date ranges) and hard limits.
* **Pagination:** Use cursor-based pagination to avoid billed skips.
* **Queries:** Utilize aggregation queries (`count`) to reduce reads.
* **Dashboard:** Use materialized metrics/rollups to serve dashboard data in O(1) reads.
* **Caching:** Optional Redis/short TTL caching on hot endpoints.
* **Storage:** TTL auto-delete for old notifications and logs to control storage costs.

---

## Demo (Quick Start)

**Local (Windows PowerShell):**

```pwsh
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# set DJANGO_SECRET_KEY and optional FIREBASE_ADMIN_SDK_PATH in .env
python manage.py migrate
python manage.py runserver
```

Cloud deployment is in progress; instructions will be updated once ready.

---

## Impact (KPIs to Track in Pilots)

* **Efficiency:** 30–50% reduction in admin time for admissions and hostel workflows.
* **Fee Recovery:** 10–20% improvement in fee recovery via timely alerts and summaries.
* **Retention:** 5–10% reduction in dropouts through early at-risk interventions.
* **Flexibility:** Near-zero vendor lock-in; the solution runs on commodity infrastructure.

---

## Alignment with SIH 2025 Evaluation

* **Innovation:** Predictive at-risk dashboard and cost-optimized Firestore patterns.
* **Feasibility:** Working code, instant local deployment, minimal infrastructure.
* **Scalability:** Horizontal by design; a stateless app layer with Firestore and Postgres.
* **Sustainability:** Low operating cost and documented guardrails to keep bills down.
* **User-Centric Design:** Simple flows for students and admins, with data exports for compliance.
* **Completion:** End-to-end flows are fully implemented and deployable locally now.

---

## Contact

* **Team:** Data Weavers
* **Email:** [chaitanythakar851@gmail.com](mailto:chaitanythakar851@gmail.com)
* **Demo:** [https://mini-erp-web.onrender.com](https://mini-erp-web.onrender.com) [deployment in progress]
