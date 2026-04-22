"""
Backend Flask para Vercel - Versión Debug
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from pathlib import Path
import os
import traceback

app = Flask(__name__)
CORS(app)

print("[INIT] Iniciando servidor...")
print(f"[INIT] CWD: {os.getcwd()}")
print(f"[INIT] Archivos en directorio actual:")
for item in os.listdir('.'):
    print(f"  - {item}")

# Encontrar sueldos.db
BD_PATH = None
rutas_a_probar = [
    Path('./sueldos.db'),
    Path('./data/sueldos.db'),
    Path('./public/sueldos.db'),
    Path('/tmp/sueldos.db'),
    Path('/var/task/sueldos.db'),
]

print("[DEBUG] Buscando sueldos.db...")
for ruta in rutas_a_probar:
    ruta_abs = ruta.resolve()
    existe = ruta.exists()
    tamaño = ruta.stat().st_size if existe else 0
    print(f"  {ruta_abs}: {'✓ ENCONTRADO' if existe else '✗ no existe'} ({tamaño} bytes)")
    if existe and BD_PATH is None:
        BD_PATH = str(ruta)
        print(f"  → Usando: {BD_PATH}")

if not BD_PATH:
    print("[ERROR] NO SE ENCONTRÓ SUELDOS.DB EN NINGUNA UBICACIÓN")

def get_connection():
    if not BD_PATH:
        raise Exception("sueldos.db no encontrado en ninguna ubicación")
    try:
        conn = sqlite3.connect(BD_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        raise Exception(f"Error conectando a {BD_PATH}: {str(e)}")

# ============== ENDPOINTS ==============

@app.route('/api/debug', methods=['GET'])
def debug():
    """Endpoint para debuggear"""
    return jsonify({
        'status': 'debug mode',
        'cwd': os.getcwd(),
        'bd_path': BD_PATH,
        'bd_existe': Path(BD_PATH).exists() if BD_PATH else False,
        'archivos': os.listdir('.')
    }), 200

@app.route('/api/health', methods=['GET'])
def health():
    try:
        if not BD_PATH:
            return jsonify({'status': 'error', 'message': 'BD no encontrada'}), 500
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM empleados")
        count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'empleados': count,
            'db_path': BD_PATH
        }), 200
    except Exception as e:
        print(f"[ERROR] health: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

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
        print(f"[ERROR] empleados: {str(e)}")
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
        print(f"[ERROR] quincenas: {str(e)}")
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
        print(f"[ERROR] categorias: {str(e)}")
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
        print(f"[ERROR] deudas: {str(e)}")
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
        print(f"[ERROR] retroactivos: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(500)
def error_500(e):
    return jsonify({'error': 'Error interno', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
