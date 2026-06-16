"""
etl_pipeline.py
Proyecto Final BI: Accidentes de Tránsito en México
ATUS 2021-2023 - INEGI
"""

import logging
import sys
from pathlib import Path
from getpass import getpass

import pandas as pd
from dbfread import DBF
from sqlalchemy import create_engine, text


DATASETS_DIR = Path("Datasets")
SCHEMA = "accidentes"

ARCHIVOS_DBF = [
    DATASETS_DIR / "ATUS_21.DBF",
    DATASETS_DIR / "ATUS_22.DBF",
    DATASETS_DIR / "ATUS_23.DBF",
]

CATALOGO_ESTADOS = {
    1: "Aguascalientes", 2: "Baja California", 3: "Baja California Sur",
    4: "Campeche", 5: "Coahuila", 6: "Colima", 7: "Chiapas",
    8: "Chihuahua", 9: "Ciudad de México", 10: "Durango",
    11: "Guanajuato", 12: "Guerrero", 13: "Hidalgo", 14: "Jalisco",
    15: "Estado de México", 16: "Michoacán", 17: "Morelos",
    18: "Nayarit", 19: "Nuevo León", 20: "Oaxaca", 21: "Puebla",
    22: "Querétaro", 23: "Quintana Roo", 24: "San Luis Potosí",
    25: "Sinaloa", 26: "Sonora", 27: "Tabasco", 28: "Tamaulipas",
    29: "Tlaxcala", 30: "Veracruz", 31: "Yucatán", 32: "Zacatecas",
}

CATALOGO_DIAS = {
    1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves",
    5: "Viernes", 6: "Sábado", 7: "Domingo", 8: "No especificado",
}

CATALOGO_MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

CATALOGO_SEXO = {
    1: "Se fugó",
    2: "Hombre",
    3: "Mujer",
}


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

log = logging.getLogger(__name__)


def crear_engine():
    host = input("Host de Aurora: ")
    database = input("Database: ")
    user = input("Usuario: ")
    password = getpass("Password: ")

    url = f"postgresql+psycopg2://{user}:{password}@{host}:5432/{database}"
    return create_engine(url, echo=False)


def extract():
    frames = []

    for archivo in ARCHIVOS_DBF:
        if not archivo.exists():
            raise FileNotFoundError(f"No se encontró el archivo: {archivo}")

        log.info(f"Leyendo {archivo.name}")
        tabla = DBF(str(archivo), encoding="latin-1")
        df = pd.DataFrame(iter(tabla))
        frames.append(df)

        log.info(f"{archivo.name}: {len(df):,} filas")

    df_total = pd.concat(frames, ignore_index=True)
    log.info(f"Total extraído: {len(df_total):,} filas")

    return df_total


def describir_tipo_zona(row):
    if row["URBANA"] in [1, 2]:
        return "Urbana"
    if row["SUBURBANA"] in [1, 2, 3]:
        return "Suburbana"
    return "No especificado"


def limpiar_codigos(df):
    df = df.copy()

    df["HORA"] = df["HORA"].apply(
        lambda x: int(x) if pd.notna(x) and 0 <= int(x) <= 23 else 99
    )

    df["DIASEMANA"] = df["DIASEMANA"].apply(
        lambda x: int(x) if pd.notna(x) and 1 <= int(x) <= 7 else 8
    )

    df["MES"] = df["MES"].apply(
        lambda x: int(x) if pd.notna(x) and 1 <= int(x) <= 12 else None
    )

    df["EDAD"] = df["EDAD"].apply(
        lambda x: int(x) if pd.notna(x) and 1 <= int(x) <= 98 else None
    )

    df["TIPACCID"] = df["TIPACCID"].apply(
        lambda x: int(x) if pd.notna(x) and 1 <= int(x) <= 12 else 12
    )

    df["CAUSAACCI"] = df["CAUSAACCI"].apply(
        lambda x: int(x) if pd.notna(x) and 1 <= int(x) <= 5 else 5
    )

    return df


