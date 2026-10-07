import hmac
import os
import secrets
import sqlite3
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

VALID_JORNADAS = [
    "Jornada Completa (8 hrs)",
    "Media Jornada Manana (4 hrs)",
    "Media Jornada Tarde (4 hrs)",
    "Nocturno / Cena",
    "Horario Especial"
]

VALID_CATEGORIAS = ["Alojamiento", "Eventos / Catering"]
VALID_MODALIDADES = ["Compra Agil", "Licitacion Publica"]
VALID_ADJUNTOS = ["Valida", "Error ID / Discrepancia"]
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
    ticket_configurado = bool(mercado_publico.get_ticket())

    return render_template(
        "dashboard.html",
        licitaciones=licitaciones,
        metrics=metrics,
        categoria=categoria or "",
        modalidad=modalidad or "",
        estado=estado or "",
        q=q or "",
        ticket_configurado=ticket_configurado,
        user=session.get("user")
    )


def _parse_iso_date(field_label, raw_value, errors):
    if not raw_value:
        errors.append(f"La {field_label} es un campo obligatorio.")
        return None
    try:
        return date.fromisoformat(raw_value)
    except ValueError:
        errors.append(f"La {field_label} debe tener formato AAAA-MM-DD.")
        return None


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
    if categoria not in VALID_CATEGORIAS:
        errors.append(f"Categoria '{categoria}' invalida. Seleccione una categoria valida.")

    modalidad = form.get("modalidad", "").strip() or "Compra Agil"
    if modalidad not in VALID_MODALIDADES:
        errors.append(f"Modalidad '{modalidad}' invalida. Seleccione una modalidad valida.")

    estado_embudo = form.get("estado_embudo", "").strip() or "Identificada"
    if estado_embudo not in VALID_ESTADOS:
        errors.append(f"Estado de embudo '{estado_embudo}' invalido. Seleccione una etapa valida.")

    validacion_adjuntos = form.get("validacion_adjuntos", "").strip() or "Valida"
    if validacion_adjuntos not in VALID_ADJUNTOS:
        errors.append(f"Validacion de adjuntos '{validacion_adjuntos}' invalida. Seleccione una opcion valida.")

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

    tiene_anexo4, tiene_escrituras, tiene_poderes, tiene_vigencias = [
        1 if form.get(k) in ("1", "true", "on", "yes") else 0
        for k in ("tiene_anexo4", "tiene_escrituras", "tiene_poderes", "tiene_vigencias")
    ]

    fecha_publicacion = form.get("fecha_publicacion", "").strip()
    fecha_pub_date = _parse_iso_date("Fecha de Publicacion", fecha_publicacion, errors)

    fecha_cierre = form.get("fecha_cierre", "").strip()
    fecha_cierre_date = _parse_iso_date("Fecha de Cierre de Ofertas", fecha_cierre, errors)

    if fecha_pub_date and fecha_cierre_date and fecha_cierre_date < fecha_pub_date:
        errors.append("La Fecha de Cierre no puede ser anterior a la Fecha de Publicacion.")

    descripcion_tdr = form.get("descripcion_tdr", "").strip()

    # Dimensionamiento operativo: Aforo, Jornada, Horarios y Salon
    cantidad_asistentes_val = 0
    cantidad_asistentes_str = form.get("cantidad_asistentes", "0").strip()
    if cantidad_asistentes_str:
        try:
            cantidad_asistentes_val = int(cantidad_asistentes_str)
            if cantidad_asistentes_val < 0:
                errors.append("La Cantidad de Asistentes debe ser un valor numerico mayor o igual a cero.")
        except (ValueError, TypeError):
            errors.append("La Cantidad de Asistentes debe ser un valor numerico entero.")

    tipo_jornada = form.get("tipo_jornada", "").strip() or "Jornada Completa (8 hrs)"
    if tipo_jornada not in VALID_JORNADAS:
        errors.append(f"Tipo de jornada '{tipo_jornada}' invalido. Seleccione una opcion valida.")

    horario_evento = form.get("horario_evento", "").strip() or "08:30 a 18:30 hrs"
    id_salon_asignado = form.get("id_salon_asignado", "").strip()
    if id_salon_asignado and database.get_salon_by_id(id_salon_asignado) is None:
        errors.append(f"El salon '{id_salon_asignado}' no existe en el catalogo del hotel.")

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
        "descripcion_tdr": descripcion_tdr,
        "cantidad_asistentes": cantidad_asistentes_val,
        "tipo_jornada": tipo_jornada,
        "horario_evento": horario_evento,
        "id_salon_asignado": id_salon_asignado
    }
    return data, errors


