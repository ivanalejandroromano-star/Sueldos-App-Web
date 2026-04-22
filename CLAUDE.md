# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Sueldos App Web** is a web-based payroll management system for a construction company. It replicates the exact functionality of the desktop application (CustomTkinter version at `/home/ivan/PROYECTOS/Sueldos/`) but with a modern web interface.

**Purpose**: Automates bi-weekly salary calculations, debt management, PDF generation, and Excel reporting for employee payroll processing.

**Key Feature**: Multi-obra system — each construction project (obra) has an isolated SQLite database.

## Technology Stack

**Frontend**:
- HTML5 + CSS3 (Tailwind CSS 3 via CDN)
- Alpine.js 3.x (reactive SPA, no build step)
- XLSX.js (Excel export)
- Fetch API + FormData (file uploads)

**Backend**:
- Flask 3.0 + Flask-CORS
- SQLite with PRAGMA WAL (prevents locks)
- Python 3.8+
- pdfplumber (PDF data extraction)
- ReportLab (PDF generation)
- openpyxl (Excel generation)

## Project Structure

```
Sueldos App Web/
├── frontend/
│   ├── index.html           # Main SPA (entire app in one file)
│   ├── logo.png             # Company logo
│   └── requirements.txt      # Python dependencies
├── backend/
│   └── app.py              # Flask server (~1000 lines)
├── venv/                    # Python virtual environment
└── data/
    └── sueldos.db          # SQLite database (auto-created if missing)
```

**Critical**: Shared modules are imported from desktop app at `/home/ivan/PROYECTOS/Sueldos/sueldos_app/`:
- `database.py` (CRUD, multi-obra support)
- `calculations.py` (financial formulas)
- `pdf_generator.py` (PDF output)

## Development: Quick Start

### Setup
```bash
cd /home/ivan/PROYECTOS/Sueldos\ App\ Web

# Create virtual environment (one-time)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running Locally

**Terminal 1 — Backend (Flask)**
```bash
cd /home/ivan/PROYECTOS/Sueldos\ App\ Web
source venv/bin/activate
python backend/app.py
# Runs on http://localhost:5000
```

**Terminal 2 — Frontend (HTTP Server)**
```bash
cd /home/ivan/PROYECTOS/Sueldos\ App\ Web/frontend
python3 -m http.server 8000
# Accessible at http://localhost:8000
```

### Clean Cache (Important in WSL)
```bash
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## Critical Conventions

### Monetary Values: Centavos (Integers)
All internal calculations use **centavos** (not pesos or floats):
- **Storage**: 123456 centavos (not 1234.56)
- **Conversion**: `centavos / 100 = pesos`
- **Frontend**: `formatearPesos(centavos)` → "$1.234,56" (es-AR locale)
- **User Input**: Frontend multiplies by 100 before sending to backend

Example flow:
```
User enters: 1500 pesos
Frontend: 1500 * 100 = 150000 centavos → POST to API
Backend: receives 150000, stores as-is
Display: 150000 / 100 = 1500 → "$1.500,00"
```

### Database Location (Multi-Obra)
- **Dev**: `/home/ivan/PROYECTOS/Sueldos App Web/data/sueldos.db`
- **Production**: `obras/<obra_name>.db` (relative to backend)
- **Note**: Database auto-creates if missing; wipes and recreates on schema changes

## Architecture: Frontend (index.html)

**Single-file SPA** (~2500 lines) with Alpine.js data structure:

```javascript
app() {
  return {
    // Global state
    obraActual, vistaActual, quincenaActual
    
    // Data arrays
    empleados[], quincenas[], deudas[], pasajes[], retroactivos[]
    
    // Filtered arrays (for "Por Empleado" tabs)
    deudasFiltradas[], pasajesFiltrados[], retroactivosFiltrados[]
    
    // Form states
    formDeuda{}, formPasaje{}, formRetroactivo{}
    
    // Dialogs & flags
    mostrarDialogoNuevaDeuda, pestaña_deudas ('empleado' | 'todos')
    
    // Methods
    async init()                  // Initialize all data
    async llamarAPI()             // Fetch wrapper with error handling
    async cargarXXX()             // Load global arrays
    async cerrarQuincena()        // Apply debts/pasajes/retroactivos
    formatearPesos()              // Display format
    obtenerPeriodoQuincena()      // ID → period lookup
  }
}
```

**6 Main Views**:
1. **Quincena** (📊) — Fortnightly payroll management
2. **Empleados** (👥) — Employee CRUD
3. **Deudas** (💰) — Debt management (Por Empleado + Todos)
4. **Pasajes** (🚕) — Travel expenses (Por Empleado + Todos)
5. **Retroactivos** (📆) — Back-pay (Por Empleado + Todos)
6. **Historial** (📈) — Past fortnights

