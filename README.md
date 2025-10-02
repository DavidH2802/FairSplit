# FairSplit

A web application (CS50 Final Project, Week 10) for fairly splitting shared expenses among a group.

# Purpose

When multiple people share costs (e.g. roommates, trips, group projects), it’s often tedious to calculate who owes what, especially when not everyone pays the same amount or contributes at different times. **FairSplit** helps automate and simplify that process: input expenses, assign payers, and compute who owes whom to balance things out.

# Repository Structure
FairSplit/
├── app.py — main Flask app and route definitions
├── helpers.py — utility functions for calculations, data     validation, etc.
├── templates/ — HTML templates (Jinja) for rendering pages
├── static/ — CSS, JS, images, and other front-end assets
├── fairsplit.db — SQLite database file (data storage)
├── requirements.txt — Python dependencies list
├── README.md - Read for Info
└── .gitignore


# Setup & Installation

1. **Clone the repo**  
   git clone https://github.com/DavidH2802/FairSplit.git
   cd FairSplit

2. **Create a virtual enviroment and install dependencies**
    python3 -m venv venv
    source venv/bin/activate      # (Linux/macOS)
    venv\Scripts\activate         # (Windows)
    pip install -r requirements.txt

3. **Run the app**
    flask run

4. **Open in browser**
    Visit http://127.0.0.1:5000 (or whatever address Flask outputs).

# Usage Overview

Create a “group” or session.

Add members (people) in the group.

Log expenses: who paid, how much, for whom.

FairSplit runs the algorithm to compute net balances so everyone pays their fair share.

View summary of debts and credits between members.

# Key Features & Algorithm

Handles uneven contributions (some pay more, some pay less)

Minimizes unnecessary transfers: the algorithm tries to simplify who pays who rather than having many small cross-payments

Validates input (no negative contributions, correct group membership, etc.)

Persistent data storage via SQLite (fairsplit.db)

# Limitations & Future Enhancements

No user authentication (so every session is “public” within your local environment)

All data stored in a local SQLite DB — scaling to many users or deploying to a server would require migrating to a more robust DB

No real-time collaboration (i.e. multiple users editing same session simultaneously)

UX enhancements (better dashboard, charts, mobile friendliness)

Export/import (CSV/Excel), email summaries, mobile app version

# Testing & Validation

Manual testing via UI: add test groups, members, expenses, verify balances

Edge cases: zero expenses, negative input, single-member groups

(Optional) You may add unit tests in the future for helpers.py functions

# License & Attribution

This project is released under the MIT License.
Built as part of CS50’s Week 10 final project (Harvard’s Introduction to Computer Science course).


