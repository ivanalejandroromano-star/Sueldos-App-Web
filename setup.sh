#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  Sueldos App Web - Setup Script${NC}"
echo -e "${BLUE}=====================================${NC}\n"

# Check Python
echo -e "${BLUE}Verificando Python 3...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no está instalado${NC}"
    echo "Descargalo desde: https://www.python.org/downloads/"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 encontrado$(python3 --version)${NC}\n"

# Create virtual environment
echo -e "${BLUE}Creando entorno virtual...${NC}"
python3 -m venv venv
echo -e "${GREEN}✅ Entorno virtual creado${NC}\n"

# Activate virtual environment
echo -e "${BLUE}Activando entorno virtual...${NC}"
source venv/bin/activate || . venv/Scripts/activate
echo -e "${GREEN}✅ Entorno activado${NC}\n"

# Install dependencies
echo -e "${BLUE}Instalando dependencias...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencias instaladas${NC}\n"

# Create .env file
if [ ! -f .env ]; then
    echo -e "${BLUE}Creando archivo .env...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Archivo .env creado${NC}\n"
fi

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  ✅ Setup completado exitosamente${NC}"
echo -e "${GREEN}=====================================${NC}\n"

echo -e "${BLUE}Próximos pasos:${NC}"
echo "1. Abre DOS terminales (Terminal 1 y Terminal 2)"
echo ""
echo -e "${BLUE}Terminal 1 - Backend (Flask):${NC}"
echo "  source venv/bin/activate  # En Windows: venv\\Scripts\\activate"
echo "  python backend/app.py"
echo ""
echo -e "${BLUE}Terminal 2 - Frontend (HTTP Server):${NC}"
echo "  cd frontend"
echo "  python3 -m http.server 8000"
echo ""
echo -e "${BLUE}Luego abre en tu navegador:${NC}"
echo "  http://localhost:8000"
echo ""
