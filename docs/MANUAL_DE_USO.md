# Manual de uso

**Asistente Virtual de Licitaciones**
Hotel Plaza San Francisco | Programa de Vinculacion con el Medio, DUOC UC

Este manual esta escrito para el equipo comercial que usa la plataforma todos los
dias. Para instalacion, despliegue y detalles tecnicos ver `README.md` y
`docs/WORKFLOW.md`.

---

## 1. Que hace la plataforma

Centraliza la revision de licitaciones de Mercado Publico que el hotel puede
atender, descarta temprano las que no son viables y deja registro de quien
reviso, evaluo y decidio cada oportunidad.

El alcance es **estrictamente intramuros** del hotel:

| Se puede ofrecer | Donde |
|---|---|
| Salones, eventos y A&B / catering | Solo Hotel Plaza San Francisco |
| Alojamiento corporativo | Hotel Plaza San Francisco y Hotel Ismael |

Queda fuera de alcance cualquier servicio de banqueteria o produccion fuera del
hotel, aunque la licitacion sea de un cliente conocido.

---

## 2. Acceso

La direccion de la plataforma la entrega el administrador. En un equipo local es
`http://127.0.0.1:5000`.

| Usuario | Perfil |
|---|---|
| `admin` | Administrador |
| `daniela` | Daniela |
| `francisca` | Francisca |
| `mari` | Mari |

La clave de cada usuario la configura el administrador en el archivo `.env`
(`LICITACIONES_PASSWORD_<USUARIO>`). Las claves que aparecen en el codigo son
solo para pruebas locales y deben cambiarse antes de publicar la plataforma.

**Importante:** los cuatro perfiles ven exactamente lo mismo y pueden hacer las
mismas acciones. No hay datos separados por persona: estados, evaluaciones,
notas, reservas e historial son compartidos para que cualquiera pueda retomar
una licitacion que otro empezo.

Despues de 5 intentos fallidos desde la misma conexion, el acceso se bloquea por
5 minutos.

---

## 3. Flujo diario recomendado

1. **Sincronizar.** En Licitaciones, boton `Sincronizar Mercado Publico`. Sin
   fecha trae la ultima semana; con fecha trae solo ese dia.
2. **Revisar lo priorizado.** La franja "Oportunidades Priorizadas de Hoy"
   muestra lo que tiene presupuesto viable y capacidad compatible.
3. **Filtrar el listado** por estado, modalidad, cliente, motivo de descarte o
   persona que reviso.
4. **Abrir la ficha**, revisar el resumen, el presupuesto y el dimensionamiento
   del salon.
5. **Evaluar**: asistentes, propiedad, salon propuesto y sellos.
6. **Decidir**: `Revisada`, `Participamos` o `No participamos` con motivo y
   descripcion.
7. **Dejar nota** si hay contexto que el resto del equipo necesita saber.
8. **Revisar informes** al cierre de la semana o del mes.

---

## 4. Pantalla Licitaciones (inicio)

Es la pantalla principal. Arriba estan las metricas del embudo y mas abajo el
listado de oportunidades.

### 4.1 Metricas del embudo

| Tarjeta | Que muestra |
|---|---|
| Total Oportunidades | Todas las licitaciones registradas |
| Compra Agil | Cantidad y monto total sin comision de las compras agiles |
| Identificadas | Deteccion inicial, sin revisar |
| Calificadas | Revisadas y con posibilidad real de participar |
| Participadas | El equipo decidio ofertar |
| Adjudicadas | Procesos ganados |
| Descartadas | No se participa |

Cada tarjeta es clickeable: abre el listado con el filtro correspondiente y baja
directo a la seccion de resultados. El enlace `Ver oportunidades de Compra Agil`
hace lo mismo con la modalidad Compra Agil.

### 4.2 Ajustes rapidos

- **Margen de tolerancia:** margen minimo exigido para priorizar una
  oportunidad. Se puede definir como porcentaje del presupuesto o como monto
  fijo en CLP. No relaja el descarte cuando el costo supera el presupuesto.
