import flask
import functools
import sqlite3
import os

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def error(message, code=400):
    """Render message as an apology to user."""
    return flask.render_template("error.html", code=code, message=message), code

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if flask.session.get("user_id") is None:
            return flask.redirect(flask.url_for("login", next=flask.request.url))
        return f(*args, **kwargs)

    return decorated_function

def get_db():
    db_path = os.path.join(flask.current_app.instance_path, "fairsplit.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def split_expense(amount, members, payer_id):

    if len(members) <= 1:
        raise ValueError("At least two members are required to split an expense.")
    if amount <= 0:
        raise ValueError("Amount must be positive.")
    if not payer_id in [m["id"] for m in members]:
        raise ValueError("Payer must be a member of the group.")
    
    share = amount / len(members)
    loans = []
    for m in members:
        if m["id"] != payer_id:
            loans.append((payer_id, m["id"], share))
    return loans

def calculate_balances(loans, user_id, members):
    if len(members) <= 1:
        raise ValueError("At least two members are required to calculate balances.")
    if not loans:
        return {member["id"]: 0 for member in members}
    if not user_id in [m["id"] for m in members]:
        raise ValueError("User must be a member of the group.")
    if not all(k in loans[0] for k in ("payer_id", "payee_id", "amount")) and loans:
        raise ValueError("Loans must have payer_id, payee_id, and amount fields.")
    if not all(isinstance(l["amount"], (int, float)) for l in loans):
        raise ValueError("Loan amounts must be numeric.")
    if not all(l["amount"] > 0 for l in loans):
        raise ValueError("Loan amounts must be positive.")
    if not all(l["payer_id"] in [m["id"] for m in members] for l in loans):
        raise ValueError("Payer must be a member of the group.")
    if not all(l["payee_id"] in [m["id"] for m in members] for l in loans):
        raise ValueError("Payee must be a member of the group.")

    balances = {member["id"]: 0 for member in members}

    for loan in [l for l in loans if l["payer_id"] == user_id]:
        balances[loan["payee_id"]] += loan["amount"]

    for loan in [l for l in loans if l["payee_id"] == user_id]:
        balances[loan["payer_id"]] -= loan["amount"]

    return balances
