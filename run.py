"""
Script de inicio para el Asistente Virtual de Licitaciones (Mercado Publico).
Hotel Plaza San Francisco - Programa de Vinculacion con el Medio (VcM) DUOC UC.
"""

import os
import sys

from app import app, USERS, DEMO_PASSWORDS
import database

DEBUG = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "5000") or 5000)


def _es_local(host):
    return host in ("127.0.0.1", "localhost", "::1")


def main():
    """Inicializa la base de datos relacional y ejecuta el servidor web corporativo."""
    print("=" * 72)
    print("  ASISTENTE VIRTUAL PARA LICITACIONES (MERCADO PUBLICO)")
    print("  Hotel Plaza San Francisco | Programa VcM DUOC UC")
    print("=" * 72)
    if not _es_local(HOST):
        if not os.environ.get("FLASK_SECRET_KEY"):
            print("[FAIL] Para exponer el servidor configure FLASK_SECRET_KEY en .env.")
            return 1
        if any(USERS[u]["password"] == p for u, p in DEMO_PASSWORDS.items()):
            print("[FAIL] Para exponer el servidor cambie las claves demo con LICITACIONES_PASSWORD_<USUARIO>.")
            return 1
    print("[INFO] Inicializando motor de persistencia SQLite...")
    database.init_db()
    print("[INFO] Esquema relacional y datos de prueba verificados correctamente.")
    print("[INFO] Arquitectura 100% Web activa. Acceso exclusivo mediante navegador.")
    print("=" * 72)
    print(f"  Punto de Acceso Web: http://{HOST}:{PORT}")
    print("=" * 72)
    print("[INFO] Servidor web iniciado. Presione CTRL+C para detener.")
    print("=" * 72)

    app.run(host=HOST, port=PORT, debug=DEBUG)
    return 0


if __name__ == "__main__":
    sys.exit(main())
