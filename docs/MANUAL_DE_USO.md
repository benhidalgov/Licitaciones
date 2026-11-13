# Manual de uso

**Asistente Virtual de Licitaciones**
Hotel Plaza San Francisco | Programa de Vinculacion con el Medio, DUOC UC

Esta guia explica, paso a paso, como usar la plataforma en el trabajo diario.

---

## Antes de empezar

- La direccion de la plataforma te la entrega el administrador.
- Tu usuario y tu clave tambien te los entrega el administrador.
- Los cuatro perfiles ven la misma informacion y pueden realizar las mismas
  acciones. Lo que cambia es el nombre que queda registrado en el historial.
- Todo lo que hagas se guarda al instante y lo ve el resto del equipo.

Perfiles disponibles:

| Usuario | Perfil |
|---|---|
| `admin` | Administrador |
| `daniela` | Daniela |
| `francisca` | Francisca |
| `mari` | Mari |

---

## 1. Ingresar a la plataforma

1. Abre el navegador y entra a la direccion que te entrego el administrador.
2. Escribe tu usuario.
3. Escribe tu clave.
4. Presiona `Iniciar Sesion`.
5. Para salir, usa el boton `Cerrar Sesion` de la barra superior.

Si te equivocas 5 veces seguidas, el acceso se bloquea por 5 minutos.

---

## 2. Conocer la pantalla principal

Al entrar veras la pantalla `Licitaciones`. De arriba hacia abajo:

1. **Barra superior:** acceso a Licitaciones, Salones y Agenda, Historial de
   Adjudicacion, Informes y cierre de sesion.
2. **Margen de tolerancia:** valor minimo que se exige para priorizar una
   oportunidad. Se puede expresar en porcentaje o en pesos.
3. **Oportunidades Priorizadas de Hoy:** las licitaciones abiertas que tienen
   presupuesto y capacidad viables. Cada tarjeta incluye un enlace `MP` a la
   ficha publica en Mercado Publico.
4. **Metricas del Embudo Comercial:** Total, Compra Agil, Identificadas,
   Calificadas, Participadas, Adjudicadas, Descartadas y Cerradas.
5. **Filtros:** busqueda, cliente clave, categoria, modalidad, estado, motivo de
   descarte, revision y vencimiento.
6. **Listado de licitaciones:** hasta 8 por pagina.
7. **Paginacion:** al final del listado.

Las tarjetas de las metricas son clickeables: al presionarlas, la pagina baja al
listado con ese filtro aplicado.

### Cambiar el margen de tolerancia

1. Escribe el valor en el campo del margen.
2. Elige `% del presupuesto` o `CLP fijo`.
3. Presiona `Guardar margen`.

### Cambiar el tope de Compra Agil

1. Ubica la tarjeta `Compra Agil`.
2. Escribe el valor de la **UTM del mes**.
3. Presiona `Guardar`.

El tope se calcula automaticamente como 100 UTM. Actualiza la UTM cada mes.

---

## 3. Sincronizar licitaciones desde Mercado Publico

1. En la pantalla `Licitaciones`, presiona `Sincronizar Mercado Publico`.
2. Si quieres traer solo un dia, escribe la fecha en formato `DDMMAAAA` antes de
   presionar el boton.
3. Espera a que termine. El boton se deshabilita mientras la consulta esta en
   curso.
4. Lee el mensaje final: indica cuantas licitaciones se consultaron y cuantas se
   guardaron o actualizaron.

Sin fecha, la plataforma revisa los ultimos 7 dias. Puede demorar varios minutos
porque consulta el detalle de cada licitacion pertinente. Con una fecha
especifica es mucho mas rapida.

No abras dos sincronizaciones al mismo tiempo.

---

## 4. Revisar las oportunidades del dia

1. Mira la franja `Oportunidades Priorizadas de Hoy`.
2. Haz clic en la tarjeta o en el ID de la oportunidad que quieras revisar.
3. Lee la ficha y revisa el presupuesto, el margen y el salon propuesto.
4. Si la oportunidad no es viable, puedes descartarla con su motivo.
5. Si es viable, continua con la evaluacion y la decision.

---

## 5. Buscar y filtrar licitaciones

1. Escribe en `Busqueda General` si conoces el ID, el titulo, el organismo o la
   region. Tambien puedes presionar `/` para ir directo al buscador.
