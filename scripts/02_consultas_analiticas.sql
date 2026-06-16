-- =====================================================
-- PROYECTO FINAL BI
-- CONSULTAS ANALÍTICAS AVANZADAS
-- Guadalupe León Morales
-- =====================================================

-- =====================================================
-- CONSULTA 1
-- Estados con más accidentes fatales
-- Técnica: CTE
-- =====================================================

WITH accidentes_fatales AS (
    SELECT
        dl.nom_estado,
        COUNT(*) AS total_accidentes_fatales
    FROM accidentes.fact_accidente fa
    JOIN accidentes.dim_lugar dl
        ON fa.sk_lugar = dl.sk_lugar
    WHERE fa.es_fatal = TRUE
    GROUP BY dl.nom_estado
)
SELECT *
FROM accidentes_fatales
ORDER BY total_accidentes_fatales DESC
LIMIT 10;


-- =====================================================
-- CONSULTA 2
-- Ranking de estados por porcentaje de fatalidad
-- Técnicas: CTE + Window Function RANK() + ROUND()
-- =====================================================

WITH resumen_estado AS (
    SELECT
        dl.nom_estado,
        COUNT(*) AS total_accidentes,
        COUNT(*) FILTER (WHERE fa.es_fatal = TRUE) AS accidentes_fatales,
        ROUND(
            100.0 * COUNT(*) FILTER (WHERE fa.es_fatal = TRUE) / COUNT(*),
            2
        ) AS pct_fatalidad
    FROM accidentes.fact_accidente fa
    JOIN accidentes.dim_lugar dl
        ON fa.sk_lugar = dl.sk_lugar
    GROUP BY dl.nom_estado
)
SELECT
    nom_estado,
    total_accidentes,
    accidentes_fatales,
    pct_fatalidad,
    RANK() OVER (ORDER BY pct_fatalidad DESC) AS ranking_fatalidad
FROM resumen_estado
ORDER BY ranking_fatalidad
LIMIT 10;


-- =====================================================
-- CONSULTA 3
-- Distribución acumulada de accidentes fatales por estado
-- Técnicas: CTE + SUM() OVER()
-- =====================================================

WITH fatales_estado AS (
    SELECT
        dl.nom_estado,
        COUNT(*) AS total_fatales
    FROM accidentes.fact_accidente fa
    JOIN accidentes.dim_lugar dl
        ON fa.sk_lugar = dl.sk_lugar
    WHERE fa.es_fatal = TRUE
    GROUP BY dl.nom_estado
)
SELECT
    nom_estado,
    total_fatales,
    SUM(total_fatales) OVER (
        ORDER BY total_fatales DESC
    ) AS acumulado_fatales,
    ROUND(
        100.0 * SUM(total_fatales) OVER (ORDER BY total_fatales DESC)
        / SUM(total_fatales) OVER (),
        2
    ) AS pct_acumulado
FROM fatales_estado
ORDER BY total_fatales DESC;


-- =====================================================
-- CONSULTA 4
-- Riesgo por franja horaria
-- Técnicas: CASE + ROUND() + COUNT FILTER
-- =====================================================

SELECT
    CASE
        WHEN dt.hora BETWEEN 0 AND 5 THEN 'Madrugada'
        WHEN dt.hora BETWEEN 6 AND 11 THEN 'Mañana'
        WHEN dt.hora BETWEEN 12 AND 17 THEN 'Tarde'
        ELSE 'Noche'
    END AS franja_horaria,
    COUNT(*) AS total_accidentes,
    COUNT(*) FILTER (WHERE fa.es_fatal = TRUE) AS accidentes_fatales,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE fa.es_fatal = TRUE) / COUNT(*),
        2
    ) AS porcentaje_fatalidad
FROM accidentes.fact_accidente fa
JOIN accidentes.dim_tiempo dt
    ON fa.sk_tiempo = dt.sk_tiempo
GROUP BY 1
ORDER BY porcentaje_fatalidad DESC;


-- =====================================================
-- CONSULTA 5
-- Pregunta principal del proyecto
-- Día + hora + tipo de vía + causa presunta
-- Técnica: GROUP BY analítico + ROUND() + COUNT FILTER
-- =====================================================

SELECT
    dt.nom_dia,
    dt.hora,
    dl.tipo_zona,
    dc.desc_causa,
    COUNT(*) AS total_accidentes,
    COUNT(*) FILTER (WHERE fa.es_fatal = TRUE) AS accidentes_fatales,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE fa.es_fatal = TRUE) / COUNT(*),
        2
    ) AS porcentaje_fatalidad
FROM accidentes.fact_accidente fa
JOIN accidentes.dim_tiempo dt
    ON fa.sk_tiempo = dt.sk_tiempo
JOIN accidentes.dim_lugar dl
    ON fa.sk_lugar = dl.sk_lugar
JOIN accidentes.dim_causa dc
    ON fa.sk_causa = dc.sk_causa
GROUP BY
    dt.nom_dia,
    dt.hora,
    dl.tipo_zona,
    dc.desc_causa
HAVING COUNT(*) >= 30
ORDER BY porcentaje_fatalidad DESC, accidentes_fatales DESC
LIMIT 20;
-- =====================================================
-- CONSULTA 6
-- Variación año a año de accidentes fatales por estado
-- Técnica: CTE + LAG() OVER (Window Function)
-- Responde: ¿qué estados empeoraron entre 2021 y 2023?
-- =====================================================

WITH fatales_por_anio AS (
    SELECT
        l.nom_estado,
        t.anio,
        COUNT(*) AS total_fatales
    FROM accidentes.fact_accidente f
    JOIN accidentes.dim_lugar  l ON f.sk_lugar  = l.sk_lugar
    JOIN accidentes.dim_tiempo t ON f.sk_tiempo = t.sk_tiempo
    WHERE f.es_fatal = TRUE
    GROUP BY l.nom_estado, t.anio
),
con_variacion AS (
    SELECT
        nom_estado,
        anio,
        total_fatales,
        LAG(total_fatales) OVER (
            PARTITION BY nom_estado
            ORDER BY anio
        ) AS fatales_anio_anterior,
        total_fatales - LAG(total_fatales) OVER (
            PARTITION BY nom_estado
            ORDER BY anio
        ) AS diferencia,
        ROUND(
            100.0 * (
                total_fatales - LAG(total_fatales) OVER (
                    PARTITION BY nom_estado ORDER BY anio
                )
            ) / NULLIF(LAG(total_fatales) OVER (
                PARTITION BY nom_estado ORDER BY anio
            ), 0),
            1
        ) AS variacion_pct
    FROM fatales_por_anio
)
SELECT
    nom_estado,
    anio,
    total_fatales,
    fatales_anio_anterior,
    diferencia,
    variacion_pct,
    CASE
        WHEN diferencia > 0 THEN 'Empeoró'
        WHEN diferencia < 0 THEN 'Mejoró'
        WHEN diferencia = 0 THEN 'Sin cambio'
        ELSE '—'
    END AS tendencia
FROM con_variacion
ORDER BY anio, diferencia DESC NULLS LAST;
