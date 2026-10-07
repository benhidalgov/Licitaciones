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
        flask_app.app.config["CSRF_ENABLED"] = False
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

    def test_get_reserva_by_id(self):
        # Existing seed reservation
        reserva = database.get_reserva_by_id(1)
        self.assertIsNotNone(reserva)
        self.assertEqual(reserva["id_salon"], "SALON-ALAMEDA")
        self.assertEqual(reserva["organismo_o_empresa"], "Subsecretaria de Turismo")

        # Non-existent
        res_null = database.get_reserva_by_id(99999)
        self.assertIsNone(res_null)

    def test_update_reserva(self):
        update_data = {
            "cliente_evento": "Jornada Actualizada",
            "asistentes_estimados": 95,
            "estado_reserva": "Confirmada"
        }
        success = database.update_reserva(1, update_data)
        self.assertTrue(success)

        reserva = database.get_reserva_by_id(1)
        self.assertEqual(reserva["cliente_evento"], "Jornada Actualizada")
        self.assertEqual(reserva["asistentes_estimados"], 95)

    def test_delete_reserva(self):
        # Create a temp reservation and delete it
        temp_id = database.create_reserva({
            "id_salon": "SALON-DIRECTORIO",
            "cliente_evento": "Reunion Temporal",
            "organismo_o_empresa": "Empresa Test",
            "tipo_evento": "Reunion",
            "fecha_inicio": "2026-11-20",
            "fecha_fin": "2026-11-20",
            "horario": "10:00 a 12:00 hrs"
        })
        self.assertIsNotNone(database.get_reserva_by_id(temp_id))
        deleted = database.delete_reserva(temp_id)
        self.assertTrue(deleted)
        self.assertIsNone(database.get_reserva_by_id(temp_id))

    def test_conflictos_reserva_exclude_self(self):
        # Reservation 1 is on 2026-09-20 in SALON-ALAMEDA
        conflictos = database.get_conflictos_reserva("SALON-ALAMEDA", "2026-09-20", "2026-09-20")
        self.assertEqual(len(conflictos), 1)

        # Excluding self (id_reserva = 1) should yield no conflicts
        conflictos_self = database.get_conflictos_reserva("SALON-ALAMEDA", "2026-09-20", "2026-09-20", exclude_id_reserva=1)
        self.assertEqual(len(conflictos_self), 0)

    def test_crear_reserva_get_view(self):
        response = self.client.get("/reservas/nueva?salon=SALON-ALAMEDA&licitacion=1058-12-COT24")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Registrar Nueva Reserva", html)
        self.assertIn("SALON-ALAMEDA", html)
        self.assertIn("1058-12-COT24", html)

    def test_crear_reserva_post_success(self):
        payload = {
            "id_salon": "SALON-COLONIAL",
            "cliente_evento": "Cena de Gala Anual",
            "organismo_o_empresa": "Asociacion de Hoteleria",
            "tipo_evento": "Banquete",
            "fecha_inicio": "2026-11-10",
            "fecha_fin": "2026-11-10",
            "horario": "19:00 a 23:30 hrs",
            "asistentes_estimados": "120",
            "estado_reserva": "Confirmada",
            "id_licitacion": "",
            "contacto_responsable": "Maria Lopez",
            "observaciones": "Montaje en mesas redondas de 10 personas"
        }
        response = self.client.post("/reservas/nueva", data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Cena de Gala Anual", html)
        self.assertIn("Asociacion de Hoteleria", html)

    def test_crear_reserva_post_invalid_dates(self):
        payload = {
            "id_salon": "SALON-COLONIAL",
            "cliente_evento": "Evento Fechas Invalidas",
            "organismo_o_empresa": "Organismo Test",
            "tipo_evento": "Banquete",
            "fecha_inicio": "2026-11-20",
            "fecha_fin": "2026-11-10",  # Fin antes de inicio
            "horario": "10:00 hrs",
            "asistentes_estimados": "50",
            "estado_reserva": "Confirmada"
        }
        response = self.client.post("/reservas/nueva", data=payload)
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("fecha de inicio no puede ser posterior", html)

    def test_crear_reserva_post_collision_warning(self):
        # 2026-09-20 already has Subsecretaria de Turismo in SALON-ALAMEDA
        payload = {
            "id_salon": "SALON-ALAMEDA",
            "cliente_evento": "Evento Colisionante",
            "organismo_o_empresa": "Entidad Competidora",
            "tipo_evento": "Seminario",
            "fecha_inicio": "2026-09-20",
            "fecha_fin": "2026-09-20",
            "horario": "10:00 hrs",
            "asistentes_estimados": "40",
            "estado_reserva": "Confirmada"
        }
        response = self.client.post("/reservas/nueva", data=payload)
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Conflicto de disponibilidad", html)

    def test_editar_reserva_get_and_post(self):
        # GET edit
        get_resp = self.client.get("/reservas/1/editar")
        self.assertEqual(get_resp.status_code, 200)
        get_html = get_resp.data.decode("utf-8")
        self.assertIn("Editar Reserva", get_html)
        self.assertIn("Subsecretaria de Turismo", get_html)

        # POST edit
        edit_payload = {
            "id_salon": "SALON-ALAMEDA",
            "cliente_evento": "Jornada Estrategica Modificada",
            "organismo_o_empresa": "Subsecretaria de Turismo Actualizada",
            "tipo_evento": "Planificacion",
            "fecha_inicio": "2026-09-20",
            "fecha_fin": "2026-09-20",
            "horario": "08:30 a 19:00 hrs",
            "asistentes_estimados": "80",
            "estado_reserva": "Confirmada",
            "id_licitacion": "1058-12-COT24",
            "contacto_responsable": "Claudia Morales",
            "observaciones": "Actualizado para jornada extendida"
        }
        post_resp = self.client.post("/reservas/1/editar", data=edit_payload, follow_redirects=True)
        self.assertEqual(post_resp.status_code, 200)
        post_html = post_resp.data.decode("utf-8")
        self.assertIn("Jornada Estrategica Modificada", post_html)

    def test_eliminar_reserva_post(self):
        # Create temp reservation to delete
        temp_id = database.create_reserva({
            "id_salon": "SALON-LONDRES",
            "cliente_evento": "Evento Para Eliminar",
            "organismo_o_empresa": "Organismo X",
            "tipo_evento": "Taller",
            "fecha_inicio": "2026-12-01",
            "fecha_fin": "2026-12-01",
            "horario": "10:00 hrs"
        })
        del_resp = self.client.post(f"/reservas/{temp_id}/eliminar", follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)
        self.assertIsNone(database.get_reserva_by_id(temp_id))

    def test_reservar_desde_licitacion_button_rendered(self):
        # In detail view of 1058-12-COT24 (which has SALON-ALAMEDA assigned)
        resp = self.client.get("/licitaciones/1058-12-COT24")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("/reservas/nueva", html)

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
            os.path.join(repo_root, "templates", "reserva_form.html"),
        ]
        for fpath in target_files:
            if os.path.exists(fpath):
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
            os.path.join(repo_root, "templates", "reserva_form.html"),
        ]
        forbidden = "".join(["a", "i", "o", "p", "s"])
        for fpath in target_files:
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.assertNotIn(
                        forbidden,
                        content.lower(),
                        f"El archivo {fpath} contiene el termino prohibido."
                    )


if __name__ == "__main__":
    unittest.main()

