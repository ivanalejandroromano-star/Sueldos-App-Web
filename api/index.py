"""
Backend Flask para Vercel
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from pathlib import Path
import os
import stat
import traceback

app = Flask(__name__)
CORS(app)

BD_PATH = '/var/task/sueldos.db'

print(f"[INIT] BD_PATH: {BD_PATH}")
print(f"[INIT] Existe: {os.path.exists(BD_PATH)}")

# Verificar permisos y tamaño
if os.path.exists(BD_PATH):
    stat_info = os.stat(BD_PATH)
    print(f"[INIT] Tamaño: {stat_info.st_size} bytes")
    print(f"[INIT] Permisos: {oct(stat_info.st_mode)}")
    print(f"[INIT] Legible: {os.access(BD_PATH, os.R_OK)}")

def get_connection():
    """Abre conexión a SQLite"""
    if not os.path.exists(BD_PATH):
        raise Exception(f"Archivo no existe: {BD_PATH}")
    
    if not os.access(BD_PATH, os.R_OK):
        raise Exception(f"No hay permiso de lectura: {BD_PATH}")
    
    try:
        # Intentar abrir con check_same_thread=False
        conn = sqlite3.connect(f'file:{BD_PATH}?mode=ro', uri=True, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        # Si falla con URI, intentar de forma normal
        try:
            conn = sqlite3.connect(BD_PATH, timeout=10.0)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e2:
            raise Exception(f"Error SQLite: {str(e2)}")

# ============== ENDPOINTS ==============

@app.route('/api/debug', methods=['GET'])
def debug():
    info = {
        'status': 'debug',
        'bd_path': BD_PATH,
        'bd_existe': os.path.exists(BD_PATH),
        'cwd': os.getcwd(),
    }
    
    if os.path.exists(BD_PATH):
        stat_info = os.stat(BD_PATH)
        info['tamaño'] = stat_info.st_size
        info['legible'] = os.access(BD_PATH, os.R_OK)
        info['permisos'] = oct(stat_info.st_mode)
    
    return jsonify(info), 200

@app.route('/api/health', methods=['GET'])
def health():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM empleados")
        count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({'status': 'ok', 'empleados': count}), 200
    except Exception as e:
        print(f"[ERROR] health: {e}")
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

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
        return jsonify({'error': str(e)}), 500

@app.route('/api/quincenas', methods=['GET'])
def get_quincenas():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quincenas ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return jsonify([dict(row) for row in rows]), 200
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
        return jsonify([dict(row) for row in rows]), 200
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
        return jsonify([dict(row) for row in rows]), 200
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
        return jsonify([dict(row) for row in rows]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)
