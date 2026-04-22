# 📦 Guía de Instalación - Sueldos App Web

## Opción 1: Instalación Automática (Recomendado)

### En Linux/Mac:
```bash
chmod +x setup.sh
./setup.sh
```

### En Windows:
Haz doble click en `setup.bat`

---

## Opción 2: Instalación Manual

### Requisitos
- Python 3.8 o superior
- Git (opcional)

### Paso 1: Descargar/Clonar el proyecto

**Con Git:**
```bash
git clone <url-repositorio>
cd Sueldos-App-Web
```

**Sin Git:**
- Descarga el ZIP desde GitHub
- Descomprime en una carpeta
- Abre terminal/CMD en esa carpeta

### Paso 2: Crear entorno virtual

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate.ps1
```

### Paso 3: Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Paso 4: Ejecutar la Aplicación

**Abre DOS terminales/CMD**

### Terminal 1 - Backend (Flask)

```bash
# Activar entorno (si no lo hiciste ya)
source venv/bin/activate              # Linux/Mac
# o
venv\Scripts\activate                 # Windows CMD

# Ejecutar backend
python backend/app.py
```

Deberías ver:
```
 * Running on http://127.0.0.1:5000
 * Debugger is active!
```

### Terminal 2 - Frontend (HTTP Server)

```bash
cd frontend
python3 -m http.server 8000
```

Deberías ver:
```
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
```

---

## Paso 5: Acceder a la Aplicación

**Abre tu navegador y ve a:**
```
http://localhost:8000
```

✅ ¡Listo! La aplicación debería cargar completamente.

---

## Solución de Problemas

### ❌ "Port 5000 already in use" (Backend)
El puerto 5000 ya está siendo usado por otra aplicación.

**Solución:**
```bash
# Linux/Mac - encontrar y matar el proceso
lsof -i :5000
kill -9 <PID>

# Windows - cambiar el puerto en app.py
# En backend/app.py, cambia:
# app.run(debug=True, port=5000)
# A:
# app.run(debug=True, port=5001)
```

### ❌ "Port 8000 already in use" (Frontend)
```bash
cd frontend
python3 -m http.server 8001  # Usa otro puerto
# Luego accede a: http://localhost:8001
```

### ❌ "Failed to fetch" al cargar la página
El backend no está corriendo.

**Verificar:**
1. ¿Está la Terminal 1 corriendo `python backend/app.py`?
2. ¿Dice "Running on http://127.0.0.1:5000"?
3. Si no, ejecuta nuevamente el comando

### ❌ "ModuleNotFoundError" (falta algún módulo)
```bash
# Asegúrate de que el entorno virtual está activado
# Debería ver (venv) al inicio de la terminal

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### ❌ "python: command not found"
Python no está en el PATH.

**Solución:**
- En Windows: Desinstala Python y reinstala (marca "Add Python to PATH")
- En Mac: Instala Python desde https://www.python.org/downloads/
- En Linux: `sudo apt install python3`

### ❌ La página carga pero no se ve contenido
Presiona `Ctrl+F5` (o `Cmd+Shift+R` en Mac) para forzar recarga y limpiar cache.

---

## ¿Quieres cambiar el puerto?

### Backend (cambiar de 5000):
Edita `backend/app.py`, encuentra la última línea:
```python
if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

Cambia `5000` al puerto que quieras (ej: `5001`):
```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)
```

### Frontend (cambiar de 8000):
```bash
cd frontend
python3 -m http.server 8001  # Cambia 8000 a 8001
```

---

## Próximas Sesiones: Cómo ejecutar sin hacer setup nuevamente

```bash
# Solo necesitas:
source venv/bin/activate              # Linux/Mac
# o
venv\Scripts\activate                 # Windows

# Luego en 2 terminales:
# Terminal 1:
python backend/app.py

# Terminal 2:
cd frontend
python3 -m http.server 8000
```

---

## Documentación Técnica

Para desarrolladores que quieran entender la arquitectura:
- Lee `CLAUDE.md` — Documentación completa para desarrolladores
- Lee `README.md` — Features y endpoints API

---

**¿Necesitas ayuda?**
- Revisa el archivo de logs: `/tmp/backend.log` (Linux/Mac)
- Abre DevTools en el navegador: `F12` → Console para ver errores JavaScript

**Última actualización:** 2026-04-22
