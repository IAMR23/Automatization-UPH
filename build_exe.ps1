$ErrorActionPreference = "Stop"

$appName = "GeneradorReportes"
$entryPoint = "app.py"

Write-Host "Instalando dependencias..."
python -m pip install -r requirements.txt

Write-Host "Generando ejecutable..."
python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name $appName `
    --hidden-import openpyxl `
    --hidden-import xlrd `
    --hidden-import pdfplumber `
    $entryPoint

Write-Host ""
Write-Host "Ejecutable creado en: dist\$appName.exe"
Write-Host "Ese archivo se puede copiar a una computadora sin Python."
