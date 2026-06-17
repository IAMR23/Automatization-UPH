import pandas as pd


ARCHIVO_ENTRADA = "Documentos.xls"
ARCHIVO_SALIDA = "contifico_limpio.xlsx"

COLUMNAS = [
    "Tipo Documento",
    "Persona",
    "Identificación",
    "Nombre",
    "Nombre Manual",
    "Total",
]


def limpiar_contifico(archivo_entrada=ARCHIVO_ENTRADA, archivo_salida=ARCHIVO_SALIDA):
    df = pd.read_excel(archivo_entrada, skiprows=3)

    columnas_requeridas = set(COLUMNAS + ["Saldo"])
    faltantes = columnas_requeridas.difference(df.columns)
    if faltantes:
        raise ValueError(
            "El archivo de Contifico no tiene las columnas requeridas: "
            + ", ".join(sorted(faltantes))
        )

    df = df[
        (df["Tipo Documento"] == "Factura")
        & (df["Persona"] != "CREDITV-ECUADOR S.A.S")
        & (df["Saldo"] != 0)
    ]

    df = df[COLUMNAS]
    df = df.rename(
        columns={
            "Persona": "CLIENTE",
            "Nombre": "MODELO",
            "Nombre Manual": "IMEI",
            "Total": "VENTAS",
        }
    )

    df.to_excel(archivo_salida, index=False)
    return {"output_file": archivo_salida, "registros": len(df)}


if __name__ == "__main__":
    resultado = limpiar_contifico()
    print("Archivo limpio generado:", resultado["output_file"])