- **Tope Compra Agil:** monto de referencia del limite normativo. Si una compra
  agil lo supera, la ficha y el listado muestran una advertencia. No descarta la
  licitacion automaticamente.

### 4.3 Filtros

| Filtro | Que hace |
|---|---|
| Busqueda general | Busca en ID, titulo, organismo, region y notas. Atajo: `/` |
| Cliente Clave | Mineduc, Minsal, universidades, productoras y otros clientes prioritarios |
| Categoria Comercial | Alojamiento o Eventos / Catering |
| Modalidad de Compra | Compra Agil o Licitacion Publica |
| Estado en Embudo | Identificada, Calificada, Participada, Adjudicada o Descartada |
| Motivo de Descarte | Precio, Disponibilidad, Fuera de alcance, Otro o Sin motivo |
| Revision | Todas, Pendientes sin revisar o Revisadas por una persona |

Los filtros se mantienen al paginar y tambien se aplican a la vista priorizada y
a la exportacion.

### 4.4 Listado de licitaciones

- Se muestran **hasta 8 licitaciones por pagina**.
- Cada fila muestra: ID, fecha de cierre, fecha y hora de actualizacion, titulo,
  organismo, region, cliente clave, categoria, modalidad, presupuesto, costo
  base y estado.
- **Revisada por:** si alguien marco la oportunidad como revisada, aparece el
  nombre y la fecha/hora de la ultima revision.
- **Viabilidad presupuestaria:** `Sobre tope Compra Agil`, `Monto no informado`,
  `Inviable / Costo Excede`, `Margen bajo el minimo` o `Viable / Margen
  Positivo`, con el monto de margen o deficit.
- **Cruce ID Adjuntos:** `ID Verificado`, `Discrepancia ID` o `Sin verificar`.
- La fila completa es clickeable y abre la ficha.

### 4.5 Botones

- `Exportar a Excel`: descarga un CSV con el listado filtrado, incluyendo quien
  reviso y la fecha de revision.
- `Sincronizar Mercado Publico`: consulta la API. Ver tiempos y limites en la
  seccion 8.

---

## 5. Ficha de la licitacion

Se abre haciendo clic en el ID, en el titulo o en cualquier parte de la fila.

### 5.1 Encabezado

Muestra el ID, categoria, cliente clave, estado de revision, motivo de descarte
si corresponde y modalidad. En la parte superior estan las acciones:

| Accion | Efecto |
|---|---|
| `Ver documentos` | Abre el visor oficial de anexos de Mercado Publico |
| `Ver ficha MD` / `Descargar .md` | Genera una ficha resumida en Markdown |
| `Refrescar ficha` | Vuelve a consultar la API y actualiza los datos oficiales |
| `Eliminar` | Borra la licitacion y su historial (accion irreversible) |

### 5.2 Ficha Resumen

Fechas, numero de personas, espacio requerido, alimentacion y un puntaje
ponderado con los criterios principales. Se genera por reglas deterministas; si
hay proveedor de IA configurado se enriquece, pero la plataforma funciona igual
sin IA. Si la IA falla, se muestra la version por reglas.

### 5.3 Control presupuestario

Compara el presupuesto mandante contra el costo base del hotel y muestra el
margen o el deficit. Si el costo base supera el presupuesto, la oportunidad no se
puede marcar como `Participamos` y se descarta por precio.

### 5.4 Evaluacion

| Campo | Detalle |
|---|---|
| Propiedad | Plaza San Francisco o Hotel Ismael |
| Asistentes / Personas | Base para el dimensionamiento y el costeo |
| Tipo de jornada y horario | Texto libre para el evento |
| Salon propuesto | Lista de salones con su aforo |
| Costo base minimo | Si se deja vacio, se calcula con la tarifa del salon y el consumo por persona |
| Sellos | Sello Mujer, Jornada de 40 horas, Sello Sernatur, Inclusion laboral |

Hotel Ismael solo admite alojamiento: si se elige esa propiedad, el selector de
salon se desactiva y no se permiten eventos.

