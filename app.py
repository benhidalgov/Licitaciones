from functools import wraps
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
import database

app = Flask(__name__)
app.secret_key = "licitaciones-secret-key-2026"

DEMO_USER = "admin"
DEMO_PASS = "admin123"

VALID_ESTADOS = [
    "Identificada",
    "Calificada",
    "Participada",
    "Adjudicada",
    "Descartada"
]


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


@app.route("/licitaciones/<id_licitacion>")
@login_required
def licitacion_detalle(id_licitacion):
    lic = database.get_licitacion_by_id(id_licitacion)
    if not lic:
        abort(404)

    presupuesto = lic["presupuesto_mandante"]
    costo = lic["costo_base_hotel"]
    diferencia = presupuesto - costo
    es_inviable = costo > presupuesto
    deficit = abs(diferencia) if es_inviable else 0
    margen_porcentaje = round((diferencia / presupuesto) * 100, 1) if presupuesto > 0 else 0

    return render_template(
        "detail.html",
        lic=lic,
        diferencia=diferencia,
        es_inviable=es_inviable,
        deficit=deficit,
        margen_porcentaje=margen_porcentaje,
        valid_estados=VALID_ESTADOS,
        user=session.get("user")
    )


@app.route("/licitaciones/<id_licitacion>/cambiar_estado", methods=["POST"])
@login_required
def cambiar_estado_licitacion(id_licitacion):
    lic = database.get_licitacion_by_id(id_licitacion)
    if not lic:
        abort(404)

    nuevo_estado = request.form.get("estado_embudo", "").strip()
    if nuevo_estado not in VALID_ESTADOS:
        flash(f"Estado invalido '{nuevo_estado}'. Seleccione una etapa valida del embudo comercial.", "error")
        return redirect(url_for("licitacion_detalle", id_licitacion=id_licitacion))

    database.update_licitacion(id_licitacion, {"estado_embudo": nuevo_estado})
    flash(f"Estado en el embudo comercial actualizado exitosamente a '{nuevo_estado}' para la licitacion {id_licitacion}.", "success")
    return redirect(url_for("licitacion_detalle", id_licitacion=id_licitacion))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    database.init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)

