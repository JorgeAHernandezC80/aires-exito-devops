# Actualización de datos desde un computador propio (Windows / PowerShell).
#
# Se usa cuando el workflow "Actualizar datos (semanal)" termina en amarillo porque Éxito.com
# bloquea a los servidores de GitHub con la verificación anti-bots de Cloudflare.
# Hace lo mismo que el workflow: scraping -> validación -> limpieza -> fecha -> reporte -> PR.
#
# Uso, desde la carpeta del repositorio:
#   powershell -ExecutionPolicy Bypass -File scripts\actualizar_datos_local.ps1
#
# Requisitos: Python 3.11+, Google Chrome y Git. GitHub CLI (gh) es opcional: si está instalado
# y con sesión iniciada, el script abre el pull request; si no, muestra el enlace para abrirlo.

$ErrorActionPreference = "Continue"  # los errores se controlan con $LASTEXITCODE

function Paso($texto) { Write-Host "`n==> $texto" -ForegroundColor Cyan }
function Fallar($texto) { Write-Host "`nERROR: $texto" -ForegroundColor Red; exit 1 }
function Ejecutar([string]$descripcion, [scriptblock]$comando) {
    & $comando
    if ($LASTEXITCODE -ne 0) { Fallar "$descripcion (código $LASTEXITCODE)." }
}

# --- 1. Verificar que estamos en el repositorio correcto y al día -----------------------------
Paso "Verificando el repositorio"
$raiz = git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0) { Fallar "esta carpeta no es un repositorio de Git. Entra a la carpeta clonada (por ejemplo Documents\aires-repo)." }
Set-Location $raiz
$origen = git remote get-url origin 2>$null
if ($origen -notmatch "aires-exito-devops") { Fallar "el remoto 'origin' no es aires-exito-devops ($origen)." }
if (git status --porcelain) { Fallar "hay cambios sin guardar. Haz commit o descártalos antes de actualizar los datos." }

Ejecutar "no se pudo cambiar a main" { git switch main }
Ejecutar "no se pudo actualizar main" { git pull --ff-only }

# --- 2. Dependencias ------------------------------------------------------------------------
Paso "Instalando dependencias (solo la primera vez tarda)"
Ejecutar "falló la instalación" { python -m pip install --quiet --disable-pip-version-check -e ".[scraping]" }

# --- 3. Scraping y validación -----------------------------------------------------------------
Paso "Scraping de Éxito.com (Chrome en segundo plano, 1 a 3 minutos)"
python -m aires_exito scrape --salida data/aires_acondicionados_exito_crudo.csv
if ($LASTEXITCODE -eq 3) {
    Fallar ("Éxito.com también mostró la verificación anti-bots en este equipo. Los datos no se tocaron.`n" +
            "Alternativa: guardar las páginas desde el navegador en data\raw\page_01.html, page_02.html, ...`n" +
            "y ejecutar: python -m aires_exito desde-html data\raw")
}
if ($LASTEXITCODE -ne 0) { git checkout -- data/; Fallar "el scraping falló; revisa la carpeta debug\. Los datos se dejaron como estaban." }

Paso "Validando la extracción"
python -m aires_exito validar --entrada data/aires_acondicionados_exito_crudo.csv
if ($LASTEXITCODE -ne 0) { git checkout -- data/; Fallar "la extracción no pasó la validación. Los datos se dejaron como estaban." }

# --- 4. Limpieza, fecha y reporte --------------------------------------------------------------
Paso "Limpiando y fechando"
Ejecutar "falló la limpieza" { python -m aires_exito limpiar }
$fecha = Get-Date -Format "yyyy-MM-dd"
[System.IO.File]::WriteAllText((Join-Path $raiz "data\fecha_extraccion.txt"), "$fecha`n")

Paso "Generando el reporte (_site\index.html)"
Ejecutar "falló el reporte" { python -m aires_exito reporte }
Start-Process (Join-Path $raiz "_site\index.html")

if (-not (git status --porcelain -- data/)) {
    Write-Host "`nLos datos no cambiaron desde la última extracción; no hay nada que subir." -ForegroundColor Yellow
    exit 0
}

# --- 5. Rama, commit, push y pull request -------------------------------------------------------
$rama = "data/actualizacion-" + (Get-Date -Format "yyyyMMdd")
Paso "Subiendo los datos a la rama $rama"
Ejecutar "no se pudo crear la rama" { git switch -C $rama }
Ejecutar "git add falló" { git add data/ }
Ejecutar "git commit falló" { git commit -m "data: actualización manual del $fecha" }
Ejecutar "git push falló" { git push --force -u origin $rama }

$titulo = "data: actualización manual del $fecha"
$cuerpo = "Extracción hecha en local con scripts/actualizar_datos_local.ps1 porque Éxito.com bloquea a los runners de GitHub (Cloudflare). Revisar el diff del CSV antes de fusionar."
if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh pr create --base main --head $rama --title $titulo --body $cuerpo
    if ($LASTEXITCODE -eq 0) { Write-Host "`nListo: PR abierto. Cuando el CI pase, fusiónalo y el Deploy publica el reporte." -ForegroundColor Green; git switch main; exit 0 }
}
$repo = ($origen -replace '\.git$', '') -replace '^git@github.com:', 'https://github.com/'
Write-Host "`nListo. Abre el PR aquí: $repo/compare/main...$rama" -ForegroundColor Green
git switch main
