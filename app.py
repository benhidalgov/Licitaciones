from functools import wraps
from flask import Flask, flash, redirect, render_template, request, session, url_for
import database

app = Flask(__name__)
app.secret_key = "licitaciones-secret-key-2026"

DEMO_USER = "admin"
DEMO_PASS = "admin123"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if user == DEMO_USER and password == DEMO_PASS:
            session["user"] = user
            flash("Sesion iniciada correctamente.", "info")
            return redirect(url_for("dashboard"))
        else:
            flash("Credenciales invalidas. Ingrese las credenciales de prueba proporcionadas.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Ha cerrado sesion correctamente.", "info")
    return redirect(url_for("login"))


@app.route("/")
@app.route("/licitaciones")
@login_required
def dashboard():
    return render_template("dashboard.html", user=session.get("user"))


if __name__ == "__main__":
    database.init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