2. Selecciona uno o varios filtros.
3. Presiona `Aplicar Filtros`.
4. Para limpiar todo, usa el enlace `Limpiar Filtros`.
5. Para ver mas resultados, usa la paginacion. Se muestran hasta 8 por pagina.

Filtros disponibles:

| Filtro | Para que sirve |
|---|---|
| Busqueda General | Busca por ID, titulo, organismo, region o notas |
| Cliente Clave | Filtra clientes prioritarios como Mineduc, Minsal o universidades |
| Categoria Comercial | Alojamiento o Eventos / Catering |
| Modalidad de Compra | Compra Agil o Licitacion Publica |
| Estado en Embudo | Identificada, Calificada, Participada, Cerrada, Adjudicada o Descartada |
| Motivo de Descarte | Precio, Disponibilidad, Fuera de alcance, Otro o Sin motivo |
| Revision | Todas, Pendientes sin revisar o Revisadas por una persona |
| Vencimiento | Todas, Vigentes o Vencidas |

Los filtros tambien se aplican a la vista priorizada y a la exportacion.

---

## 6. Leer el listado de licitaciones

Cada fila muestra:

1. **ID y fecha de cierre.** Ademas, la fecha y hora de la ultima
   actualizacion.
2. **Titulo y organismo.** Incluye la region y el cliente clave si corresponde.
3. **Revision.** Si alguien ya la reviso, aparece `Revisada por <nombre>` con la
   fecha y hora.
4. **Categoria y modalidad.**
5. **Presupuesto mandante y costo base.**
6. **Viabilidad presupuestaria:** viable, margen bajo el minimo, inviable,
   monto no informado o sobre el tope de Compra Agil.
7. **Cruce de ID con adjuntos:** verificado, discrepancia o sin verificar.
8. **Estado del embudo.**
9. **Acciones:** ver detalle, abrir la ficha en Mercado Publico (MP) o
   eliminar.

Haz clic en cualquier parte de la fila para abrir la ficha.

---

## 7. Abrir y recorrer una ficha

Dentro de la ficha encontraras, en este orden:

1. **Encabezado:** ID, categoria, cliente clave, estado de revision, motivo de
   descarte y modalidad.
2. **Acciones superiores:** ver documentos, ver o descargar la ficha en Markdown,
   refrescar desde Mercado Publico y eliminar.
3. **Ficha Resumen:** fechas, personas, espacio, alimentacion y puntaje.
4. **Control presupuestario:** presupuesto contra costo base, con margen o
   deficit.
5. **Evaluacion:** propiedad, asistentes, jornada, salon, costo y sellos.
6. **Capacidad y salones:** salones compatibles con el aforo.
7. **Documentos y admisibilidad:** validacion del ID y checklist de documentos.
8. **Notas compartidas:** comentarios del equipo con autor y fecha.
9. **Historial de Actividad:** todo lo que paso con la licitacion.
10. **Sintesis de TDR:** resumen de lo que pide el documento.
11. **Decisiones:** revisar, participar o no participar.

Los bloques 7, 9 y 10 (validacion documental, checklist, historial y TDR) vienen
plegados para que la ficha no sea larga. Haz clic en el titulo del bloque para
abrirlo o cerrarlo; los demas bloques estan siempre visibles.

---

## 8. Evaluar una licitacion

1. Abre la ficha de la licitacion.
2. En el bloque de evaluacion, selecciona la **propiedad**.
   - Plaza San Francisco permite salones y eventos.
   - Hotel Ismael solo permite alojamiento.
3. Indica la **cantidad de asistentes**.
4. Completa el **tipo de jornada** y el **horario** si corresponde.
5. Selecciona el **salon propuesto**.
6. Revisa o escribe el **costo base**.
   - Si lo dejas vacio, la plataforma suma la tarifa del salon (si esta cargada) y el consumo por persona.
   - Si la tarifa del salon esta pendiente, el costo y el margen son estimaciones.
7. Marca los **sellos** que correspondan.
8. Presiona `Guardar asignacion`.
9. Lee el mensaje: si el costo supera el presupuesto, la oportunidad se descarta
   por precio.

---

## 9. Tomar una decision

En la parte inferior de la ficha estan los tres botones de decision.

### 9.1 Marcar como revisada