def transform(df):
    log.info("Transformando datos")

    df = limpiar_codigos(df)

    cols_muertos = [
        "CONDMUERTO", "PASAMUERTO", "PEATMUERTO",
        "CICLMUERTO", "OTROMUERTO"
    ]

    cols_heridos = [
        "CONDHERIDO", "PASAHERIDO", "PEATHERIDO",
        "CICLHERIDO", "OTROHERIDO"
    ]

    df["total_muertos"] = df[cols_muertos].fillna(0).astype(int).sum(axis=1)
    df["total_heridos"] = df[cols_heridos].fillna(0).astype(int).sum(axis=1)
    df["total_victimas"] = df["total_muertos"] + df["total_heridos"]
    df["es_fatal"] = df["total_muertos"] > 0

    dim_tiempo = (
        df[["ANIO", "MES", "DIA", "HORA", "DIASEMANA"]]
        .dropna()
        .drop_duplicates()
        .copy()
    )

    dim_tiempo = dim_tiempo.rename(
        columns={
            "ANIO": "anio",
            "MES": "mes",
            "DIA": "dia",
            "HORA": "hora",
            "DIASEMANA": "diasemana_num",
        }
    )

    dim_tiempo["nom_dia"] = dim_tiempo["diasemana_num"].map(CATALOGO_DIAS)
    dim_tiempo["nom_mes"] = dim_tiempo["mes"].map(CATALOGO_MESES)
    dim_tiempo["es_fin_semana"] = dim_tiempo["diasemana_num"].isin([6, 7])

    dim_tiempo = dim_tiempo.sort_values(
        ["anio", "mes", "dia", "hora", "diasemana_num"]
    ).reset_index(drop=True)

    dim_tiempo["sk_tiempo"] = dim_tiempo.index + 1

    dim_lugar = (
        df[["EDO", "MPIO", "URBANA", "SUBURBANA"]]
        .drop_duplicates()
        .copy()
    )

    dim_lugar["nom_estado"] = dim_lugar["EDO"].map(CATALOGO_ESTADOS)
    dim_lugar["tipo_zona"] = dim_lugar.apply(describir_tipo_zona, axis=1)

    dim_lugar = dim_lugar.rename(
        columns={
            "EDO": "cve_edo",
            "MPIO": "cve_mpio",
            "URBANA": "urbana",
            "SUBURBANA": "suburbana",
        }
    )

    dim_lugar = dim_lugar.dropna(subset=["nom_estado"])
    dim_lugar = dim_lugar.sort_values(
        ["cve_edo", "cve_mpio", "urbana", "suburbana"]
    ).reset_index(drop=True)

    dim_lugar["sk_lugar"] = dim_lugar.index + 1

    dim_conductor = (
        df[["SEXO", "EDAD", "ALIENTO", "CINTURON"]]
        .drop_duplicates()
        .copy()
    )

    dim_conductor["desc_sexo"] = dim_conductor["SEXO"].map(CATALOGO_SEXO)
    dim_conductor["aliento"] = dim_conductor["ALIENTO"].map(
        {4: True, 5: False, 6: None}
    )
    dim_conductor["uso_cinturon"] = dim_conductor["CINTURON"].map(
        {7: True, 8: False, 9: None}
    )

    dim_conductor = dim_conductor.rename(
        columns={
            "SEXO": "cve_sexo",
            "EDAD": "edad",
        }
    )

    dim_conductor = dim_conductor[
        ["cve_sexo", "desc_sexo", "edad", "aliento", "uso_cinturon"]
    ].drop_duplicates()

    dim_conductor = dim_conductor.sort_values(
        ["cve_sexo", "edad"], na_position="last"
    ).reset_index(drop=True)

    dim_conductor["sk_conductor"] = dim_conductor.index + 1

    fact = df.copy()

    fact = fact.merge(
        dim_tiempo,
        left_on=["ANIO", "MES", "DIA", "HORA", "DIASEMANA"],
        right_on=["anio", "mes", "dia", "hora", "diasemana_num"],
        how="left",
    )

    fact = fact.merge(
        dim_lugar,
        left_on=["EDO", "MPIO", "URBANA", "SUBURBANA"],
        right_on=["cve_edo", "cve_mpio", "urbana", "suburbana"],
        how="left",
    )

    fact["aliento_bool"] = fact["ALIENTO"].map({4: True, 5: False, 6: None})
    fact["cinturon_bool"] = fact["CINTURON"].map({7: True, 8: False, 9: None})

    fact = fact.merge(
        dim_conductor,
        left_on=["SEXO", "EDAD", "aliento_bool", "cinturon_bool"],
        right_on=["cve_sexo", "edad", "aliento", "uso_cinturon"],
        how="left",
    )

    fact["sk_tipo"] = fact["TIPACCID"]
    fact["sk_causa"] = fact["CAUSAACCI"]
    fact["anio_origen"] = fact["ANIO"]

    fact_accidente = fact[
        [
            "sk_tiempo",
            "sk_lugar",
            "sk_tipo",
            "sk_causa",
            "sk_conductor",
            "anio_origen",
            "CONDMUERTO",
            "CONDHERIDO",
            "PASAMUERTO",
            "PASAHERIDO",
            "PEATMUERTO",
            "PEATHERIDO",
            "CICLMUERTO",
            "CICLHERIDO",
            "OTROMUERTO",
            "OTROHERIDO",
            "total_muertos",
            "total_heridos",
            "total_victimas",
            "es_fatal",
        ]
    ].copy()

    fact_accidente = fact_accidente.rename(
        columns={
            "CONDMUERTO": "condmuerto",
            "CONDHERIDO": "condherido",
            "PASAMUERTO": "pasamuerto",
            "PASAHERIDO": "pasaherido",
            "PEATMUERTO": "peatmuerto",
            "PEATHERIDO": "peatherido",
            "CICLMUERTO": "ciclmuerto",
            "CICLHERIDO": "ciclherido",
            "OTROMUERTO": "otromuerto",
            "OTROHERIDO": "otroherido",
        }
    )

    fact_accidente = fact_accidente.dropna(
        subset=["sk_tiempo", "sk_lugar", "sk_tipo", "sk_causa", "sk_conductor"]
    )

    for col in ["sk_tiempo", "sk_lugar", "sk_tipo", "sk_causa", "sk_conductor"]:
        fact_accidente[col] = fact_accidente[col].astype(int)

    log.info(f"dim_tiempo: {len(dim_tiempo):,} filas")
    log.info(f"dim_lugar: {len(dim_lugar):,} filas")
    log.info(f"dim_conductor: {len(dim_conductor):,} filas")
    log.info(f"fact_accidente: {len(fact_accidente):,} filas")

    return {
        "dim_tiempo": dim_tiempo,
        "dim_lugar": dim_lugar,
        "dim_conductor": dim_conductor,
        "fact_accidente": fact_accidente,
    }


