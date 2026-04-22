"""
Backend Flask simplificado para Vercel
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from pathlib import Path
import traceback

app = Flask(__name__)
CORS(app)

# Encontrar sueldos.db
def encontrar_bd():
    rutas = [
        Path('./sueldos.db'),
        Path('./data/sueldos.db'),
        Path('./public/sueldos.db'),
        Path('/tmp/sueldos.db'),
    ]

    for ruta in rutas:
        if ruta.exists():
            print(f"[DEBUG] BD encontrada: {ruta}")
            return str(ruta)

    print("[ERROR] No se encontró sueldos.db")
    return None

BD_PATH = encontrar_bd()

def get_connection():
    if not BD_PATH:
        raise Exception("Base de datos no encontrada")
    conn = sqlite3.connect(BD_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/health', methods=['GET'])
def health():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM empleados")
        count = cursor.fetchone()[0]
        conn.close()
        return jsonify({'status': 'ok', 'empleados': count, 'db_path': BD_PATH}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

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
        cursor.execute("SELECT * FROM deudas ORDER BY id DESC")
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
        cursor.execute("SELECT * FROM retroactivos_programados ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        
        retroactivos = [dict(row) for row in rows]
        return jsonify(retroactivos), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'No encontrado'}), 404

if __name__ == '__main__':
    app.run(debug=False)
