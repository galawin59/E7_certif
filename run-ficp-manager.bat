@echo off
chcp 65001 >nul
echo.
echo ================================================================
echo    E7 CERTIFICATION - GESTIONNAIRE FICP PRINCIPAL
echo ================================================================
echo.

REM Vérification environnement virtuel
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Erreur: Environnement virtuel non trouvé
    echo Créez l'environnement avec: python -m venv .venv
    pause
    exit /b 1
)

echo 🔧 Activation environnement virtuel...
call .venv\Scripts\activate.bat

echo.
echo � Vérification modules Python...
python -c "import pandas, subprocess, json" 2>nul
if errorlevel 1 (
    echo ⚠️ Installation des dépendances...
    pip install -r requirements.txt
)

echo.
echo 🚀 Lancement gestionnaire FICP...
python scripts\data-processing\ficp-manager.py

echo.
pause