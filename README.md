# Sueldos App Web

Sistema web de gestión de nómina para empresas constructoras. Automatiza el cálculo quincenal de sueldos, gestiona deudas de empleados, genera PDFs y reportes en Excel.

**Características principales:**
- 📊 Cálculo automático de sueldo bruto, recibos y cierre de quincena
- 💰 Gestión de deudas con cuotas automáticas y postergar/espacios
- 🚕 Control de pasajes y retroactivos distribuidos en múltiples quincenas
- 📄 Generación de PDFs (Recibo B, Cinta Billete)
- 📈 Exportación a Excel con reportes
- 🏗️ Sistema multi-obra (cada proyecto con BD aislada)

## Requisitos

- **Python 3.8+**
- **Git**
- Navegador web moderno (Chrome, Firefox, Safari, Edge)

## Instalación Rápida

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd Sueldos-App-Web
```

### 2. Crear entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

## Ejecución en Desarrollo

### Terminal 1: Backend (Flask)
```bash
source venv/bin/activate  # En Windows: venv\Scripts\activate
python backend/app.py
```
✅ Backend corriendo en `http://localhost:5000`

### Terminal 2: Frontend (HTTP Server)
```bash
cd frontend
python3 -m http.server 8000
```
✅ Interfaz accesible en `http://localhost:8000`

## Estructura del Proyecto

```
├── frontend/
│   ├── index.html          # Aplicación SPA completa (Alpine.js)
│   └── logo.png            # Logo de la empresa
├── backend/
│   └── app.py              # Servidor Flask con todos los endpoints
├── requirements.txt         # Dependencias Python
├── CLAUDE.md               # Documentación técnica detallada
└── .gitignore              # Archivos a ignorar en Git
```

## Funcionalidades Principales

### 📊 Quincena
- Selector de período con auto-generación de 24 quincenas anuales
- Tabla de liquidaciones (editable: días, pasajes, retroactivos)
- Cálculo automático: Sueldo Bruto, Recibo A/B, Deuda, Cinta Billete
- Botones: Importar PDF, Actualizar Todo, Generar PDFs, Exportar Excel, Cerrar Quincena

### 👥 Empleados
- Tabla con búsqueda A-Z por apellido
- CRUD de empleados (legajo, nombre, apellido, CUIL, categoría)
- Gestión de categorías (precio por día)

### 💰 Deudas
- Pestañas: Por Empleado / Todos los Empleados
- Tipos: Monto Fijo o % del Recibo B
- Seguimiento: Monto Total, Ya Pagado, Saldo Pendiente, Progreso visual
- Edición y postergar deudas por quincena

### 🚕 Pasajes
- Registro de viajes con monto y fechas
- Estado: Activo → Pago (al cerrar quincena)
- Edición individual

### 📆 Retroactivos
- Distribución inteligente en múltiples quincenas
- Ejemplo: Retroactivo de 4 meses se paga en 4 quincenas consecutivas
- Saldo decrece automáticamente con cada cierre
- Estado: Activo → Pago (cuando todas las cuotas se pagaron)

### 📈 Historial
- Consulta de quincenas anteriores
- Re-generación de PDFs
- Exportación a Excel de períodos pasados

## Cálculos Clave (Todos en Centavos)

```
Sueldo Bruto = Precio/día × Días trabajados

Recibo B (efectivo) = Sueldo Bruto - (Recibo A - Hab. S/Desc)

Cinta Billete = Recibo B - Deudas + Pasajes + Retroactivos

Deuda por quincena:
  - Monto Fijo: cuota_por_quincena
  - Porcentaje: Recibo B × (% / 100)

Retroactivo: cuota = monto_total / cantidad_meses
  (aplicada en quincena_inicio, +1, +2, ..., hasta cantidad_meses)
```

## Convenciones Importantes

### Valores Monetarios
- **Internamente**: Centavos (enteros) → 123456 centavos
- **Conversión**: centavos / 100 = pesos ($1.234,56)
- **Frontend**: Acepta pesos, multiplica por 100 antes de enviar
- **Backend**: Recibe centavos, almacena como-es

### Orden de Empleados
- **Alfabético A-Z** por apellido, luego nombre

### Estados de Deudas
- 🔵 **Activa** (azul): saldo > 0
- ⚪ **Pagada** (gris): saldo = 0

