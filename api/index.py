"""Flask backend para Vercel - BD embebida como base64"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import base64
import os

app = Flask(__name__)
CORS(app)

# Importar la constante DB_B64 del módulo
from db_embedded import DB_B64

def get_db_path():
    """Descodifica BD desde base64 y guarda en /tmp"""
    db_path = '/tmp/sueldos.db'
    if not os.path.exists(db_path):
        db_bytes = base64.b64decode(DB_B64)
        with open(db_path, 'wb') as f:
            f.write(db_bytes)
    return db_path

def get_connection():
    """Abre conexión a SQLite"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

# ============== ENDPOINTS ==============

@app.route('/api/debug', methods=['GET'])
def debug():
    try:
        db_path = get_db_path()
        info = {
            'status': 'ok',
            'bd_path': db_path,
            'bd_existe': os.path.exists(db_path),
            'tamaño': os.path.getsize(db_path) if os.path.exists(db_path) else 0
        }
        return jsonify(info), 200
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

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
        return jsonify({'error': str(e)}), 500

@app.route('/api/empleados', methods=['GET'])
def get_empleados():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM empleados ORDER BY apellido, nombre")
        rows = cursor.fetchall()
        conn.close()
        return jsonify([dict(row) for row in rows]), 200
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
