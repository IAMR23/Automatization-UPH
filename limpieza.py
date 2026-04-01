import pandas as pd

# Leer el archivo generado
df = pd.read_excel("uphone.xlsx")

# Filtrar filas donde IMEI no esté vacío
df_limpio = df[df["IMEI"].notna()]

# Opcional: eliminar espacios vacíos también
df_limpio = df_limpio[df_limpio["IMEI"].astype(str).str.strip() != ""]

# Guardar el resultado
df_limpio.to_excel("uphone_limpio.xlsx", index=False)

print("Archivo limpio generado: uphone_limpio.xlsx")