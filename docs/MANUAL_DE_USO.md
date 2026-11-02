# Manual de uso

**Asistente Virtual de Licitaciones**
Hotel Plaza San Francisco | Programa de Vinculacion con el Medio, DUOC UC

Este manual esta escrito para el equipo comercial que usa la plataforma todos los
dias. Para la parte tecnica (arquitectura, despliegue, convenciones de codigo)
ver `README.md` y `docs/WORKFLOW.md`.

---

## 1. Que hace la plataforma

Centraliza la revision de licitaciones de Mercado Publico que el hotel puede
atender, y descarta temprano las que no son viables.

El alcance es **estrictamente intramuros** del hotel:

| Se puede ofrecer | Donde |
|---|---|
| Salones, eventos y A&B / catering | Solo Hotel Plaza San Francisco |
| Alojamiento corporativo | Hotel Plaza San Francisco y Hotel Ismael |

Queda fuera de alcance cualquier servicio de banqueteria o produccion fuera del
hotel, aunque la licitacion sea de un cliente conocido.

---

## 2. Puesta en marcha

### 2.1 Requisitos

- Python 3.10 o superior (verificado en Python 3.12).
- Ticket de la API de Mercado Publico (se obtiene en `api.mercadopublico.cl`).
- Conexion a internet, solo para sincronizar. El resto de la plataforma funciona
  sin red.

### 2.2 Instalacion

```bash
pip install -r requirements.txt
```

Son solo dos dependencias: Flask y openpyxl (esta ultima solo se usa para
importar el historial de ordenes de compra desde Excel; si falta, la plataforma
funciona igual y avisa al intentar importar un `.xlsx`).

### 2.3 Configuracion (archivo `.env`)

Copiar `.env.example` a `.env` y completar:

| Variable | Obligatoria | Para que sirve |
|---|---|---|
| `MERCADO_PUBLICO_TICKET` | Si | Ticket de la API. Sin el no se puede sincronizar. |
| `FLASK_SECRET_KEY` | Si al exponer el servidor | Firma las sesiones. Sin el, la sesion se pierde al reiniciar. |
| `LICITACIONES_PASSWORD_<USUARIO>` | Si al exponer el servidor | Reemplaza las claves demo. Ejemplo: `LICITACIONES_PASSWORD_DANIELA`. |
| `MERCADO_PUBLICO_INTERVALO_MS` | No | Milisegundos entre consultas a la API. Por defecto 500. |
| `HOST` / `PORT` | No | Donde escucha el servidor. Por defecto `127.0.0.1:5000`. |
| `RESUMEN_IA_API_KEY` | No | Activa el enriquecimiento con IA de la ficha resumen. Sin ella se usa la version por reglas. |

### 2.4 Arranque

```bash
python run.py
```

Abrir en el navegador: `http://127.0.0.1:5000`

El servidor se detiene con `CTRL+C`.

Por seguridad, si `HOST` no es local la plataforma **se niega a arrancar** cuando
detecta claves demo o falta `FLASK_SECRET_KEY`.

---

## 3. Acceso y perfiles

| Usuario | Clave demo | Perfil |
|---|---|---|
| `admin` | `admin123` | Administrador |
| `daniela` | `daniela123` | Daniela |
| `francisca` | `francisca123` | Francisca |
| `mari` | `mari123` | Mari Carmen |

**Importante:** estas claves estan en el codigo y son solo para pruebas. Antes de
publicar la plataforma en la red del hotel hay que reemplazarlas con
`LICITACIONES_PASSWORD_<USUARIO>` en `.env`.

Los cuatro perfiles **ven exactamente lo mismo**. No hay datos separados por
persona: los estados, las evaluaciones y las notas son compartidos, para que
cualquiera pueda retomar una licitacion que otro empezo. Lo que identifica quien
hizo cada cambio es el autor de la nota.

Tras 5 intentos fallidos desde la misma IP, el acceso se bloquea por 5 minutos.

---

## 4. Flujo diario recomendado

1. **Sincronizar.** En la pantalla Licitaciones, boton `Sincronizar Mercado
   Publico`. Sin fecha trae la ultima semana; con fecha trae solo ese dia.
