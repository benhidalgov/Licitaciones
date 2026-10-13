# {{ lic.titulo }}

- **Codigo:** {{ lic.id_licitacion }}
- **Ficha oficial (Mercado Publico):** https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={{ lic.id_licitacion }}
- **Organismo:** {{ lic.organismo }}
- **Region de ejecucion:** {{ lic.region }}
- **Categoria:** {{ lic.categoria }}
- **Modalidad:** {{ lic.modalidad }}
- **Presupuesto mandante:** {{ lic.presupuesto_mandante | clp }}
- **Costo base hotel:** {{ lic.costo_base_hotel | clp }}
- **Publicacion:** {{ lic.fecha_publicacion }}
- **Cierre:** {{ lic.fecha_cierre }}
- **Estado embudo:** {{ lic.estado_embudo }}
{% if lic.cantidad_asistentes %}
- **Aforo estimado:** {{ lic.cantidad_asistentes }} asistentes{% if lic.tipo_jornada %} ({{ lic.tipo_jornada }}){% endif %}
{% endif %}

## Necesidad (Descripcion TDR)

{{ lic.descripcion_tdr }}
