# Modelo Estrella - ATUS

## Grano

Una fila de la tabla de hechos representa un accidente de tránsito registrado en ATUS.

## Tabla de hechos

### fact_accidentes

Medidas:

- total_muertos
- total_heridos
- total_victimas
- es_fatal
- conteo_accidentes

## Dimensiones

### dim_fecha

- fecha_key
- anio
- mes
- dia
- dia_semana
- nombre_dia
- es_fin_semana

### dim_hora

- hora_key
- hora
- periodo_dia

### dim_ubicacion

- ubicacion_key
- edo
- mpio

### dim_causa

- causa_key
- causa_codigo
- causa_descripcion

### dim_tipo_accidente

- tipo_accidente_key
- tipo_accidente_codigo
- tipo_accidente_descripcion

### dim_via

- via_key
- urbana
- suburbana
- tipo_via
