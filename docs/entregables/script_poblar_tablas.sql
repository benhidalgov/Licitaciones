-- Script de esquema y poblado de la base de datos del sistema
-- Copilot de Licitaciones y Operaciones Hoteleras (SQLite 3)
-- Generado desde database.py (init_db): CREATE TABLE + datos semilla oficiales.
-- Uso: sqlite3 licitaciones.db < script_poblar_tablas.sql

BEGIN TRANSACTION;
CREATE TABLE ajustes (
                clave TEXT PRIMARY KEY,
                valor INTEGER NOT NULL
            );
INSERT INTO "ajustes" VALUES('seed_demo',1);
INSERT INTO "ajustes" VALUES('utm_valor',72440);
CREATE TABLE historial_licitacion (
                id_evento INTEGER PRIMARY KEY AUTOINCREMENT,
                id_licitacion TEXT NOT NULL,
                fecha TEXT NOT NULL DEFAULT '',
                usuario TEXT NOT NULL DEFAULT '',
                tipo TEXT NOT NULL DEFAULT '',
                detalle TEXT NOT NULL DEFAULT ''
            );
CREATE TABLE historial_oc (
                id_oc INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL DEFAULT '',
                organismo TEXT NOT NULL DEFAULT '',
                objeto TEXT NOT NULL DEFAULT '',
                monto INTEGER NOT NULL DEFAULT 0,
                modalidad TEXT NOT NULL DEFAULT '',
                archivo TEXT NOT NULL DEFAULT '',
                cargado_en TEXT NOT NULL DEFAULT ''
            );
CREATE TABLE licitaciones (
                id_licitacion TEXT PRIMARY KEY,
                titulo TEXT NOT NULL,
                organismo TEXT NOT NULL,
                categoria TEXT NOT NULL,
                modalidad TEXT NOT NULL,
                region TEXT NOT NULL,
                presupuesto_mandante INTEGER NOT NULL,
                costo_base_hotel INTEGER NOT NULL,
                estado_embudo TEXT NOT NULL,
                validacion_adjuntos TEXT NOT NULL,
                tiene_anexo4 INTEGER NOT NULL DEFAULT 1,
                tiene_escrituras INTEGER NOT NULL DEFAULT 1,
                tiene_poderes INTEGER NOT NULL DEFAULT 1,
                tiene_vigencias INTEGER NOT NULL DEFAULT 1,
                fecha_publicacion TEXT NOT NULL,
                fecha_cierre TEXT NOT NULL,
                descripcion_tdr TEXT,
                cantidad_asistentes INTEGER NOT NULL DEFAULT 0,
                tipo_jornada TEXT NOT NULL DEFAULT '',
                horario_evento TEXT NOT NULL DEFAULT '',
                id_salon_asignado TEXT NOT NULL DEFAULT '',
                propiedad TEXT NOT NULL DEFAULT 'Plaza San Francisco',
                revisada INTEGER NOT NULL DEFAULT 0,
                motivo_descarte TEXT NOT NULL DEFAULT '',
                descripcion_descarte TEXT NOT NULL DEFAULT '',
                notas TEXT NOT NULL DEFAULT '',
                costeo_validado INTEGER NOT NULL DEFAULT 0,
                sello_mujer INTEGER NOT NULL DEFAULT 0,
                jornada_40h INTEGER NOT NULL DEFAULT 0,
                sello_sernatur INTEGER NOT NULL DEFAULT 0,
                inclusion_laboral INTEGER NOT NULL DEFAULT 0,
                adjudicatario TEXT NOT NULL DEFAULT '',
                puntaje_adjudicacion REAL NOT NULL DEFAULT 0,
                precio_final INTEGER NOT NULL DEFAULT 0,
                actualizado_en TEXT NOT NULL DEFAULT ''
            );
