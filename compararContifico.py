import re
import unicodedata
from difflib import SequenceMatcher

import pandas as pd


CONTIFICO = "contifico_limpio.xlsx"
SAAS = "uphone_limpio.xlsx"
REPORTE = "errores_completo.xlsx"

COLUMNA_CLIENTE = "CLIENTE"
COLUMNA_MODELO = "MODELO"
COLUMNA_VENTAS = "VENTAS"
COLUMNA_IMEI = "IMEI"

UMBRAL_CLIENTE = 0.8
TOLERANCIA_PRECIO = 0.01


def limpiar_texto(texto):
    if pd.isna(texto):
        return ""

    texto = str(texto)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    texto = texto.replace("\n", " ")
    texto = re.sub(r"[^a-zA-Z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip().lower()


def similitud(a, b):
    return SequenceMatcher(None, limpiar_texto(a), limpiar_texto(b)).ratio()


def similitud_cliente(a, b):
    texto_a = limpiar_texto(a)
    texto_b = limpiar_texto(b)
    tokens_a = set(texto_a.split())
    tokens_b = set(texto_b.split())

    if not tokens_a or not tokens_b:
        return 0

    interseccion = tokens_a.intersection(tokens_b)
    similitud_tokens = (2 * len(interseccion)) / (len(tokens_a) + len(tokens_b))
    similitud_orden = SequenceMatcher(None, texto_a, texto_b).ratio()

    return max(similitud_tokens, similitud_orden)


def coinciden_clientes(c1, c2):
    return similitud_cliente(c1, c2) >= UMBRAL_CLIENTE


def limpiar_numero(valor):
    if pd.isna(valor):
        return 0

    valor = re.sub(r"[^\d.]", "", str(valor))

    try:
        return float(valor)
    except ValueError:
        return 0


def limpiar_imei(imei):
    if pd.isna(imei):
        return ""

    return re.sub(r"\D", "", str(imei))


def cargar_excel(path):
    df = pd.read_excel(path)
    df.columns = [col.strip().upper() for col in df.columns]

    columnas_requeridas = {
        COLUMNA_CLIENTE,
        COLUMNA_MODELO,
        COLUMNA_VENTAS,
        COLUMNA_IMEI,
    }
    faltantes = columnas_requeridas.difference(df.columns)
    if faltantes:
        raise ValueError(f"{path} no tiene columnas requeridas: {', '.join(faltantes)}")

    df = df[[COLUMNA_CLIENTE, COLUMNA_MODELO, COLUMNA_VENTAS, COLUMNA_IMEI]].copy()
    df["FILA"] = df.index + 2

    return df


def comparar(df1, df2):
    errores = []
    contifico_usados = set()

    for _, row1 in df1.iterrows():
        cliente1 = row1[COLUMNA_CLIENTE]
        venta1 = limpiar_numero(row1[COLUMNA_VENTAS])
        imei1 = limpiar_imei(row1[COLUMNA_IMEI])
        fila1 = row1["FILA"]

        if not imei1:
            errores.append(
                {
                    "fila_excel1": fila1,
                    "fila_excel2": None,
                    "cliente": cliente1,
                    "imei_excel1": imei1,
                    "error": "IMEI VACIO EN REPORTE PDF",
                }
            )
            continue

        candidatos_cliente = []
        for indice2, row2 in df2.iterrows():
            cliente2 = row2[COLUMNA_CLIENTE]
            sim_cliente = similitud_cliente(cliente1, cliente2)
            if sim_cliente >= UMBRAL_CLIENTE:
                candidatos_cliente.append((indice2, row2, sim_cliente))

        if not candidatos_cliente:
            errores.append(
                {
                    "fila_excel1": fila1,
                    "fila_excel2": None,
                    "cliente": cliente1,
                    "error": "CLIENTE NO ENCONTRADO",
                }
            )
            continue

        candidatos_imei = [
            (indice2, row2, sim_cliente)
            for indice2, row2, sim_cliente in candidatos_cliente
            if limpiar_imei(row2[COLUMNA_IMEI]) == imei1
        ]

        if not candidatos_imei:
            imeis_contifico = sorted(
                {
                    limpiar_imei(row2[COLUMNA_IMEI])
                    for _, row2, _ in candidatos_cliente
                    if limpiar_imei(row2[COLUMNA_IMEI])
                }
            )
            errores.append(
                {
                    "fila_excel1": fila1,
                    "fila_excel2": None,
                    "cliente": cliente1,
                    "imei_excel1": imei1,
                    "imeis_contifico_cliente": ", ".join(imeis_contifico[:5]),
                    "error": "IMEI NO ENCONTRADO PARA CLIENTE",
                }
            )
            continue

        candidatos_disponibles = [
            candidato
            for candidato in candidatos_imei
            if candidato[0] not in contifico_usados
        ]

        if not candidatos_disponibles:
            errores.append(
                {
                    "fila_excel1": fila1,
                    "fila_excel2": None,
                    "cliente": cliente1,
                    "imei_excel1": imei1,
                    "error": "IMEI DUPLICADO EN REPORTE PDF",
                }
            )
            continue

        indice2, row2, sim_cliente = min(
            candidatos_disponibles,
            key=lambda candidato: abs(
                venta1 - limpiar_numero(candidato[1][COLUMNA_VENTAS])
            ),
        )
        contifico_usados.add(indice2)

        venta2 = limpiar_numero(row2[COLUMNA_VENTAS])
        fila2 = row2["FILA"]

        if abs(venta1 - venta2) > TOLERANCIA_PRECIO:
            errores.append(
                {
                    "fila_excel1": fila1,
                    "fila_excel2": fila2,
                    "cliente": cliente1,
                    "cliente_contifico": row2[COLUMNA_CLIENTE],
                    "similitud_cliente": round(sim_cliente, 2),
                    "imei": imei1,
                    "venta_excel1": venta1,
                    "venta_excel2": venta2,
                    "diferencia": round(abs(venta1 - venta2), 2),
                    "error": "PRECIO NO COINCIDE",
                }
            )

    return errores


def generar_reporte_errores(saas=SAAS, contifico=CONTIFICO, reporte=REPORTE):
    df1 = cargar_excel(saas)
    df2 = cargar_excel(contifico)
    errores = comparar(df1, df2)

    if errores:
        pd.DataFrame(errores).to_excel(reporte, index=False)
    else:
        pd.DataFrame(columns=["error"]).to_excel(reporte, index=False)

    return {
        "output_file": reporte,
        "incidencias": len(errores),
        "registros_saas": len(df1),
        "registros_contifico": len(df2),
    }


if __name__ == "__main__":
    resultado = generar_reporte_errores()
    print("\n--- RESULTADOS ---\n")
    print(f"Total incidencias: {resultado['incidencias']}")
    print("\nArchivo generado:", resultado["output_file"])
