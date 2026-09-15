import os
import unittest
import database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        database.DB_NAME = "test_licitaciones.db"
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)
        database.init_db()

    def tearDown(self):
        if os.path.exists(database.DB_NAME):
            try:
                os.remove(database.DB_NAME)
            except PermissionError:
                pass

    def test_seed_data_loaded(self):
        licitaciones = database.get_all_licitaciones()
        self.assertGreaterEqual(len(licitaciones), 8)

        # Verificar presencia de categorias requeridas
        categorias = {item["categoria"] for item in licitaciones}
        self.assertIn("Alojamiento", categorias)
        self.assertIn("Eventos / Catering", categorias)

        # Verificar presencia de modalidades
        modalidades = {item["modalidad"] for item in licitaciones}
        self.assertIn("Compra Agil", modalidades)
        self.assertIn("Licitacion Publica", modalidades)

        # Verificar caso de alerta presupuestaria: costo_base_hotel > presupuesto_mandante
        costo_alerta = [
            item for item in licitaciones
            if item["costo_base_hotel"] > item["presupuesto_mandante"]
        ]
        self.assertGreaterEqual(len(costo_alerta), 1)

        # Verificar caso de discrepancia de ID / Efecto ID
        efecto_id = [
            item for item in licitaciones
            if item["validacion_adjuntos"] != "Valida"
        ]
        self.assertGreaterEqual(len(efecto_id), 1)

        # Verificar checklist de admisibilidad con falta documental
        falta_documento = [
            item for item in licitaciones
            if item["tiene_anexo4"] == 0
            or item["tiene_escrituras"] == 0
            or item["tiene_poderes"] == 0
            or item["tiene_vigencias"] == 0
        ]
        self.assertGreaterEqual(len(falta_documento), 1)

    def test_get_db_connection(self):
        conn = database.get_db_connection()
        self.assertIsNotNone(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test_col")
        row = cursor.fetchone()
        self.assertEqual(row["test_col"], 1)
        conn.close()

    def test_get_all_licitaciones_filters(self):
        # Filtro por categoria
        alojamiento = database.get_all_licitaciones(categoria="Alojamiento")
        self.assertTrue(all(item["categoria"] == "Alojamiento" for item in alojamiento))
        self.assertGreater(len(alojamiento), 0)

        # Filtro por modalidad
        compra_agil = database.get_all_licitaciones(modalidad="Compra Agil")
        self.assertTrue(all(item["modalidad"] == "Compra Agil" for item in compra_agil))
        self.assertGreater(len(compra_agil), 0)

        # Filtro por estado del embudo
        calificadas = database.get_all_licitaciones(estado="Calificada")
        self.assertTrue(all(item["estado_embudo"] == "Calificada" for item in calificadas))
        self.assertGreater(len(calificadas), 0)

        # Busqueda por texto (q) en organismo
        busqueda_organismo = database.get_all_licitaciones(q="Turismo")
        self.assertGreater(len(busqueda_organismo), 0)
        self.assertIn("Turismo", busqueda_organismo[0]["organismo"])

        # Busqueda por texto (q) en id_licitacion
        busqueda_id = database.get_all_licitaciones(q="1058-12-COT24")
        self.assertEqual(len(busqueda_id), 1)
        self.assertEqual(busqueda_id[0]["id_licitacion"], "1058-12-COT24")

        # Busqueda sin resultados
        busqueda_vacia = database.get_all_licitaciones(q="TerminoInexistenteXYZ")
        self.assertEqual(len(busqueda_vacia), 0)

    def test_create_and_get_licitacion(self):
        nueva = {
            "id_licitacion": "9999-01-LP26",
            "titulo": "Servicio de Alojamiento Corporativo Test",
            "organismo": "Ministerio de Economia",
            "categoria": "Alojamiento",
            "modalidad": "Licitacion Publica",
            "region": "Region Metropolitana (Santiago)",
            "presupuesto_mandante": 15000000,
            "costo_base_hotel": 12000000,
            "estado_embudo": "Identificada",
            "validacion_adjuntos": "Valida",
            "tiene_anexo4": 1,
            "tiene_escrituras": 1,
            "tiene_poderes": 1,
            "tiene_vigencias": 1,
            "fecha_publicacion": "2026-09-10",
            "fecha_cierre": "2026-09-25",
            "descripcion_tdr": "Servicio de 50 habitaciones para delegacion oficial."
        }
        id_creado = database.create_licitacion(nueva)
        self.assertEqual(id_creado, "9999-01-LP26")

        item = database.get_licitacion_by_id("9999-01-LP26")
        self.assertIsNotNone(item)
        self.assertEqual(item["titulo"], "Servicio de Alojamiento Corporativo Test")
        self.assertEqual(item["organismo"], "Ministerio de Economia")
        self.assertEqual(item["presupuesto_mandante"], 15000000)
        self.assertEqual(item["costo_base_hotel"], 12000000)

    def test_get_licitacion_by_id_not_found(self):
        item = database.get_licitacion_by_id("NO-EXISTE-000")
        self.assertIsNone(item)

    def test_update_and_delete_licitacion(self):
        item = database.get_licitacion_by_id("1058-12-COT24")
        self.assertIsNotNone(item)

        # Actualizar estado
        resultado_update = database.update_licitacion("1058-12-COT24", {"estado_embudo": "Calificada"})
        self.assertTrue(resultado_update)
        updated = database.get_licitacion_by_id("1058-12-COT24")
        self.assertEqual(updated["estado_embudo"], "Calificada")

        # Actualizar registro inexistente retorna False
        self.assertFalse(database.update_licitacion("NO-EXISTE", {"estado_embudo": "Calificada"}))

        # Eliminar licitacion
        resultado_delete = database.delete_licitacion("1058-12-COT24")
        self.assertTrue(resultado_delete)
        deleted = database.get_licitacion_by_id("1058-12-COT24")
        self.assertIsNone(deleted)

        # Eliminar licitacion inexistente retorna False
        self.assertFalse(database.delete_licitacion("1058-12-COT24"))

    def test_get_funnel_metrics(self):
        metrics = database.get_funnel_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn("Identificada", metrics)
        self.assertIn("Calificada", metrics)
        self.assertIn("Participada", metrics)
        self.assertIn("Adjudicada", metrics)
        self.assertIn("Descartada", metrics)
        self.assertIn("Compra_Agil", metrics)
        self.assertIn("Total", metrics)

        total_estados = (
            metrics["Identificada"]
            + metrics["Calificada"]
            + metrics["Participada"]
            + metrics["Adjudicada"]
            + metrics["Descartada"]
        )
        self.assertEqual(metrics["Total"], total_estados)
        self.assertGreaterEqual(metrics["Total"], 8)
        self.assertGreaterEqual(metrics["Compra_Agil"], 1)

    def test_init_db_does_not_duplicate_when_called_twice(self):
        total_antes = len(database.get_all_licitaciones())
        database.init_db()
        total_despues = len(database.get_all_licitaciones())
        self.assertEqual(total_antes, total_despues)

    def test_combined_filters_and_ordering(self):
        # Filtro combinado por categoria y modalidad
        resultado = database.get_all_licitaciones(
            categoria="Eventos / Catering",
            modalidad="Compra Agil"
        )
        self.assertGreater(len(resultado), 0)
        for r in resultado:
            self.assertEqual(r["categoria"], "Eventos / Catering")
            self.assertEqual(r["modalidad"], "Compra Agil")

        # Verificar orden ascendente por fecha_cierre
        all_items = database.get_all_licitaciones()
        fechas = [item["fecha_cierre"] for item in all_items]
        self.assertEqual(fechas, sorted(fechas))

    def test_update_empty_data_returns_false(self):
        self.assertFalse(database.update_licitacion("1058-12-COT24", {}))


if __name__ == "__main__":
    unittest.main()