### Estados de Pasajes/Retroactivos
- 🔵 **Activo** (azul): aún sin pagar
- 🟢 **Pago** (verde): descuento aplicado

## API Endpoints (Backend)

### Quincenas
- `GET /api/quincenas` — Listar todas
- `GET /api/quincenas/<id>` — Detalle con liquidaciones
- `POST /api/quincenas/<id>/cerrar` — Aplicar deudas/pasajes/retroactivos
- `POST /api/quincenas/<id>/reabrir` — Permitir edición nuevamente
- `POST /api/quincenas/<id>/importar-pdf` — Extraer datos del PDF del banco
- `POST /api/quincenas/<id>/generar-pdfs` — Generar Recibo B + Cinta Billete
- `POST /api/quincenas/<id>/exportar-excel` — Generar XLSX

### Empleados
- `GET /api/empleados` — Listar
- `POST /api/empleados` — Crear
- `PUT /api/empleados/<id>` — Actualizar
- `DELETE /api/empleados/<id>` — Eliminar

### Deudas
- `GET /api/deudas` — Listar todas
- `GET /api/deudas?empleado_id=X` — Filtrar por empleado
- `POST /api/deudas` — Crear
- `PUT /api/deudas/<id>` — Actualizar
- `DELETE /api/deudas/<id>` — Eliminar
- `GET /api/deudas/<id>/pagos` — Historial de pagos

### Pasajes
- `GET /api/pasajes` — Listar
- `GET /api/pasajes?empleado_id=X` — Filtrar
- `POST /api/pasajes` — Crear
- `PUT /api/pasajes/<id>` — Actualizar
- `DELETE /api/pasajes/<id>` — Eliminar

### Retroactivos
- `GET /api/retroactivos` — Listar
- `GET /api/retroactivos?empleado_id=X` — Filtrar
- `POST /api/retroactivos` — Crear
- `PUT /api/retroactivos/<id>` — Actualizar
- `DELETE /api/retroactivos/<id>` — Eliminar

## Problemas Comunes

### Backend no responde (ERR_CONNECTION_REFUSED)
```bash
# Verificar que está corriendo
ps aux | grep "python.*app.py"

# Reiniciar
python backend/app.py
```

### "Failed to fetch" en la página
- Verificar que backend está en `http://localhost:5000`
- Revisar CORS: el backend incluye `@cross_origin()` en todas las rutas

### Base de datos corrupta
```bash
# Eliminar para recrear
rm data/sueldos.db
# Se recreará automáticamente al próximo inicio
```

### Cache del navegador
- Abrir en incógnito: `Ctrl+Shift+N` (Windows) o `Cmd+Shift+N` (Mac)
- O forzar recarga: `Ctrl+F5` (Windows) o `Cmd+Shift+R` (Mac)

## Base de Datos

**SQLite** con 11 tablas (auto-creadas en primer inicio):

| Tabla | Propósito |
|-------|-----------|
| `categorias` | Tipos de empleados (precio/día) |
| `empleados` | Registro de empleados |
| `quincenas` | Períodos de pago (24/año) |
| `liquidaciones` | Nómina por empleado/quincena |
| `deudas` | Deudas de empleados |
| `cuotas_aplicadas` | Historial de pagos de deudas |
| `deudas_postergadas` | Deudas que se saltaron una quincena |
| `pasajes_programados` | Gastos de viaje |
| `retroactivos_programados` | Back-pay distribuidos en quincenas |
| `configuracion` | Ajustes globales |
| `obras` | Proyectos (carpeta con múltiples .db) |

## Despliegue en Producción

Para desplegar en producción (ej: Heroku, AWS, DigitalOcean):

1. **Backend**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
   ```

2. **Frontend**: Servir como archivos estáticos via Nginx o similares

3. **Base de datos**: Migrar a PostgreSQL (cambiar `database.py`)

4. **Variables de entorno**:
   ```bash
   FLASK_ENV=production
   DATABASE_URL=postgresql://...
   ```

## Soporte & Documentación

- **CLAUDE.md**: Documentación técnica detallada para desarrolladores
- **Comentarios en código**: Cada endpoint explica su lógica
- **Ejemplos de API**: Ver `requirements.txt` para versiones exactas de dependencias

## Licencia

Privado - Uso interno solamente

---

**Última actualización**: 2026-04-22  
**Versión**: 1.0  
**Autor**: Ivan (ivarojero@gmail.com)
