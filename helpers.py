import flask
import functools
import sqlite3

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
    conn = sqlite3.connect("fairsplit.db")
    conn.row_factory = sqlite3.Row
    return conn
