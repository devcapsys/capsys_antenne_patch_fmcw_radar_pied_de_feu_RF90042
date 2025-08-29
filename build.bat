@echo off
echo =============================================
echo     Compilation CAPSYS Banc De Test
echo =============================================

echo.
echo Verification Git et mise a jour de la version...
python version_manager.py git

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERREUR: La verification Git a echoue.
    echo La compilation est annulee.
    exit /b 1
)

echo.
echo Lancement de PyInstaller...
pyinstaller main.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERREUR: PyInstaller a echoue.
    exit /b 1
)

echo.
echo Remise de VERSION a DEBUG...
python version_manager.py debug

echo.
echo =============================================
echo     Compilation terminee avec succes !
echo =============================================
echo L'executable se trouve dans le dossier dist/