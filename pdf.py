import pdfplumber
import pandas as pd
import os
import re
from glob import glob

# Carpeta donde están los PDFs
PDF_FOLDER = "pdf"  # cambia si tu carpeta tiene otro nombre
OUTPUT_FILE = "uphone.xlsx"

all_dataframes = []


def clean_cell(text):
    """
    Limpia saltos de línea y espacios extras dentro de una celda
    """
    if text is None:
        return text

    # Reemplazar saltos de línea por espacio
    text = re.sub(r'[\n\r]+', ' ', str(text))

    # Eliminar espacios duplicados
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def clean_dataframe(df):
    """
    Limpia el dataframe eliminando filas innecesarias
    y normalizando texto
    """

    # Limpiar cada celda
    df = df.apply(lambda col: col.map(clean_cell))

    # Eliminar filas que contengan "TOTALES GENERALES"
    df = df[
        ~df.apply(
            lambda row: row.astype(str).str.contains(
                "TOTALES GENERALES", case=False
            ).any(),
            axis=1
        )
    ]

    # Eliminar filas completamente vacías
    df = df.dropna(how="all")

    return df


def extract_tables_from_pdf(pdf_path):
    """
    Extrae todas las tablas de un PDF
    """
    dataframes = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:

            tables = page.extract_tables()

            for table in tables:

                if not table or len(table) < 2:
                    continue

                # Primera fila como encabezado
                df = pd.DataFrame(table[1:], columns=table[0])

                df = clean_dataframe(df)

                # Agregar columna con nombre del archivo
                df["archivo_origen"] = os.path.basename(pdf_path)

                dataframes.append(df)

    return dataframes


# Buscar todos los PDFs en la carpeta
pdf_files = glob(os.path.join(PDF_FOLDER, "*.pdf"))

for pdf_file in pdf_files:
    print(f"Procesando: {pdf_file}")

    dfs = extract_tables_from_pdf(pdf_file)

    all_dataframes.extend(dfs)


if not all_dataframes:
    print("No se encontraron tablas.")
else:

    # Unir todos los dataframes
    final_df = pd.concat(all_dataframes, ignore_index=True, sort=False)

    # Exportar a Excel
    final_df.to_excel(OUTPUT_FILE, index=False)

    print(f"Archivo generado correctamente: {OUTPUT_FILE}")