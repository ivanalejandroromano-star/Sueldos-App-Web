"""
Backend Flask para Vercel
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from pathlib import Path
import os
import traceback

app = Flask(__name__)
CORS(app)

# Usar ruta absoluta en Vercel
BD_PATH = '/var/task/sueldos.db'

print(f"[INIT] BD_PATH: {BD_PATH}")
print(f"[INIT] Existe: {Path(BD_PATH).exists()}")
print(f"[INIT] CWD: {os.getcwd()}")

def get_connection():
    """Abre conexión a SQLite"""
    try:
        conn = sqlite3.connect(BD_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        raise Exception(f"No se pudo conectar a {BD_PATH}: {str(e)}")

# ============== ENDPOINTS ==============

@app.route('/api/debug', methods=['GET'])
def debug():
    return jsonify({
        'status': 'debug',
        'bd_path': BD_PATH,
        'bd_existe': Path(BD_PATH).exists(),
        'cwd': os.getcwd()
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
        return jsonify({'error': str(e)}), 500

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

@app.errorhandler(500)
def error_500(e):
    return jsonify({'error': 'Error interno'}), 500

if __name__ == '__main__':
    app.run(debug=False)
