import os
import unittest
import app as flask_app
import database


VALID_RESERVA_FORM = {
    "id_salon": "SALON-LONDRES",
    "cliente_evento": "Evento de Validacion",
    "organismo_o_empresa": "Organismo de Prueba",
    "tipo_evento": "Reunion",
    "fecha_inicio": "2027-01-05",
    "fecha_fin": "2027-01-05",
    "horario": "09:00 a 12:00 hrs",
    "asistentes_estimados": "10",
    "estado_reserva": "Confirmada",
    "id_licitacion": "",
    "contacto_responsable": "",
    "observaciones": ""
}


class TestValidation(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_validation_licitaciones.db"
        database.DB_NAME = self.db_name
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass
        database.init_db()

        flask_app.app.config["TESTING"] = True
        flask_app.app.config["SECRET_KEY"] = "test-validation-secret"
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

    def _post_reserva(self, **overrides):
        data = dict(VALID_RESERVA_FORM)
        data.update(overrides)
        return self.client.post("/reservas/nueva", data=data)

    def test_reserva_with_nonexistent_salon_rejected(self):
        response = self._post_reserva(id_salon="SALON-QUE-NO-EXISTE")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"no existe en el catalogo", response.data)

    def test_reserva_with_nonexistent_licitacion_rejected(self):
        response = self._post_reserva(id_licitacion="CONT-2026-99")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"licitacion vinculada no existe", response.data)

    def test_reserva_invalid_estado_rejected_not_silenced(self):
        response = self._post_reserva(estado_reserva="Estado Inventado")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Estado de reserva", response.data)

    def test_reserva_invalid_date_format_rejected(self):
        response = self._post_reserva(fecha_inicio="05/01/2027")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"formato AAAA-MM-DD", response.data)

    def test_reserva_empty_asistentes_accepted_as_zero(self):
        data = dict(VALID_RESERVA_FORM)
        data["asistentes_estimados"] = ""
        data["fecha_inicio"] = "2027-02-01"
        data["fecha_fin"] = "2027-02-01"
        response = self.client.post("/reservas/nueva", data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        reservas = database.get_all_reservas(id_salon="SALON-LONDRES")
        nueva = [r for r in reservas if r["cliente_evento"] == "Evento de Validacion"]
        self.assertEqual(len(nueva), 1)
        self.assertEqual(nueva[0]["asistentes_estimados"], 0)


class TestDatabaseIntegrity(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_validation_licitaciones.db"
        database.DB_NAME = self.db_name
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass
        database.init_db()

    def tearDown(self):
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass

    def test_foreign_keys_pragma_enabled(self):
        conn = database.get_db_connection()
        try:
            enabled = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(enabled, 1)

    def test_delete_licitacion_clears_reservation_links(self):
        reserva = database.get_reserva_by_id(1)
        self.assertEqual(reserva["id_licitacion"], "1058-12-COT24")

        database.delete_licitacion("1058-12-COT24")

        self.assertIsNone(database.get_licitacion_by_id("1058-12-COT24"))
        reserva_after = database.get_reserva_by_id(1)
        self.assertEqual(reserva_after["id_licitacion"], "")


if __name__ == "__main__":
    unittest.main()