INSERT INTO "licitaciones" VALUES('1058-12-COT26','Servicio de Banquetería y Salones Jornada de Planificación Estrategica','Subsecretaría de Turismo','Eventos / Catering','Compra Agil','Región Metropolitana (Santiago)',5800000,4200000,'Cerrada','Valida',1,1,1,1,'2026-09-12','2026-09-20','Arriendo de salon plenario para 80 asistentes con servicio de coctel y coffee break continuo.',80,'Jornada Completa (8 hrs)','08:30 a 18:30 hrs','SALON-DANUBIO','Plaza San Francisco',0,'','','',0,0,0,0,0,'',0.0,0,'');
INSERT INTO "licitaciones" VALUES('723-4-LP26','Hospedaje y Alimentación Delegacion Internacional Encuentro Minero','Ministerio de Minería','Alojamiento','Licitacion Publica','Región Metropolitana (Santiago)',28000000,22500000,'Cerrada','Valida',1,1,1,1,'2026-09-08','2026-09-28','Alojamiento single superior para 35 expertos extranjeros durante 4 noches con desayuno y cena ejecutiva.',35,'Jornada Completa (8 hrs)','09:00 a 18:00 hrs','SALON-PARRA','Plaza San Francisco',0,'','','',0,0,0,0,0,'',0.0,0,'');
INSERT INTO "licitaciones" VALUES('1840-22-COT26','Catering y Coffee Break Seminario Innovacion Publica','Dirección de Presupuestos (DIPRES)','Eventos / Catering','Compra Agil','Región Metropolitana (Santiago)',6400000,6700000,'Cerrada','Valida',1,1,1,1,'2026-09-14','2026-09-21','Servicio de alimentacion para 120 personas. El presupuesto mandante queda por debajo del costo base hotel.',120,'Media Jornada Manana (4 hrs)','08:30 a 13:00 hrs','SALON-PERGOLA','Plaza San Francisco',0,'','','',0,0,0,0,0,'',0.0,0,'');
INSERT INTO "licitaciones" VALUES('512-10-LE26','Alojamiento y Salones para Conferencia Anual de Rectores','Consejo de Rectores de las Universidades Chilenas (CRUCH)','Alojamiento','Licitacion Publica','Región Metropolitana (Santiago)',18500000,14200000,'Cerrada','Valida',1,1,1,1,'2026-08-25','2026-09-15','Bloqueo de 40 habitaciones ejecutivas y uso de salon de convenciones durante 2 jornadas.',60,'Jornada Completa (8 hrs)','08:30 a 19:00 hrs','SALON-DANUBIO','Plaza San Francisco',0,'','','',0,0,0,0,0,'',0.0,0,'');
INSERT INTO "licitaciones" VALUES('930-15-LP26','Servicio Integral de Eventos de Cierre Ano Fiscal','Servicio de Impuestos Internos (SII)','Eventos / Catering','Licitacion Publica','Región Metropolitana (Santiago)',12000000,9500000,'Adjudicada','Valida',1,1,1,1,'2026-08-01','2026-08-20','Cena de premiacion anual en salon principal para 150 colaboradores. Adjudicado con exito.',150,'Nocturno / Cena','19:30 a 23:30 hrs','SALON-PERGOLA','Plaza San Francisco',0,'','','',0,0,0,0,0,'',0.0,0,'');
INSERT INTO "licitaciones" VALUES('440-8-COT26','Alojamiento de Emergencia Personal Medico','Servicio de Salud Metropolitano Central','Alojamiento','Compra Agil','Región Metropolitana (Santiago)',4500000,3800000,'Cerrada','Valida',0,1,1,1,'2026-09-13','2026-09-18','Hospedaje por turnos rotativos. Nota: Falta Anexo 4 de Pacto de Integridad en bases iniciales.',20,'Horario Especial','Turnos rotativos 24 hrs','','Plaza San Francisco',0,'','','',0,0,0,0,0,'',0.0,0,'');
INSERT INTO "licitaciones" VALUES('805-19-LP26','Arriendo de Salones y Equipamiento Audiovisual para Foro Regional','Gobierno Regional Metropolitano de Santiago','Eventos / Catering','Licitacion Publica','Región Metropolitana (Santiago)',9800000,7500000,'Cerrada','Error ID / Discrepancia',1,1,1,1,'2026-09-11','2026-09-24','Alerta Efecto ID: El ID de la ficha resumen no coincide con el correlativo de las bases adjuntas.',250,'Jornada Completa (8 hrs)','08:00 a 18:00 hrs','SALON-PERGOLA','Plaza San Francisco',0,'','','',0,0,0,0,0,'',0.0,0,'');
INSERT INTO "licitaciones" VALUES('310-7-COT26','Servicio de Coctel Protocolar Visita Delegacion Extranjera','Ministerio de Relaciones Exteriores','Eventos / Catering','Compra Agil','Región Metropolitana (Santiago)',5100000,4100000,'Descartada','Valida',1,1,1,1,'2026-09-02','2026-09-09','Descartada por conflicto de disponibilidad de salones para la fecha requerida por el mandante.',70,'Media Jornada Tarde (4 hrs)','15:00 a 19:30 hrs','SALON-DANUBIO','Plaza San Francisco',0,'Disponibilidad','','',0,0,0,0,0,'',0.0,0,'');
INSERT INTO "licitaciones" VALUES('620-14-LE26','Hospedaje y Salones Seminario Internacional de Ciberseguridad','Agencia Nacional de Inteligencia','Alojamiento','Licitacion Publica','Región Metropolitana (Santiago)',22000000,17500000,'Cerrada','Valida',1,1,1,1,'2026-09-15','2026-10-02','Hospedaje para expositores internacionales y arriendo de salon plenario con cabinas de traduccion simultanea.',180,'Jornada Completa (8 hrs)','08:30 a 18:30 hrs','SALON-PERGOLA','Plaza San Francisco',0,'','','',0,0,0,0,0,'',0.0,0,'');
CREATE TABLE reservas_salones (
                id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
                id_salon TEXT NOT NULL,
                cliente_evento TEXT NOT NULL,
                organismo_o_empresa TEXT NOT NULL,
                tipo_evento TEXT NOT NULL,
                montaje TEXT NOT NULL DEFAULT '',
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT NOT NULL,
                horario TEXT NOT NULL,
                asistentes_estimados INTEGER NOT NULL DEFAULT 0,
                estado_reserva TEXT NOT NULL DEFAULT 'Confirmada',
                id_licitacion TEXT NOT NULL DEFAULT '',
                contacto_responsable TEXT NOT NULL DEFAULT '',
                observaciones TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (id_salon) REFERENCES salones(id_salon)
            );
