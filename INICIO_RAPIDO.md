# ⚡ Inicio Rápido - Sueldos App Web

## Carpeta: Github

Esta carpeta contiene **TODOS** los archivos necesarios para:
1. Subir a GitHub
2. Que corra localmente sin modificaciones
3. Desplegar en servidor

---

## ¿Qué hay adentro?

```
Github/
├── README.md              ← Descripción del proyecto
├── INSTALACION.md         ← Guía paso-a-paso de instalación
├── CLAUDE.md              ← Documentación técnica para desarrolladores
├── INICIO_RAPIDO.md       ← Este archivo
│
├── setup.sh               ← Script de instalación (Linux/Mac)
├── setup.bat              ← Script de instalación (Windows)
│
├── requirements.txt       ← Dependencias Python
├── .env.example           ← Plantilla de variables de entorno
├── .gitignore             ← Qué archivos NO subir a GitHub
│
├── frontend/
│   ├── index.html         ← Aplicación completa (SPA)
│   └── logo.png           ← Logo de la empresa
│
└── backend/
    └── app.py             ← Servidor Flask
```

---

## Instalación en 3 pasos

### 1️⃣ Linux/Mac
```bash
chmod +x setup.sh
./setup.sh
```

### 1️⃣ Windows
Haz doble click en `setup.bat`

### 2️⃣ Ejecutar (en 2 terminales)

**Terminal 1:**
```bash
source venv/bin/activate   # (venv\Scripts\activate en Windows)
python backend/app.py
```

**Terminal 2:**
```bash
cd frontend
python3 -m http.server 8000
```

### 3️⃣ Acceder
Abre navegador: `http://localhost:8000` ✅

---

## Preparar para GitHub

### 1. Crear repositorio en GitHub
- Ve a https://github.com/new
- Nombre: `Sueldos-App-Web` (o similar)
- Descripción: "Sistema de gestión de nómina web"
- ❌ NO inicialices con README (lo copiarás después)

### 2. Subir los archivos

```bash
cd /ruta/a/Github  # Entra en esta carpeta

git init
git add .
git commit -m "Initial commit: Sueldos App Web"
git branch -M main
git remote add origin https://github.com/tu-usuario/Sueldos-App-Web.git
git push -u origin main
```

### 3. Resultado
Tu GitHub tendrá:
- ✅ Código frontend y backend
- ✅ README profesional
- ✅ Guía de instalación
- ✅ Scripts de setup automático
- ✅ Documentación técnica
- ✅ .gitignore (sin venv, __pycache__, .db, etc.)

---

## Para Clonar Después (Tú o Alguien Más)

```bash
git clone https://github.com/tu-usuario/Sueldos-App-Web.git
cd Sueldos-App-Web

# Linux/Mac:
chmod +x setup.sh && ./setup.sh

# Windows:
setup.bat
```

Luego ejecutar como antes (2 terminales).

---

## ¿Qué NO está incluido?

- ❌ `venv/` (se crea con setup)
- ❌ `data/sueldos.db` (se crea automáticamente)
- ❌ `__pycache__/` (cache de Python)
- ❌ `.pyc` files (compilados)

Esto está en `.gitignore` por seguridad y para evitar conflictos.

---

## Cambios antes de subir (Opcionales)

### En `README.md`:
Reemplaza:
```
**Autor**: Ivan (ivarojero@gmail.com)
```
Con tu info.

### En `CLAUDE.md`:
Actualiza la fecha en "Version History" si hiciste cambios.

### En `backend/app.py`:
Si quieres cambiar puerto (por defecto 5000):
```python
app.run(debug=True, port=5000)  # Cambia el 5000
```

---

## Estructura de Carpetas

```
Tu Máquina (Local)
├── /ruta/a/Github/          ← Esta carpeta (subes a GitHub)
│   ├── frontend/
│   ├── backend/
│   ├── README.md
│   ├── requirements.txt
│   └── ...
│
└── GitHub (Nube)
    └── tu-usuario/Sueldos-App-Web/
        ├── frontend/
        ├── backend/
        └── ...
```

---

## Checklist Final

Antes de subir a GitHub:

- ✅ `setup.sh` tiene permisos de ejecución (`chmod +x`)
- ✅ `setup.bat` existe y funciona (prueba haciendo doble click)
- ✅ `requirements.txt` tiene todas las dependencias
- ✅ `.gitignore` excluye `venv/`, `*.db`, `__pycache__`
- ✅ `README.md` tiene instrucciones claras
- ✅ `INSTALACION.md` es detallado
- ✅ `CLAUDE.md` explica la arquitectura
- ✅ `frontend/index.html` está completo
- ✅ `backend/app.py` está completo
- ✅ `frontend/logo.png` existe

---

## Soporte Rápido

| Problema | Solución |
|----------|----------|
| Port already in use | Cambia puerto en app.py o usa otro |
| Module not found | Ejecuta `pip install -r requirements.txt` |
| Frontend no ve backend | Verifica que Terminal 1 está corriendo |
| Página en blanco | Presiona `Ctrl+F5` para limpiar cache |
| GitHub no deja subir | Agrega `.gitignore` ANTES de `git add .` |

---

## Resumen

- 📂 Carpeta `Github/` = Listo para subir
- 🚀 Setup automático (Windows + Linux/Mac)
- 📖 Documentación completa (README + INSTALACION + CLAUDE)
- 🔧 Scripts para inicializar proyecto
- 🎯 Cualquiera puede clonar y correr en 5 minutos

**Última actualización:** 2026-04-22
