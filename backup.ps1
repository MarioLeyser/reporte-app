# backup.ps1 - Script de backup rapido con Git
# Uso: .\backup.ps1 "mensaje del commit"
# Si no se pasa mensaje, usa la fecha/hora actual

param(
    [string]$Message = ""
)

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

if ($Message -eq "") {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    $Message = "backup: $timestamp"
}

Write-Host "📦 Guardando backup: '$Message'" -ForegroundColor Cyan

git add -A
$status = git status --short

if ($status -eq "") {
    Write-Host "✅ No hay cambios nuevos desde el ultimo backup." -ForegroundColor Yellow
}
else {
    git commit -m $Message
    Write-Host "✅ Backup guardado exitosamente!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Archivos guardados:" -ForegroundColor White
    git show --stat HEAD

    # Subir a GitHub
    Write-Host ""
    Write-Host "☁️  Subiendo a GitHub..." -ForegroundColor Cyan
    $pushResult = git push origin main 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Subido a GitHub correctamente!" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  No se pudo subir a GitHub (puede que no haya internet). El backup local sí se guardó." -ForegroundColor Yellow
        Write-Host $pushResult -ForegroundColor DarkGray
    }
}
