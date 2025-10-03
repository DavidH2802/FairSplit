import flask
import os
from dotenv import load_dotenv
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import helpers
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_migrate import Migrate

load_dotenv()
app = flask.Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fairsplit.db"
app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True

db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.config["SESSION_SQLALCHEMY"] = db

Session(app)

csrf = CSRFProtect(app)

limiter = Limiter(get_remote_address, app=app, default_limits=["600 per day", "150 per hour"])

app.jinja_env.filters["usd"] = helpers.usd

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return flask.render_template("csrf_error.html", reason=e.description), 400

@app.route("/")
@helpers.login_required
def index():
    return flask.redirect("/groups")

@app.route("/login", methods=["GET", "POST"])
def login():
    flask.session.clear()

    if flask.request.method == "POST":
        username = flask.request.form.get("username")
        password = flask.request.form.get("password")

        if not username:
            return helpers.error("must provide username", 403)
        elif not password:
            return helpers.error("must provide password", 403)

        cursor = helpers.get_db().cursor()
        rows = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchall()

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return helpers.error("invalid username and/or password", 403)

        flask.session["user_id"] = rows[0]["id"]

        return flask.redirect("/")
    
    return flask.render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    flask.session.clear()

    if flask.request.method == "POST":
        username = flask.request.form.get("username")
        password = flask.request.form.get("password")
        confirmation = flask.request.form.get("confirmation")

        if not username:
            return helpers.error("must provide username", 403)
        elif not password:
            return helpers.error("must provide password", 403)
        elif password != confirmation:
            return helpers.error("passwords must match", 403)
        
        if len(password) < 8:
            return helpers.error("password must be at least 8 characters long", 403)
        if not any(x.isupper() for x in password):
            return helpers.error("Password must contain an uppercase letter", 403)

        with helpers.get_db() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                               (username, generate_password_hash(password)))
                conn.commit()
            except sqlite3.IntegrityError:
                return helpers.error("username already taken", 403)

        return flask.redirect("/")

    return flask.render_template("register.html")

@app.route("/logout")
def logout():
    flask.session.clear()
    return flask.redirect("/login")

@app.route("/groups", methods=["GET", "POST"])
@helpers.login_required
def groups():
    cursor = helpers.get_db().cursor()

    groups = cursor.execute("SELECT * FROM groups JOIN memberships ON groups.id = memberships.group_id WHERE memberships.user_id = ?", (flask.session["user_id"],)).fetchall()
    invites = cursor.execute("SELECT * FROM invites JOIN groups ON invites.group_id = groups.id WHERE invites.receiver_id = ?", (flask.session["user_id"],)).fetchall()

    return flask.render_template("groups.html", groups=groups, invites=invites)

@app.route("/groups/create", methods=["GET", "POST"])
@helpers.login_required
def create_group():
    if flask.request.method == "POST":
        group_name = flask.request.form.get("groupname")

        if not group_name:
            return helpers.error("must provide group name", 403)

        with helpers.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO groups (name) VALUES (?)", (group_name,))
            group_id = cursor.lastrowid
            cursor.execute("INSERT INTO memberships (user_id, group_id, group_creator) VALUES (?, ?, ?)", (flask.session["user_id"], group_id, 1))
            conn.commit()

        return flask.redirect("/groups")

    return flask.render_template("groups.html")

@app.route("/groups/accept", methods=["GET","POST"])
@helpers.login_required
def accept_invite():
    if flask.request.method == "POST":
        invite_id = flask.request.form.get("invite_id")

        if not invite_id:
            return helpers.error("must provide invite ID", 403)

        cursor = helpers.get_db().cursor()
        group = cursor.execute("SELECT * FROM groups WHERE id = (SELECT group_id FROM invites WHERE id = ?)", (invite_id,)).fetchone()

        if not group:
            return helpers.error("group does not exist", 403)

        with helpers.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO memberships (user_id, group_id, group_creator) VALUES (?, ?, ?)", (flask.session["user_id"], group["id"], 0))
            cursor.execute("DELETE FROM invites WHERE receiver_id = ? AND group_id = ?", (flask.session["user_id"], group["id"]))
            conn.commit()

        return flask.redirect("/groups")

    return helpers.error("invalid request", 403)

