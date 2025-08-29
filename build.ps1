# Script PowerShell pour la compilation CAPSYS Banc De Test
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "     Compilation CAPSYS Banc De Test" -ForegroundColor Cyan  
Write-Host "=============================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Vérification Git et mise à jour de la version..." -ForegroundColor Yellow

# Exécuter le script de vérification Git
python version_manager.py git

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERREUR: La vérification Git a échoué." -ForegroundColor Red
    Write-Host "La compilation est annulée." -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour continuer"
    exit 1
}

Write-Host ""
Write-Host "Lancement de PyInstaller..." -ForegroundColor Yellow

# Exécuter PyInstaller
pyinstaller main.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERREUR: PyInstaller a échoué." -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour continuer"
    exit 1
}

Write-Host ""
Write-Host "Remise de VERSION à DEBUG..." -ForegroundColor Yellow
python version_manager.py debug

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "     Compilation terminée avec succès !" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "L'exécutable se trouve dans le dossier dist/" -ForegroundColor Green