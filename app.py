import hmac
import os
import secrets
import time
from datetime import date
from functools import wraps
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
import database
import mercado_publico

mercado_publico.load_env_file()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "licitaciones-secret-key-2026")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_COOKIE_SECURE", "") == "1"
app.config["CSRF_ENABLED"] = True
app.config["LOGIN_RATE_LIMIT"] = 5
app.config["LOGIN_RATE_WINDOW"] = 300

DEMO_USER = "admin"
DEMO_PASS = "admin123"

VALID_ESTADOS = [
    "Identificada",
    "Calificada",
    "Participada",
    "Adjudicada",
    "Descartada"
]

VALID_ESTADOS_RESERVA = ["Confirmada", "Tentativa", "Bloqueo Interno"]


@app.context_processor
def inject_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return {"csrf_token": session["csrf_token"]}


@app.before_request
def verify_csrf_token():
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return None
    if not app.config.get("CSRF_ENABLED", True):
        return None
    token = request.form.get("csrf_token", "")
    expected = session.get("csrf_token", "")
    if not token or not expected or not hmac.compare_digest(token.encode("utf-8"), expected.encode("utf-8")):
        return ("Token de seguridad ausente o invalido. Recargue la pagina e intente nuevamente.", 400)
    return None


_login_attempts = {}


def _is_login_blocked(ip):
    now = time.monotonic()
    entry = _login_attempts.get(ip)
    if not entry:
        return False
    count, started = entry
    if now - started >= app.config["LOGIN_RATE_WINDOW"]:
        _login_attempts.pop(ip, None)
        return False
    return count >= app.config["LOGIN_RATE_LIMIT"]