@app.route("/groups/decline", methods=["GET","POST"])
@helpers.login_required
def decline_invite():
    if flask.request.method == "POST":
        invite_id = flask.request.form.get("invite_id")

        if not invite_id:
            return helpers.error("must provide invite ID", 403)

        with helpers.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM invites WHERE receiver_id = ? AND id = ?", (flask.session["user_id"], invite_id))
            conn.commit()

        return flask.redirect("/groups")

    return helpers.error("invalid request", 403)

@app.route("/groups/<int:group_id>", methods=["GET", "POST"])
@helpers.login_required
def view_group(group_id):
    cursor = helpers.get_db().cursor()
    group = cursor.execute("SELECT * FROM groups WHERE id = ?", (group_id,)).fetchone()
    if not group:
        return helpers.error("group does not exist", 404)

    members = cursor.execute("SELECT users.username, users.id FROM memberships JOIN users ON memberships.user_id = users.id WHERE memberships.group_id = ?", (group_id,)).fetchall()
    if not members:
        return helpers.error("no members in this group", 404)
    if flask.session["user_id"] not in [m["id"] for m in members]:
        return helpers.error("you are not a member of this group", 403)
    
    member_count = len(members)
    if member_count <= 1:
        return helpers.error("group must have at least 2 members to split expenses", 400)
    
    loans = cursor.execute("SELECT * FROM loans WHERE group_id = ?", (group_id,)).fetchall()
    balances = helpers.calculate_balances(loans, flask.session["user_id"], members)

    tmp = cursor.execute("SELECT group_creator FROM memberships WHERE user_id = ? AND group_id = ?", (flask.session["user_id"], group_id)).fetchone()
    if not tmp:
        return helpers.error("you are not a member of this group", 403)
    is_creator = False
    if tmp["group_creator"] == 1:
        is_creator = True

    transactions = cursor.execute("SELECT * FROM transactions WHERE group_id = ?", (group_id,)).fetchall()

    return flask.render_template("view_group.html", group=group, members=members, current_user_id=flask.session["user_id"], balances=balances, is_creator=is_creator, transactions=transactions)

@app.route("/groups/<int:group_id>/invite", methods=["GET", "POST"])
@helpers.login_required
def invite_member(group_id):
    if flask.request.method == "POST":
        username = flask.request.form.get("username")
        if not username:
            return helpers.error("must provide username", 403)

        with helpers.get_db() as conn:
            cursor = conn.cursor()
            group = cursor.execute("SELECT * FROM groups WHERE id = ?", (group_id,)).fetchone()
            if not group:
                return helpers.error("group does not exist", 404)
            user = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if not user:
                return helpers.error("user not found", 404)

            is_member = cursor.execute("SELECT * FROM memberships WHERE user_id = ? AND group_id = ?", (user["id"], group_id)).fetchone()
            if is_member:
                return helpers.error("user is already a member of this group", 400)
            
            is_invited = cursor.execute("SELECT * FROM invites WHERE receiver_id = ? AND group_id = ?", (user["id"], group_id)).fetchone()
            if is_invited:
                return helpers.error("user has already been invited to this group", 400)

            cursor.execute("INSERT INTO invites (sender_id, receiver_id, group_id, group_name, status) VALUES (?, ?, ?, ?, ?)", (flask.session["user_id"], user["id"], group_id, group["name"], "active"))

        return flask.redirect("/groups")

    return helpers.error("invalid request", 403)