# ATENCION: Registrar /licitaciones/nueva ANTES de /licitaciones/<id_licitacion>
# para evitar que Flask confunda 'nueva' con un parametro dinamico de ID.
@app.route("/licitaciones/nueva", methods=["GET", "POST"])
@login_required
def crear_licitacion():
    salones = database.get_all_salones()
    if request.method == "POST":
        data, errors = parse_and_validate_licitacion_form(request.form, is_create=True)
        if not errors:
            try:
                database.create_licitacion(data)
            except sqlite3.IntegrityError:
                errors.append(f"El ID de licitacion '{data['id_licitacion']}' ya existe en el sistema (ID duplicado). Ingrese un identificador unico.")
        if errors:
            for err in errors:
                flash(err, "error") 
            form_view_data = dict(data)
            form_view_data["presupuesto_mandante"] = request.form.get("presupuesto_mandante", "")
            form_view_data["costo_base_hotel"] = request.form.get("costo_base_hotel", "")
            form_view_data["cantidad_asistentes"] = request.form.get("cantidad_asistentes", "0")
            return render_template(
                "form.html",
                mode="create",
                lic=form_view_data,
                salones=salones,
                valid_jornadas=VALID_JORNADAS,
                valid_estados=VALID_ESTADOS,
                user=session.get("user")
            )
        flash(f"Licitacion {data['id_licitacion']} registrada exitosamente.", "success")
        return redirect(url_for("licitacion_detalle", id_licitacion=data["id_licitacion"]))

    default_lic = {
        "id_licitacion": "",
        "titulo": "",
        "organismo": "",
        "categoria": "Eventos / Catering",
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
        "descripcion_tdr": "",
        "cantidad_asistentes": 0,
        "tipo_jornada": "Jornada Completa (8 hrs)",
        "horario_evento": "08:30 a 18:30 hrs",
        "id_salon_asignado": ""
    }
    return render_template(
        "form.html",
        mode="create",
        lic=default_lic,
        salones=salones,
        valid_jornadas=VALID_JORNADAS,
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
        valid_estados=VALID_ESTADOS,
        user=session.get("user")
    )


@app.route("/licitaciones/<id_licitacion>/editar", methods=["GET", "POST"])
@login_required
def editar_licitacion(id_licitacion):
    lic = database.get_licitacion_by_id(id_licitacion)
    if not lic:
        abort(404)

    salones = database.get_all_salones()
    if request.method == "POST":
        data, errors = parse_and_validate_licitacion_form(request.form, is_create=False, existing_id=id_licitacion)
        if errors:
            for err in errors:
                flash(err, "error")
            form_view_data = dict(data)
            form_view_data["presupuesto_mandante"] = request.form.get("presupuesto_mandante", "")
            form_view_data["costo_base_hotel"] = request.form.get("costo_base_hotel", "")
            form_view_data["cantidad_asistentes"] = request.form.get("cantidad_asistentes", "0")
            return render_template(
                "form.html",
                mode="edit",
                lic=form_view_data,
                salones=salones,
                valid_jornadas=VALID_JORNADAS,
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
        salones=salones,
        valid_jornadas=VALID_JORNADAS,
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
    reservas = database.get_all_reservas(id_salon=filtro_salon, q=q)

    total_salones = len(salones)
    total_reservas = len(reservas)
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

