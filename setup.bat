@echo off
setlocal enabledelayedexpansion

cls
echo =====================================
echo   Sueldos App Web - Setup Script
echo =====================================
echo.

REM Check Python
echo Verificando Python 3...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3 no esta instalado
    echo Descargalo desde: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

REM Create virtual environment
echo Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo Error al crear entorno virtual
    pause
    exit /b 1
)
echo OK - Entorno virtual creado
echo.

REM Activate virtual environment
echo Activando entorno virtual...
call venv\Scripts\activate.bat
echo OK - Entorno activado
echo.

REM Install dependencies
echo Instalando dependencias...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo Error al instalar dependencias
    pause
    exit /b 1
)
echo OK - Dependencias instaladas
echo.

REM Create .env file
if not exist ".env" (
    echo Creando archivo .env...
    copy .env.example .env >nul
    echo OK - Archivo .env creado
) else (
    echo El archivo .env ya existe
)
echo.

cls
echo =====================================
echo   OK - Setup completado exitosamente
echo =====================================
echo.

echo Proximos pasos:
echo.
echo 1. Abre DOS terminales (CMD o PowerShell)
echo.
echo Terminal 1 - Backend (Flask):
echo   venv\Scripts\activate
echo   python backend\app.py
echo.
echo Terminal 2 - Frontend (HTTP Server):
echo   cd frontend
echo   python -m http.server 8000
echo.
echo Luego abre en tu navegador:
echo   http://localhost:8000
echo.
echo.
pause
