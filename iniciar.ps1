# AstroCopilot - inicializador de 1 clique (Frente 5)
# Sobe o BACKEND (venv + ffmpeg + uvicorn) e o DASHBOARD (npm run dev) em
# duas janelas separadas. Use o iniciar.bat (duplo-clique) ou rode:
#   powershell -ExecutionPolicy Bypass -File iniciar.ps1
$root = $PSScriptRoot

# --- localiza o ffmpeg (instalado via winget) para a voz por arquivo/gravacao ---
$ffmpegDir = ""
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    $pkgRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    $bin = Get-ChildItem $pkgRoot -Recurse -Filter ffmpeg.exe -ErrorAction SilentlyContinue |
           Select-Object -First 1
    if ($bin) { $ffmpegDir = $bin.Directory.FullName }
}

# --- valida o venv do backend ---
$activate = Join-Path $root "backend\.venv\Scripts\Activate.ps1"
if (-not (Test-Path $activate)) {
    Write-Host "venv nao encontrado em backend\.venv" -ForegroundColor Red
    Write-Host "Crie com:  cd backend; python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt"
    Read-Host "Enter para sair"
    exit 1
}

# --- comando do BACKEND (nova janela) ---
$backendCmd = "Set-Location '$root\backend'; & '$activate';"
if ($ffmpegDir) { $backendCmd += " `$env:PATH = '$ffmpegDir;' + `$env:PATH;" }
$backendCmd += " Write-Host 'Backend: http://localhost:8000/docs' -ForegroundColor Cyan; uvicorn main:app --reload"

# --- comando do DASHBOARD (nova janela) ---
$dashCmd = "Set-Location '$root\dashboard'; if (-not (Test-Path node_modules)) { npm install }; Write-Host 'Dashboard: http://localhost:5173' -ForegroundColor Cyan; npm run dev"

Write-Host "Subindo backend e dashboard em duas janelas..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", $dashCmd

Write-Host ""
Write-Host "Pronto! Aguarde alguns segundos e abra:  http://localhost:5173  (Chrome ou Edge)" -ForegroundColor Green
Write-Host "Para parar: feche as duas janelas (ou Ctrl+C em cada uma)."
Start-Sleep -Seconds 4
