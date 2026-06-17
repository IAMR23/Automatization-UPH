import os
import re
from glob import glob

import pandas as pd
import pdfplumber


PDF_FOLDER = "pdf"
OUTPUT_FILE = "uphone.xlsx"


def clean_cell(text):
    if text is None:
        return text

    text = re.sub(r"[\n\r]+", " ", str(text))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_dataframe(df):
    df = df.apply(lambda col: col.map(clean_cell))
    df = df[
        ~df.apply(
            lambda row: row.astype(str).str.contains(
                "TOTALES GENERALES", case=False
            ).any(),
            axis=1,
        )
    ]
    return df.dropna(how="all")


def extract_tables_from_pdf(pdf_path):
    dataframes = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()

            for table in tables:
                if not table or len(table) < 2:
                    continue

                df = pd.DataFrame(table[1:], columns=table[0])
                df = clean_dataframe(df)
                df["archivo_origen"] = os.path.basename(pdf_path)
                dataframes.append(df)

    return dataframes


def generar_excel_desde_pdfs(pdf_files=None, output_file=OUTPUT_FILE, log_callback=None):
    all_dataframes = []
    archivos_no_leidos = []

    if pdf_files is None:
        pdf_files = glob(os.path.join(PDF_FOLDER, "*.pdf"))

    for pdf_file in pdf_files:
        try:
            if log_callback:
                log_callback(f"Procesando PDF: {pdf_file}")

            all_dataframes.extend(extract_tables_from_pdf(pdf_file))
        except Exception as exc:
            archivos_no_leidos.append({"archivo": pdf_file, "error": str(exc)})
            if log_callback:
                log_callback(f"No se pudo leer {pdf_file}: {exc}")

    if not all_dataframes:
        raise ValueError("No se encontraron tablas en los PDFs seleccionados.")

    final_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
    final_df.to_excel(output_file, index=False)

    return {
        "output_file": output_file,
        "pdfs": len(pdf_files),
        "registros": len(final_df),
        "no_leidos": len(archivos_no_leidos),
        "archivos_no_leidos": archivos_no_leidos,
    }


if __name__ == "__main__":
    resultado = generar_excel_desde_pdfs()
    print(f"Archivo generado correctamente: {resultado['output_file']}")