INSERT INTO "reservas_salones" VALUES(1,'SALON-DANUBIO','Jornada de Planificación Estrategica de Turismo','Subsecretaría de Turismo','Licitación Estatal (Compra Agil)','','2026-09-20','2026-09-20','08:30 a 18:30 hrs',80,'Confirmada','1058-12-COT26','Camila Morales - Jefatura de Eventos','Bloqueo formal vinculado a orden de compra adjudicada. Servicio de coffee break continuo.');
INSERT INTO "reservas_salones" VALUES(2,'SALON-PERGOLA','Foro Regional de Sostenibilidad Urbana y Cambio Climatico','Gobierno Regional Metropolitano de Santiago (GORE)','Congreso Gubernamental','','2026-09-24','2026-09-25','08:00 a 18:00 hrs',250,'Confirmada','805-19-LP26','Rodrigo Valenzuela - Direccion de Comunicaciones GORE','Uso de amplificacion total, cabinas de interpretacion y acreditacion de delegaciones.');
INSERT INTO "reservas_salones" VALUES(3,'SALON-PERGOLA','Encuentro Trimestral de Politica Financiera y Proyecciones','Banco Central de Chile','Evento Corporativo Institucional','','2026-09-22','2026-09-22','09:00 a 14:00 hrs',130,'Confirmada','','Patricia Silva - Departamento de Protocolo','Montaje tipo auditorio con servicio de desayuno ejecutivo previo y coctel de cierre.');
INSERT INTO "reservas_salones" VALUES(4,'SALON-PARRA','Sesion Mensual de Comite de Innovacion Industrial','SOFOFA / Federacion Gremial','Reunión Gremial Privada','','2026-09-23','2026-09-23','14:00 a 19:00 hrs',35,'Confirmada','','Ignacio Larrain - Coordinacion Sectorial','Mesa en herradura, videoconferencia internacional y estacion permanente de cafe.');
INSERT INTO "reservas_salones" VALUES(5,'SALON-SENA','Junta Extraordinaria de Directorio y Finanzas','Hotel Plaza San Francisco (Directorio General)','Bloqueo Interno / Sesion de Directorio','','2026-09-26','2026-09-26','08:30 a 13:30 hrs',18,'Confirmada','','Gerencia de Administracion y Finanzas','Revision de presupuestos semestrales y politicas comerciales de licitaciones publicas.');
INSERT INTO "reservas_salones" VALUES(6,'SALON-PERGOLA','Mantencion Preventiva de Iluminacion Escenica y Climatizacion','Servicios de Infraestructura Hotelera','Bloqueo de Mantenimiento Operativo','','2026-09-29','2026-09-30','07:00 a 19:00 hrs',0,'Bloqueo Interno','','Jefatura Tecnica de Mantenimiento','Calibracion tecnica de proyectores laser y revision de ductos de climatizacion central.');
INSERT INTO "reservas_salones" VALUES(7,'SALON-PERGOLA','Seminario de Gestion Presupuestaria del Sector Publico','Direccion de Presupuestos (DIPRES)','Licitación Estatal (Compra Agil)','','2026-10-05','2026-10-05','08:30 a 13:00 hrs',120,'Tentativa','1840-22-COT26','Marcelo Fuentes - Adquisiciones DIPRES','Pre-reserva en espera de adjudicacion final en portal Mercado Publico.');
INSERT INTO "reservas_salones" VALUES(8,'SALON-DANUBIO','Conferencia Anual de Rectores Universitarios','Consejo de Rectores de las Universidades Chilenas (CRUCH)','Congreso Academico','','2026-10-10','2026-10-11','08:30 a 19:00 hrs',60,'Confirmada','512-10-LE26','Secretaria General CRUCH','Jornada doble con uso continuo de pantalla interactiva y servicio gastronomico.');
CREATE TABLE salones (
                id_salon TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                tipo TEXT NOT NULL,
                capacidad_maxima INTEGER NOT NULL,
                horario_disponible TEXT NOT NULL,
                tarifa_referencial INTEGER NOT NULL DEFAULT 0,
                ubicacion TEXT NOT NULL DEFAULT '',
                equipamiento TEXT NOT NULL DEFAULT '',
                descripcion TEXT NOT NULL DEFAULT '',
                propiedad TEXT NOT NULL DEFAULT 'Plaza San Francisco',
                montajes TEXT NOT NULL DEFAULT '',
                es_provisional INTEGER NOT NULL DEFAULT 0
            );