2. **Revisar lo priorizado.** La franja "Oportunidades Priorizadas de Hoy"
   muestra lo que tiene presupuesto viable y capacidad compatible. Es el punto
   de partida real del dia.
3. **Abrir la ficha** de cada oportunidad y revisar el resumen, el presupuesto y
   el dimensionamiento del salon.
4. **Evaluar.** Completar asistentes, propiedad, salon propuesto y sellos.
   Guardar.
5. **Decidir.** Marcar como `Revisada`, `Participamos` o `No participamos` (con
   motivo). Esto deja el registro de por que se tomo la decision.
6. **Dejar nota** si hay contexto que el resto del equipo necesita saber.

---

## 5. Pantalla por pantalla

### 5.1 Licitaciones (inicio)

Es la pantalla principal. Arriba estan los indicadores del embudo:
oportunidades, calificadas, participadas, adjudicadas y descartadas.

**Barra de filtros**

| Filtro | Que hace |
|---|---|
| Busqueda general | Busca en ID, titulo y organismo. Atajo de teclado: `/`. |
| Propiedad | Plaza San Francisco o Hotel Ismael. |
| Cliente Clave | Filtra los organismos marcados como prioritarios (Mineduc, Minsal, U. de Chile, Usach, Productoras). |
| Categoria Comercial | Alojamiento o Eventos / Catering (incluye A&B). |
| Modalidad de Compra | Compra Agil o Licitacion Publica. |
| Estado en Embudo | Identificada, Calificada, Participada, Adjudicada, Descartada. |

Los filtros tambien aplican a la vista priorizada y a la exportacion.

**Botones**

- `Exportar a Excel`: descarga un CSV con el listado filtrado. Excel lo abre
  directamente.
- `Sincronizar Mercado Publico`: consulta la API. Ver tiempos en la seccion 8.
- `Margen de tolerancia`: se puede definir como porcentaje del presupuesto o
  como monto fijo en CLP. Es el colchon que se acepta al comparar presupuesto
  contra costo.
- `Tope Compra Agil`: monto de referencia del limite normativo de compra agil.
  Si el presupuesto de una licitacion de esa modalidad lo supera, la ficha
  muestra una advertencia legal.

**Oportunidades Priorizadas de Hoy**

Cada tarjeta muestra el ID destacado, el titulo, el organismo, la fecha de
cierre, el presupuesto, el margen estimado y el salon propuesto. El ID y el
boton `Mercado Publico` abren la publicacion original en el portal.

Cuando no hay tarjetas, el mensaje indica si es porque no hay oportunidades
abiertas o porque los filtros actuales no dejan pasar ninguna.

### 5.2 Ficha de la licitacion

Se abre haciendo clic en el ID o en el titulo. Contiene estos bloques:

**Ficha Resumen**
Fechas, numero de personas, espacio requerido, alimentacion y el desglose de
ponderacion de criterios, que suma 100 puntos. Se genera por reglas
deterministicas; si hay proveedor de IA configurado, se enriquece, pero nunca
depende de ella para funcionar. Si la IA falla, se muestra el aviso y se usa el
texto por reglas.

**Control Presupuestario Preventivo**
Compara presupuesto mandante contra costo base del hotel y muestra el margen.
Aplica la regla mandatoria: si el costo base supera el presupuesto, la
oportunidad se descarta por precio.

**Evaluacion Operativa y Costeo Minimo**
Aqui se completa:

| Campo | Detalle |
|---|---|
| Propiedad | Si se elige Hotel Ismael, el selector de salon se desactiva: Ismael solo admite alojamiento. |
| Asistentes / Personas | Base para el dimensionamiento y el costeo. |
| Tipo de jornada y horario | Texto libre para el evento. |
| Salon propuesto | Lista de los 17 salones con su aforo. |
| Costo base minimo | Si se deja vacio, se calcula con la tarifa del salon mas el consumo por persona. |
| Sellos | Sello Mujer, Jornada de 40 horas, Sello Sernatur, Inclusion laboral. |

