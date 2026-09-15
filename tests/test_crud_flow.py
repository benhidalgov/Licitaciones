import os
import re
import unittest
import app as flask_app
import database


class TestCrudFlow(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_crud_licitaciones.db"
        database.DB_NAME = self.db_name
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass
        database.init_db()

        flask_app.app.config["TESTING"] = True
        flask_app.app.config["SECRET_KEY"] = "test-crud-secret"
        self.client = flask_app.app.test_client()
        with self.client.session_transaction() as sess:
            sess["user"] = "admin"

    def tearDown(self):
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass

    def test_unauthenticated_access_blocked(self):
        unauth = flask_app.app.test_client()
        # GET /licitaciones/nueva
        r1 = unauth.get("/licitaciones/nueva")
        self.assertEqual(r1.status_code, 302)
        self.assertIn("/login", r1.headers["Location"])

        # POST /licitaciones/nueva
        r2 = unauth.post("/licitaciones/nueva", data={"titulo": "Test"})
        self.assertEqual(r2.status_code, 302)
        self.assertIn("/login", r2.headers["Location"])

        # GET /licitaciones/1058-12-COT24/editar
        r3 = unauth.get("/licitaciones/1058-12-COT24/editar")
        self.assertEqual(r3.status_code, 302)
        self.assertIn("/login", r3.headers["Location"])

        # POST /licitaciones/1058-12-COT24/editar
        r4 = unauth.post("/licitaciones/1058-12-COT24/editar", data={"titulo": "Test"})
        self.assertEqual(r4.status_code, 302)
        self.assertIn("/login", r4.headers["Location"])

        # POST /licitaciones/1058-12-COT24/eliminar
        r5 = unauth.post("/licitaciones/1058-12-COT24/eliminar")
        self.assertEqual(r5.status_code, 302)
        self.assertIn("/login", r5.headers["Location"])

    def test_create_licitacion_get(self):
        response = self.client.get("/licitaciones/nueva")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        # Routing check: must not hit detail view or return 404
        self.assertIn("Registrar Nueva Licitacion", html)
        self.assertIn("Guardar Licitacion", html)
        self.assertIn("Cancelar", html)

        # Six structured sections checks
        self.assertIn("Identificacion y Organismo", html)
        self.assertIn("Categoria y Modalidad", html)
        self.assertIn("Evaluacion Economica", html)
        self.assertIn("Fechas Criticas", html)
        self.assertIn("Validacion Robusta y Checklist de Admisibilidad", html)
        self.assertIn("Descripcion o Extracto de TDR", html)

        # Checkbox fields
        self.assertIn("tiene_anexo4", html)
        self.assertIn("tiene_escrituras", html)
        self.assertIn("tiene_poderes", html)
        self.assertIn("tiene_vigencias", html)

    def test_create_licitacion_post_success(self):
        payload = {
            "id_licitacion": "5555-22-COT26",
            "titulo": "Servicio de Coctel para Bienvenida de Alumnos",
            "organismo": "DUOC UC Casa Central",
            "categoria": "Eventos / Catering",
            "modalidad": "Compra Agil",
            "region": "Region Metropolitana (Santiago)",
            "presupuesto_mandante": "4500000",
            "costo_base_hotel": "3200000",
            "estado_embudo": "Identificada",
            "validacion_adjuntos": "Valida",
            "tiene_anexo4": "1",
            "tiene_escrituras": "1",
            "tiene_poderes": "1",
            "tiene_vigencias": "1",
            "fecha_publicacion": "2026-09-15",
            "fecha_cierre": "2026-09-22",
            "descripcion_tdr": "Banqueteria protocolar para autoridades."
        }
        response = self.client.post("/licitaciones/nueva", data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        # Redirection to detail page
        self.assertIn("5555-22-COT26", html)
        self.assertIn("Servicio de Coctel para Bienvenida de Alumnos", html)

        # Database verification
        item = database.get_licitacion_by_id("5555-22-COT26")
        self.assertIsNotNone(item)
        self.assertEqual(item["titulo"], "Servicio de Coctel para Bienvenida de Alumnos")
        self.assertEqual(item["presupuesto_mandante"], 4500000)
        self.assertEqual(item["costo_base_hotel"], 3200000)
        self.assertEqual(item["tiene_anexo4"], 1)
        self.assertEqual(item["tiene_escrituras"], 1)
        self.assertEqual(item["tiene_poderes"], 1)
        self.assertEqual(item["tiene_vigencias"], 1)

    def test_create_licitacion_post_unchecked_checkboxes(self):
        payload = {
            "id_licitacion": "5555-99-COT26",
            "titulo": "Alojamiento con Antecedentes Pendientes",
            "organismo": "Ministerio de Salud",
            "categoria": "Alojamiento",
            "modalidad": "Compra Agil",
            "region": "Region Metropolitana (Santiago)",
            "presupuesto_mandante": "3000000",
            "costo_base_hotel": "2500000",
            "estado_embudo": "Identificada",
            "validacion_adjuntos": "Error ID / Discrepancia",
            # No checkbox values sent when user leaves them unchecked
            "fecha_publicacion": "2026-09-15",
            "fecha_cierre": "2026-09-22",
            "descripcion_tdr": "Turnos rotativos sin anexos cargados aun."
        }
        response = self.client.post("/licitaciones/nueva", data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        item = database.get_licitacion_by_id("5555-99-COT26")
        self.assertIsNotNone(item)
        self.assertEqual(item["tiene_anexo4"], 0)
        self.assertEqual(item["tiene_escrituras"], 0)
        self.assertEqual(item["tiene_poderes"], 0)
        self.assertEqual(item["tiene_vigencias"], 0)
        self.assertEqual(item["validacion_adjuntos"], "Error ID / Discrepancia")

    def test_create_licitacion_duplicate_id(self):
        # 1058-12-COT24 already exists from seed data
        payload = {
            "id_licitacion": "1058-12-COT24",
            "titulo": "Intento Duplicado",
            "organismo": "Subsecretaria",
            "categoria": "Alojamiento",
            "modalidad": "Compra Agil",
            "region": "Region Metropolitana (Santiago)",
            "presupuesto_mandante": "5000000",
            "costo_base_hotel": "4000000",
            "estado_embudo": "Identificada",
            "validacion_adjuntos": "Valida",
            "fecha_publicacion": "2026-09-15",
            "fecha_cierre": "2026-09-20",
            "descripcion_tdr": "Test duplicado."
        }
        response = self.client.post("/licitaciones/nueva", data=payload, follow_redirects=True)
        html = response.data.decode("utf-8")
        self.assertIn("duplicado", html.lower())

        # Verify original record was NOT overwritten
        original = database.get_licitacion_by_id("1058-12-COT24")
        self.assertEqual(original["titulo"], "Servicio de Banqueteria y Salones Jornada de Planificacion Estrategica")

    def test_create_licitacion_validation_errors(self):
        # Missing required fields: ID is empty
        payload = {
            "id_licitacion": "   ",
            "titulo": "Titulo Sin ID",
            "organismo": "Organismo",
            "categoria": "Alojamiento",
            "modalidad": "Compra Agil",
            "region": "Region Metropolitana (Santiago)",
            "presupuesto_mandante": "5000000",
            "costo_base_hotel": "4000000",
            "estado_embudo": "Identificada",
            "validacion_adjuntos": "Valida",
            "fecha_publicacion": "2026-09-15",
            "fecha_cierre": "2026-09-20"
        }
        response = self.client.post("/licitaciones/nueva", data=payload, follow_redirects=True)
        html = response.data.decode("utf-8")
        self.assertIn("obligatorio", html.lower())

        # Non-numeric budget
        payload["id_licitacion"] = "9999-99-LP26"
        payload["presupuesto_mandante"] = "cinco-millones"
        response = self.client.post("/licitaciones/nueva", data=payload, follow_redirects=True)
        html = response.data.decode("utf-8")
        self.assertTrue("numerico" in html.lower() or "invalido" in html.lower())

    def test_edit_licitacion_get_success(self):
        response = self.client.get("/licitaciones/1058-12-COT24/editar")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        self.assertIn("Editar Licitacion", html)
        self.assertIn("1058-12-COT24", html)
        self.assertIn("Subsecretaria de Turismo", html)
        self.assertIn("Guardar Licitacion", html)
        self.assertIn("Cancelar", html)

    def test_edit_licitacion_get_not_found(self):
        response = self.client.get("/licitaciones/NO-EXISTE-999/editar")
        self.assertEqual(response.status_code, 404)

    def test_edit_licitacion_post_success(self):
        payload = {
            "titulo": "Servicio de Banqueteria y Salones Edicion Actualizada",
            "organismo": "Subsecretaria de Turismo Modificada",
            "categoria": "Eventos / Catering",
            "modalidad": "Compra Agil",
            "region": "Region Metropolitana (Santiago)",
            "presupuesto_mandante": "6200000",
            "costo_base_hotel": "4300000",
            "estado_embudo": "Calificada",
            "validacion_adjuntos": "Valida",
            "tiene_anexo4": "1",
            "tiene_escrituras": "1",
            "tiene_poderes": "1",
            "tiene_vigencias": "1",
            "fecha_publicacion": "2026-09-12",
            "fecha_cierre": "2026-09-25",
            "descripcion_tdr": "TDR actualizado con nuevas directrices de montaje."
        }
        response = self.client.post("/licitaciones/1058-12-COT24/editar", data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        # Redirection to detail
        self.assertIn("Servicio de Banqueteria y Salones Edicion Actualizada", html)

        # Database verification
        item = database.get_licitacion_by_id("1058-12-COT24")
        self.assertEqual(item["titulo"], "Servicio de Banqueteria y Salones Edicion Actualizada")
        self.assertEqual(item["organismo"], "Subsecretaria de Turismo Modificada")
        self.assertEqual(item["presupuesto_mandante"], 6200000)
        self.assertEqual(item["costo_base_hotel"], 4300000)
        self.assertEqual(item["estado_embudo"], "Calificada")
        self.assertEqual(item["descripcion_tdr"], "TDR actualizado con nuevas directrices de montaje.")

    def test_edit_licitacion_post_not_found(self):
        response = self.client.post("/licitaciones/NO-EXISTE-999/editar", data={"titulo": "Test"})
        self.assertEqual(response.status_code, 404)

    def test_edit_licitacion_post_validation_errors(self):
        payload = {
            "titulo": "",  # Empty title
            "organismo": "Subsecretaria de Turismo",
            "categoria": "Eventos / Catering",
            "modalidad": "Compra Agil",
            "region": "Region Metropolitana (Santiago)",
            "presupuesto_mandante": "invalid_num",
            "costo_base_hotel": "4300000",
            "estado_embudo": "Calificada",
            "validacion_adjuntos": "Valida",
            "fecha_publicacion": "2026-09-12",
            "fecha_cierre": "2026-09-25",
            "descripcion_tdr": "Test"
        }
        response = self.client.post("/licitaciones/1058-12-COT24/editar", data=payload, follow_redirects=True)
        html = response.data.decode("utf-8")
        self.assertTrue("obligatorio" in html.lower() or "invalido" in html.lower() or "numerico" in html.lower())

    def test_delete_licitacion_post_success(self):
        response = self.client.post("/licitaciones/1058-12-COT24/eliminar", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        # Redirected to dashboard
        self.assertIn("Tablero Principal", html)

        # Database verification
        item = database.get_licitacion_by_id("1058-12-COT24")
        self.assertIsNone(item)

    def test_delete_licitacion_post_not_found(self):
        response = self.client.post("/licitaciones/NO-EXISTE-999/eliminar")
        self.assertEqual(response.status_code, 404)

    def test_no_emojis_in_crud_flow(self):
        emoji_pattern = re.compile(
            "[\U00010000-\U0010ffff]|"
            "[\u2600-\u27bf]|"
            "[\u2300-\u23ff]|"
            "[\u2b50\u2b55\u2934\u2935\u25aa\u25ab\u25b6\u25c0\u25fb-\u25fe]"
        )
        # Create form
        res_create = self.client.get("/licitaciones/nueva")
        self.assertEqual(res_create.status_code, 200)
        matches = emoji_pattern.findall(res_create.data.decode("utf-8"))
        self.assertEqual(matches, [], f"Found emojis in create form: {matches}")

        # Edit form
        res_edit = self.client.get("/licitaciones/1058-12-COT24/editar")
        self.assertEqual(res_edit.status_code, 200)
        matches = emoji_pattern.findall(res_edit.data.decode("utf-8"))
        self.assertEqual(matches, [], f"Found emojis in edit form: {matches}")


if __name__ == "__main__":
    unittest.main()