@app.route("/groups/<int:group_id>/expenses/add", methods=["GET", "POST"])
@helpers.login_required
def add_expense(group_id):
    if flask.request.method == "POST":
        description = flask.request.form.get("description")
        amount = flask.request.form.get("amount")

        if not description:
            return helpers.error("must provide description", 403)
        if not amount:
            return helpers.error("must provide amount", 403)
        try:
            amount = float(amount)
            if amount <= 0:
                return helpers.error("amount must be positive", 403)
        except ValueError:
            return helpers.error("amount must be a number", 403)

        cursor = helpers.get_db().cursor()
        group = cursor.execute("SELECT * FROM groups WHERE id = ?", (group_id,)).fetchone()
        if not group:
            return helpers.error("group does not exist", 404)

        is_member = cursor.execute("SELECT * FROM memberships WHERE user_id = ? AND group_id = ?", (flask.session["user_id"], group_id)).fetchone()
        if not is_member:
            return helpers.error("you are not a member of this group", 403)

        cursor = helpers.get_db().cursor()
        cursor.execute("INSERT INTO transactions (group_id, payer_id, description, amount) VALUES (?, ?, ?, ?)", (group_id, flask.session["user_id"], description, amount))
        transaction_id = cursor.lastrowid

        members = cursor.execute("SELECT users.id FROM memberships JOIN users ON memberships.user_id = users.id WHERE memberships.group_id = ?", (group_id,)).fetchall()
        try:
            loans = helpers.split_expense(amount, members, flask.session["user_id"])
        except ValueError as e:
            return helpers.error(str(e), 403)
        for loan in loans:
            cursor.execute("INSERT INTO loans (payer_id, payee_id, amount, transaction_id, group_id) VALUES (?, ?, ?, ?, ?)", (loan[0], loan[1], loan[2], transaction_id, group_id))
        cursor.connection.commit()
        return flask.redirect(f"/groups/{group_id}")

    return helpers.error("invalid request", 403)

@app.route("/groups/<int:group_id>/settle", methods=["GET", "POST"])
@helpers.login_required
def settle_expense(group_id):
    if flask.request.method == "POST":
        payee_id = flask.request.form.get("payee_id")

        if not payee_id:
            return helpers.error("must provide payee ID", 403)

        cursor = helpers.get_db().cursor()
        group = cursor.execute("SELECT * FROM groups WHERE id = ?", (group_id,)).fetchone()
        if not group:
            return helpers.error("group does not exist", 404)

        is_member = cursor.execute("SELECT * FROM memberships WHERE user_id = ? AND group_id = ?", (flask.session["user_id"], group_id)).fetchone()
        if not is_member:
            return helpers.error("you are not a member of this group", 403)

        payee = cursor.execute("SELECT * FROM users WHERE id = ?", (payee_id,)).fetchone()
        if not payee:
            return helpers.error("payee does not exist", 404)

        is_payee_member = cursor.execute("SELECT * FROM memberships WHERE user_id = ? AND group_id = ?", (payee_id, group_id)).fetchone()
        if not is_payee_member:
            return helpers.error("payee is not a member of this group", 403)

        loans = cursor.execute("SELECT * FROM loans WHERE payer_id = ? AND payee_id = ? AND group_id = ?", (flask.session["user_id"], payee_id, group_id)).fetchall()
        if not loans:
            return helpers.error("no outstanding loans to settle", 400)

        
        for loan in loans:
            cursor.execute("DELETE FROM loans WHERE id = ?", (loan["id"],))
    
        cursor.connection.commit()

        return flask.redirect(f"/groups/{group_id}")

    return helpers.error("invalid request", 403)

@app.route("/groups/<int:group_id>/expenses/<int:transaction_id>/remove", methods=["GET", "POST"])
@helpers.login_required
def remove_expense(group_id, transaction_id):
    if flask.request.method == "POST":
        cursor = helpers.get_db().cursor()
        transaction = cursor.execute("SELECT * FROM transactions WHERE id = ? AND group_id = ?", (transaction_id, group_id)).fetchone()
        if not transaction:
            return helpers.error("transaction does not exist", 404)

        if transaction["payer_id"] != flask.session["user_id"]:
            return helpers.error("only the payer can remove this transaction", 403)

        cursor.execute("DELETE FROM loans WHERE transaction_id = ?", (transaction_id,))
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))

        return flask.redirect(f"/groups/{group_id}")

    return helpers.error("invalid request", 403)


