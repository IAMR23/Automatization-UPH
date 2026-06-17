import pandas as pd


def limpiar_uphone(archivo_entrada="uphone.xlsx", archivo_salida="uphone_limpio.xlsx"):
    df = pd.read_excel(archivo_entrada)

    if "IMEI" not in df.columns:
        raise ValueError("El archivo de UPHONE no tiene la columna IMEI.")

    df_limpio = df[df["IMEI"].notna()]
    df_limpio = df_limpio[df_limpio["IMEI"].astype(str).str.strip() != ""]
    df_limpio.to_excel(archivo_salida, index=False)

    return {"output_file": archivo_salida, "registros": len(df_limpio)}


if __name__ == "__main__":
    resultado = limpiar_uphone()
    print("Archivo limpio generado:", resultado["output_file"])