**Dimensionamiento Operativo, Aforo y Horarios de Salones**
Muestra los salones compatibles con el aforo y una advertencia permanente:
*la disponibilidad final se valida en el PMS del hotel*. La plataforma no se
sincroniza con el PMS ni con Mercado Publico para disponibilidad.

**Benchmarking de Adjudicacion**
Registro manual del resultado de procesos anteriores: adjudicatario, puntaje y
precio final. La API publica de Mercado Publico no expone puntajes, por eso se
carga a mano.

**Validacion de Consistencia Documental**
Cruza el ID de la licitacion con el correlativo de las bases adjuntas y avisa si
no coinciden.

**Checklist de Admisibilidad Administrativa Formal**
Lista de verificacion de documentos y requisitos formales.

**Notas Compartidas del Equipo**
Historial de notas con autor y fecha. Es el canal para dejar contexto entre
turnos.

**Sintesis de Terminos de Referencia (TDR)**
Resumen de lo que pide el documento.

**Decisiones**

| Boton | Efecto |
|---|---|
| `Revisada` | Marca la oportunidad como vista, sin cambiar de estado. |
| `Participamos` | Pasa a estado Participada. **Se bloquea si el costo base supera el presupuesto.** |
| `No participamos` | Pasa a Descartada y exige un motivo. |

Motivos de descarte: `Precio`, `Disponibilidad`, `Fuera de alcance`, `Otro`.

### 5.3 Salones y Agenda

**Catalogo de Infraestructura de Salones**
Los 17 salones del hotel con piso, superficie, aforo maximo y el desglose de
aforos por montaje (auditorio, escuela, imperial, U, mesas redondas de 1,50 m y
1,20 m, coctel). Se puede filtrar por salon y buscar por cliente u organismo.

| Salon | Piso | Superficie | Aforo maximo |
|---|---|---|---|
| Pergola | 1 | 362 m2 | 450 |
| Araucaria | -2 | 105 m2 | 100 |
| Danubio | 2 | 108 m2 | 100 |
| Sena | 2 | 65 m2 | 60 |
| Rhin | 2 | 84 m2 | 60 |
| Duero | 2 | 58 m2 | 50 |
| Arrau | -1 | 62 m2 | 50 |
| Tam | 2 | 50 m2 | 50 |
| Parra | -1 | 62 m2 | 40 |
| Alerce | -2 | 41 m2 | 30 |
| Roble | -2 | 41 m2 | 30 |
| Mistral | -1 | 47 m2 | 30 |
| Neruda | -1 | 50 m2 | 30 |
| Ebro | 2 | 48 m2 | 30 |
| Tiber | 2 | 46 m2 | 30 |
| Volga | 2 | 49 m2 | 30 |
| Ejecutivo | 2 | 28 m2 | 8 |

El Salon Tam aparece marcado como **provisional**: el documento del hotel no le
dedica una fila propia y sus aforos se deducen de las combinaciones "Danubio
Abierto" y "Dan + Tam + Rhin". Conviene confirmarlo con el hotel.

**Agenda de Ocupacion**
Reservas y bloqueos por fecha, con deteccion de colisiones. Al crear una reserva
la plataforma avisa si el salon ya esta ocupado en ese rango de fechas.

### 5.4 Analitica

Dos bloques:

- **Benchmarking de Adjudicaciones**: consolidado de los resultados cargados en
  las fichas.
- **Historial de Ordenes de Compra**: importador de `.xlsx` o `.csv`. Los
  encabezados son tolerantes a variantes de nombre. Con estos datos, la ficha de
  una licitacion muestra la experiencia previa con ese organismo.

### 5.5 Informes

Resumen ejecutivo con oportunidades, presupuesto total, costo base, margen
proyectado, el embudo por estado y la tasa de cierre. Ademas:

- Demanda por categoria.
- Principales organismos.
- Motivos de descarte.

Se puede descargar todo con `Exportar CSV`.

---

## 6. Reglas de negocio que aplica la plataforma

Entenderlas evita pelearse con el sistema:

1. **Alcance intramuros.** Solo salones, alojamiento y A&B del hotel. No se
   ofrecen servicios fuera del hotel.