def load(tablas, engine):
    log.info("Cargando tablas a Aurora PostgreSQL")

    orden_carga = [
        "dim_tiempo",
        "dim_lugar",
        "dim_conductor",
        "fact_accidente",
    ]

    for nombre_tabla in orden_carga:
        df = tablas[nombre_tabla]

        log.info(f"Cargando {nombre_tabla}: {len(df):,} filas")

        df.to_sql(
            nombre_tabla,
            con=engine,
            schema=SCHEMA,
            if_exists="append",
            index=False,
            chunksize=2000,
            method="multi",
        )

        log.info(f"{nombre_tabla} cargada correctamente")


def validar(engine, filas_origen):
    log.info("Validando carga final")

    consultas = {
        "filas_fact": f"SELECT COUNT(*) FROM {SCHEMA}.fact_accidente",
        "accidentes_fatales": f"""
            SELECT COUNT(*)
            FROM {SCHEMA}.fact_accidente
            WHERE es_fatal = TRUE
        """,
        "total_muertos": f"SELECT SUM(total_muertos) FROM {SCHEMA}.fact_accidente",
        "total_heridos": f"SELECT SUM(total_heridos) FROM {SCHEMA}.fact_accidente",
        "total_victimas": f"SELECT SUM(total_victimas) FROM {SCHEMA}.fact_accidente",
    }

    with engine.connect() as conn:
        for nombre, consulta in consultas.items():
            resultado = conn.execute(text(consulta)).scalar()
            log.info(f"{nombre}: {resultado:,}")

    log.info(f"filas_origen: {filas_origen:,}")
    log.info("ETL finalizado correctamente")


def main():
    log.info("=== INICIO ETL ATUS ===")

    engine = crear_engine()

    df_raw = extract()
    filas_origen = len(df_raw)

    tablas = transform(df_raw)
    load(tablas, engine)
    validar(engine, filas_origen)

    log.info("=== FIN ETL ATUS ===")


if __name__ == "__main__":
    main()