## Architecture: Backend (app.py)

Flask server with 30+ endpoints across 5 route groups:

```
/api/obras/*              Multi-obra selection & creation
/api/quincenas/*          Fortnights: list, detail, close, reopen
/api/empleados/*          Employees: CRUD
/api/deudas/*             Debts: CRUD + payment history
/api/pasajes/*            Travel expenses: CRUD
/api/retroactivos/*       Back-pay: CRUD
/api/liquidaciones/*      Individual payroll update
/api/historial/*          Past fortnights
/api/quincenas/<id>/importar-pdf     Bank PDF extraction
/api/quincenas/<id>/generar-pdfs     Recibo B + Cinta Billete
/api/quincenas/<id>/exportar-excel   XLSX export
/api/health               Server status
```

## Key Formulas (All in Centavos)

```
Sueldo Bruto = precio_día_categoría × días_trabajados

Recibo B (cash to deliver) = Sueldo Bruto − (Recibo A − Hab.S/Desc)

Cinta Billete (bundle summary) = Recibo B − Deuda Total + Pasajes + Retroactivos

Deuda por quincena:
  - FIJO: cuota_por_quincena
  - PORCENTAJE: Recibo B × (porcentaje / 100)

Retroactivo cuota (NUEVA ARQUITECTURA - 2026-04-22):
  - cuota = monto_total / cantidad_meses
  - Aplicada en: quincena_inicio, quincena_inicio+1, ..., quincena_inicio+cantidad_meses-1
  - Solo si esa quincena está en el rango

Redondeo Cinta Billete a $500:
  resto = monto % 50000 (50000 centavos = $500)
  if resto > 25000: redondea arriba
  else: redondea abajo
```

## Recent Architectural Changes (2026-04-22)

### Retroactivos Distributed Across Multiple Fortnights (Major Change)

**Problem solved**: Previously, retroactivos (back-pay) were applied as a single lump-sum deduction. This was incorrect.

**New behavior**:
- Retroactivo with `cantidad_meses=4` is paid across 4 consecutive fortnights
- In each closed fortnight, one cuota is subtracted: `cuota = monto_total / cantidad_meses`
- Status changes to "Pago" (green) only when all cuotas are fully paid

**Implementation**:
1. **Backend (`cerrar_quincena()`)**: 
   - Calculates fortnights ordered by period
   - For each retroactivo: checks if current fortnight is within `[quincena_inicio, quincena_inicio + cantidad_meses - 1]`
   - Only subtracts one cuota if true
   
2. **Backend (`get_quincena()`)**: 
   - Calculates `retroactivo_total` for each payroll line dynamically
   - Only includes retroactivos applicable to that fortnight

3. **Frontend**: 
   - Shows "Retroactivos" column with cuota amount (if applicable)
   - Saldo Pendiente decreases by one cuota per closed fortnight
   - Estado changes to "Pago" (green) when `saldo_pendiente = 0`

**Critical SQL**:
- Retroactivos ordered: `SELECT id FROM quincenas ORDER BY periodo ASC`
- Index-based range check: `indice_quincena_actual >= indice_inicio AND quincenas_desde_inicio <= cantidad_meses`

## Sync with Desktop App (CRITICAL)

**Rule**: When fixing bugs or adding features, **always verify against desktop app first**.

**Desktop App Location**: `/home/ivan/PROYECTOS/Sueldos/` (DO NOT MODIFY)

**Process**:
1. Understand exact logic in desktop (read Python files in `sueldos_app/`)
2. Replicate identically in web (same formulas, same order, same colors)
3. Cross-check: vistas, cálculos, orden, colores deben coincidir exactamente

**Key Files to Reference**:
- `sueldos_app/database.py` — CRUD logic
- `sueldos_app/calculations.py` — All financial formulas
- `sueldos_app/pdf_generator.py` — PDF generation
- `sueldos_app/ui/quincena_view.py` — Payroll view logic
- `sueldos_app/ui/deudas_view.py` — Debt logic

## Common Workflows

### Closing a Fortnight (Cierre de Quincena)

**Frontend Trigger**: Button "✓ Cerrar Quincena" in Quincena view

**Backend Flow** (`POST /api/quincenas/<id>/cerrar`):
1. For each employee's debt:
   - Check if `quincena_inicio_id <= actual`
   - Check if NOT postponed
   - Calculate cuota (FIJO or PORCENTAJE)
   - Create/update `cuotas_aplicadas` record
   - Recalculate: `nuevo_saldo = monto_total - SUM(all_cuotas_aplicadas)` (dynamic, not cumulative)
   - If `nuevo_saldo <= 0`: mark debt `activo = 0` (Pagada)

