import os
import unittest
from unittest import mock
import app as flask_app
import database


VALID_LICITACION_FORM = {
    "id_licitacion": "9999-1-COT26",
    "titulo": "Solicitud de Validacion de Formulario",
    "organismo": "Organismo de Prueba",
    "categoria": "Alojamiento",
    "modalidad": "Compra Agil",
    "region": "Region Metropolitana (Santiago)",
    "presupuesto_mandante": "1000000",
    "costo_base_hotel": "500000",
    "estado_embudo": "Identificada",
    "validacion_adjuntos": "Valida",
    "tiene_anexo4": "1",
    "fecha_publicacion": "2026-11-01",
    "fecha_cierre": "2026-11-10",
    "descripcion_tdr": "Descripcion de prueba.",
    "cantidad_asistentes": "10",
    "tipo_jornada": "Jornada Completa (8 hrs)",
    "horario_evento": "08:30 a 18:30 hrs",
    "id_salon_asignado": ""
}

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

    def _post_licitacion(self, **overrides):
        data = dict(VALID_LICITACION_FORM)
        data.update(overrides)
        return self.client.post("/licitaciones/nueva", data=data)

    def _post_reserva(self, **overrides):
        data = dict(VALID_RESERVA_FORM)
        data.update(overrides)
        return self.client.post("/reservas/nueva", data=data)

    def test_invalid_categoria_rejected(self):
        response = self._post_licitacion(categoria="Categoria Inventada")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Categoria", response.data)
        self.assertIn(b"invalida", response.data)
        self.assertIsNone(database.get_licitacion_by_id("9999-1-COT26"))

    def test_invalid_modalidad_rejected(self):
        response = self._post_licitacion(modalidad="Modalidad Inventada")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Modalidad", response.data)
        self.assertIsNone(database.get_licitacion_by_id("9999-1-COT26"))

    def test_invalid_validacion_adjuntos_rejected(self):
        response = self._post_licitacion(validacion_adjuntos="Cualquier Cosa")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Validacion de adjuntos", response.data)
        self.assertIsNone(database.get_licitacion_by_id("9999-1-COT26"))

    def test_invalid_tipo_jornada_rejected(self):
        response = self._post_licitacion(tipo_jornada="Jornada de 300 hrs")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tipo de jornada", response.data)
        self.assertIsNone(database.get_licitacion_by_id("9999-1-COT26"))

    def test_fecha_with_invalid_format_rejected(self):
        response = self._post_licitacion(fecha_publicacion="15/11/2026")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"formato AAAA-MM-DD", response.data)
        self.assertIsNone(database.get_licitacion_by_id("9999-1-COT26"))

    def test_fecha_cierre_before_publicacion_rejected(self):
        response = self._post_licitacion(fecha_publicacion="2026-11-10", fecha_cierre="2026-11-01")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Fecha de Cierre no puede ser anterior", response.data)
        self.assertIsNone(database.get_licitacion_by_id("9999-1-COT26"))

    def test_nonexistent_salon_asignado_rejected(self):
        response = self._post_licitacion(id_salon_asignado="SALON-QUE-NO-EXISTE")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"no existe en el catalogo", response.data)
        self.assertIsNone(database.get_licitacion_by_id("9999-1-COT26"))

    def test_duplicate_id_race_returns_error_not_500(self):
        with mock.patch("database.get_licitacion_by_id", return_value=None):
            response = self._post_licitacion(id_licitacion="1058-12-COT24")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ya existe en el sistema", response.data)

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
