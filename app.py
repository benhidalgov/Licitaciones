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


def parse_and_validate_licitacion_form(form, is_create=True, existing_id=None):
    errors = []
    if is_create:
        id_licitacion = form.get("id_licitacion", "").strip()
        if not id_licitacion:
            errors.append("El ID de Mercado Publico es un campo obligatorio.")
        elif database.get_licitacion_by_id(id_licitacion) is not None:
            errors.append(f"El ID de licitacion '{id_licitacion}' ya existe en el sistema (ID duplicado). Ingrese un identificador unico.")
    else:
        id_licitacion = existing_id

    titulo = form.get("titulo", "").strip()
    if not titulo:
        errors.append("El Titulo de la licitacion es un campo obligatorio.")

    organismo = form.get("organismo", "").strip()
    if not organismo:
        errors.append("El Organismo Mandante es un campo obligatorio.")

    region = form.get("region", "").strip() or "Region Metropolitana (Santiago)"

    categoria = form.get("categoria", "").strip() or "Alojamiento"
    modalidad = form.get("modalidad", "").strip() or "Compra Agil"

    estado_embudo = form.get("estado_embudo", "").strip() or "Identificada"
    if estado_embudo not in VALID_ESTADOS:
        errors.append(f"Estado de embudo '{estado_embudo}' invalido. Seleccione una etapa valida.")

    validacion_adjuntos = form.get("validacion_adjuntos", "").strip() or "Valida"

    presupuesto_val = 0
    presupuesto_str = form.get("presupuesto_mandante", "").strip()
    if not presupuesto_str:
        errors.append("El Presupuesto Mandante es un campo obligatorio.")
    else:
        try:
            presupuesto_val = int(presupuesto_str)
            if presupuesto_val < 0:
                errors.append("El Presupuesto Mandante debe ser un valor numerico mayor o igual a cero.")
        except (ValueError, TypeError):
            errors.append("El Presupuesto Mandante debe ser un valor numerico entero valido.")

    costo_val = 0
    costo_str = form.get("costo_base_hotel", "").strip()
    if not costo_str:
        errors.append("El Costo Base Hotel es un campo obligatorio.")
    else:
        try:
            costo_val = int(costo_str)
            if costo_val < 0:
                errors.append("El Costo Base Hotel debe ser un valor numerico mayor o igual a cero.")
        except (ValueError, TypeError):
            errors.append("El Costo Base Hotel debe ser un valor numerico entero valido.")

    tiene_anexo4 = 1 if form.get("tiene_anexo4") in ("1", "true", "on", "yes") else 0
    tiene_escrituras = 1 if form.get("tiene_escrituras") in ("1", "true", "on", "yes") else 0
    tiene_poderes = 1 if form.get("tiene_poderes") in ("1", "true", "on", "yes") else 0
    tiene_vigencias = 1 if form.get("tiene_vigencias") in ("1", "true", "on", "yes") else 0

    fecha_publicacion = form.get("fecha_publicacion", "").strip()
    if not fecha_publicacion:
        errors.append("La Fecha de Publicacion es un campo obligatorio.")

    fecha_cierre = form.get("fecha_cierre", "").strip()
    if not fecha_cierre:
        errors.append("La Fecha de Cierre de Ofertas es un campo obligatorio.")

    descripcion_tdr = form.get("descripcion_tdr", "").strip()

    data = {
        "id_licitacion": id_licitacion,
        "titulo": titulo,
        "organismo": organismo,
        "categoria": categoria,
        "modalidad": modalidad,
        "region": region,
        "presupuesto_mandante": presupuesto_val,
        "costo_base_hotel": costo_val,
        "estado_embudo": estado_embudo,
        "validacion_adjuntos": validacion_adjuntos,
        "tiene_anexo4": tiene_anexo4,
        "tiene_escrituras": tiene_escrituras,
        "tiene_poderes": tiene_poderes,
        "tiene_vigencias": tiene_vigencias,
        "fecha_publicacion": fecha_publicacion,
        "fecha_cierre": fecha_cierre,
        "descripcion_tdr": descripcion_tdr
    }
    return data, errors


# ATENCION: Registrar /licitaciones/nueva ANTES de /licitaciones/<id_licitacion>
# para evitar que Flask confunda 'nueva' con un parametro dinamico de ID.
@app.route("/licitaciones/nueva", methods=["GET", "POST"])
@login_required
def crear_licitacion():
    if request.method == "POST":
        data, errors = parse_and_validate_licitacion_form(request.form, is_create=True)
        if errors:
            for err in errors:
                flash(err, "error")
            form_view_data = dict(data)
            form_view_data["presupuesto_mandante"] = request.form.get("presupuesto_mandante", "")
            form_view_data["costo_base_hotel"] = request.form.get("costo_base_hotel", "")
            return render_template(
                "form.html",
                mode="create",
                lic=form_view_data,
                valid_estados=VALID_ESTADOS,
                user=session.get("user")
            )
        database.create_licitacion(data)
        flash(f"Licitacion {data['id_licitacion']} registrada exitosamente.", "success")
        return redirect(url_for("licitacion_detalle", id_licitacion=data["id_licitacion"]))

    default_lic = {
        "id_licitacion": "",
        "titulo": "",
        "organismo": "",
        "categoria": "Alojamiento",
        "modalidad": "Compra Agil",
        "region": "Region Metropolitana (Santiago)",
        "presupuesto_mandante": "",
        "costo_base_hotel": "",
        "estado_embudo": "Identificada",
        "validacion_adjuntos": "Valida",
        "tiene_anexo4": 1,
        "tiene_escrituras": 1,
        "tiene_poderes": 1,
        "tiene_vigencias": 1,
        "fecha_publicacion": "",
        "fecha_cierre": "",
        "descripcion_tdr": ""
    }
    return render_template(
        "form.html",
        mode="create",
        lic=default_lic,
        valid_estados=VALID_ESTADOS,
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


@app.route("/licitaciones/<id_licitacion>/editar", methods=["GET", "POST"])
@login_required
def editar_licitacion(id_licitacion):
    lic = database.get_licitacion_by_id(id_licitacion)
    if not lic:
        abort(404)

    if request.method == "POST":
        data, errors = parse_and_validate_licitacion_form(request.form, is_create=False, existing_id=id_licitacion)
        if errors:
            for err in errors:
                flash(err, "error")
            form_view_data = dict(data)
            form_view_data["presupuesto_mandante"] = request.form.get("presupuesto_mandante", "")
            form_view_data["costo_base_hotel"] = request.form.get("costo_base_hotel", "")
            return render_template(
                "form.html",
                mode="edit",
                lic=form_view_data,
                valid_estados=VALID_ESTADOS,
                user=session.get("user")
            )
        update_data = dict(data)
        update_data.pop("id_licitacion", None)
        database.update_licitacion(id_licitacion, update_data)
        flash(f"Licitacion {id_licitacion} actualizada exitosamente.", "success")
        return redirect(url_for("licitacion_detalle", id_licitacion=id_licitacion))

    return render_template(
        "form.html",
        mode="edit",
        lic=dict(lic),
        valid_estados=VALID_ESTADOS,
        user=session.get("user")
    )


@app.route("/licitaciones/<id_licitacion>/eliminar", methods=["POST"])
@login_required
def eliminar_licitacion(id_licitacion):
    lic = database.get_licitacion_by_id(id_licitacion)
    if not lic:
        abort(404)
    database.delete_licitacion(id_licitacion)
    flash(f"Licitacion {id_licitacion} eliminada exitosamente.", "success")
    return redirect(url_for("dashboard"))


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

