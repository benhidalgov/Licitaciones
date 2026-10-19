import os
import unittest
import app as flask_app
import database
import mercado_publico
import resumen


class TestEvaluacionOperativa(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_evaluacion_licitaciones.db"
        database.DB_NAME = self.db_name
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass
        database.init_db()

        flask_app.app.config["TESTING"] = True
        flask_app.app.config["SECRET_KEY"] = "test-evaluacion-secret"
        flask_app.app.config["CSRF_ENABLED"] = False
        self.client = flask_app.app.test_client()
        with self.client.session_transaction() as sess:
            sess["user"] = "daniela"
            sess["nombre"] = "Daniela"

    def tearDown(self):
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass

    def test_catalogo_tiene_17_salones_del_hotel(self):
        salones = database.get_all_salones()
        self.assertEqual(len(salones), 17)
        self.assertTrue(all(s["propiedad"] == "Plaza San Francisco" for s in salones))

        # Solo "Tam" sigue como provisional: el catalogo oficial no le dedica
        # fila propia y sus aforos se deducen de las combinaciones.
        prov = [s["nombre"] for s in salones if s["es_provisional"]]
        self.assertEqual(prov, ["Salon Tam"])

        # Aforos tomados del documento oficial del hotel, no estimados.
        por_id = {s["id_salon"]: s for s in salones}
        self.assertEqual(por_id["SALON-PERGOLA"]["capacidad_maxima"], 450)
        self.assertEqual(por_id["SALON-DANUBIO"]["capacidad_maxima"], 100)
        self.assertEqual(por_id["SALON-EJECUTIVO"]["capacidad_maxima"], 8)
        # Superficie del Salon Pergola, la unica apta para 450 personas.
        self.assertIn("362 m2", por_id["SALON-PERGOLA"]["ubicacion"])
        # Ningun salon del catalogo real se llama como los de prueba.
        self.assertFalse(any("Andes" in s["nombre"] or "Cordillera" in s["nombre"]
                             for s in salones))

    def test_costo_minimo_suma_salon_y_consumo(self):
        costo = database.calcular_costo_minimo("Eventos / Catering", 10, "SALON-SENA")
        # El catalogo oficial no publica tarifas, por lo que solo se cuenta el
        # consumo por persona.
        self.assertEqual(costo, 10 * database.COSTO_ALIMENTACION_PERSONA)

        hospedaje = database.calcular_costo_minimo("Alojamiento", 2)
        self.assertEqual(hospedaje, 2 * database.COSTO_HABITACION_PERSONA)

    def test_evaluacion_descarta_por_presupuesto(self):
        response = self.client.post(
            "/licitaciones/1058-12-COT24/evaluacion",
            data={
                "propiedad": "Plaza San Francisco",
                "cantidad_asistentes": "1000",
                "id_salon_asignado": "SALON-DANUBIO",
                "tipo_jornada": "Jornada Completa (8 hrs)",
                "horario_evento": "08:30 a 18:30 hrs",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        lic = database.get_licitacion_by_id("1058-12-COT24")
        self.assertEqual(lic["costeo_validado"], 1)
        self.assertGreater(lic["costo_base_hotel"], lic["presupuesto_mandante"])
        self.assertEqual(lic["estado_embudo"], "Descartada")
        self.assertEqual(lic["motivo_descarte"], "Precio")

    def test_ismael_solo_acepta_alojamiento(self):
        response = self.client.post(
            "/licitaciones/1058-12-COT24/evaluacion",
            data={"propiedad": "Hotel Ismael", "cantidad_asistentes": "10"},
            follow_redirects=True,
        )
        self.assertIn("Hotel Ismael solo puede postular a servicios de alojamiento".encode("utf-8"), response.data)
        lic = database.get_licitacion_by_id("1058-12-COT24")
        self.assertEqual(lic["propiedad"], "Plaza San Francisco")

    def test_no_participar_guarda_motivo_y_nota_compartida(self):
        self.client.post(
            "/licitaciones/1058-12-COT24/decision",
            data={"decision": "no_participar", "motivo": "Disponibilidad"},
        )
        self.client.post(
            "/licitaciones/1058-12-COT24/notas",
            data={"nota": "PMS sin disponibilidad para la fecha."},
        )

        lic = database.get_licitacion_by_id("1058-12-COT24")
        self.assertEqual(lic["estado_embudo"], "Descartada")
        self.assertEqual(lic["motivo_descarte"], "Disponibilidad")
        self.assertIn("PMS sin disponibilidad", lic["notas"])
        self.assertIn("Daniela", lic["notas"])

    def test_exportacion_csv_abre_en_excel(self):
        response = self.client.get("/licitaciones/exportar.csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.headers["Content-Type"])
        self.assertTrue(response.data.startswith("\ufeff".encode("utf-8")))
        self.assertIn(b"ID;Titulo;Organismo", response.data)

    def test_priorizadas_incluye_oportunidad_abierta_y_viable(self):
        database.create_licitacion({
            "id_licitacion": "TEST-PRIORIDAD-01",
            "titulo": "Jornada viable para priorizacion",
            "organismo": "Ministerio de Prueba",
            "categoria": "Eventos / Catering",
            "modalidad": "Compra Agil",
            "region": "Region Metropolitana (Santiago)",
            "presupuesto_mandante": 5000000,
            "costo_base_hotel": 1000000,
            "estado_embudo": "Identificada",
            "validacion_adjuntos": "Valida",
            "tiene_anexo4": 1,
            "tiene_escrituras": 1,
            "tiene_poderes": 1,
            "tiene_vigencias": 1,
            "fecha_publicacion": "2026-01-01",
            "fecha_cierre": "2026-12-31",
            "descripcion_tdr": "Servicio de salon",
            "cantidad_asistentes": 10,
            "id_salon_asignado": "SALON-SENA",
        })
        priorizadas = database.get_oportunidades_prioritarias(hoy="2026-01-01", limit=100)
        self.assertIn("TEST-PRIORIDAD-01", {p["id_licitacion"] for p in priorizadas})

    def test_clasificacion_estima_aforo_desde_la_descripcion(self):
        item = {
            "CodigoExterno": "9100-1-COT24",
            "Nombre": "Coffee break para jornada institucional",
            "FechaCierre": "2026-12-01T18:00:00",
            "Descripcion": "Servicio de alimentacion para 80 personas en salon",
            "Comprador": {"NombreOrganismo": "Servicio de Prueba"},
            "MontoEstimado": 3000000,
        }
        res = mercado_publico.filtrar_y_clasificar_licitacion(item)
        self.assertIsNotNone(res)
        self.assertEqual(res["cantidad_asistentes"], 80)

    def test_descarta_banqueteria_fuera_del_hotel(self):
        item = {
            "CodigoExterno": "9000-1-COT24",
            "Nombre": "Banqueteria a domicilio para evento institucional",
            "FechaCierre": "2026-12-01T18:00:00",
            "Descripcion": "Servicio de coctel a domicilio en oficinas del mandante",
            "Comprador": {"NombreOrganismo": "Servicio de Prueba"},
            "MontoEstimado": 3000000,
        }
        self.assertIsNone(mercado_publico.filtrar_y_clasificar_licitacion(item))


def _lic_ejemplo():
    """Licitacion minima para alimentar la ficha resumen."""
    return {
        "id_licitacion": "1-2026",
        "titulo": "Servicio de coffee break y almuerzo para 120 asistentes",
        "organismo": "Servicio de Prueba",
        "categoria": "Eventos / Catering",
        "modalidad": "Licitacion Publica",
        "region": "Region Metropolitana",
        "estado_embudo": "Identificada",
        "validacion_adjuntos": "Valida",
        "descripcion_tdr": "Evento el 15 de marzo de 2026 y el 20/03/2026, "
                           "entrega de coffee break y almuerzo para 120 personas.",
        "fecha_publicacion": "2026-10-01",
        "fecha_cierre": "2026-11-30",
        "presupuesto_mandante": 20000000,
        "costo_base_hotel": 16000000,
        "cantidad_asistentes": 120,
        "propiedad": "Plaza San Francisco",
        "id_salon_asignado": "",
        "sello_mujer": 1, "jornada_40h": 1, "sello_sernatur": 0, "inclusion_laboral": 1,
        "tiene_anexo4": 1, "tiene_escrituras": 1, "tiene_poderes": 1, "tiene_vigencias": 1,
    }


class TestFichaResumen(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_resumen_licitaciones.db"
        database.DB_NAME = self.db_name
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass
        database.init_db()
        # Por defecto no hay llave de IA: el resumen debe degradar a reglas.
        os.environ.pop("RESUMEN_IA_API_KEY", None)

    def tearDown(self):
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except PermissionError:
                pass

    def test_resumen_por_reglas_cubre_lo_pedido_en_la_reunion(self):
        ficha = resumen.generar_resumen(_lic_ejemplo())
        self.assertEqual(ficha["fuente"], "reglas")

        # Fechas del evento (no solo las de publicacion/cierre del proceso).
        self.assertTrue(any("marzo" in f for f in ficha["fechas_evento"]))

        # Cantidad de personas.
        self.assertEqual(ficha["personas"], 120)

        # Servicios de alimentacion intramuros.
        self.assertIn("Coffee break", ficha["servicios_alimentacion"])
        self.assertIn("Almuerzo", ficha["servicios_alimentacion"])

        # Espacio requerido y alternativas de salon con aviso de disponibilidad.
        self.assertIn("Salones", ficha["espacio"]["tipo"])
        self.assertTrue(ficha["espacio"]["alternativas"])

        # Desglose de ponderacion que suma 100.
        self.assertEqual(sum(c["peso"] for c in ficha["ponderacion"]), 100)
        self.assertTrue(0 <= ficha["puntaje_total"] <= 100)

    def test_ponderacion_penaliza_presupuesto_insuficiente(self):
        lic = _lic_ejemplo()
        lic["costo_base_hotel"] = 30000000  # supera el presupuesto
        ficha = resumen.generar_resumen_reglas(lic)
        presupuesto = next(c for c in ficha["ponderacion"] if c["criterio"].startswith("Presupuesto"))
        self.assertEqual(presupuesto["puntuacion"], 0)

    def test_sin_llave_ia_usa_reglas(self):
        self.assertFalse(resumen.get_ia_config()["api_key"])
        ficha = resumen.generar_resumen(_lic_ejemplo(), usar_ia=True)
        self.assertEqual(ficha["fuente"], "reglas")

    def test_detalle_de_licitacion_muestra_la_ficha(self):
        lic = _lic_ejemplo()
        database.create_licitacion(lic)

        flask_app.app.config["TESTING"] = True
        flask_app.app.config["CSRF_ENABLED"] = False
        client = flask_app.app.test_client()
        with client.session_transaction() as sess:
            sess["user"] = "daniela"
            sess["nombre"] = "Daniela"

        resp = client.get("/licitaciones/1-2026")
        html = resp.get_data(as_text=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Ficha Resumen", html)
        self.assertIn("Desglose de Ponderacion de Criterios", html)


if __name__ == "__main__":
    unittest.main()