def _record_login_failure(ip):
    now = time.monotonic()
    entry = _login_attempts.get(ip)
    if not entry or now - entry[1] >= app.config["LOGIN_RATE_WINDOW"]:
        _login_attempts[ip] = (1, now)
    else:
        _login_attempts[ip] = (entry[0] + 1, entry[1])


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
        ip = request.remote_addr or "desconocido"
        if _is_login_blocked(ip):
            flash("Demasiados intentos fallidos. Espere unos minutos antes de volver a intentar.", "error")
            return render_template("login.html"), 429
        user = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user_ok = hmac.compare_digest(user.encode("utf-8"), DEMO_USER.encode("utf-8"))
        pass_ok = hmac.compare_digest(password.encode("utf-8"), DEMO_PASS.encode("utf-8"))
        if user_ok and pass_ok:
            _login_attempts.pop(ip, None)
            session["user"] = user
            flash("Sesion iniciada correctamente.", "info")
            return redirect(url_for("dashboard"))
        _record_login_failure(ip)
        flash("Credenciales invalidas. Ingrese las credenciales de prueba proporcionadas.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    flash("Ha cerrado sesion correctamente.", "info")
    return redirect(url_for("login"))


@app.template_filter("clp")
def format_clp(value):
    if value is None or value == "":
        return "$0 CLP"
    try:
        val = int(value)
        return f"-${abs(val):,} CLP".replace(",", ".") if val < 0 else f"${val:,} CLP".replace(",", ".")
    except (ValueError, TypeError):
        return f"${value} CLP"


app.jinja_env.globals["format_clp"] = format_clp


@app.template_filter("miles")
def format_miles(value):
    """Separador de miles estilo chileno: 1234567 -> 1.234.567"""
    try:
        return f"{int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(value)


MAX_PAGINA = 25


@app.route("/")
@app.route("/licitaciones")
@login_required
def dashboard():
    categoria = request.args.get("categoria", "").strip() or None
    modalidad = request.args.get("modalidad", "").strip() or None
    estado = request.args.get("estado", "").strip() or None
    q = request.args.get("q", "").strip() or None

    # Filtros no vacios, reutilizados para construir los enlaces del paginador
    filtros = {
        k: v for k, v in dict(categoria=categoria, modalidad=modalidad, estado=estado, q=q).items()
        if v
    }

    total = database.count_licitaciones(**filtros)
    paginas = max(1, -(-total // MAX_PAGINA))  # division entera hacia arriba
    pagina = min(max(1, request.args.get("pagina", 1, type=int)), paginas)

    licitaciones = database.get_all_licitaciones(
        limit=MAX_PAGINA,
        offset=(pagina - 1) * MAX_PAGINA,
        **filtros
    )
    metrics = database.get_funnel_metrics()
    ticket_configurado = bool(mercado_publico.get_ticket())
    tope_compra_agil = database.get_tope_compra_agil()

    return render_template(
        "dashboard.html",
        licitaciones=licitaciones,
        metrics=metrics,
        categoria=categoria or "",
        modalidad=modalidad or "",
        estado=estado or "",
        q=q or "",
        total=total,
        pagina=pagina,
        paginas=paginas,
        filtros=filtros,
        ticket_configurado=ticket_configurado,
        tope_compra_agil=tope_compra_agil,
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

    # Dimensionamiento de Capacidad, Aforo y Salones
    salones = database.get_all_salones()
    asistentes = lic.get("cantidad_asistentes") or 0
    salon_id = lic.get("id_salon_asignado") or ""
    salon_asignado = database.get_salon_by_id(salon_id) if salon_id else None

    excede_aforo = False
    sobrecupo = 0
    if salon_asignado and asistentes > 0:
        capacidad_max = salon_asignado["capacidad_maxima"]
        if asistentes > capacidad_max:
            excede_aforo = True
            sobrecupo = asistentes - capacidad_max

    salones_compatibles = []
    if asistentes > 0:
        salones_compatibles = database.get_salones_aptos(asistentes)

    # Cruce de agenda y disponibilidad con reservas existentes
    conflictos_agenda = []
    if salon_id and lic.get("fecha_cierre"):
        fecha_ref = lic["fecha_cierre"]
        conflictos_agenda = database.get_conflictos_reserva(salon_id, fecha_ref, fecha_ref)

    return render_template(
        "detail.html",
        lic=lic,
        diferencia=diferencia,
        es_inviable=es_inviable,
        deficit=deficit,
        margen_porcentaje=margen_porcentaje,
        salon_asignado=salon_asignado,
        excede_aforo=excede_aforo,
        sobrecupo=sobrecupo,
        salones_compatibles=salones_compatibles,
        conflictos_agenda=conflictos_agenda,
        salones=salones,
        tope_compra_agil=database.get_tope_compra_agil(),
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


@app.route("/ajustes/tope_compra_agil", methods=["POST"])
@login_required
def guardar_tope_compra_agil():
    # Acepta formato chileno ("6.900.000") y numerico plano ("6900000")
    bruto = request.form.get("tope_compra_agil", "")
    digitos = bruto.replace(".", "").replace("$", "").replace(" ", "")
    try:
        valor = int(digitos)
    except ValueError:
        valor = 0
    if valor <= 0:
        flash("El tope de Compra Agil debe ser un numero entero mayor a cero.", "error")
    else:
        database.set_tope_compra_agil(valor)
        flash(f"Tope de Compra Agil actualizado a {format_clp(valor)}.", "success")
    return redirect(url_for("dashboard"))


@app.route("/licitaciones/sincronizar", methods=["GET", "POST"])
@login_required
def sincronizar_licitaciones_route():
    fecha = request.form.get("fecha", "").strip() or request.args.get("fecha", "").strip() or None
    resumen = mercado_publico.sincronizar_licitaciones(fecha=fecha)
    if resumen.get("total_guardadas", 0) > 0:
        flash(f"[OK] {resumen['mensaje']}", "success")
    elif resumen.get("total_consultadas", 0) > 0:
        flash(f"[INFO] {resumen['mensaje']}", "info")
    else:
        flash(f"[WARN] {resumen['mensaje']}", "warning")
    return redirect(url_for("dashboard"))


@app.route("/salones")
@login_required
def salones_catalogo():
    salones = database.get_all_salones()
    filtro_salon = request.args.get("salon", "").strip() or None
    q = request.args.get("q", "").strip() or None

    filtros = dict(id_salon=filtro_salon, q=q)
    filtros = {k: v for k, v in filtros.items() if v}

    total_reservas = database.count_reservas(**filtros)
    paginas = max(1, -(-total_reservas // MAX_PAGINA))
    pagina = min(max(1, request.args.get("pagina", 1, type=int)), paginas)

    reservas = database.get_all_reservas(
        limit=MAX_PAGINA,
        offset=(pagina - 1) * MAX_PAGINA,
        **filtros
    )

    total_salones = len(salones)
    capacidad_total = sum(s["capacidad_maxima"] for s in salones)

    return render_template(
        "salones.html",
        salones=salones,
        reservas=reservas,
        filtro_salon=filtro_salon or "",
        q=q or "",
        total_salones=total_salones,
        total_reservas=total_reservas,
        capacidad_total=capacidad_total,
        pagina=pagina,
        paginas=paginas,
        filtros={k: v for k, v in {"salon": filtro_salon, "q": q}.items() if v},
        user=session.get("user")
    )


@app.route("/salones/<id_salon>")
@login_required
def salon_detalle(id_salon):
    salon = database.get_salon_detalle(id_salon)
    if not salon:
        abort(404)
    return render_template(
        "salon_detail.html",
        salon=salon,
        user=session.get("user")
    )


def parse_and_validate_reserva_form(form, exclude_id_reserva=None):
    id_salon = form.get("id_salon", "").strip()
    cliente_evento = form.get("cliente_evento", "").strip()
    organismo_o_empresa = form.get("organismo_o_empresa", "").strip()
    tipo_evento = form.get("tipo_evento", "").strip()
    fecha_inicio = form.get("fecha_inicio", "").strip()
    fecha_fin = form.get("fecha_fin", "").strip()
    horario = form.get("horario", "").strip()
    asistentes_str = form.get("asistentes_estimados", "0").strip()
    estado_reserva = form.get("estado_reserva", "Confirmada").strip()
    id_licitacion = form.get("id_licitacion", "").strip()
    contacto_responsable = form.get("contacto_responsable", "").strip()
    observaciones = form.get("observaciones", "").strip()

    errors = []
    if not id_salon:
        errors.append("Debe seleccionar un salon del hotel.")
    elif database.get_salon_by_id(id_salon) is None:
        errors.append("El salon seleccionado no existe en el catalogo del hotel.")
    if not cliente_evento:
        errors.append("Debe indicar el nombre o descripcion del evento.")
    if not organismo_o_empresa:
        errors.append("Debe indicar el organismo mandante o empresa cliente.")
    if not fecha_inicio or not fecha_fin:
        errors.append("Debe especificar la fecha de inicio y de termino del evento.")
    else:
        try:
            d_inicio = date.fromisoformat(fecha_inicio)
            d_fin = date.fromisoformat(fecha_fin)
            if d_inicio > d_fin:
                errors.append("La fecha de inicio no puede ser posterior a la fecha de fin.")
        except ValueError:
            errors.append("Las fechas deben tener formato AAAA-MM-DD.")
    if id_licitacion and database.get_licitacion_by_id(id_licitacion) is None:
        errors.append("La licitacion vinculada no existe en el sistema.")

    asistentes = 0
    if asistentes_str:
        try:
            asistentes = int(asistentes_str)
            if asistentes < 0:
                errors.append("La cantidad de asistentes estimados no puede ser negativa.")
        except (ValueError, TypeError):
            errors.append("La cantidad de asistentes debe ser un numero entero valido.")

    if estado_reserva not in VALID_ESTADOS_RESERVA:
        errors.append(f"Estado de reserva '{estado_reserva}' invalido. Seleccione una etapa valida.")

    if not errors:
        conflictos = database.get_conflictos_reserva(
            id_salon, fecha_inicio, fecha_fin, exclude_id_reserva=exclude_id_reserva
        )
        if conflictos and estado_reserva == "Confirmada":
            conflictos_nombres = ", ".join(f"{c['organismo_o_empresa']} ({c['fecha_inicio']})" for c in conflictos[:3])
            errors.append(f"Conflicto de disponibilidad detectado: El salon ya registra {len(conflictos)} evento(s) en esas fechas ({conflictos_nombres}).")

    form_data = {
        "id_salon": id_salon,
        "cliente_evento": cliente_evento,
        "organismo_o_empresa": organismo_o_empresa,
        "tipo_evento": tipo_evento,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "horario": horario,
        "asistentes_estimados": asistentes,
        "estado_reserva": estado_reserva,
        "id_licitacion": id_licitacion,
        "contacto_responsable": contacto_responsable,
        "observaciones": observaciones
    }
    return form_data, errors


@app.route("/reservas/nueva", methods=["GET", "POST"])
@login_required
def crear_reserva():
    salones = database.get_all_salones()
    licitaciones = database.get_all_licitaciones()

    if request.method == "POST":
        form_data, errors = parse_and_validate_reserva_form(request.form)
        if errors:
            for err in errors:
                flash(err, "error")
            return render_template(
                "reserva_form.html",
                mode="create",
                reserva=form_data,
                salones=salones,
                licitaciones=licitaciones,
                valid_estados_reserva=VALID_ESTADOS_RESERVA,
                user=session.get("user")
            )

        database.create_reserva(form_data)
        flash("Reserva registrada exitosamente en la agenda del hotel.", "success")
        return redirect(url_for("salones_catalogo"))

    pre_salon = request.args.get("salon", "").strip()
    pre_lic_id = request.args.get("licitacion", "").strip()
    pre_fecha_inicio = request.args.get("fecha_inicio", "").strip()
    pre_fecha_fin = request.args.get("fecha_fin", "").strip()

    reserva_init = {
        "id_salon": pre_salon,
        "cliente_evento": "",
        "organismo_o_empresa": "",
        "tipo_evento": "Reunion / Seminario",
        "fecha_inicio": pre_fecha_inicio,
        "fecha_fin": pre_fecha_fin or pre_fecha_inicio,
        "horario": "08:30 a 18:30 hrs",
        "asistentes_estimados": 0,
        "estado_reserva": "Confirmada",
        "id_licitacion": pre_lic_id,
        "contacto_responsable": "",
        "observaciones": ""
    }

    if pre_lic_id:
        lic = database.get_licitacion_by_id(pre_lic_id)
        if lic:
            reserva_init["cliente_evento"] = lic.get("titulo", "")
            reserva_init["organismo_o_empresa"] = lic.get("organismo", "")
            reserva_init["asistentes_estimados"] = lic.get("cantidad_asistentes", 0)
            reserva_init["horario"] = lic.get("horario_evento", "08:30 a 18:30 hrs") or "08:30 a 18:30 hrs"
            if not pre_salon and lic.get("id_salon_asignado"):
                reserva_init["id_salon"] = lic.get("id_salon_asignado")
            if not pre_fecha_inicio and lic.get("fecha_cierre"):
                reserva_init["fecha_inicio"] = lic.get("fecha_cierre")
                reserva_init["fecha_fin"] = lic.get("fecha_cierre")

    return render_template(
        "reserva_form.html",
        mode="create",
        reserva=reserva_init,
        salones=salones,
        licitaciones=licitaciones,
        valid_estados_reserva=VALID_ESTADOS_RESERVA,
        user=session.get("user")
    )


@app.route("/reservas/<int:id_reserva>/editar", methods=["GET", "POST"])
@login_required
def editar_reserva(id_reserva):
    reserva = database.get_reserva_by_id(id_reserva)
    if not reserva:
        abort(404)

    salones = database.get_all_salones()
    licitaciones = database.get_all_licitaciones()

    if request.method == "POST":
        form_data, errors = parse_and_validate_reserva_form(request.form, exclude_id_reserva=id_reserva)
        if errors:
            for err in errors:
                flash(err, "error")
            view_data = dict(form_data)
            view_data["id_reserva"] = id_reserva
            return render_template(
                "reserva_form.html",
                mode="edit",
                reserva=view_data,
                salones=salones,
                licitaciones=licitaciones,
                valid_estados_reserva=VALID_ESTADOS_RESERVA,
                user=session.get("user")
            )

        database.update_reserva(id_reserva, form_data)
        flash("Reserva actualizada exitosamente en la agenda.", "success")
        return redirect(url_for("salones_catalogo"))

    return render_template(
        "reserva_form.html",
        mode="edit",
        reserva=reserva,
        salones=salones,
        licitaciones=licitaciones,
        valid_estados_reserva=VALID_ESTADOS_RESERVA,
        user=session.get("user")
    )


@app.route("/reservas/<int:id_reserva>/eliminar", methods=["POST"])
@login_required
def eliminar_reserva(id_reserva):
    reserva = database.get_reserva_by_id(id_reserva)
    if not reserva:
        abort(404)
    database.delete_reserva(id_reserva)
    flash(f"La reserva para '{reserva.get('cliente_evento')}' ha sido eliminada de la agenda.", "info")
    return redirect(url_for("salones_catalogo"))


@app.errorhandler(404)

def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    database.init_db()
    debug_mode = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(debug=debug_mode, host="127.0.0.1", port=5000)

