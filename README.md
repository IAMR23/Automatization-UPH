# Generador de Reportes PDF a Excel

Aplicacion de escritorio para ejecutar el flujo completo:

1. Extraer tablas de PDFs con `pdf.py`.
2. Limpiar el archivo generado con `limpieza.py`.
3. Limpiar el archivo descargado de Contifico con `limpiarContifico.py`.
4. Comparar ambos archivos limpios con `compararContifico.py`.
5. Generar `errores_completo.xlsx`.

## Instalacion

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Ejecutar

```powershell
python app.py
```

## Crear ejecutable

```powershell
.\build_exe.ps1
```

El ejecutable queda en:

```text
dist\GeneradorReportes.exe
```

Ese archivo puede copiarse a otra computadora Windows sin instalar Python.

Tambien puedes seguir ejecutando los scripts individuales:

```powershell
python pdf.py
python limpieza.py
python limpiarContifico.py
python compararContifico.py
```
