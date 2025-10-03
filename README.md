# FairSplit

FairSplit is a Flask web application for splitting shared expenses across groups. It began as a CS50 Week 10 final project and has evolved with a proper `instance/` folder for local data and optional database migrations using **Flask‑Migrate** (Alembic). The goal is to make it easy to record expenses, assign participants, and compute minimal settlements.

---

## Table of Contents

* [Features](#features)
* [What’s New](#whats-new)
* [Tech Stack](#tech-stack)
* [Project Structure](#project-structure)
* [Prerequisites](#prerequisites)
* [Quick Start](#quick-start)
* [Configuration](#configuration)
* [Database Setup](#database-setup)

  * [Choosing an Approach](#choosing-an-approach)
  * [Option A — Flask‑Migrate (recommended)](#option-a--flaskmigrate-recommended)
  * [Option B — schema.sql (simple/legacy)](#option-b--schemasql-simplelegacy)
* [Running the App](#running-the-app)
* [Usage Overview](#usage-overview)
* [Common Tasks](#common-tasks)
* [Troubleshooting](#troubleshooting)
* [Git Hygiene](#git-hygiene)
* [Roadmap](#roadmap)
* [License](#license)
* [Attribution](#attribution)

---

## Features

* Create groups and add members.
* Log expenses with payer, amount, and covered participants.
* Compute a minimal set of settlements (who pays whom) to balance the group.
* Simple local development with SQLite; optional migrations for evolving schemas.

---

## Tech Stack

* **Backend**: Flask (Python)
* **Templates**: Jinja2
* **Database**: SQLite (development)
* **Migrations**: Flask‑Migrate (Alembic) — optional
* **Tooling**: `pip` + `venv`

---

## Project Structure

```
FairSplit/
├── app.py                 # Flask app & routes
├── helpers.py             # Utilities (validation, DB helpers, etc.)
├── templates/             # Jinja2 HTML templates
├── static/                # CSS/JS/assets
├── schema.sql             # Reference schema for legacy/simple bootstrap
├── requirements.txt       # Python dependencies
├── README.md
├── .gitignore
├── instance/              # (local-only) fairsplit.db and local configs
└── migrations/            # (created after enabling Flask-Migrate)
```

> Do not commit the `instance/` folder or `fairsplit.db`.

---

## Prerequisites

* Python 3.10+ recommended
* `pip`, `venv`
* SQLite (preinstalled on most systems)

---

## Quick Start

Clone and create a virtual environment:

```bash
git clone https://github.com/DavidH2802/FairSplit.git
cd FairSplit

python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the instance folder:

```bash
mkdir -p instance
```

> The app expects the SQLite file at `instance/fairsplit.db` by default (or as configured via environment variables).

---

## Configuration

Set environment variables (examples):

**macOS/Linux**

```bash
export FLASK_APP=app.py
export FLASK_ENV=development
export SECRET_KEY="change-this-in-production"
# If using SQLAlchemy + Flask-Migrate (Option A):
export SQLALCHEMY_DATABASE_URI="sqlite:///instance/fairsplit.db"
```

**Windows PowerShell**

```powershell
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"
$env:SECRET_KEY = "change-this-in-production"
# If using SQLAlchemy + Flask-Migrate (Option A):
$env:SQLALCHEMY_DATABASE_URI = "sqlite:///instance/fairsplit.db"
```

> Ensure your app reads `SECRET_KEY` for session security. When deploying, use a strong, unique key.

---

## Database Setup

### Choosing an Approach

There are two supported paths for local development:

* **Option A (recommended)**: Use SQLAlchemy models + **Flask‑Migrate** to manage schema changes. Best for long‑term evolution and collaboration.
* **Option B (simple/legacy)**: Use the provided `schema.sql` to create the SQLite DB quickly without migrations.

If your current codebase still uses direct SQLite helpers (e.g., a `get_db()` helper with `sqlite3`), Option B is fine. If you plan to expand and refactor toward SQLAlchemy models, choose Option A.

### Option A — Flask‑Migrate (recommended)

**1) Install migration dependencies (if not already in `requirements.txt`):**

```bash
pip install Flask-SQLAlchemy SQLAlchemy Flask-Migrate
```

**2) Wire up SQLAlchemy and Migrate in your app:**

```python
# app.py (example sketch)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///instance/fairsplit.db")
app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

db = SQLAlchemy(app)
Migrate(app, db)

# define your models here
# class User(db.Model): ...
```

**3) Initialize and create the database:**

```bash
flask db init
flask db migrate -m "initial schema"
flask db upgrade
```

**4) Making schema changes later:**

```bash
# After editing models
flask db migrate -m "describe your change"
flask db upgrade
```

**5) Roll back a migration if needed:**

```bash
flask db downgrade
```

**Importing an existing SQLite (from `schema.sql`) into migrations**

If you already created tables via `schema.sql`, you can bring Alembic in sync:

```bash
# Reflect current DB state as baseline for Alembic
flask db stamp head
# Next time you change models, create a new migration
flask db migrate -m "first change after baseline"
flask db upgrade
```

> If autogenerate does not detect changes, ensure all models are imported before `Migrate(app, db)` and before running `flask db migrate`.

### Option B — `schema.sql` (simple/legacy)

Create the database directly from the SQL file:

```bash
sqlite3 instance/fairsplit.db < schema.sql
```

This is sufficient for quick demos or if you are iterating on raw SQL without SQLAlchemy.

---

## Running the App

```bash
flask run
```

Open the app at the address shown in the terminal (usually `http://127.0.0.1:5000/`).

---

## Usage Overview

1. Create or open a group.
2. Add members.
3. Log expenses: who paid, how much, which members are included.
4. Review the computed settlements and settle up.

---

## Common Tasks

**Reset the local database (Option B users):**

```bash
rm -f instance/fairsplit.db            # macOS/Linux
# or
del .\instance\fairsplit.db           # Windows PowerShell
sqlite3 instance/fairsplit.db < schema.sql
```

**Start fresh migrations (Option A users):**

```bash
rm -rf migrations
flask db init
flask db migrate -m "initial schema"
flask db upgrade
```

**Seeding data (optional):**
Create a small Python script (e.g., `seed.py`) that inserts demo users, groups, and expenses via your ORM or direct SQL, then run:

```bash
python seed.py
```

---

## Troubleshooting

* **Database path issues**: Ensure the `instance/` directory exists and the configured DB path is `sqlite:///instance/fairsplit.db` (Option A) or that your helper points to `instance/fairsplit.db` (Option B).
* **Migrations not detected**: Import all model modules before initializing `Migrate(app, db)` and running `flask db migrate`.
* **Bring existing DB under Alembic control**: `flask db stamp head` to mark current schema as the baseline.
* **`remote contains work` when pushing**: Integrate remote changes and then push.

  ```bash
  git pull --rebase
  git push
  ```
* **`.pyc` files or `__pycache__/` still show up in `git status`**: They may already be tracked.

  ```bash
  git rm -r --cached __pycache__
  git commit -m "Remove cached bytecode"
  ```
* **Windows venv activation errors**: Make sure you are using PowerShell and the correct path: `.venv\Scripts\Activate.ps1`.

---

## Git Hygiene

A reasonable `.gitignore` for this project includes:

```
# Python
__pycache__/
*.py[cod]

# Environments
.venv/
.env
*.env

# SQLite
*.sqlite3
*.db
instance/

# Migrations cache (keep the folder, ignore compiled stuff if needed)
*.egg-info/
```

> Keep `instance/` out of version control to avoid committing local databases and secrets.

---

## Roadmap

* Improved dashboard and mobile‑friendly UI.
* Import/export (CSV/Excel).
* Optional authentication and invitations for multi‑user scenarios.
* Deployment presets for Render/Fly.io and production databases.

---

## License

MIT License. See `LICENSE` for details.

---

## Attribution

Originally created as a CS50 Week 10 final project; now generalized for broader use and maintainability.



