# Mini ERP for Education -- SIH 2025 Pitch

A lightweight, cloud-ready Student ERP that unifies **Admissions, Fees,
Hostel Management, and a Predictive At-Risk Dashboard**.\
Built for rapid rollout in government and private institutions with
**minimal infrastructure and maximum impact**.

------------------------------------------------------------------------

## Why this Solution? (Problem → Impact)

-   **Problem:** Fragmented spreadsheets and paper workflows slow down
    admissions, fee tracking, and hostel allocation.\
-   **Problem:** The absence of an early-warning system for attendance,
    fees, and exam risk contributes to higher dropout rates.\
-   **Problem:** The high cost and complexity of traditional ERPs hinder
    adoption in smaller institutions.

✅ **Our Mini ERP addresses these challenges with a simple, secure, and
scalable system that can be deployed in hours---not months.**

------------------------------------------------------------------------

## What's Unique? (Key Differentiators)

-   **Predictive At-Risk Dashboard**
    -   Flags students at risk based on attendance, overdue fees, and
        exam performance.\
    -   Supports real-time updates via SSE; optional Firestore listeners
        stream only deltas.
-   **Low-Cost, High-Efficiency Firestore Usage**
    -   Cursor-based pagination and server-side validation minimize
        costs.\
    -   Pre-computed (materialized) metrics per student avoid expensive
        collection scans.\
    -   Aggregations (`count`) reduce reads; optional caching available
        for hot endpoints.
-   **Production-Ready (Cloud Deployment in Progress)**
    -   Designed for easy deployment on managed cloud platforms.\
    -   Automated migrations and static file serving with WhiteNoise.\
    -   Secure configuration using `.env` files and Firebase Admin SDK
        via secret management.
-   **Practical Workflows That Matter**
    -   Admissions approval pipeline, hostel allocation, PDF fee
        receipts, Excel exports.
-   **Secure by Design**
    -   Role-Based Access Control (RBAC) with Django groups.\
    -   CSRF protection, HTTPS-only cookies, and SSL redirects.
-   **Extensible & Standards-Based**
    -   Django REST + Firestore architecture allows future integrations
        (e.g., BigQuery, React/Flutter).

------------------------------------------------------------------------

## Functional Highlights

-   **Admissions:** Application creation, review, approve/reject, and
    status tracking.\
-   **Fees:** Payment logging, PDF receipt generation, pending/overdue
    tracking.\
-   **Hostel:** Requests, room allocation, and occupancy statistics.\
-   **Dashboard:** At-risk student insights with distribution analytics
    and live updates.\
-   **Exports:** Excel reports for students, attendance, and fees
    (styled for readability).

------------------------------------------------------------------------

## Architecture (High-Level)

-   **Backend:** Django (Gunicorn for production).\
-   **Data Layer:** Firestore for operational data (attendance, fees,
    exams, notifications).\
-   **Realtime:** SSE endpoints with optional Firestore snapshot
    listeners.\
-   **Static Assets:** Served via WhiteNoise (no CDN required for MVP).\
-   **Secrets Management:** Secure handling via environment/secret
    files.

👉 This hybrid model balances **developer speed, operating cost, and
scalability**.

------------------------------------------------------------------------

## Security & Governance

-   **Secrets:** Never stored in the repository; managed via
    environment/secret files.\
-   **RBAC:** Admin, teacher, and accountant roles managed with Django
    groups.\
-   **Protection:** CSRF enforcement, secure proxy headers, HTTPS
    redirection.\
-   **Alerts:** Optional email alerts via configurable SMTP server.

------------------------------------------------------------------------

## Cost & Performance Optimizations

-   **Reads:** Avoid full collection scans---queries always filtered by
    `student_id` and date ranges.\
-   **Pagination:** Cursor-based pagination avoids billed skips.\
-   **Aggregations:** Use Firestore `count` queries to minimize reads.\
-   **Dashboard:** Materialized metrics/rollups provide O(1) reads.\
-   **Caching:** Optional Redis/short TTL caching on high-traffic
    endpoints.\
-   **Storage:** TTL auto-deletion for old logs and notifications.

------------------------------------------------------------------------

## Demo (Quick Start)

**Local Setup (Windows PowerShell):**

``` pwsh
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Set DJANGO_SECRET_KEY and FIREBASE_ADMIN_SDK_PATH in .env
python manage.py migrate
python manage.py runserver
```

☁️ Cloud deployment is in progress; instructions will be added once
available.

------------------------------------------------------------------------

## Impact (KPIs for Pilot Institutes)

-   **Efficiency:** 30--50% reduction in admin time for
    admissions/hostel workflows.\
-   **Fee Recovery:** 10--20% improvement via timely alerts and
    dashboards.\
-   **Retention:** 5--10% reduction in dropouts due to early at-risk
    interventions.\
-   **Flexibility:** Near-zero vendor lock-in; runs on commodity
    infrastructure.

------------------------------------------------------------------------

## Alignment with SIH 2025 Evaluation

-   **Innovation:** Predictive at-risk dashboard, cost-optimized
    Firestore usage.\
-   **Feasibility:** Working code, instant deployment, minimal
    infrastructure needs.\
-   **Scalability:** Stateless app layer with Firestore + Postgres;
    horizontally scalable.\
-   **Sustainability:** Low operating cost with documented guardrails.\
-   **User-Centric:** Simple workflows, Excel/PDF exports for compliance
    and reporting.\
-   **Completion:** End-to-end flows functional and deployable locally.

------------------------------------------------------------------------

## Contact

**Team:** Data Weavers\
**Email:** <chaitanythakar851@gmail.com> \|
<trivedimaharshim@gmail.com>\
**Demo:** <https://mini-erp-web.onrender.com> *(deployment in progress)*