2. **El presupuesto manda.** Si el costo base supera el presupuesto del
   mandante, la oportunidad se descarta por precio y no se puede marcar como
   Participamos.
3. **La comuna no descarta.** Las Condes, Vitacura o cualquier otra comuna no
   son motivo de descarte. La region es solo informativa.
4. **Disponibilidad es manual.** El match de salones es por capacidad; la
   disponibilidad real la confirma una persona en el PMS.
5. **Hotel Ismael solo hospedaje.** Nunca salones ni eventos.
6. **Tolerancia a errores de tipeo.** La busqueda reconoce variantes como
   "catring" o "hospedagh" cuando la coincidencia exacta no encuentra nada. Si
   el texto no se parece a nada del vocabulario, no se fuerza una clasificacion.
7. **Costeo provisional.** Mientras no se carguen las tarifas reales, el costo
   se estima y no se descarta automaticamente por presupuesto hasta que una
   persona valide el costo.

---

## 7. Estados del embudo

| Estado | Significa |
|---|---|
| `Identificada` | Recien sincronizada, sin revisar. |
| `Calificada` | Revisada y con posibilidad real de participar. |
| `Participada` | El equipo decidio ofertar. |
| `Adjudicada` | Ganada. |
| `Descartada` | No se participa, siempre con motivo registrado. |

---

## 8. Problemas frecuentes

**La sincronizacion se demora varios minutos.**
Es normal. Sin fecha sincroniza 7 dias y puede tomar entre 5 y 7 minutos; con una
fecha especifica toma alrededor de 1 minuto. La demora es intencional: la API
limita la cantidad de consultas por minuto.

**Aparece el aviso "La API bloqueo N consulta(s)".**
La plataforma espacia las consultas y reintenta, pero si el bloqueo persiste
algunas fichas quedan sin datos de detalle. Solucion: subir
`MERCADO_PUBLICO_INTERVALO_MS` a 1000 en `.env` y repetir la sincronizacion, o
sincronizar dia por dia usando el campo de fecha.

**No aparecen licitaciones nuevas.**
Revisar que los filtros esten limpios y que la sincronizacion haya terminado sin
errores. Si el ticket de la API no esta configurado, la sincronizacion se omite y
lo informa.

**Una licitacion aparece con "Salon por asignar".**
No hay ningun salon con aforo suficiente, o nadie ha completado la evaluacion
operativa. Abrir la ficha y revisar el bloque de dimensionamiento.

**La tarifa del salon aparece en $0.**
Es correcto por ahora: el catalogo oficial del hotel no publica tarifas. Mientras
no se carguen, el costo minimo solo considera el consumo por persona.

**El historial de ordenes de compra esta vacio.**
Nunca se ha importado. Cargarlo desde Analitica con el Excel del hotel.

**No puedo marcar Participamos.**
El costo base supera el presupuesto mandante. Ajustar el costeo o registrar el
descarte con su motivo.

---

## 9. Datos que aun faltan cargar

Estos datos los tiene el hotel, no la plataforma:

1. **Tarifas por salon.** El documento oficial trae aforos y superficies, pero no
   precios.
2. **Equipamiento por salon.** Hoy figura como "Por confirmar con el hotel".
3. **Aforos del Salon Tam.** Deducidos de las combinaciones; confirmar.
4. **Historico de ordenes de compra** en Excel o CSV.
5. **Claves definitivas** de los cuatro perfiles.
6. **Proveedor de IA** para la ficha resumen, si se decide usarlo.

---

## 10. Para el equipo tecnico

- Verificacion obligatoria antes de integrar cambios:

```bash
python verify.py
```

- La base de datos es SQLite (`licitaciones.db`) y se inicializa sola al arrancar.
- Toda la plataforma es web: no se instala nada en los puestos de trabajo del
  hotel, solo se abre el navegador.
- Convenciones de ramas, commits e integracion en `docs/WORKFLOW.md`.
- Matriz de brechas contra la reunion de levantamiento en
  `docs/ALINEACION_REUNION.md`.
