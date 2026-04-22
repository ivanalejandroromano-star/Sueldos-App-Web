# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Sueldos App Web** is a web-based payroll management system for a construction company. It automates bi-weekly salary calculations, debt management, and expense tracking for employee payroll processing.

**Purpose**: Cloud-hosted alternative to the desktop application. Users access the app from any device without needing a server running on their PC.

**Current State**: Deployed on Vercel with fully functional CRUD operations, real-time data persistence, and multi-obra support.

**Live URL**: https://sueldos-app-web.vercel.app/

## Technology Stack

**Frontend**:
- HTML5 + CSS3 (Tailwind CSS 3 via CDN)
- Alpine.js 3.x (reactive SPA, no build step)
- Single-file application (~2500 lines in `public/index.html`)

**Backend**:
- Flask 3.0 + Flask-CORS
- SQLite with PRAGMA WAL (prevents locks)
- Deployed on Vercel as serverless functions (`api/index.py`)
- Database embedded as base64 in code (120KB) and decoded at runtime

## Repository Structure

```
Github/
├── public/
│   ├── index.html          # Main SPA frontend (2500 lines)
│   └── logo.png            # Company logo
├── api/
│   ├── index.py            # Flask backend (500+ lines, all endpoints)
│   └── db_embedded.py       # Compact: base64 DB + get_db_path()
├── vercel.json             # Vercel build & routing configuration
├── requirements.txt        # Flask, Flask-CORS, python-dotenv
└── CLAUDE.md               # This file
```

## Architecture: Vercel Serverless

### How It Works

1. **User visits** https://sueldos-app-web.vercel.app/
   - Vercel serves `public/index.html`

2. **Frontend calls** `/api/empleados` (or other endpoints)
   - Vercel routes to `api/index.py` (serverless function)

3. **Database access**:
   - Base64 string in `api/db_embedded.py` is decoded
   - `get_db_path()` writes to `/tmp/sueldos.db` (once per runtime)
   - Flask queries SQLite
   - **WAL mode + 30s timeout** = no database locks

4. **Response** = JSON back to frontend, Alpine.js updates

### Key Code Details

**Database initialization** (`api/index.py`):
```python
_DB_B64 = "U1FMaXRlIGZvcm1hdCAz..."  # 120KB base64
_db_init_lock = False

def get_db_path():
    global _db_init_lock
    db_path = '/tmp/sueldos.db'
    
    # Synchronize if multiple requests arrive simultaneously
    while _db_init_lock:
        time.sleep(0.1)
    
    if not os.path.exists(db_path):
        _db_init_lock = True
        db_bytes = base64.b64decode(_DB_B64)
        with open(db_path, 'wb') as f:
            f.write(db_bytes)
        _db_init_lock = False
    
    return db_path

def get_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn
```

**Why WAL + 30s timeout?**
- Vercel = multiple concurrent requests to same SQLite database
- WAL (Write-Ahead Logging) allows reads during writes
- 30s timeout prevents "database is locked" errors
- `/tmp` is writable in Vercel's runtime environment

## API Endpoints

All defined in `api/index.py`:

**Employees**:
- `GET /api/empleados` — List with categoria_nombre, precio_dia
- `POST /api/empleados` — Create
- `PUT /api/empleados/<id>` — Update
- `DELETE /api/empleados/<id>` — Delete

**Fortnights**:
- `GET /api/quincenas` — List all
- `GET /api/quincenas/<id>` — Detail + liquidaciones + employee data

**Payroll Rows**:
- `PUT /api/liquidaciones/<id>` — Update dias_trabajados, sueldo_bruto, etc.

**Debts**:
- `GET /api/deudas`
- `POST /api/deudas` — Create
- `PUT /api/deudas/<id>` — Update
- `DELETE /api/deudas/<id>` — Delete

**Travel Expenses**:
- `GET /api/pasajes`
- `POST /api/pasajes` — Create
- `PUT /api/pasajes/<id>` — Update
- `DELETE /api/pasajes/<id>` — Delete

**Back-pay**:
- `GET /api/retroactivos`
- `POST /api/retroactivos` — Create
- `PUT /api/retroactivos/<id>` — Update
- `DELETE /api/retroactivos/<id>` — Delete

**Categories**:
- `GET /api/categorias`
- `POST /api/categorias` — Create

**Health**:
- `GET /api/health` — Returns `{"status": "ok", "empleados": N}`

## Database Schema

11 tables (embedded in base64, decoded at runtime):

```sql
categorias              -- nombres, precios_dia
empleados               -- linked to categorias
quincenas               -- 1Q/2Q per month, cerrada flag
liquidaciones           -- rows per quincena×empleado
deudas                  -- debts with saldo_pendiente
cuotas_aplicadas        -- audit trail for debt payments
deudas_postergadas      -- postponed debts
pasajes_programados     -- travel expenses
retroactivos_programados-- back-pay (distributed across months)
configuracion           -- key-value settings
```

