import re
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
UMBRAL_MODELO = 0.6
TOLERANCIA_PRECIO = 0.01


def limpiar_texto(texto):
    if pd.isna(texto):
        return ""

    texto = str(texto)
    texto = texto.replace("\n", " ")
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip().lower()


def similitud(a, b):
    return SequenceMatcher(None, limpiar_texto(a), limpiar_texto(b)).ratio()


def coinciden_clientes(c1, c2):
    return similitud(c1, c2) >= UMBRAL_CLIENTE


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

    for _, row1 in df1.iterrows():
        cliente1 = row1[COLUMNA_CLIENTE]
        modelo1 = row1[COLUMNA_MODELO]
        venta1 = limpiar_numero(row1[COLUMNA_VENTAS])
        imei1 = limpiar_imei(row1[COLUMNA_IMEI])
        fila1 = row1["FILA"]

        encontrado = False

        for _, row2 in df2.iterrows():
            cliente2 = row2[COLUMNA_CLIENTE]
            modelo2 = row2[COLUMNA_MODELO]
            venta2 = limpiar_numero(row2[COLUMNA_VENTAS])
            imei2 = limpiar_imei(row2[COLUMNA_IMEI])
            fila2 = row2["FILA"]

            if coinciden_clientes(cliente1, cliente2):
                encontrado = True

                if imei1 != imei2 or len(imei1) != len(imei2):
                    errores.append(
                        {
                            "fila_excel1": fila1,
                            "fila_excel2": fila2,
                            "cliente": cliente1,
                            "imei_excel1": imei1,
                            "imei_excel2": imei2,
                            "error": "IMEI DIFERENTE O LONGITUD INCORRECTA",
                        }
                    )

                if abs(venta1 - venta2) > TOLERANCIA_PRECIO:
                    errores.append(
                        {
                            "fila_excel1": fila1,
                            "fila_excel2": fila2,
                            "cliente": cliente1,
                            "venta_excel1": venta1,
                            "venta_excel2": venta2,
                            "diferencia": round(abs(venta1 - venta2), 2),
                            "error": "PRECIO FUERA DE RANGO",
                        }
                    )

                sim = similitud(modelo1, modelo2)
                if sim < UMBRAL_MODELO:
                    errores.append(
                        {
                            "fila_excel1": fila1,
                            "fila_excel2": fila2,
                            "cliente": cliente1,
                            "modelo_excel1": modelo1,
                            "modelo_excel2": modelo2,
                            "similitud": round(sim, 2),
                            "error": "MODELO DIFERENTE",
                        }
                    )

                break

        if not encontrado:
            errores.append(
                {
                    "fila_excel1": fila1,
                    "fila_excel2": None,
                    "cliente": cliente1,
                    "error": "CLIENTE NO ENCONTRADO",
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
