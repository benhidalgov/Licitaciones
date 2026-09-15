"""
Script de inicio para el Asistente Virtual de Licitaciones (Mercado Publico).
Hotel Plaza San Francisco - Programa de Vinculacion con el Medio (VcM) DUOC UC.
"""

from app import app, DEMO_USER, DEMO_PASS
import database


def main():
    """Inicializa la base de datos relacional y ejecuta el servidor web corporativo."""
    print("=" * 72)
    print("  ASISTENTE VIRTUAL PARA LICITACIONES (MERCADO PUBLICO)")
    print("  Hotel Plaza San Francisco | Programa VcM DUOC UC")
    print("=" * 72)
    print("[INFO] Inicializando motor de persistencia SQLite...")
    database.init_db()
    print("[INFO] Esquema relacional y datos de prueba verificados correctamente.")
    print("[INFO] Arquitectura 100% Web activa. Acceso exclusivo mediante navegador.")
    print("=" * 72)
    print("  Punto de Acceso Web: http://127.0.0.1:5000")
    print("  Credenciales de Demostracion:")
    print(f"    - Usuario:         {DEMO_USER}")
    print(f"    - Contrasena:      {DEMO_PASS}")
    print("=" * 72)
    print("[INFO] Servidor web iniciado en modo local. Presione CTRL+C para detener.")
    print("=" * 72)

    app.run(host="127.0.0.1", port=5000, debug=True)


if __name__ == "__main__":
    main()