@app.route("/groups/<int:group_id>/remove", methods=["GET", "POST"])
@helpers.login_required
def remove_group(group_id):
    if flask.request.method == "POST":
        cursor = helpers.get_db().cursor()
        group = cursor.execute("SELECT * FROM groups WHERE id = ?", (group_id,)).fetchone()
        if not group:
            return helpers.error("group does not exist", 404)

        is_creator = cursor.execute("SELECT * FROM memberships WHERE user_id = ? AND group_id = ? AND group_creator = 1", (flask.session["user_id"], group_id)).fetchone()
        if not is_creator:
            return helpers.error("only the group creator can remove the group", 403)

        cursor.execute("DELETE FROM loans WHERE group_id = ?", (group_id,))
        cursor.execute("DELETE FROM transactions WHERE group_id = ?", (group_id,))
        cursor.execute("DELETE FROM memberships WHERE group_id = ?", (group_id,))
        cursor.execute("DELETE FROM invites WHERE group_id = ?", (group_id,))
        cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))
        cursor.connection.commit()

        return flask.redirect("/groups")
    
    return helpers.error("invalid request", 403)

@app.route("/profile", methods=["GET", "POST"])
@helpers.login_required
def profile():
    cursor = helpers.get_db().cursor()
    user = cursor.execute("SELECT * FROM users WHERE id = ?", (flask.session["user_id"],)).fetchone()
    if not user:
        return helpers.error("user does not exist", 404)
    groups = cursor.execute("SELECT * FROM groups JOIN memberships ON groups.id = memberships.group_id WHERE memberships.user_id = ?", (flask.session["user_id"],)).fetchall()

    if flask.request.method == "POST":
        cursor.execute("DELETE FROM invites WHERE sender_id = ? OR receiver_id = ?", (flask.session["user_id"], flask.session["user_id"]))
        cursor.execute("DELETE FROM memberships WHERE user_id = ?", (flask.session["user_id"],))
        cursor.execute("DELETE FROM users WHERE id = ?", (flask.session["user_id"],))
        cursor.execute("DELETE FROM loans WHERE payer_id = ? OR payee_id = ?", (flask.session["user_id"], flask.session["user_id"]))
        cursor.execute("DELETE FROM transactions WHERE payer_id = ?", (flask.session["user_id"],))

        cursor.connection.commit()
        flask.session.clear()
        return flask.redirect("/register")

    return flask.render_template("profile.html", username=user["username"], groups=groups)

@app.route("/profile/change-password", methods=["GET", "POST"])
@helpers.login_required
def change_password():
    if flask.request.method == "POST":
        current_password = flask.request.form.get("current_password")
        new_password = flask.request.form.get("new_password")
        confirmation = flask.request.form.get("confirmation")

        if not current_password:
            return helpers.error("must provide current password", 403)
        if not new_password:
            return helpers.error("must provide new password", 403)
        if new_password != confirmation:
            return helpers.error("new passwords must match", 403)

        cursor = helpers.get_db().cursor()
        user = cursor.execute("SELECT * FROM users WHERE id = ?", (flask.session["user_id"],)).fetchone()
        if not user:
            return helpers.error("user does not exist", 404)

        if not check_password_hash(user["hash"], current_password):
            return helpers.error("current password is incorrect", 403)
        
        if current_password == new_password:
            return helpers.error("new password must be different from current password", 403)
        
        if len(new_password) < 8:
            return helpers.error("password must be at least 8 characters long", 403)
        if not any(x.isupper() for x in new_password):
            return helpers.error("Password must contain an uppercase letter", 403)

        if new_password != confirmation:
            return helpers.error("new passwords must match", 403)

        cursor.execute("UPDATE users SET hash = ? WHERE id = ?", (generate_password_hash(new_password), flask.session["user_id"]))
        cursor.connection.commit()

        return flask.redirect("/profile")

    return flask.render_template("change_password.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()