INSERT INTO "salones" VALUES('SALON-EJECUTIVO','Salón Ejecutivo','Mesa ejecutiva',8,'Por confirmar con el hotel',0,'Piso 2 - 28 m2','Por confirmar con el hotel','Aforos del catalogo oficial: Mesa imperial (8). Superficie 28 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','Mesa imperial',0);
INSERT INTO "salones" VALUES('SALON-ALERCE','Salón Alerce','Sala de reuniones',30,'Por confirmar con el hotel',0,'Piso -2 - 41 m2','Por confirmar con el hotel','Aforos del catalogo oficial: U (20), Auditorio (30), Mesa imperial (20), Escuela (25), Mesa redonda 1,50 m (10 pax) (30), Mesa redonda 1,20 m (5 pax) (20). Superficie 41 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','U, Auditorio, Mesa imperial, Escuela, Mesa redonda 1,50 m (10 pax), Mesa redonda 1,20 m (5 pax)',0);
INSERT INTO "salones" VALUES('SALON-ROBLE','Salón Roble','Sala de reuniones',30,'Por confirmar con el hotel',0,'Piso -2 - 41 m2','Por confirmar con el hotel','Aforos del catalogo oficial: U (20), Auditorio (30), Mesa imperial (20), Escuela (25), Mesa redonda 1,50 m (10 pax) (30), Mesa redonda 1,20 m (5 pax) (20). Superficie 41 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','U, Auditorio, Mesa imperial, Escuela, Mesa redonda 1,50 m (10 pax), Mesa redonda 1,20 m (5 pax)',0);
INSERT INTO "salones" VALUES('SALON-MISTRAL','Salón Mistral','Sala de reuniones',30,'Por confirmar con el hotel',0,'Piso -1 - 47 m2','Por confirmar con el hotel','Aforos del catalogo oficial: U (20), Auditorio (30), Mesa imperial (20), Escuela (25), Mesa redonda 1,50 m (10 pax) (30), Mesa redonda 1,20 m (5 pax) (25). Superficie 47 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','U, Auditorio, Mesa imperial, Escuela, Mesa redonda 1,50 m (10 pax), Mesa redonda 1,20 m (5 pax)',0);
INSERT INTO "salones" VALUES('SALON-NERUDA','Salón Neruda','Sala de reuniones',30,'Por confirmar con el hotel',0,'Piso -1 - 50 m2','Por confirmar con el hotel','Aforos del catalogo oficial: U (20), Auditorio (30), Mesa imperial (20), Escuela (25), Mesa redonda 1,50 m (10 pax) (30), Mesa redonda 1,20 m (5 pax) (20). Superficie 50 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','U, Auditorio, Mesa imperial, Escuela, Mesa redonda 1,50 m (10 pax), Mesa redonda 1,20 m (5 pax)',0);
INSERT INTO "salones" VALUES('SALON-PARRA','Salón Parra','Sala de reuniones',40,'Por confirmar con el hotel',0,'Piso -1 - 62 m2','Por confirmar con el hotel','Aforos del catalogo oficial: U (20), Auditorio (35), Mesa imperial (20), Escuela (25), Mesa redonda 1,50 m (10 pax) (40), Mesa redonda 1,20 m (5 pax) (25). Superficie 62 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','U, Auditorio, Mesa imperial, Escuela, Mesa redonda 1,50 m (10 pax), Mesa redonda 1,20 m (5 pax)',0);
INSERT INTO "salones" VALUES('SALON-EBRO','Salón Ebro','Sala de reuniones',30,'Por confirmar con el hotel',0,'Piso 2 - 48 m2','Por confirmar con el hotel','Aforos del catalogo oficial: U (20), Auditorio (30), Mesa imperial (20), Escuela (25), Mesa redonda 1,50 m (10 pax) (30), Mesa redonda 1,20 m (5 pax) (25). Superficie 48 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','U, Auditorio, Mesa imperial, Escuela, Mesa redonda 1,50 m (10 pax), Mesa redonda 1,20 m (5 pax)',0);
INSERT INTO "salones" VALUES('SALON-TIBER','Salón Tiber','Sala de reuniones',30,'Por confirmar con el hotel',0,'Piso 2 - 46 m2','Por confirmar con el hotel','Aforos del catalogo oficial: U (15), Auditorio (20), Mesa imperial (15), Escuela (20), Mesa redonda 1,50 m (10 pax) (30), Mesa redonda 1,20 m (5 pax) (25), Coctel de pie (15). Superficie 46 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','U, Auditorio, Mesa imperial, Escuela, Mesa redonda 1,50 m (10 pax), Mesa redonda 1,20 m (5 pax), Coctel de pie',0);
INSERT INTO "salones" VALUES('SALON-VOLGA','Salón Volga','Sala de reuniones',30,'Por confirmar con el hotel',0,'Piso 2 - 49 m2','Por confirmar con el hotel','Aforos del catalogo oficial: U (20), Auditorio (30), Mesa imperial (20), Escuela (25), Mesa redonda 1,50 m (10 pax) (30), Mesa redonda 1,20 m (5 pax) (25), Coctel de pie (30). Superficie 49 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','U, Auditorio, Mesa imperial, Escuela, Mesa redonda 1,50 m (10 pax), Mesa redonda 1,20 m (5 pax), Coctel de pie',0);
INSERT INTO "salones" VALUES('SALON-DUERO','Salón Duero','Salón de eventos',50,'Por confirmar con el hotel',0,'Piso 2 - 58 m2','Por confirmar con el hotel','Aforos del catalogo oficial: U (25), Auditorio (50), Mesa imperial (25), Escuela (30), Mesa redonda 1,50 m (10 pax) (40), Mesa redonda 1,20 m (5 pax) (30), Coctel de pie (30). Superficie 58 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','U, Auditorio, Mesa imperial, Escuela, Mesa redonda 1,50 m (10 pax), Mesa redonda 1,20 m (5 pax), Coctel de pie',0);
INSERT INTO "salones" VALUES('SALON-ARRAU','Salón Arrau','Salón de eventos',50,'Por confirmar con el hotel',0,'Piso -1 - 62 m2','Por confirmar con el hotel','Aforos del catalogo oficial: U (25), Auditorio (50), Mesa imperial (25), Escuela (30), Mesa redonda 1,50 m (10 pax) (40), Mesa redonda 1,20 m (5 pax) (30), Coctel de pie (30). Superficie 62 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','U, Auditorio, Mesa imperial, Escuela, Mesa redonda 1,50 m (10 pax), Mesa redonda 1,20 m (5 pax), Coctel de pie',0);
INSERT INTO "salones" VALUES('SALON-ARAUCARIA','Salón Araucaria','Salón de gran capacidad',100,'Por confirmar con el hotel',0,'Piso -2 - 105 m2','Por confirmar con el hotel','Aforos del catalogo oficial: U (40), Auditorio (100), Mesa imperial (40), Escuela (60), Mesa redonda 1,50 m (10 pax) (80), Mesa redonda 1,20 m (5 pax) (40), Coctel de pie (60). Superficie 105 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','U, Auditorio, Mesa imperial, Escuela, Mesa redonda 1,50 m (10 pax), Mesa redonda 1,20 m (5 pax), Coctel de pie',0);
INSERT INTO "salones" VALUES('SALON-SENA','Salón Sena','Salón de eventos',60,'Por confirmar con el hotel',0,'Piso 2 - 65 m2','Por confirmar con el hotel','Aforos del catalogo oficial: U (30), Auditorio (60), Mesa imperial (30), Escuela (35), Mesa redonda 1,50 m (10 pax) (50), Mesa redonda 1,20 m (5 pax) (30), Coctel de pie (40). Superficie 65 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','U, Auditorio, Mesa imperial, Escuela, Mesa redonda 1,50 m (10 pax), Mesa redonda 1,20 m (5 pax), Coctel de pie',0);
INSERT INTO "salones" VALUES('SALON-DANUBIO','Salón Danubio','Salón de gran capacidad',100,'Por confirmar con el hotel',0,'Piso 2 - 108 m2','Por confirmar con el hotel','Aforos del catalogo oficial: U (35), Auditorio (100), Mesa imperial (35), Escuela (50), Mesa redonda 1,50 m (10 pax) (70), Mesa redonda 1,20 m (5 pax) (40), Coctel de pie (80). Superficie 108 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','U, Auditorio, Mesa imperial, Escuela, Mesa redonda 1,50 m (10 pax), Mesa redonda 1,20 m (5 pax), Coctel de pie',0);
INSERT INTO "salones" VALUES('SALON-RHIN','Salón Rhin','Salón de eventos',60,'Por confirmar con el hotel',0,'Piso 2 - 84 m2','Por confirmar con el hotel','Aforos del catalogo oficial: U (20), Auditorio (60), Mesa imperial (20), Escuela (30), Mesa redonda 1,50 m (10 pax) (50), Mesa redonda 1,20 m (5 pax) (30), Coctel de pie (60). Superficie 84 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','U, Auditorio, Mesa imperial, Escuela, Mesa redonda 1,50 m (10 pax), Mesa redonda 1,20 m (5 pax), Coctel de pie',0);
INSERT INTO "salones" VALUES('SALON-PERGOLA','Salón Pergola','Salón de gran capacidad',450,'Por confirmar con el hotel',0,'Piso 1 - 362 m2','Por confirmar con el hotel','Aforos del catalogo oficial: U (60), Auditorio (450), Mesa imperial (60), Escuela (200), Mesa redonda 1,50 m (10 pax) (280), Mesa redonda 1,20 m (5 pax) (150), Coctel de pie (300). Superficie 362 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','U, Auditorio, Mesa imperial, Escuela, Mesa redonda 1,50 m (10 pax), Mesa redonda 1,20 m (5 pax), Coctel de pie',0);
INSERT INTO "salones" VALUES('SALON-TAM','Salón Tam','Salón de eventos',50,'Por confirmar con el hotel',0,'Piso 2 - 50 m2','Por confirmar con el hotel','Aforos deducidos de las combinaciones Danubio Abierto (158 m2) y Dan+Tam+Rhin (242 m2); el salon no tiene fila propia en el catalogo, confirmar con el hotel: Escuela (50), Mesa redonda 1,50 m (10 pax) (30), Coctel de pie (20). Superficie 50 m2. Tarifa por confirmar con el hotel.','Plaza San Francisco','Escuela, Mesa redonda 1,50 m (10 pax), Coctel de pie',1);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('reservas_salones',8);
COMMIT;
