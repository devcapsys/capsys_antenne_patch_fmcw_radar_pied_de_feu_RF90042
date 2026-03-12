@echo off
echo =============================================
echo     Compilation CAPSYS Banc De Test
echo =============================================

echo.
echo Initialisation des sous-modules...
python init_submodules.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERREUR: L'initialisation des sous-modules a echoue.
    echo La compilation est annulee.
    exit /b 1
)
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
python -m PyInstaller main.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERREUR: PyInstaller a echoue.
    exit /b 1
)

echo.
echo Remise de VERSION a DEBUG...
python version_manager.py debug

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERREUR: Impossible de remettre HASH_GIT a DEBUG.
    exit /b 1
)

echo.
echo Incrementation de VERSION...
python version_manager.py bump

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERREUR: Impossible d'incrementer VERSION.
    exit /b 1
)

echo.
echo =============================================
echo     Compilation terminee avec succes !
echo =============================================
echo L'executable se trouve dans le dossier dist/