### 5.5 Capacidad y salones

Muestra los salones compatibles con el aforo y advierte si el salon asignado no
tiene capacidad suficiente. El match es por capacidad; la disponibilidad real se
confirma en la agenda de salones y en el PMS del hotel.

### 5.6 Documentos y admisibilidad

- **Validacion de consistencia documental:** cruza el ID de la licitacion con el
  correlativo de las bases adjuntas y avisa si no coinciden.
- **Checklist de admisibilidad:** verifica Anexo 4, escrituras, poderes y
  vigencias. El estado puede ser `Valida`, `Error ID / Discrepancia` o `Sin
  verificar`.

### 5.7 Notas compartidas

Historial de notas con autor y fecha. Es el canal para dejar contexto entre
turnos o entre personas del equipo.

### 5.8 Historial de Actividad

Lista cronologica de todo lo que paso con la licitacion, con fecha, usuario,
tipo y detalle:

- cambios de estado
- decisiones (`Revisada`, `Participamos`, `No participamos`)
- evaluaciones de salon y costo
- notas
- validacion de documentos
- datos de adjudicacion
- refrescos desde Mercado Publico

Es la forma de saber **quien hizo que y cuando**, ademas del badge de revision.

### 5.9 Sintesis de Terminos de Referencia (TDR)

Resumen de lo que pide el documento.

### 5.10 Decisiones

| Boton | Efecto |
|---|---|
| `Marcar como Revisada` | Marca la oportunidad como vista y registra quien la reviso |
| `Participamos` | Pasa a estado Participada. Se bloquea si el costo base supera el presupuesto |
| `No participamos` | Pasa a Descartada y exige un motivo |

Al elegir `No participamos` se puede agregar una **descripcion del motivo**
(opcional, hasta 500 caracteres). Esa descripcion aparece en la ficha y en el
informe.

Debajo del boton de revision se muestra `Ultima revision: <nombre> - <fecha y
hora>` cuando ya existe una revision.

Motivos de descarte disponibles: `Precio`, `Disponibilidad`, `Fuera de alcance`
y `Otro`.

---

## 6. Salones y agenda

### 6.1 Catalogo de salones

Muestra los 17 salones del hotel con:

- direccion: `Av. Libertador Bernardo O'Higgins 816, Santiago`
- ubicacion interna: piso y superficie
- capacidad maxima
- aforos por montaje (auditorio, escuela, imperial, U, mesas redondas y coctel)
- equipamiento
- fechas ocupadas

Cada tarjeta tiene un boton `Ficha Tecnica` que abre el detalle en una ventana
emergente, sin salir de la pagina. El enlace `Ver Agenda de Fechas` lleva a la
agenda filtrada por ese salon.

La agenda se puede filtrar por salon y buscar por cliente u organismo. El
desplegable de clientes se alimenta de las reservas existentes.

### 6.2 Reservas

Estados disponibles: `Confirmada`, `Tentativa` y `Bloqueo Interno`.

Al crear o editar una reserva la plataforma valida:

- que el salon exista
- que las fechas tengan formato valido y la fecha de inicio no sea posterior a
  la de termino
- que la cantidad de asistentes no supere el aforo, cuando la reserva esta
  `Confirmada`
- que no exista otra reserva `Confirmada` en el mismo rango de fechas

Las reservas `Tentativa` y `Bloqueo Interno` no bloquean el salon, pero quedan
visibles en la agenda. Usar `Confirmada` solo cuando el evento este cerrado.

Una reserva se puede vincular a una licitacion para mantener la trazabilidad.

---

## 7. Historial de Adjudicacion y Ordenes de Compra

Se accede desde el menu `Historial de Adjudicacion` (pantalla Analitica).

### 7.1 Historial de Adjudicacion

Consolidado de los procesos con precio final cargado. Muestra adjudicatario,
precio final, desviacion respecto del presupuesto y puntaje.

Cada fila tiene un boton `Editar` para actualizar en linea:

