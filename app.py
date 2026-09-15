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


def format_clp(value):
    if value is None or value == "":
        return "$0 CLP"
    try:
        val = int(value)
        if val < 0:
            return f"-${abs(val):,} CLP".replace(",", ".")
        return f"${val:,} CLP".replace(",", ".")
    except (ValueError, TypeError):
        return f"${value} CLP"


@app.template_filter("clp")
def clp_filter(value):
    return format_clp(value)


app.jinja_env.globals["format_clp"] = format_clp


@app.route("/")
@app.route("/licitaciones")
@login_required
def dashboard():
    categoria = request.args.get("categoria", "").strip() or None
    modalidad = request.args.get("modalidad", "").strip() or None
    estado = request.args.get("estado", "").strip() or None
    q = request.args.get("q", "").strip() or None

    licitaciones = database.get_all_licitaciones(
        categoria=categoria,
        modalidad=modalidad,
        estado=estado,
        q=q
    )
    metrics = database.get_funnel_metrics()

    return render_template(
        "dashboard.html",
        licitaciones=licitaciones,
        metrics=metrics,
        categoria=categoria or "",
        modalidad=modalidad or "",
        estado=estado or "",
        q=q or "",
        user=session.get("user")
    )


if __name__ == "__main__":
    database.init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
