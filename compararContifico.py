import pandas as pd
import re
from difflib import SequenceMatcher

# ---------- CONFIG ----------
CONTIFICO = "contifico_limpio.xlsx"
SAAS = "uphone_limpio.xlsx"

COLUMNA_CLIENTE = "CLIENTE"
COLUMNA_MODELO = "MODELO"
COLUMNA_VENTAS = "VENTAS"
COLUMNA_IMEI = "IMEI"

UMBRAL_CLIENTE = 0.8
UMBRAL_MODELO = 0.6
TOLERANCIA_PRECIO = 0.01

# ---------- FUNCIONES ----------

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
    except:
        return 0


def limpiar_imei(imei):
    if pd.isna(imei):
        return ""

    return re.sub(r"\D", "", str(imei))


# ---------- CARGA ----------

def cargar_excel(path):
    df = pd.read_excel(path)

    df.columns = [col.strip().upper() for col in df.columns]

    if (
        COLUMNA_CLIENTE not in df.columns
        or COLUMNA_MODELO not in df.columns
        or COLUMNA_VENTAS not in df.columns
        or COLUMNA_IMEI not in df.columns
    ):
        raise Exception(f"{path} no tiene columnas requeridas")

    df = df[[COLUMNA_CLIENTE, COLUMNA_MODELO, COLUMNA_VENTAS, COLUMNA_IMEI]].copy()
    df["FILA"] = df.index + 2

    return df


# ---------- COMPARACIÓN ----------

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

                # ---------- IMEI ----------
                if imei1 != imei2 or len(imei1) != len(imei2):
                    errores.append({
                        "fila_excel1": fila1,
                        "fila_excel2": fila2,
                        "cliente": cliente1,
                        "imei_excel1": imei1,
                        "imei_excel2": imei2,
                        "error": "IMEI DIFERENTE O LONGITUD INCORRECTA",
                    })

                # ---------- PRECIO ----------
                if abs(venta1 - venta2) > TOLERANCIA_PRECIO:
                    errores.append({
                        "fila_excel1": fila1,
                        "fila_excel2": fila2,
                        "cliente": cliente1,
                        "venta_excel1": venta1,
                        "venta_excel2": venta2,
                        "diferencia": round(abs(venta1 - venta2), 2),
                        "error": "PRECIO FUERA DE RANGO",
                    })

                # ---------- MODELO ----------
                sim = similitud(modelo1, modelo2)

                if sim < UMBRAL_MODELO:
                    errores.append({
                        "fila_excel1": fila1,
                        "fila_excel2": fila2,
                        "cliente": cliente1,
                        "modelo_excel1": modelo1,
                        "modelo_excel2": modelo2,
                        "similitud": round(sim, 2),
                        "error": "MODELO DIFERENTE",
                    })

                break

        if not encontrado:
            errores.append({
                "fila_excel1": fila1,
                "fila_excel2": None,
                "cliente": cliente1,
                "error": "CLIENTE NO ENCONTRADO",
            })

    return errores


# ---------- MAIN ----------

if __name__ == "__main__":

    df1 = cargar_excel(SAAS)
    df2 = cargar_excel(CONTIFICO)

    errores = comparar(df1, df2)

    print("\n--- RESULTADOS ---\n")

    for e in errores:
        print(e)

    print(f"\nTotal incidencias: {len(errores)}")

    if errores:
        pd.DataFrame(errores).to_excel("errores_completo.xlsx", index=False)
        print("\nArchivo generado: errores_completo.xlsx")