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

        # Filtro por estado del embudo (una vigente creada aqui; las del
        # ejemplo ya vencieron y quedaron en 'Cerrada')
        database.create_licitacion({
            "id_licitacion": "0001-01-CAL26",
            "titulo": "Vigente para probar filtro Calificada",
            "organismo": "Organismo Filtro",
            "categoria": "Alojamiento",
            "modalidad": "Licitacion Publica",
            "region": "Región Metropolitana (Santiago)",
            "presupuesto_mandante": 1000000,
            "costo_base_hotel": 800000,
            "estado_embudo": "Calificada",
            "validacion_adjuntos": "Pendiente",
            "tiene_anexo4": 0, "tiene_escrituras": 0,
            "tiene_poderes": 0, "tiene_vigencias": 0,
            "fecha_publicacion": database.hoy_chile().isoformat(),
            "fecha_cierre": "2027-01-31",
            "descripcion_tdr": "",
        })
        calificadas = database.get_all_licitaciones(estado="Calificada")
        self.assertTrue(all(item["estado_embudo"] == "Calificada" for item in calificadas))
        self.assertGreater(len(calificadas), 0)

        # Busqueda por texto (q) en organismo
        busqueda_organismo = database.get_all_licitaciones(q="Turismo")
        self.assertGreater(len(busqueda_organismo), 0)
        self.assertIn("Turismo", busqueda_organismo[0]["organismo"])

        # Busqueda por texto (q) en id_licitacion
        busqueda_id = database.get_all_licitaciones(q="1058-12-COT26")
        self.assertEqual(len(busqueda_id), 1)
        self.assertEqual(busqueda_id[0]["id_licitacion"], "1058-12-COT26")

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
            "region": "Región Metropolitana (Santiago)",
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
        item = database.get_licitacion_by_id("1058-12-COT26")
        self.assertIsNotNone(item)

        # Actualizar estado
        resultado_update = database.update_licitacion("1058-12-COT26", {"estado_embudo": "Calificada"})
        self.assertTrue(resultado_update)
        updated = database.get_licitacion_by_id("1058-12-COT26")
        self.assertEqual(updated["estado_embudo"], "Calificada")

        # Actualizar registro inexistente retorna False
        self.assertFalse(database.update_licitacion("NO-EXISTE", {"estado_embudo": "Calificada"}))

        # Eliminar licitacion
        resultado_delete = database.delete_licitacion("1058-12-COT26")
        self.assertTrue(resultado_delete)
        deleted = database.get_licitacion_by_id("1058-12-COT26")
        self.assertIsNone(deleted)

        # Eliminar licitacion inexistente retorna False
        self.assertFalse(database.delete_licitacion("1058-12-COT26"))

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
            + metrics["Cerrada"]
            + metrics["Adjudicada"]
            + metrics["Descartada"]
        )
        self.assertEqual(metrics["Total"], total_estados)
        # El ejemplo completo vencio: todas las fases abiertas quedan cerradas.
        self.assertGreater(metrics["Cerrada"], 0)
        self.assertGreaterEqual(metrics["Total"], 8)
        self.assertGreaterEqual(metrics["Compra_Agil"], 1)

    def test_normalizar_texto_agrega_tildes_conocidas(self):
        self.assertEqual(database.normalizar_texto("Licitacion Publica"), "Licitación Pública")
        self.assertEqual(database.normalizar_texto("salon plenario"), "salón plenario")
        self.assertEqual(database.normalizar_texto("Region Metropolitana"), "Región Metropolitana")
        # No toca palabras que solo se parecen ni los plurales.
        self.assertEqual(database.normalizar_texto("Licitaciones"), "Licitaciones")
        self.assertEqual(database.normalizar_texto("Salones"), "Salones")
        self.assertEqual(database.normalizar_texto(""), "")
        self.assertIsNone(database.normalizar_texto(None))

    def test_marcar_cerradas_cierra_solo_fases_abiertas(self):
        # Vigente y abierta: no debe tocarse.
        database.create_licitacion({
            "id_licitacion": "0002-01-ABI26",
            "titulo": "Vigente abierta",
            "organismo": "Organismo Test",
            "categoria": "Alojamiento",
            "modalidad": "Compra Agil",
            "region": "Región Metropolitana (Santiago)",
            "presupuesto_mandante": 1000000,
            "costo_base_hotel": 800000,
            "estado_embudo": "Identificada",
            "validacion_adjuntos": "Pendiente",
            "fecha_publicacion": database.hoy_chile().isoformat(),
            "fecha_cierre": "2027-02-01",
            "descripcion_tdr": "",
        })
        # Vencida pero ya resuelta: estado final no se toca.
        database.create_licitacion({
            "id_licitacion": "0003-01-ADJ26",
            "titulo": "Vencida adjudicada",
            "organismo": "Organismo Test",
            "categoria": "Alojamiento",
            "modalidad": "Compra Agil",
            "region": "Región Metropolitana (Santiago)",
            "presupuesto_mandante": 1000000,
            "costo_base_hotel": 800000,
            "estado_embudo": "Adjudicada",
            "validacion_adjuntos": "Pendiente",
            "fecha_publicacion": "2026-01-01",
            "fecha_cierre": "2026-01-15",
            "descripcion_tdr": "",
        })

        # Vencida y todavia abierta: es la que debe cerrarse.
        database.create_licitacion({
            "id_licitacion": "0004-01-VEN26",
            "titulo": "Vencida sin decidir",
            "organismo": "Organismo Test",
            "categoria": "Alojamiento",
            "modalidad": "Compra Agil",
            "region": "Región Metropolitana (Santiago)",
            "presupuesto_mandante": 1000000,
            "costo_base_hotel": 800000,
            "estado_embudo": "Identificada",
            "validacion_adjuntos": "Pendiente",
            "fecha_publicacion": "2026-01-01",
            "fecha_cierre": "2026-01-15",
            "descripcion_tdr": "",
        })

        self.assertGreater(database.marcar_cerradas(), 0)

        self.assertEqual(
            database.get_licitacion_by_id("0002-01-ABI26")["estado_embudo"], "Identificada"
        )
        self.assertEqual(
            database.get_licitacion_by_id("0003-01-ADJ26")["estado_embudo"], "Adjudicada"
        )
        self.assertEqual(
            database.get_licitacion_by_id("0004-01-VEN26")["estado_embudo"], "Cerrada"
        )
        # El ejemplo completo esta vencido: sus fases abiertas quedaron cerradas.
        self.assertEqual(
            database.get_licitacion_by_id("1058-12-COT26")["estado_embudo"], "Cerrada"
        )

    def test_init_db_renombr_ids_demo_al_anio_2026(self):
        viejo, nuevo = "1058-12-COT24", "1058-12-COT26"
        conn = database.get_db_connection()
        try:
            # Deja la base como estaba antes: solo IDs viejos (sin la fila nueva).
            conn.execute("DELETE FROM licitaciones WHERE id_licitacion = ?", (nuevo,))
            conn.execute("DELETE FROM reservas_salones WHERE id_licitacion = ?", (nuevo,))
            conn.execute("""
                INSERT INTO licitaciones (
                    id_licitacion, titulo, organismo, categoria, modalidad, region,
                    presupuesto_mandante, costo_base_hotel, estado_embudo,
                    validacion_adjuntos, fecha_publicacion, fecha_cierre
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                viejo, "Servicio de prueba", "Organismo de prueba", "Alojamiento",
                "Compra Agil", "Region Metropolitana (Santiago)",
                1000000, 800000, "Cerrada", "Sin verificar",
                "2026-01-01", "2026-01-31",
            ))
            conn.execute("""
                INSERT INTO reservas_salones (
                    id_salon, cliente_evento, organismo_o_empresa, tipo_evento,
                    fecha_inicio, fecha_fin, horario, asistentes_estimados,
                    estado_reserva, id_licitacion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "SALON-DANUBIO", "Evento de prueba", "Organismo de prueba",
                "Seminario", "2027-01-05", "2027-01-05", "09:00 a 18:00",
                10, "Tentativa", viejo,
            ))
            conn.execute("""
                INSERT INTO historial_licitacion (id_licitacion, fecha, usuario, tipo, detalle)
                VALUES (?, ?, ?, ?, ?)
            """, (viejo, "2026-01-01 10:00", "admin", "Decision", "Registro previo"))
            conn.commit()
        finally:
            conn.close()

        database.init_db()

        self.assertIsNone(database.get_licitacion_by_id(viejo))
        self.assertIsNotNone(database.get_licitacion_by_id(nuevo))
        reservas = [r for r in database.get_all_reservas() if r["id_licitacion"] == nuevo]
        self.assertEqual(len(reservas), 1)
        conn = database.get_db_connection()
        try:
            historial = conn.execute(
                "SELECT COUNT(*) AS n FROM historial_licitacion WHERE id_licitacion = ?",
                (nuevo,),
            ).fetchone()
        finally:
            conn.close()
        self.assertEqual(historial["n"], 1)

    def test_init_db_does_not_duplicate_when_called_twice(self):
        total_antes = len(database.get_all_licitaciones())
        database.init_db()
        total_despues = len(database.get_all_licitaciones())
        self.assertEqual(total_antes, total_despues)

    def test_init_db_no_resiembra_despues_de_borrar_todo(self):
        conn = database.get_db_connection()
        try:
            conn.execute("DELETE FROM reservas_salones")
            conn.execute("DELETE FROM licitaciones")
            conn.commit()
        finally:
            conn.close()
        database.init_db()
        self.assertEqual(len(database.get_all_licitaciones()), 0)
        self.assertEqual(len(database.get_all_reservas()), 0)

    def test_init_db_no_pisa_aforo_editado(self):
        conn = database.get_db_connection()
        try:
            conn.execute("UPDATE salones SET capacidad_maxima = 300 WHERE id_salon = 'SALON-PERGOLA'")
            conn.commit()
        finally:
            conn.close()
        database.init_db()
        self.assertEqual(database.get_salon_by_id("SALON-PERGOLA")["capacidad_maxima"], 300)

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
        self.assertFalse(database.update_licitacion("1058-12-COT26", {}))

    def test_salones_catalog_loaded(self):
        salones = database.get_all_salones()
        self.assertGreaterEqual(len(salones), 5)
        ids = {s["id_salon"] for s in salones}
        self.assertIn("SALON-PERGOLA", ids)
        self.assertIn("SALON-PERGOLA", ids)
        self.assertIn("SALON-DANUBIO", ids)
        self.assertIn("SALON-SENA", ids)

        # Verificar campos obligatorios del catalogo
        for s in salones:
            self.assertTrue(s["nombre"])
            self.assertTrue(s["tipo"])
            self.assertGreater(s["capacidad_maxima"], 0)
            self.assertTrue(s["horario_disponible"])

    def test_get_salon_by_id(self):
        pergola = database.get_salon_by_id("SALON-PERGOLA")
        self.assertIsNotNone(pergola)
        self.assertEqual(pergola["capacidad_maxima"], 450)
        self.assertEqual(pergola["nombre"], "Salón Pergola")

        inexistente = database.get_salon_by_id("SALON-INEXISTENTE")
        self.assertIsNone(inexistente)

        vacio = database.get_salon_by_id("")
        self.assertIsNone(vacio)

    def test_get_salones_aptos(self):
        aptos_50 = database.get_salones_aptos(50)
        self.assertTrue(all(s["capacidad_maxima"] >= 50 for s in aptos_50))

        aptos_200 = database.get_salones_aptos(200)
        self.assertEqual(len(aptos_200), 1)
        self.assertEqual(aptos_200[0]["id_salon"], "SALON-PERGOLA")

        aptos_500 = database.get_salones_aptos(500)
        self.assertEqual(len(aptos_500), 0)

    def test_opciones_reserva_excluye_descartadas(self):
        ids = {lic["id_licitacion"] for lic in database.get_licitaciones_para_reserva()}
        self.assertNotIn("310-7-COT26", ids)
        self.assertIn("1058-12-COT26", ids)

    def test_create_and_update_licitacion_with_capacity_and_salon(self):
        data = {
            "id_licitacion": "TEST-CAPACIDAD-01",
            "titulo": "Seminario Regional de Capacitacion",
            "organismo": "Ministerio de Economia",
            "categoria": "Eventos / Catering",
            "modalidad": "Compra Agil",
            "region": "Región Metropolitana (Santiago)",
            "presupuesto_mandante": 5000000,
            "costo_base_hotel": 3800000,
            "estado_embudo": "Identificada",
            "validacion_adjuntos": "Valida",
            "tiene_anexo4": 1,
            "tiene_escrituras": 1,
            "tiene_poderes": 1,
            "tiene_vigencias": 1,
            "fecha_publicacion": "2026-10-01",
            "fecha_cierre": "2026-10-15",
            "descripcion_tdr": "Uso de salon plenario",
            "cantidad_asistentes": 120,
            "tipo_jornada": "Media Jornada Manana (4 hrs)",
            "horario_evento": "08:30 a 13:00 hrs",
            "id_salon_asignado": "SALON-PERGOLA"
        }
        database.create_licitacion(data)

        creada = database.get_licitacion_by_id("TEST-CAPACIDAD-01")
        self.assertIsNotNone(creada)
        self.assertEqual(creada["cantidad_asistentes"], 120)
        self.assertEqual(creada["tipo_jornada"], "Media Jornada Manana (4 hrs)")
        self.assertEqual(creada["horario_evento"], "08:30 a 13:00 hrs")
        self.assertEqual(creada["id_salon_asignado"], "SALON-PERGOLA")
        self.assertEqual(creada["nombre_salon"], "Salón Pergola")
        self.assertEqual(creada["capacidad_salon"], 450)

        # Actualizar asignacion de salon y aforo
        database.update_licitacion("TEST-CAPACIDAD-01", {
            "cantidad_asistentes": 200,
            "id_salon_asignado": "SALON-PERGOLA"
        })
        actualizada = database.get_licitacion_by_id("TEST-CAPACIDAD-01")
        self.assertEqual(actualizada["cantidad_asistentes"], 200)
        self.assertEqual(actualizada["id_salon_asignado"], "SALON-PERGOLA")
        self.assertEqual(actualizada["nombre_salon"], "Salón Pergola")


if __name__ == "__main__":
    unittest.main()