**Key Relationships**:
- empleados.categoria_id → categorias.id
- liquidaciones.quincena_id → quincenas.id
- liquidaciones.empleado_id → empleados.id

## Key Conventions

### Monetary Values: Centavos (Integers)

All calculations use centavos, not pesos:
- Database stores: 123456 = $1.234,56
- Frontend sends: centavos (user input × 100)
- API returns: centavos
- Display: `formatearPesos(centavos)` → "$1.234,56" (es-AR locale)

Example:
```
User enters: 1500
Frontend: 1500 * 100 = 150000 centavos
POST /api/liquidaciones/38 {"sueldo_bruto": 150000}
Backend stores 150000, returns same
Frontend displays: 150000 / 100 = "$1.500,00"
```

### Frontend: Single Alpine.js App

State object:
```javascript
{
  empleados: [],        // All with categoria_nombre
  quincenas: [],        // All with cerrada flag
  deudas: [],
  pasajes: [],
  retroactivos: [],
  quincenaActual: null,
  
  // Methods
  async cargarEmpleados()
  async guardarEmpleado(data)
  async cargarQuincena(id)
  async updateLiquidacion(id, data)
}
```

6 main tabs: Quincena, Empleados, Deudas, Pasajes, Retroactivos, Historial

## Deployment & Updates

### Push Changes to Vercel

All changes go through GitHub:

1. **Edit files** (`api/index.py`, `public/index.html`, etc.)
2. **Git commit & push**:
   ```bash
   git add .
   git commit -m "Description of change"
   git push
   ```
3. **Vercel rebuilds automatically** (~5-10 seconds)
4. **Test** at https://sueldos-app-web.vercel.app/

### Update Embedded Database

The database is base64-encoded in `api/db_embedded.py`:

1. **Get latest DB** from desktop app:
   ```bash
   cp /home/ivan/PROYECTOS/Sueldos/sueldos_app/data/obras/Tandil.db /tmp/new.db
   ```

2. **Encode to base64**:
   ```bash
   base64 /tmp/new.db > /tmp/db.b64
   ```

3. **Update db_embedded.py**:
   - Copy content of `/tmp/db.b64`
   - Paste as value of `DB_B64 = "..."` (single line, no newlines)

4. **Commit & push**:
   ```bash
   git add api/db_embedded.py
   git commit -m "Update database"
   git push
   ```

### Local Testing (Optional)

**Local backend**:
```bash
cd /home/ivan/PROYECTOS/Sueldos\ App\ Web
source venv/bin/activate
pip install -r requirements.txt
python backend/app.py  # Runs on http://localhost:5000
```

**Local frontend**:
```bash
cd /home/ivan/PROYECTOS/Sueldos\ App\ Web/frontend
python3 -m http.server 8000  # Runs on http://localhost:8000
```

But **GitHub is the source of truth** — Vercel only deploys from GitHub.

## Troubleshooting

### "database is locked"
- Vercel is experiencing concurrent database access
- WAL mode + 30s timeout should handle this
- If persistent: increase timeout in `get_connection()`, rebuild

### API returns 500 error
- Check browser Network tab for error details
- Common: missing required field in POST/PUT payload
- Solution: Verify request JSON matches schema (all fields required)

### Frontend shows "undefined" for all data
- `/api/health` returning error? (Check browser Network tab)
- If 404: endpoint doesn't exist, add it to `api/index.py`
- If 500: database error, check endpoint code

### Changes not appearing after push
- Vercel deployment takes 5-10 seconds
- Hard refresh browser: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
- Check Vercel dashboard for deploy errors

## Version History

| Date | Version | Change |
|------|---------|--------|
| 2026-04-22 | 1.0 | Initial Vercel deployment (Flask serverless) |
| 2026-04-22 | 1.1 | Database embedded as base64 in code |
| 2026-04-22 | 1.2 | All CRUD endpoints (POST/PUT/DELETE) implemented |
| 2026-04-22 | 1.3 | Fixed database locking: WAL mode + 30s timeout |
| 2026-04-22 | 1.4 | Frontend includes categoria_nombre, precio_dia |

## Critical Notes for Future Work

1. **Database is immutable in code** — To change it, re-encode from `/tmp/new.db` and update `api/db_embedded.py`
2. **WAL mode is essential** — Do not remove `PRAGMA journal_mode=WAL` from `get_connection()`
3. **Timeout prevents locks** — Increasing from 30s is safe; decreasing will cause "database is locked" errors
4. **No authentication** — App assumes single user or trusted network; add Auth0/JWT if needed
5. **Vercel `/tmp` is ephemeral** — Data written to `/tmp/sueldos.db` survives only during serverless function runtime; database updates must be committed back to `api/db_embedded.py`
