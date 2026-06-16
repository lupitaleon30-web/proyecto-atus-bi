-- ============================================================
-- Proyecto Final de Business Intelligence
-- Alumna: Guadalupe León Morales
-- Dataset: ATUS 2021-2023 - INEGI
-- Grano: una fila en fact_accidente representa un accidente.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS accidentes;
SET search_path = accidentes;

DROP TABLE IF EXISTS fact_accidente CASCADE;
DROP TABLE IF EXISTS dim_conductor CASCADE;
DROP TABLE IF EXISTS dim_causa CASCADE;
DROP TABLE IF EXISTS dim_tipo_accidente CASCADE;
DROP TABLE IF EXISTS dim_lugar CASCADE;
DROP TABLE IF EXISTS dim_tiempo CASCADE;

CREATE TABLE dim_tiempo (
    sk_tiempo SERIAL PRIMARY KEY,
    anio SMALLINT NOT NULL,
    mes SMALLINT NOT NULL,
    dia SMALLINT NOT NULL,
    hora SMALLINT NOT NULL,
    diasemana_num SMALLINT NOT NULL,
    nom_dia VARCHAR(20) NOT NULL,
    nom_mes VARCHAR(20) NOT NULL,
    es_fin_semana BOOLEAN NOT NULL
);

CREATE TABLE dim_lugar (
    sk_lugar SERIAL PRIMARY KEY,
    cve_edo SMALLINT NOT NULL,
    nom_estado VARCHAR(50) NOT NULL,
    cve_mpio SMALLINT NOT NULL,
    urbana SMALLINT,
    suburbana SMALLINT,
    tipo_zona VARCHAR(30) NOT NULL
);

CREATE TABLE dim_tipo_accidente (
    sk_tipo SERIAL PRIMARY KEY,
    cve_tipaccid SMALLINT NOT NULL UNIQUE,
    desc_tipo VARCHAR(80) NOT NULL
);

CREATE TABLE dim_causa (
    sk_causa SERIAL PRIMARY KEY,
    cve_causaacci SMALLINT NOT NULL UNIQUE,
    desc_causa VARCHAR(60) NOT NULL
);

CREATE TABLE dim_conductor (
    sk_conductor SERIAL PRIMARY KEY,
    cve_sexo SMALLINT,
    desc_sexo VARCHAR(20),
    edad SMALLINT,
    aliento BOOLEAN,
    uso_cinturon BOOLEAN
);

CREATE TABLE fact_accidente (
    sk_accidente BIGSERIAL PRIMARY KEY,
    sk_tiempo INT NOT NULL REFERENCES dim_tiempo(sk_tiempo),
    sk_lugar INT NOT NULL REFERENCES dim_lugar(sk_lugar),
    sk_tipo INT NOT NULL REFERENCES dim_tipo_accidente(sk_tipo),
    sk_causa INT NOT NULL REFERENCES dim_causa(sk_causa),
    sk_conductor INT NOT NULL REFERENCES dim_conductor(sk_conductor),
    anio_origen SMALLINT NOT NULL,
    condmuerto SMALLINT NOT NULL DEFAULT 0,
    condherido SMALLINT NOT NULL DEFAULT 0,
    pasamuerto SMALLINT NOT NULL DEFAULT 0,
    pasaherido SMALLINT NOT NULL DEFAULT 0,
    peatmuerto SMALLINT NOT NULL DEFAULT 0,
    peatherido SMALLINT NOT NULL DEFAULT 0,
    ciclmuerto SMALLINT NOT NULL DEFAULT 0,
    ciclherido SMALLINT NOT NULL DEFAULT 0,
    otromuerto SMALLINT NOT NULL DEFAULT 0,
    otroherido SMALLINT NOT NULL DEFAULT 0,
    total_muertos SMALLINT NOT NULL DEFAULT 0,
    total_heridos SMALLINT NOT NULL DEFAULT 0,
    total_victimas SMALLINT NOT NULL DEFAULT 0,
    es_fatal BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_fact_tiempo ON fact_accidente(sk_tiempo);
CREATE INDEX idx_fact_lugar ON fact_accidente(sk_lugar);
CREATE INDEX idx_fact_tipo ON fact_accidente(sk_tipo);
CREATE INDEX idx_fact_causa ON fact_accidente(sk_causa);
CREATE INDEX idx_fact_conductor ON fact_accidente(sk_conductor);
CREATE INDEX idx_fact_es_fatal ON fact_accidente(es_fatal);
CREATE INDEX idx_fact_anio_origen ON fact_accidente(anio_origen);

INSERT INTO dim_tipo_accidente (cve_tipaccid, desc_tipo) VALUES
(1, 'Colisión con vehículo automotor'),
(2, 'Colisión con peatón / atropellamiento'),
(3, 'Colisión con animal'),
(4, 'Colisión con objeto fijo'),
(5, 'Volcadura'),
(6, 'Caída de pasajero'),
(7, 'Salida del camino'),
(8, 'Incendio'),
(9, 'Colisión con ferrocarril'),
(10, 'Colisión con motocicleta'),
(11, 'Colisión con ciclista'),
(12, 'Otro');

INSERT INTO dim_causa (cve_causaacci, desc_causa) VALUES
(1, 'Conductor'),
(2, 'Peatón o pasajero'),
(3, 'Falla del vehículo'),
(4, 'Mala condición del camino'),
(5, 'Otra');

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'accidentes'
ORDER BY table_name;