- adjudicatario (hasta 200 caracteres)
- puntaje de adjudicacion (0 a 100)
- precio final en CLP

Tambien se puede cargar el adjudicatario, puntaje y precio desde la ficha de una
licitacion. Los datos quedan disponibles para comparar procesos futuros.

### 7.2 Historial de Ordenes de Compra

Importa el archivo que entrega el hotel en formato `.xlsx`, `.xlsm` o `.csv`.
Los encabezados son tolerantes a variantes de nombre (organismo/cliente,
objeto/descripcion, fecha, monto). Si el archivo no tiene columnas reconocibles,
la plataforma avisa y no importa nada.

Los registros importados permiten que la ficha de una licitacion muestre la
experiencia previa con ese organismo.

---

## 8. Informes

Se accede desde el menu `Informes`.

### 8.1 Periodo

- **Semanal:** ultimos 7 dias.
- **Mensual:** ultimos 30 dias.
- **Personalizado:** rango de fechas elegido con el calendario.

Si la fecha de inicio es posterior a la de termino, la plataforma las invierte.
Si el rango no es valido, vuelve al periodo semanal.

El informe considera las licitaciones **publicadas** dentro del periodo.

### 8.2 Contenido

- Oportunidades, presupuesto total, costo base y margen proyectado.
- Embudo por estado.
- Tasa de cierre: adjudicadas / (participadas + adjudicadas).
- Demanda por categoria.
- **Todos los organismos** del periodo, ordenados por presupuesto. Cada organismo
  enlaza al listado filtrado.
- Motivos de descarte, incluidos los descartes **sin motivo**.
- Tabla de licitaciones descartadas con motivo, descripcion y enlace
  `Ver licitacion`.

### 8.3 Exportar

`Exportar CSV` descarga el informe completo con el periodo seleccionado. El
archivo se abre directamente en Excel.

---

## 9. Reglas de negocio

1. **Alcance intramuros.** Solo salones, alojamiento y A&B del hotel. No se
   ofrecen servicios fuera del hotel.
2. **El presupuesto manda.** Si el costo base supera el presupuesto del
   mandante, la oportunidad se descarta por precio y no se puede marcar como
   `Participamos`.
3. **La comuna no descarta.** La region es solo informativa.
4. **Disponibilidad manual.** El match de salones es por capacidad; la
   disponibilidad real se confirma en la agenda y en el PMS.
5. **Hotel Ismael solo hospedaje.** Nunca salones ni eventos.
6. **Tolerancia a errores de tipeo.** La busqueda reconoce variantes cuando la
   coincidencia exacta no encuentra nada. Si el texto no se parece a nada del
   vocabulario, no se fuerza una clasificacion.
7. **Costeo provisional.** Mientras no se carguen las tarifas reales, el costo
   se estima y no se descarta automaticamente por presupuesto hasta que una
   persona valide el costo.
8. **Tope Compra Agil.** Superar el tope genera una advertencia, no un descarte
   automatico.
9. **Ultima escritura gana.** Si dos personas editan la misma licitacion al
   mismo tiempo, se guarda el ultimo cambio. El historial de actividad deja
   registro de ambos.

---

## 10. Estados del embudo

| Estado | Significa |
|---|---|
| `Identificada` | Recien sincronizada, sin revisar |
| `Calificada` | Revisada y con posibilidad real de participar |
| `Participada` | El equipo decidio ofertar |
| `Adjudicada` | Ganada |
| `Descartada` | No se participa, con motivo registrado |

---

## 11. Revision y trabajo en equipo

- Todos los usuarios comparten la misma base de datos.
- Cada accion queda registrada en el **Historial de Actividad** con fecha,
  usuario, tipo y detalle.
- El listado muestra `Revisada por <nombre>` con la fecha y hora de la ultima
  revision.
- El filtro `Revision` permite ver `Pendientes sin revisar` o lo revisado por
  una persona especifica.
- La ficha muestra `Ultima revision: <nombre> - <fecha y hora>` debajo del boton
  de revision.
