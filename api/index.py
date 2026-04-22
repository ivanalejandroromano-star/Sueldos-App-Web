"""
Backend Flask para Vercel - Con búsqueda exhaustiva de BD
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from pathlib import Path
import os
import glob
import traceback

app = Flask(__name__)
CORS(app)

print("[INIT] ===== INICIANDO SERVIDOR =====")
print(f"[INIT] CWD: {os.getcwd()}")
print(f"[INIT] __file__: {__file__}")

# Buscar sueldos.db exhaustivamente
BD_PATH = None
rutas_a_probar = [
    '/var/task/sueldos.db',
    '/var/task/public/sueldos.db',
    os.path.join(os.getcwd(), 'sueldos.db'),
    os.path.join(os.getcwd(), 'public', 'sueldos.db'),
    os.path.join(os.getcwd(), 'data', 'sueldos.db'),
    os.path.dirname(__file__) + '/../sueldos.db',
    os.path.dirname(__file__) + '/../public/sueldos.db',
]

print("[INIT] Buscando sueldos.db...")
for ruta in rutas_a_probar:
    ruta_abs = os.path.abspath(ruta)
    existe = os.path.exists(ruta_abs)
    tamaño = os.path.getsize(ruta_abs) if existe else 0
    print(f"  [{('✓' if existe else '✗')}] {ruta_abs} ({tamaño} bytes)")
    if existe and BD_PATH is None:
        BD_PATH = ruta_abs
        print(f"      ✓✓✓ USANDO ESTA ✓✓✓")

# Búsqueda de emergencia: buscar en todo el sistema de archivos
if not BD_PATH:
    print("[INIT] Búsqueda de emergencia con glob...")
    resultados = glob.glob('/var/task/**/sueldos.db', recursive=True)
    if resultados:
        BD_PATH = resultados[0]
        print(f"  ENCONTRADO: {BD_PATH}")

print(f"[INIT] BD_PATH FINAL: {BD_PATH}")
print("[INIT] ===== FIN INIT =====\n")

def get_connection():
    if not BD_PATH or not os.path.exists(BD_PATH):
        raise Exception(f"sueldos.db no encontrado. Rutas probadas: {rutas_a_probar}")
    
    try:
        conn = sqlite3.connect(BD_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        raise Exception(f"Error abriendo {BD_PATH}: {str(e)}")

# ============== ENDPOINTS ==============

@app.route('/api/debug', methods=['GET'])
def debug():
    return jsonify({
        'status': 'debug',
        'bd_path': BD_PATH,
        'bd_existe': os.path.exists(BD_PATH) if BD_PATH else False,
        'cwd': os.getcwd(),
        'archivos_cwd': os.listdir('.')
    }), 200

@app.route('/api/health', methods=['GET'])
def health():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM empleados")
        count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'empleados': count,
            'database': 'connected'
        }), 200
    except Exception as e:
        print(f"[ERROR] health: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/empleados', methods=['GET'])
def get_empleados():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM empleados ORDER BY apellido, nombre")
        rows = cursor.fetchall()
        conn.close()
        
        empleados = [dict(row) for row in rows]
        return jsonify(empleados), 200
    except Exception as e:
        print(f"[ERROR] empleados: {e}")
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/quincenas', methods=['GET'])
def get_quincenas():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quincenas ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        
        quincenas = [dict(row) for row in rows]
        return jsonify(quincenas), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categorias', methods=['GET'])
def get_categorias():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categorias ORDER BY nombre")
        rows = cursor.fetchall()
        conn.close()
        
        categorias = [dict(row) for row in rows]
        return jsonify(categorias), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/deudas', methods=['GET'])
def get_deudas():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM deudas")
        rows = cursor.fetchall()
        conn.close()
        
        deudas = [dict(row) for row in rows]
        return jsonify(deudas), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/retroactivos', methods=['GET'])
def get_retroactivos():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM retroactivos_programados")
        rows = cursor.fetchall()
        conn.close()
        
        retroactivos = [dict(row) for row in rows]
        return jsonify(retroactivos), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)
