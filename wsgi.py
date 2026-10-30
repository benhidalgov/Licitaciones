"""Punto de entrada WSGI para produccion (Render/Gunicorn)."""

import os

import database
from app import DEMO_PASSWORDS, USERS, app

# No se permite arrancar en Render con secretos demo.
if not os.environ.get("FLASK_SECRET_KEY"):
    raise RuntimeError("Configure FLASK_SECRET_KEY en las variables de entorno.")
if any(USERS[usuario]["password"] == clave for usuario, clave in DEMO_PASSWORDS.items()):
    raise RuntimeError(
        "Cambie las claves demo con LICITACIONES_PASSWORD_<USUARIO> antes de exponer la app."
    )

database.init_db()