1. Presiona `Marcar como Revisada`.
2. La plataforma registra tu nombre y la fecha/hora.
3. En el encabezado aparecera `Revisada por <tu nombre>`.
4. Debajo del boton aparecera `Ultima revision: <nombre> - <fecha y hora>`.

Usar este boton cuando ya se reviso la oportunidad pero todavia no se decide
participar.

### 9.2 Participamos

1. Presiona `Participamos`.
2. La licitacion pasa al estado `Participada`.
3. Si el costo base supera el presupuesto, la accion se bloquea.
4. En ese caso, ajusta el costeo o registra el descarte con su motivo.

### 9.3 No participamos

1. Selecciona el **motivo** de descarte.
2. Escribe una **descripcion** si quieres dejar mas contexto.
3. Presiona `No participamos`.
4. La licitacion pasa a `Descartada` y queda registrada en el informe.

Motivos disponibles: `Precio`, `Disponibilidad`, `Fuera de alcance` y `Otro`.

---

## 10. Dejar una nota para el equipo

1. Abre la ficha de la licitacion.
2. Baja hasta `Notas Compartidas del Equipo`.
3. Escribe la nota.
4. Presiona `Agregar Nota`.

La nota queda con tu nombre y la fecha. Es el canal para dejar contexto entre
turnos o entre personas del equipo.

---

## 11. Saber quien reviso una licitacion

Tienes tres formas:

1. **En el listado:** busca el badge `Revisada por <nombre>` con la fecha y hora.
2. **En la ficha:** mira el encabezado y la linea bajo el boton de revision.
3. **Con el filtro Revision:** elige `Pendientes sin revisar` o
   `Revisadas por <nombre>`.

Para ver el detalle completo de lo que hizo cada persona, abre el
`Historial de Actividad` de la ficha. Ahi aparece fecha, usuario, tipo de accion
y detalle.

---

## 12. Revisar los salones

1. Entra a `Salones y Agenda` desde la barra superior.
2. Revisa el catalogo: direccion, ubicacion interna, capacidad y fechas
   ocupadas.
3. Presiona `Ficha Tecnica` para ver el detalle del salon en una ventana
   emergente.
4. Presiona `Ver Agenda de Fechas` para ver la agenda filtrada por ese salon.
5. Usa los filtros de la agenda para buscar por salon o por cliente/organismo.

Direccion del hotel: `Av. Libertador Bernardo O'Higgins 816, Santiago`.

---

## 13. Crear una reserva de salon

1. Entra a `Salones y Agenda`.
2. Abre la `Ficha Tecnica` del salon y presiona `Reservar salon`, o abre la
   ficha completa del salon y usa `Reservar este Salon`.
3. Completa:
   - nombre o descripcion del evento
   - organismo o empresa cliente
   - tipo de evento
   - fecha de inicio y fecha de termino
   - horario
   - cantidad de asistentes
   - montaje (auditorio, escuela, mesas redondas, etc.)
   - estado de la reserva
   - licitacion vinculada, si corresponde
   - contacto responsable y observaciones
4. Presiona `Guardar Reserva`.
5. Revisa el mensaje de confirmacion.

La plataforma avisa si:

- el salon no existe
- las fechas no son validas
- la fecha de inicio es posterior a la de termino
- los asistentes superan el aforo
- ya hay una reserva confirmada en ese rango de fechas

Estados de reserva:

| Estado | Cuando usarlo |
|---|---|
| `Confirmada` | El evento esta cerrado. Bloquea el salon |
| `Tentativa` | Todavia se esta negociando. No bloquea |
| `Bloqueo Interno` | Reserva interna del hotel. No bloquea |

---

## 14. Editar o eliminar una reserva

1. Entra a `Salones y Agenda`.
2. Ubica la reserva en la agenda.
3. Presiona `Editar` para cambiarla o `Eliminar` para borrarla.
4. Confirma la accion.

Al editar se aplican las mismas validaciones que al crear.

---

## 15. Revisar el Historial de Adjudicacion

1. Entra a `Historial de Adjudicacion` desde la barra superior.
2. Revisa el consolidado: adjudicatario, precio final, desviacion y puntaje.
3. Para actualizar una fila, presiona `Editar`.
4. Completa adjudicatario, puntaje (0 a 100) y precio final.
5. Presiona `Guardar`.

