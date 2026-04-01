import pandas as pd

# -------- CONFIGURACIÓN --------
ARCHIVO_ENTRADA = "Contifico.xlsx"
ARCHIVO_SALIDA = "contifico_limpio.xlsx"

# Columnas que necesitamos
COLUMNAS = [
    "Tipo Documento",
    "Persona",
    "Identificación",
    "Nombre",
    "Nombre Manual",
    "Total"
]

# -------- LEER EXCEL --------
df = pd.read_excel(ARCHIVO_ENTRADA)

# -------- FILTROS --------
df = df[
    (df["Tipo Documento"] == "Factura") &
    (df["Persona"] != "CREDITV-ECUADOR S.A.S") &
    (df["Saldo"] != 0)
]

# -------- SELECCIONAR COLUMNAS --------
df = df[COLUMNAS]

# -------- RENOMBRAR COLUMNAS --------
df = df.rename(columns={
    "Persona": "CLIENTE",
    "Nombre": "MODELO",
    "Nombre Manual": "IMEI",
    "Total": "VENTAS"
})

# -------- GUARDAR NUEVO EXCEL --------
df.to_excel(ARCHIVO_SALIDA, index=False)

print("Archivo limpio generado:", ARCHIVO_SALIDA)