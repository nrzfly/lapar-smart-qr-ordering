# Lapar Smart: QR Menu Ordering System

A mobile-first QR code ordering system for **Lazaria Cafe**, developed for FAMA (Federal Agricultural Marketing Authority) staff, built as the implementation for the BIT4008 Undergraduate Project. This app implements the ten use cases described in `002_Chapter_Page_LaparSmart_-_QR_Menu_Ordering_System.docx`.

## Features (mapped to use cases)

| # | Use Case | Where |
|---|----------|-------|
| UC1 | Scan QR Code | `/` landing page (generates a live QR code linking to the menu) |
| UC2 | View Daily Menu | `/menu` |
| UC3 | Place Order | `/menu` → submit → `/order` |
| UC4 | Reserve Meeting Room Order | `/menu` (tick "Meeting Room reservation") |
| UC5 | Receive Order Notification | `/order/<id>/status` (polls `/api/order/<id>` every 3s) |
| UC6 | Pay at Counter | Admin "Mark Completed" action on `/admin/orders` |
| UC7 | Update Daily Menu | `/admin/menu` |
| UC8 | View Orders | `/admin/orders` |
| UC9 | Update Order Status | `/admin/orders` (Pending → Preparing → Ready → Completed) |
| UC10 | Manage Users | `/admin/users` |

## Tech stack

Matches Chapter 4 of the report: **HTML5/CSS3/JavaScript** (server-rendered Jinja2 templates, mobile-first CSS, vanilla JS for the cart and notification polling), **Python Flask**, and **SQLite** (built-in).

## Running locally

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python run.py
```

Then open http://localhost:5000. Demo staff IDs: `S001`, `S002`, `S003`. Admin passcode: `admin123` (override with the `ADMIN_PASSCODE` environment variable).

## Deploying to Vercel

This repo includes `vercel.json` configured for the `@vercel/python` runtime.

```bash
vercel login
vercel --prod
```

### Demo data note

Vercel's serverless functions do not provide a persistent disk. This app stores its SQLite database at `/tmp/laparsmart.db`, which is seeded automatically on first request and persists only for the lifetime of a warm serverless instance — perfect for a live click-through demo, but data **resets** on a cold start or redeploy. For a production deployment, replace `app/db.py` with a managed database such as PostgreSQL (e.g. Vercel Postgres, Supabase, or Neon).

## Project structure

```
lapar-smart/
  api/index.py          # Vercel entrypoint (WSGI app)
  app/
    __init__.py         # Flask app factory
    db.py                # SQLite schema, seed data, connection helper
    routes_staff.py      # UC1-UC6 (staff-facing)
    routes_admin.py       # UC7-UC10 (admin dashboard)
    templates/
    static/css, static/js
  run.py                 # local dev server
  requirements.txt
  vercel.json
```