2. For each fortnight's pasajes:
   - Only mark `activo = 0` if `quincena_pago_id == actual_quincena`

3. For each retroactivo in range:
   - Check if `quincena_inicio <= actual <= quincena_inicio + cantidad_meses - 1`
   - Subtract one cuota
   - If `nuevo_saldo <= 0`: mark `activo = 0` (Pago)

4. Mark fortnight `cerrada = 1`

**Frontend Refresh**: Reloads deudas, pasajes, retroactivos arrays

### Creating a Retroactivo

1. Select employee
2. Input monto_total, cantidad_meses, quincena_inicio_id
3. Backend stores with `saldo_pendiente = monto_total` (full amount initially)
4. On each fortnight close in range: `saldo_pendiente -= (monto_total / cantidad_meses)`

### Viewing Data in "Todos los Empleados"

- **Deudas**: Aggregated per employee (Monto Total, Ya Pagado, Saldo)
- **Pasajes**: Individual rows (Empleado, Fecha Viaje, Fecha Pago, Monto, Estado)
- **Retroactivos**: Aggregated per employee (Meses, Quincena Inicio, Activos count)

## Database Schema

**11 Tables** (auto-created by `database.py`):

```sql
categorias              (id, nombre, precio_dia, vigente_desde, vigente_hasta)
empleados               (id, legajo, nombre, apellido, cuil, categoria_id, fecha_alta, fecha_baja)
quincenas               (id, periodo, fecha_inicio, fecha_fin, cerrada)
liquidaciones           (id, quincena_id, empleado_id, dias_trabajados, sueldo_bruto, recibo_a, hab_s_desc, recibo_b, cinta_billete)
deudas                  (id, empleado_id, motivo, monto_total, cuota_por_quincena, saldo_pendiente, activa, tipo_cobro, porcentaje_variable, quincena_inicio_id, fecha_alta)
cuotas_aplicadas        (id, deuda_id, liquidacion_id, monto_aplicado, fecha_aplicacion) [audit trail]
deudas_postergadas      (id, deuda_id, quincena_id, fecha_postergacion)
pasajes_programados     (id, empleado_id, monto, fecha_pago, fecha_viaje, quincena_pago_id, activo, fecha_creacion)
retroactivos_programados (id, empleado_id, monto_total, cantidad_meses, monto_por_mes, saldo_pendiente, activo, quincena_inicio_id, fecha_creacion)
configuracion           (clave, valor)
obras                   (carpeta con múltiples .db files)
```

## Known Issues & Limitations

### Fixed (Session 2026-04-22)

- ✅ Double multiplication of pasajes/retroactivos montos (backend was multiplying by 100 twice)
- ✅ Logo not displaying (path was wrong, fixed to `logo.png` in frontend folder)
- ✅ Retroactivos saldo_pendiente not updating (now correctly subtracts one cuota per closed fortnight)
- ✅ Retroactivos "Quincena Inicio" not showing in "Todos los Empleados" view (fixed with `obtenerPeriodoQuincena()`)

### Outstanding

- **Retroactivo display in Quincena**: "Retroactivos" column now shows correct cuota for applicable fortnights
- **State transitions**: Retroactivo Estado correctly changes "Activo" → "Pago" when all cuotas paid

## Testing Workflow

### Manual End-to-End Test: Retroactivos

1. Create Retroactivo: monto_total=4000, cantidad_meses=4, quincena_inicio=May-1Q
2. Close May-1Q → saldo = 3000, Estado = "Activo"
3. Close May-2Q → saldo = 2000, Estado = "Activo"
4. Close Jun-1Q → saldo = 1000, Estado = "Activo"
5. Close Jun-2Q → saldo = 0, Estado = "Pago" (green)

**Verify**:
- Retroactivos column shows 1000 in each of 4 fortnights
- Saldo Pend. decreases correctly
- Estado changes only on final close

## Debugging Tips

### Backend Logs
- Check `/tmp/backend.log` for Flask debug output
- `[DEBUG]` lines show retroactivo calculations during fortnight close
- `[ERROR]` lines indicate exceptions (database, API)

### Frontend Issues
- Use browser DevTools Console (F12) for Alpine.js state inspection
- Network tab shows API requests/responses (centavos)
- Check CORS errors if backend is unavailable

### Database Issues
- Delete `data/sueldos.db` to force recreation with current schema
- WAL mode enabled: check for `.db-wal` and `.db-shm` files

## Version History

| Date | Change |
|------|--------|
| 2026-04-21 | Project initialized; Phase 1 dialogs completed |
| 2026-04-22 | Retroactivos architectural change (multi-fortnight distribution) |
| 2026-04-22 | Pasaje/Retroactivo double-multiplication bug fixed |
| 2026-04-22 | Logo integration, "Ya Pagado" column added to deudas |