- No hay asignacion formal de responsables: la coordinacion se hace con el
  filtro de revision y las notas compartidas.

---

## 12. Sincronizacion con Mercado Publico

- Sin fecha, sincroniza los **ultimos 7 dias**. Con fecha, solo ese dia.
- La fecha se escribe en formato `DDMMAAAA`.
- La demora es normal: la API limita las consultas y la plataforma consulta una
  ficha de detalle por cada licitacion pertinente. Puede tomar entre 3 y 6
  minutos.
- El boton se deshabilita mientras la sincronizacion esta en curso. No abrir dos
  sincronizaciones a la vez.
- Si la API responde con limite de consultas (HTTP 429), la plataforma espera y
  reintenta. Si el bloqueo persiste, algunas fichas quedan sin detalle y el
  resumen lo informa.

**Recomendacion en produccion:** si la sincronizacion de 7 dias supera el tiempo
maximo del servidor, sincronizar dia por dia usando el campo de fecha.

---

## 13. Problemas frecuentes

**La sincronizacion se demora varios minutos.**
Es normal. Sin fecha recorre 7 dias y consulta el detalle de cada licitacion
pertinente. Con una fecha especifica es mucho mas rapida.

**Aparece el aviso "La API bloqueo N consulta(s)".**
Subir `MERCADO_PUBLICO_INTERVALO_MS` a 1000 en `.env` y repetir la
sincronizacion, o sincronizar dia por dia.

**No aparecen licitaciones nuevas.**
Revisar que los filtros esten limpios y que la sincronizacion haya terminado sin
errores. Si el ticket de la API no esta configurado, la sincronizacion se omite y
lo informa.

**Una licitacion aparece con "Salon por asignar".**
No hay ningun salon con aforo suficiente, o nadie ha completado la evaluacion.
Abrir la ficha y revisar el bloque de capacidad y salones.

**La tarifa del salon aparece en $0.**
Es correcto por ahora: el catalogo oficial del hotel no publica tarifas. Mientras
no se carguen, el costo minimo solo considera el consumo por persona.

**El historial de ordenes de compra esta vacio.**
Nunca se ha importado. Cargarlo desde `Historial de Adjudicacion` con el Excel
del hotel.

**No puedo marcar Participamos.**
El costo base supera el presupuesto mandante. Ajustar el costeo o registrar el
descarte con su motivo.

**No recuerdo quien reviso una licitacion.**
Usar el filtro `Revision` en el listado o abrir la ficha y revisar el badge y el
`Historial de Actividad`.

**Una metrica no me lleva al listado.**
Las tarjetas del embudo bajan a la seccion de resultados con el filtro aplicado.
Si no ves el listado, revisa que el navegador no este bloqueando el desplazamiento
por anclas.

---

## 14. Datos que aun faltan cargar

Estos datos los tiene el hotel, no la plataforma:

1. Tarifas por salon.
2. Equipamiento por salon (hoy figura como "Por confirmar con el hotel").
3. Aforos del Salon Tam (deducidos de las combinaciones; confirmar).
4. Historico de ordenes de compra en Excel o CSV.
5. Claves definitivas de los cuatro perfiles.
6. Proveedor de IA para la ficha resumen, si se decide usarlo.

---

## 15. Para el equipo tecnico

- Verificacion obligatoria antes de integrar cambios:

```bash
python verify.py
```

- Suite de pruebas:

```bash
python -m pytest --ignore=tests/test_emoji_compliance.py
```

- La base de datos es SQLite (`licitaciones.db`) y se inicializa sola al
  arrancar.
- En produccion conviene definir `LICITACIONES_DB_PATH` en un disco persistente
  para no perder datos en cada despliegue.
- Toda la plataforma es web: no se instala nada en los puestos de trabajo del
  hotel, solo se abre el navegador.
- Convenciones de ramas, commits e integracion en `docs/WORKFLOW.md`.
- Matriz de brechas contra la reunion de levantamiento en
  `docs/ALINEACION_REUNION.md`.
