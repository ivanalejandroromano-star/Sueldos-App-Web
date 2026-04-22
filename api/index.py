import sys
from pathlib import Path

# Agregar rutas necesarias
sys.path.insert(0, '/home/ivan/PROYECTOS/Sueldos')

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
from pathlib import Path as PathlibPath

# Importar módulos
try:
    sys.path.insert(0, '/home/ivan/PROYECTOS/Sueldos')
    from sueldos_app.database import (
        init_db, Database, get_obras_disponibles, set_db_path,
        crear_nueva_obra, _get_obras_folder, DATABASE_PATH
    )
    from sueldos_app.calculations import centavos_a_pesos, pesos_a_centavos, calcular_recibo_b
    MODULOS_DISPONIBLES = True
except:
    MODULOS_DISPONIBLES = False
    print("[WARNING] No se pudo importar módulos de Sueldos App")

app = Flask(__name__)
CORS(app)

# Health check
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Backend activo en Vercel'}), 200

# Ruta de fallback para cualquier API que no esté implementada
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_handler(path):
    return jsonify({
        'status': 'ok',
        'message': f'API endpoint: {path}',
        'method': request.method
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'No encontrado'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Error interno del servidor', 'details': str(error)}), 500

if __name__ == '__main__':
    app.run(debug=False)