---

## 16. Importar el historial de ordenes de compra

1. Entra a `Historial de Adjudicacion`.
2. Baja hasta `Historial de Ordenes de Compra`.
3. Presiona `Seleccionar archivo`.
4. Elige el archivo `.xlsx`, `.xlsm` o `.csv` que entrega el hotel.
5. Presiona `Importar historial`.

La plataforma reconoce encabezados como organismo/cliente, objeto/descripcion,
fecha y monto. Si no encuentra columnas reconocibles, avisa y no importa nada.

Con estos datos, la ficha de una licitacion muestra la experiencia previa con ese
organismo.

---

## 17. Revisar los informes

1. Entra a `Informes` desde la barra superior.
2. Elige el periodo:
   - `Semanal (7 dias)`
   - `Mensual (30 dias)`
   - `Personalizado`, eligiendo fecha de inicio y de termino
3. Revisa el resumen: oportunidades, presupuesto, costo, margen, embudo y tasa de
   cierre.
4. Revisa la demanda por categoria.
5. Revisa todos los organismos del periodo. Puedes hacer clic en uno para ver sus
   licitaciones.
6. Revisa los motivos de descarte, incluidos los descartes sin motivo.
7. Revisa la tabla de licitaciones descartadas y usa `Ver licitacion` para abrir
   la ficha.

La tasa de cierre se calcula como adjudicadas dividido por participadas mas
adjudicadas.

---

## 18. Exportar a Excel

### 18.1 Exportar el listado de licitaciones

1. En `Licitaciones`, aplica los filtros que quieras.
2. Presiona `Exportar a Excel`.
3. Se descarga un archivo `.xlsx` con el listado filtrado.
4. Abrelo con Excel.

El archivo incluye quien reviso, la fecha de revision y el enlace a la ficha de Mercado Publico.

### 18.2 Exportar un informe

1. En `Informes`, elige el periodo.
2. Presiona `Exportar CSV`.
3. Se descarga el informe completo con el periodo seleccionado.

---

## 19. Preguntas frecuentes

**La sincronizacion se demora varios minutos.**
Es normal. Sin fecha revisa 7 dias y consulta el detalle de cada licitacion
pertinente. Con una fecha especifica es mucho mas rapida.

**Aparece un aviso de limite de consultas de Mercado Publico.**
La plataforma espera y reintenta. Si el aviso persiste, sincroniza dia por dia
usando el campo de fecha.

**No aparecen licitaciones nuevas.**
Revisa que los filtros esten limpios y que la sincronizacion haya terminado sin
errores.

**No puedo marcar Participamos.**
El costo base supera el presupuesto. Ajusta el costeo o registra el descarte con
su motivo.

**La tarifa del salon aparece en $0.**
Es correcto por ahora: el catalogo del hotel no publica tarifas. Mientras no se
carguen, el costo se estima con el consumo por persona.

**Una licitacion aparece con "Salon por asignar".**
No hay un salon con aforo suficiente o nadie ha completado la evaluacion. Abre la
ficha y revisa el bloque de capacidad y salones.

**No se quien reviso una licitacion.**
Usa el filtro `Revision` o abre la ficha y revisa el badge y el
`Historial de Actividad`.

**Presione una metrica y no veo el listado.**
La pagina baja a la seccion de resultados con el filtro aplicado. Si no ocurre,
revisa que el navegador no este bloqueando el desplazamiento por anclas.

---

## 20. Estados y conceptos clave

| Concepto | Significa |
|---|---|
| `Identificada` | Recien sincronizada, sin revisar |
| `Calificada` | Revisada y con posibilidad real de participar |
| `Participada` | El equipo decidio ofertar |
| `Cerrada` | Cerraron las ofertas sin decision registrada; se marca sola al vencer |
| `Adjudicada` | Proceso ganado |
| `Descartada` | No se participa, con motivo registrado |
| `Priorizada` | Oportunidad abierta con presupuesto y capacidad viables |
| `Cliente clave` | Organismo prioritario para el hotel |
| `Tope Compra Agil` | Limite de referencia de la modalidad Compra Agil (100 UTM del mes) |
| `Margen de tolerancia` | Margen minimo exigido para priorizar |
| `Revisada por` | Ultima persona que reviso la licitacion |
