import os
import re
import unittest
import app as flask_app
import database


class TestSalones(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_salones_licitaciones.db"
        database.DB_NAME = self.db_name
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass
        database.init_db()

        flask_app.app.config["TESTING"] = True
        flask_app.app.config["SECRET_KEY"] = "test-salones-secret"
        self.client = flask_app.app.test_client()
        with self.client.session_transaction() as sess:
            sess["user"] = "admin"

    def tearDown(self):
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass

    def test_salones_catalog_unauthenticated(self):
        unauth_client = flask_app.app.test_client()
        response = unauth_client.get("/salones")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_salones_catalog_view(self):
        response = self.client.get("/salones")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        # Titles and metric cards
        self.assertIn("Catalogo de Salones y Agenda de Ocupacion", html)
        self.assertIn("Capacidad Total", html)
        self.assertIn("Reservas Activas", html)

        # Salon names
        self.assertIn("Gran Salon San Francisco (Plenario)", html)
        self.assertIn("Salon Colonial", html)
        self.assertIn("Salon Alameda", html)
        self.assertIn("Salon Londres", html)
        self.assertIn("Salon Directorio Ejecutivo", html)

        # Reservation agenda items
        self.assertIn("Subsecretaria de Turismo", html)
        self.assertIn("Gobierno Regional Metropolitano de Santiago (GORE)", html)
        self.assertIn("Banco Central de Chile", html)

    def test_salon_detail_view(self):
        response = self.client.get("/salones/SALON-PLENARIO")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        self.assertIn("Gran Salon San Francisco (Plenario)", html)
        self.assertIn("Plenario / Conferencia", html)
        self.assertIn("300", html)
        self.assertIn("Nivel Subterraneo - Centro de Convenciones", html)
        self.assertIn("Pantalla LED 4K", html)
        self.assertIn("Agenda de Ocupacion", html)
        self.assertIn("Fechas de Ocupacion", html)
        self.assertIn("Cliente / Organismo (Booked Por)", html)

    def test_salon_detail_404(self):
        response = self.client.get("/salones/SALON-INEXISTENTE")
        self.assertEqual(response.status_code, 404)

    def test_reservas_filter_by_salon(self):
        response = self.client.get("/salones?salon=SALON-ALAMEDA")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        self.assertIn("Salon Alameda", html)
        self.assertIn("Subsecretaria de Turismo", html)
        # Should not show Banco Central de Chile which is in Salon Colonial
        self.assertNotIn("Banco Central de Chile", html)

    def test_reservas_search_query(self):
        response = self.client.get("/salones?q=Turismo")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        self.assertIn("Subsecretaria de Turismo", html)
        self.assertNotIn("SOFOFA", html)

    def test_conflictos_reserva_logic(self):
        # 2026-09-20 has a reservation for Subsecretaria de Turismo in SALON-ALAMEDA
        conflictos = database.get_conflictos_reserva("SALON-ALAMEDA", "2026-09-20", "2026-09-20")
        self.assertEqual(len(conflictos), 1)
        self.assertEqual(conflictos[0]["organismo_o_empresa"], "Subsecretaria de Turismo")

        # Date without reservation
        sin_conflicto = database.get_conflictos_reserva("SALON-ALAMEDA", "2026-11-01", "2026-11-01")
        self.assertEqual(len(sin_conflicto), 0)

    def test_create_reserva(self):
        new_reserva_data = {
            "id_salon": "SALON-LONDRES",
            "cliente_evento": "Taller de Auditoria de Procesos",
            "organismo_o_empresa": "Contraloria General",
            "tipo_evento": "Capacitacion Tecnica",
            "fecha_inicio": "2026-11-15",
            "fecha_fin": "2026-11-15",
            "horario": "09:00 a 17:00 hrs",
            "asistentes_estimados": 30,
            "estado_reserva": "Confirmada",
            "id_licitacion": "CONT-2026-01",
            "contacto_responsable": "Equipo de Auditoria",
            "observaciones": "Requiere proyector y estacion de cafe."
        }
        reserva_id = database.create_reserva(new_reserva_data)
        self.assertIsInstance(reserva_id, int)
        self.assertGreater(reserva_id, 0)

        reservas_londres = database.get_reservas_by_salon("SALON-LONDRES")
        nombres_eventos = [r["cliente_evento"] for r in reservas_londres]
        self.assertIn("Taller de Auditoria de Procesos", nombres_eventos)

    def test_salones_templates_and_code_have_zero_emojis(self):
        emoji_pattern = re.compile(
            "[\U00010000-\U0010ffff]|"
            "[\u2600-\u27bf]|"
            "[\u2300-\u23ff]|"
            "[\u2b50\u2b55\u2934\u2935\u25aa\u25ab\u25b6\u25c0\u25fb-\u25fe]"
        )
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        target_files = [
            os.path.join(repo_root, "templates", "salones.html"),
            os.path.join(repo_root, "templates", "salon_detail.html"),
        ]
        for fpath in target_files:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
                matches = emoji_pattern.findall(content)
                self.assertEqual(
                    matches,
                    [],
                    f"Se detectaron emojis prohibidos en {fpath}: {matches}"
                )

    def test_salones_no_prohibited_terms(self):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        target_files = [
            os.path.join(repo_root, "templates", "salones.html"),
            os.path.join(repo_root, "templates", "salon_detail.html"),
        ]
        forbidden = "".join(["a", "i", "o", "p", "s"])
        for fpath in target_files:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertNotIn(
                    forbidden,
                    content.lower(),
                    f"El archivo {fpath} contiene el termino prohibido."
                )


if __name__ == "__main__":
    unittest.main()
