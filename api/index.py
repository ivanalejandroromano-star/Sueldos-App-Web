"""
Backend Flask para Vercel - con inicialización de BD desde base64
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import base64
import os
import traceback

app = Flask(__name__)
CORS(app)

# ========== INICIALIZAR BD ==========
def init_database():
    """Descodifica sueldos.db desde base64 si es necesario"""
    db_path = '/var/task/sueldos.db'
    b64_path = '/var/task/sueldos.db.b64'
    
    print(f"[INIT] Buscando BD en {db_path}")
    
    # Si existe base64, descodificar
    if os.path.exists(b64_path):
        print(f"[INIT] Encontrado base64, descodificando...")
        try:
            with open(b64_path, 'r') as f:
                b64_content = f.read()
            
            db_bytes = base64.b64decode(b64_content)
            
            with open(db_path, 'wb') as f:
                f.write(db_bytes)
            
            print(f"[INIT] BD recreada: {len(db_bytes)} bytes")
            return db_path
        except Exception as e:
            print(f"[ERROR] Descodificación fallida: {e}")
    
    # Si el archivo binario existe, usarlo
    if os.path.exists(db_path):
        print(f"[INIT] BD encontrada en {db_path}")
        return db_path
    
    print(f"[ERROR] No se encontró BD en ninguna ubicación")
    return None

BD_PATH = init_database()

def get_connection():
    """Abre conexión a SQLite"""
    if not BD_PATH or not os.path.exists(BD_PATH):
        raise Exception(f"BD no encontrada")
    
    try:
        conn = sqlite3.connect(BD_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        raise Exception(f"Error conectando a BD: {str(e)}")

# ============== ENDPOINTS ==============

@app.route('/api/debug', methods=['GET'])
def debug():
    info = {
        'status': 'debug',
        'bd_path': BD_PATH,
        'bd_existe': os.path.exists(BD_PATH) if BD_PATH else False,
    }
    
    if BD_PATH and os.path.exists(BD_PATH):
        info['tamaño'] = os.path.getsize(BD_PATH)
    
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
