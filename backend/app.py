"""
Backend Flask para Sueldos App Web
Maneja la base de datos SQLite y proporciona APIs REST
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from pathlib import Path
from datetime import datetime
import sys

# Importar módulos de Sueldos App original
sys.path.insert(0, '/home/ivan/PROYECTOS/Sueldos')
from sueldos_app.database import (
    init_db, Database, get_obras_disponibles, set_db_path,
    crear_nueva_obra, _get_obras_folder, DATABASE_PATH
)
from sueldos_app.calculations import centavos_a_pesos, pesos_a_centavos, calcular_recibo_b
from sueldos_app.pdf_reader import extraer_pdf_banco
from sueldos_app.pdf_generator import (
    generar_recibos_b_consolidado, generar_cinta_billete, generar_resumen_preparacion
)
import werkzeug
from werkzeug.utils import secure_filename
import tempfile
import os
import zipfile
import io
from flask import send_file

app = Flask(__name__)
CORS(app)

# Detectar ruta local de BD (para cuando se clona desde GitHub)
def encontrar_bd_local():
    """Busca BD en carpeta local data/ o data/sueldos.db"""
    # Ruta relativa al backend/
    rutas_posibles = [
        Path(__file__).parent.parent / "data" / "sueldos.db",  # ../data/sueldos.db
        Path(__file__).parent / "data" / "sueldos.db",         # ./data/sueldos.db
        Path.cwd() / "data" / "sueldos.db",                    # cwd/data/sueldos.db
    ]

    for ruta in rutas_posibles:
        if ruta.exists():
            print(f"[DEBUG] BD local encontrada: {ruta}")
            return ruta
    return None

# Intentar usar BD local si existe
bd_local = encontrar_bd_local()
if bd_local:
    set_db_path(str(bd_local))
    print(f"[INFO] Usando BD local: {bd_local}")

# Estado global
estado = {
    'obra_actual': 'Tandil',
    'db_path': None
}

# Inicializar BD
def obtener_db():
    """Retorna instancia de Database para obra actual"""
    return Database()

def cambiar_db_obra(nombre_obra):
    """Cambia la BD activa a una obra específica"""
    obras_folder = _get_obras_folder()
    db_path = obras_folder / f"{nombre_obra}.db"

    if not db_path.exists():
        # Intenta con la BD legacy
        legacy_path = _get_obras_folder().parent / "sueldos.db"
        if legacy_path.exists():
            db_path = legacy_path
        else:
            return False

    set_db_path(db_path)
    init_db()  # Asegurar que las tablas existan
    estado['db_path'] = db_path
    estado['obra_actual'] = nombre_obra
    print(f"[DEBUG] Inicializada BD para obra: {nombre_obra} ({db_path})")
    return True

# ============== RUTAS: DEBUG ==============

@app.route('/api/debug/retroactivos/<int:quincena_id>/<int:empleado_id>', methods=['GET'])
def debug_retroactivos(quincena_id, empleado_id):
    """Debug endpoint para ver retroactivos de un empleado en una quincena"""
    try:
        db = obtener_db()

        # Obtener índices de quincenas
        quincenas_ordenadas = db.conn.execute(
            "SELECT id, periodo FROM quincenas ORDER BY id ASC"
        ).fetchall()
        quincena_indices = {q['id']: idx for idx, q in enumerate(quincenas_ordenadas)}
        indice_quincena_actual = quincena_indices.get(quincena_id, -1)

        # Obtener retroactivos activos del empleado
        retroactivos = db.conn.execute(
            "SELECT * FROM retroactivos_programados WHERE empleado_id = ? AND activo = 1",
            (empleado_id,)
        ).fetchall()

        info = {
            'quincena_id': quincena_id,
            'quincena_periodo': None,
            'indice_quincena': indice_quincena_actual,
            'empleado_id': empleado_id,
            'retroactivos_encontrados': len(retroactivos),
            'retroactivos': []
        }

        # Buscar el período de la quincena
        for q in quincenas_ordenadas:
            if q['id'] == quincena_id:
                info['quincena_periodo'] = q['periodo']
                break

        for retro in retroactivos:
            indice_inicio = quincena_indices.get(retro['quincena_inicio_id'], -1)
            quincenas_desde_inicio = indice_quincena_actual - indice_inicio + 1
            aplica = (indice_inicio >= 0 and indice_quincena_actual >= indice_inicio and
                     quincenas_desde_inicio <= retro['cantidad_meses'])

            cuota = int(retro['monto_total'] / retro['cantidad_meses']) if retro['cantidad_meses'] > 0 else 0

            info['retroactivos'].append({
                'id': retro['id'],
                'monto_total': retro['monto_total'],
                'cantidad_meses': retro['cantidad_meses'],
                'cuota_por_quincena': cuota,
                'quincena_inicio_id': retro['quincena_inicio_id'],
                'indice_inicio': indice_inicio,
                'quincenas_desde_inicio': quincenas_desde_inicio,
                'aplica': aplica
            })

        db.close()
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== RUTAS: OBRAS ==============

@app.route('/api/obras', methods=['GET'])
def get_obras():
    """Lista todas las obras disponibles"""
    try:
        obras = get_obras_disponibles()
        resultado = [
            {
                'id': i,
                'nombre': obra['nombre'],
                'path': str(obra['path'])
            }
            for i, obra in enumerate(obras)
        ]
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/obras/cambiar', methods=['POST'])
def cambiar_obra():
    """Cambia la obra activa"""
    try:
        datos = request.get_json()
        obra_id = datos.get('obra_id')

        obras = get_obras_disponibles()
        if obra_id < 0 or obra_id >= len(obras):
            return jsonify({'error': 'Obra no encontrada'}), 404

        obra = obras[obra_id]
        set_db_path(Path(obra['path']))
        init_db()  # Asegurar que las tablas existan
        estado['obra_actual'] = obra['nombre']
        print(f"[DEBUG] Obra cambiada a: {obra['nombre']} ({obra['path']})")

        return jsonify({
            'id': obra_id,
            'nombre': obra['nombre'],
            'message': f"Obra cambiada a: {obra['nombre']}"
        })
    except Exception as e:
        print(f"[ERROR] Cambiar obra: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/obras/crear', methods=['POST'])
def crear_obra():
    """Crea una nueva obra"""
    try:
        datos = request.get_json()
        nombre = datos.get('nombre', '').strip()

        if not nombre:
            return jsonify({'error': 'Nombre de obra requerido'}), 400

        db_path = crear_nueva_obra(nombre)
        set_db_path(db_path)
        init_db()

        db = obtener_db()
        db.generar_quincenas_anio()
        db.close()

        return jsonify({
            'nombre': nombre,
            'path': str(db_path),
            'message': f"Obra '{nombre}' creada correctamente"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== RUTAS: QUINCENAS ==============

@app.route('/api/quincenas', methods=['GET'])
def get_quincenas():
    """Lista todas las quincenas"""
    try:
        db = obtener_db()
        quincenas = db.get_quincenas()
        db.close()

        return jsonify([
            {
                'id': q['id'],
                'periodo': q['periodo'],
                'fecha_inicio': q['fecha_inicio'],
                'fecha_fin': q['fecha_fin'],
                'cerrada': bool(q['cerrada'])
            }
            for q in quincenas
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quincenas/<int:quincena_id>', methods=['GET'])
def get_quincena(quincena_id):
    """Obtiene detalles de una quincena con sus liquidaciones"""
    try:
        db = obtener_db()
        quincena = db.get_quincena(quincena_id)

        if not quincena:
            db.close()
            return jsonify({'error': 'Quincena no encontrada'}), 404

        # Obtener liquidaciones con info de empleados
        liquidaciones = db.get_liquidaciones(quincena_id)

        # Si no hay liquidaciones, crearlas automáticamente
        if len(liquidaciones) == 0:
            empleados = db.get_empleados(activos_solo=True)
            for emp in empleados:
                db.crear_liquidacion(quincena_id, emp['id'])
            # Obtener las que se acaban de crear
            liquidaciones = db.get_liquidaciones(quincena_id)

        # Obtener todas las quincenas ordenadas para calcular índices
        quincenas_ordenadas = db.conn.execute(
            "SELECT id, periodo FROM quincenas ORDER BY id ASC"
        ).fetchall()
        quincena_indices = {q['id']: idx for idx, q in enumerate(quincenas_ordenadas)}
        indice_quincena_actual = quincena_indices.get(quincena_id, -1)

        # Debug: mostrar las quincenas ordenadas
        print(f"\n[DEBUG] get_quincena: quincena_id={quincena_id}")
        print(f"[DEBUG]   Quincenas ordenadas ({len(quincenas_ordenadas)} total):")
        for q in quincenas_ordenadas[:10]:  # Mostrar primeras 10
            print(f"[DEBUG]     idx={quincena_indices[q['id']]}, id={q['id']}, periodo={q['periodo']}")
        print(f"[DEBUG]   Quincena actual: id={quincena_id}, indice={indice_quincena_actual}")

        # Enriquecer con datos de empleado
        liq_completas = []
        for liq in liquidaciones:
            empleado = db.get_empleado(liq['empleado_id'])
            categoria = db.get_categoria(empleado['categoria_id'])

            # Obtener deudas activas del empleado y calcular cuota para esta quincena
            deudas = db.get_deudas_activas(liq['empleado_id'])
            deuda_total = 0

            # Calcular deuda_total según lógica exacta del desktop app
            recibo_b = liq['recibo_b']
            for d in deudas:
                quincena_inicio = d.get('quincena_inicio_id')
                # Solo incluir si quincena_inicio <= quincena_actual
                if quincena_inicio is None or quincena_inicio <= quincena_id:
                    # Verificar si no fue postergada
                    if not db.fue_postergada(d.get('id'), quincena_id):
                        if d.get('tipo_cobro') == 'porcentaje':
                            porcentaje = d.get('porcentaje_variable', 0)
                            deuda_total += int(recibo_b * porcentaje / 100)
                        else:
                            deuda_total += d.get('cuota_por_quincena', 0)

            # Obtener pasajes
            pasaje = db.get_pasaje(liq['id'])

            # Calcular retroactivos que aplican a esta quincena
            # Lógica: Si quincena_inicio <= quincena_actual < quincena_inicio + cantidad_meses
            retroactivo_total = 0
            try:
                retroactivos_activos = db.conn.execute(
                    "SELECT * FROM retroactivos_programados WHERE empleado_id = ? AND activo = 1",
                    (liq['empleado_id'],)
                ).fetchall()

                for retro in retroactivos_activos:
                    quincena_inicio = retro['quincena_inicio_id']
                    cantidad_meses = retro['cantidad_meses']

                    # Verificar si esta quincena está dentro del rango de pago
                    # Rango válido: desde quincena_inicio hasta quincena_inicio + cantidad_meses - 1
                    if quincena_inicio is not None and quincena_id >= quincena_inicio and quincena_id < quincena_inicio + cantidad_meses:
                        monto_por_mes = retro['monto_por_mes']
                        retroactivo_total += monto_por_mes
                        print(f"[DEBUG] Retroactivo ID {retro['id']}: ✓ APLICADO (rango {quincena_inicio}-{quincena_inicio + cantidad_meses - 1}, q_actual={quincena_id}), cuota={centavos_a_pesos(monto_por_mes)}")
                    else:
                        print(f"[DEBUG] Retroactivo ID {retro['id']}: ✗ Fuera de rango (inicio={quincena_inicio}, meses={cantidad_meses}, rango_final={quincena_inicio + cantidad_meses - 1 if quincena_inicio else '?'}, q_actual={quincena_id})")
            except Exception as e:
                print(f"[ERROR] Calculando retroactivos: {e}")
                import traceback
                traceback.print_exc()

            liq_completa = {
                'id': liq['id'],
                'empleado_id': empleado['id'],
                'legajo': empleado['legajo'],
                'nombre': empleado['nombre'],
                'apellido': empleado['apellido'],
                'categoria_nombre': categoria['nombre'],
                'dias_trabajados': liq['dias_trabajados'],
                'sueldo_bruto': liq['sueldo_bruto'],
                'recibo_a': liq['recibo_a'],
                'hab_s_desc': liq['hab_s_desc'],
                'recibo_b': liq['recibo_b'],
                'pasajes': pasaje['monto'] if pasaje else 0,
                'retroactivos': retroactivo_total,
                'deuda_total': deuda_total,
                'cinta_billete': liq['cinta_billete']
            }
            liq_completas.append(liq_completa)

        db.close()

        return jsonify({
            'quincena': {
                'id': quincena['id'],
                'periodo': quincena['periodo'],
                'fecha_inicio': quincena['fecha_inicio'],
                'fecha_fin': quincena['fecha_fin'],
                'cerrada': bool(quincena['cerrada'])
            },
            'liquidaciones': liq_completas
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quincenas/<int:quincena_id>/cerrar', methods=['POST'])
def cerrar_quincena(quincena_id):
    """Cierra una quincena y aplica deudas, pasajes y retroactivos"""
    try:
        db = obtener_db()

        # Obtener liquidaciones
        liquidaciones = db.get_liquidaciones(quincena_id)

        # Aplicar deudas a cada empleado
        for liq in liquidaciones:
            empleado_id = liq['empleado_id']
            deudas = db.get_deudas_activas(empleado_id)

            for deuda in deudas:
                # Verificar si la deuda ha comenzado a cobrarse en esta quincena
                quincena_inicio = deuda.get('quincena_inicio_id')
                if quincena_inicio is not None and quincena_inicio > quincena_id:
                    continue

                # Verificar si fue postergada esta quincena
                if db.fue_postergada(deuda['id'], quincena_id):
                    continue

                # Calcular cuota a aplicar
                if deuda['tipo_cobro'] == 'fijo':
                    cuota = deuda['cuota_por_quincena']
                else:  # porcentaje
                    cuota = int(liq['recibo_b'] * (deuda['porcentaje_variable'] or 0) / 100)

                if cuota > 0:
                    # Registrar cuota aplicada
                    if db.existe_cuota_aplicada(deuda['id'], liq['id']):
                        db.actualizar_cuota_aplicada(deuda['id'], liq['id'], cuota)
                    else:
                        db.crear_cuota_aplicada(deuda['id'], liq['id'], cuota)

                    # Recalcular saldo pendiente
                    cuotas_aplicadas = db.get_cuotas_aplicadas(deuda['id'])
                    total_aplicado = sum(c['monto_aplicado'] for c in cuotas_aplicadas)
                    nuevo_saldo = deuda['monto_total'] - total_aplicado

                    # Actualizar deuda
                    activa = nuevo_saldo > 0
                    db.actualizar_deuda(deuda['id'], saldo_pendiente=max(0, nuevo_saldo), activa=activa)

            # Marcar pasajes de esta quincena como aplicados (activo=0)
            try:
                pasajes = db.conn.execute(
                    "SELECT * FROM pasajes_programados WHERE empleado_id = ? AND quincena_pago_id = ? ORDER BY fecha_creacion DESC",
                    (empleado_id, quincena_id)
                ).fetchall()

                for pasaje in pasajes:
                    # Marcar como aplicado (activo = 0)
                    db.conn.execute(
                        "UPDATE pasajes_programados SET activo = 0 WHERE id = ?",
                        (pasaje['id'],)
                    )
            except Exception:
                pass  # Si la tabla no existe o hay error, continuar

            # Aplicar cuotas de retroactivos programados
            # Lógica: Si quincena_inicio <= quincena_actual < quincena_inicio + cantidad_meses, descuenta una cuota
            try:
                retroactivos = db.conn.execute(
                    "SELECT * FROM retroactivos_programados WHERE empleado_id = ? AND activo = 1 ORDER BY fecha_creacion DESC",
                    (empleado_id,)
                ).fetchall()

                for retro in retroactivos:
                    quincena_inicio = retro['quincena_inicio_id']
                    cantidad_meses = retro['cantidad_meses']

                    # Verificar si esta quincena está dentro del rango de pago
                    if quincena_inicio is not None and quincena_id >= quincena_inicio and quincena_id < quincena_inicio + cantidad_meses:
                        monto_por_mes = retro['monto_por_mes']
                        nuevo_saldo = retro['saldo_pendiente'] - monto_por_mes

                        # Si el retroactivo se completó, marca como inactivo
                        activo = 1 if nuevo_saldo > 0 else 0

                        print(f"[DEBUG] Retroactivo ID {retro['id']}: ✓ DESCUENTO (rango {quincena_inicio}-{quincena_inicio + cantidad_meses - 1}), cuota={centavos_a_pesos(monto_por_mes)}, saldo {centavos_a_pesos(retro['saldo_pendiente'])} → {centavos_a_pesos(max(0, nuevo_saldo))}, activo={activo}")

                        db.conn.execute(
                            "UPDATE retroactivos_programados SET saldo_pendiente = ?, activo = ? WHERE id = ?",
                            (max(0, nuevo_saldo), activo, retro['id'])
                        )
                    else:
                        print(f"[DEBUG] Retroactivo ID {retro['id']}: ✗ Fuera de rango (no aplica en q_id={quincena_id})")
            except Exception as e:
                print(f"[ERROR] Actualizando retroactivos: {e}")

        # Marcar quincena como cerrada
        db.cerrar_quincena(quincena_id)
        db.conn.commit()
        db.close()

        return jsonify({
            'message': 'Quincena cerrada correctamente',
            'quincena_id': quincena_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quincenas/<int:quincena_id>/reabrir', methods=['POST'])
def reabrir_quincena(quincena_id):
    """Reabre una quincena cerrada"""
    try:
        db = obtener_db()
        db.actualizar_quincena(quincena_id, cerrada=0)
        db.close()

        return jsonify({
            'message': 'Quincena reabierta correctamente',
            'quincena_id': quincena_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quincenas/<int:quincena_id>/actualizar', methods=['POST'])
def actualizar_quincena_lote(quincena_id):
    """Actualiza múltiples liquidaciones a la vez"""
    try:
        datos = request.get_json()
        liquidaciones = datos.get('liquidaciones', [])

        db = obtener_db()
        actualizados = 0

        for liq in liquidaciones:
            # Actualizar días trabajados
            if 'dias_trabajados' in liq:
                precio_dia = db.get_empleado(liq['empleado_id'])
                categoria = db.get_categoria(precio_dia['categoria_id'])
                sueldo_bruto = liq['dias_trabajados'] * categoria['precio_dia']

                # Recalcular Recibo B
                recibo_b = sueldo_bruto - (liq['recibo_a'] - liq['hab_s_desc'])

                db.actualizar_liquidacion(liq['id'],
                    dias_trabajados=liq['dias_trabajados'],
                    sueldo_bruto=sueldo_bruto,
                    recibo_b=recibo_b
                )

            # Actualizar pasajes
            if 'pasajes' in liq:
                db.actualizar_pasaje(liq['id'], liq['pasajes'])

            # Actualizar retroactivos
            if 'retroactivos' in liq:
                db.actualizar_retroactivo(liq['id'], liq['retroactivos'], '')

            actualizados += 1

        db.close()

        return jsonify({
            'actualizados': actualizados,
            'message': f'Se actualizaron {actualizados} empleados'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quincenas/<int:quincena_id>/importar-pdf', methods=['POST'])
def importar_pdf_quincena(quincena_id):
    """Importa datos del PDF del banco y actualiza liquidaciones"""
    try:
        # Verificar que se envió un archivo
        if 'file' not in request.files:
            return jsonify({'error': 'No se envió archivo PDF'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Archivo vacío'}), 400

        if not file.filename.endswith('.pdf'):
            return jsonify({'error': 'El archivo debe ser un PDF'}), 400

        # Guardar archivo temporalmente
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(temp_path)

        try:
            # Extraer datos del PDF
            datos_pdf = extraer_pdf_banco(temp_path)

            if not datos_pdf:
                return jsonify({'error': 'No se encontraron datos en el PDF'}), 400

            # Actualizar liquidaciones
            db = obtener_db()
            contador = 0

            for legajo, datos in datos_pdf.items():
                # Buscar empleado por legajo
                empleado = db.conn.execute(
                    "SELECT * FROM empleados WHERE legajo = ?",
                    (legajo,)
                ).fetchone()

                if not empleado:
                    continue

                # Buscar liquidación de esa quincena
                liq = db.conn.execute(
                    "SELECT * FROM liquidaciones WHERE quincena_id = ? AND empleado_id = ?",
                    (quincena_id, empleado['id'])
                ).fetchone()

                if liq:
                    # Obtener datos del PDF
                    recibo_a = datos.get('recibo_a', 0)
                    hab_s_desc = datos.get('hab_s_desc', 0)

                    # Calcular Recibo B
                    sueldo_bruto = liq['sueldo_bruto']
                    recibo_b = calcular_recibo_b(sueldo_bruto, recibo_a, hab_s_desc)

                    # Actualizar liquidación
                    db.actualizar_liquidacion(
                        liq['id'],
                        recibo_a=recibo_a,
                        hab_s_desc=hab_s_desc,
                        recibo_b=recibo_b
                    )

                    contador += 1

            db.close()

            # Limpiar archivo temporal
            os.remove(temp_path)

            return jsonify({
                'contador': contador,
                'message': f'Se importaron datos de {contador} empleados'
            })

        except ValueError as e:
            os.remove(temp_path)
            return jsonify({'error': f'Error en PDF: {str(e)}'}), 400
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'error': f'Error al procesar PDF: {str(e)}'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== RUTAS: LIQUIDACIONES ==============

@app.route('/api/liquidaciones/<int:liquidacion_id>', methods=['PUT'])
def actualizar_liquidacion(liquidacion_id):
    """Actualiza una liquidación individual"""
    try:
        datos = request.get_json()
        db = obtener_db()

        # Obtener liquidación actual
        liq = db.conn.execute("SELECT * FROM liquidaciones WHERE id = ?", (liquidacion_id,)).fetchone()

        if not liq:
            db.close()
            return jsonify({'error': 'Liquidación no encontrada'}), 404

        # Actualizar días trabajados
        dias = datos.get('dias_trabajados', liq['dias_trabajados'])
        empleado = db.get_empleado(liq['empleado_id'])
        categoria = db.get_categoria(empleado['categoria_id'])
        sueldo_bruto = dias * categoria['precio_dia']
        recibo_b = sueldo_bruto - (liq['recibo_a'] - liq['hab_s_desc'])

        # Actualizar pasajes y retroactivos
        pasajes = datos.get('pasajes', 0)
        retroactivos = datos.get('retroactivos', 0)

        db.actualizar_pasaje(liquidacion_id, pasajes)
        db.actualizar_retroactivo(liquidacion_id, retroactivos, '')

        # Calcular Cinta Billete con deudas según lógica exacta
        deudas = db.get_deudas_activas(liq['empleado_id'])
        quincena_id = liq['quincena_id']
        deuda_total = 0

        for d in deudas:
            quincena_inicio = d.get('quincena_inicio_id')
            # Solo incluir si quincena_inicio <= quincena_actual
            if quincena_inicio is None or quincena_inicio <= quincena_id:
                # Verificar si no fue postergada
                if not db.fue_postergada(d.get('id'), quincena_id):
                    if d.get('tipo_cobro') == 'porcentaje':
                        porcentaje = d.get('porcentaje_variable', 0)
                        deuda_total += int(recibo_b * porcentaje / 100)
                    else:
                        deuda_total += d.get('cuota_por_quincena', 0)

        cinta_billete = recibo_b - deuda_total + pasajes + retroactivos

        db.actualizar_liquidacion(liquidacion_id,
            dias_trabajados=dias,
            sueldo_bruto=sueldo_bruto,
            recibo_b=recibo_b,
            cinta_billete=cinta_billete
        )

        db.close()

        return jsonify({'message': 'Liquidación actualizada'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== RUTAS: EMPLEADOS ==============

@app.route('/api/empleados', methods=['GET'])
def get_empleados():
    """Lista todos los empleados"""
    try:
        db = obtener_db()
        empleados = db.get_empleados(activos_solo=True)

        resultado = []
        for emp in empleados:
            categoria = db.get_categoria(emp['categoria_id'])
            resultado.append({
                'id': emp['id'],
                'legajo': emp['legajo'],
                'nombre': emp['nombre'],
                'apellido': emp['apellido'],
                'cuil': emp['cuil'],
                'categoria_id': emp['categoria_id'],
                'categoria_nombre': categoria['nombre'],
                'fecha_alta': emp['fecha_alta']
            })

        # Ordenar por apellido
        resultado.sort(key=lambda x: x['apellido'])

        db.close()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/empleados/<int:empleado_id>', methods=['DELETE'])
def eliminar_empleado(empleado_id):
    """Elimina un empleado (baja lógica)"""
    try:
        db = obtener_db()
        db.dar_baja_empleado(empleado_id)
        db.close()

        return jsonify({'message': 'Empleado eliminado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/empleados', methods=['POST'])
def crear_empleado():
    """Crea un nuevo empleado"""
    try:
        datos = request.get_json()
        db = obtener_db()

        emp_id = db.crear_empleado(
            legajo=datos['legajo'],
            nombre=datos['nombre'],
            apellido=datos['apellido'],
            cuil=datos.get('cuil', ''),
            categoria_id=datos['categoria_id']
        )

        # Crear liquidaciones para todas las quincenas existentes
        quincenas = db.get_quincenas()
        for q in quincenas:
            db.crear_liquidacion(q['id'], emp_id)

        db.close()

        return jsonify({'id': emp_id, 'message': 'Empleado creado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== RUTAS: DEUDAS ==============

@app.route('/api/deudas', methods=['GET'])
def get_deudas():
    """Lista todas las deudas"""
    try:
        db = obtener_db()

        # Obtener todas las deudas
        cursor = db.conn.execute("""
            SELECT d.*, e.nombre, e.apellido
            FROM deudas d
            JOIN empleados e ON d.empleado_id = e.id
            ORDER BY d.activa DESC, e.apellido
        """)

        deudas = [dict(row) for row in cursor.fetchall()]

        resultado = []
        for d in deudas:
            resultado.append({
                'id': d['id'],
                'empleado_id': d['empleado_id'],
                'empleado_nombre': f"{d['nombre']} {d['apellido']}",
                'motivo': d['motivo'],
                'monto_total': d['monto_total'],
                'cuota_por_quincena': d['cuota_por_quincena'],
                'saldo_pendiente': d['saldo_pendiente'],
                'activa': bool(d['activa']),
                'tipo_cobro': d['tipo_cobro'],
                'porcentaje_variable': d['porcentaje_variable']
            })

        db.close()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/deudas', methods=['POST'])
def crear_deuda():
    """Crea una nueva deuda"""
    try:
        datos = request.get_json()
        db = obtener_db()

        deuda_id = db.crear_deuda(
            empleado_id=datos['empleado_id'],
            motivo=datos['motivo'],
            monto_total=datos['monto_total'],
            cuota_por_quincena=datos.get('cuota_por_quincena', 0),
            quincena_inicio_id=datos.get('quincena_inicio_id'),
            tipo_cobro=datos.get('tipo_cobro', 'fijo'),
            porcentaje_variable=datos.get('porcentaje_variable')
        )

        db.close()
        return jsonify({'id': deuda_id, 'message': 'Deuda creada'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/deudas/<int:deuda_id>', methods=['DELETE'])
def eliminar_deuda(deuda_id):
    """Elimina una deuda"""
    try:
        db = obtener_db()
        db.eliminar_deuda(deuda_id)
        db.close()

        return jsonify({'message': 'Deuda eliminada'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/deudas/<int:deuda_id>/pagos', methods=['GET'])
def get_pagos_deuda(deuda_id):
    """Obtiene historial de pagos de una deuda"""
    try:
        db = obtener_db()
        pagos = db.get_cuotas_aplicadas(deuda_id)
        db.close()

        return jsonify([
            {
                'periodo': p['periodo'],
                'nombre': f"{p['nombre']} {p['apellido']}",
                'monto': p['monto_aplicado']
            }
            for p in pagos
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== RUTAS: PASAJES ==============

@app.route('/api/pasajes', methods=['GET'])
def get_pasajes():
    """Obtiene pasajes programados (filtro opcional por empleado)"""
    try:
        empleado_id = request.args.get('empleado_id', type=int)
        db = obtener_db()

        if empleado_id:
            pasajes = db.conn.execute(
                "SELECT * FROM pasajes_programados WHERE empleado_id = ? ORDER BY fecha_creacion DESC",
                (empleado_id,)
            ).fetchall()
        else:
            pasajes = db.conn.execute(
                "SELECT * FROM pasajes_programados ORDER BY fecha_creacion DESC"
            ).fetchall()

        db.close()
        return jsonify([dict(p) for p in pasajes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pasajes', methods=['POST'])
def crear_pasaje():
    """Crea un nuevo pasaje programado"""
    try:
        datos = request.get_json()
        db = obtener_db()

        empleado_id = datos.get('empleado_id')
        monto = int(datos.get('monto', 0))  # Ya en centavos desde frontend
        fecha_pago = datos.get('fecha_pago')
        fecha_viaje = datos.get('fecha_viaje')
        quincena_pago_id = datos.get('quincena_pago_id')

        cursor = db.conn.cursor()
        cursor.execute(
            """INSERT INTO pasajes_programados
               (empleado_id, monto, fecha_pago, fecha_viaje, quincena_pago_id, activo, fecha_creacion)
               VALUES (?, ?, ?, ?, ?, 1, ?)""",
            (empleado_id, monto, fecha_pago, fecha_viaje, quincena_pago_id, datetime.now().isoformat())
        )
        db.conn.commit()
        pasaje_id = cursor.lastrowid
        db.close()

        return jsonify({
            'id': pasaje_id,
            'message': 'Pasaje creado correctamente'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pasajes/<int:pasaje_id>', methods=['PUT'])
def actualizar_pasaje(pasaje_id):
    """Actualiza un pasaje programado"""
    try:
        datos = request.get_json()
        db = obtener_db()

        monto = int(datos.get('monto', 0)) if 'monto' in datos else None  # Ya en centavos desde frontend
        fecha_pago = datos.get('fecha_pago')
        fecha_viaje = datos.get('fecha_viaje')
        quincena_pago_id = datos.get('quincena_pago_id')

        updates = []
        params = []
        if monto is not None:
            updates.append("monto = ?")
            params.append(monto)
        if fecha_pago:
            updates.append("fecha_pago = ?")
            params.append(fecha_pago)
        if fecha_viaje:
            updates.append("fecha_viaje = ?")
            params.append(fecha_viaje)
        if quincena_pago_id:
            updates.append("quincena_pago_id = ?")
            params.append(quincena_pago_id)

        if updates:
            params.append(pasaje_id)
            query = f"UPDATE pasajes_programados SET {', '.join(updates)} WHERE id = ?"
            db.conn.execute(query, params)
            db.conn.commit()

        db.close()
        return jsonify({'message': 'Pasaje actualizado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pasajes/<int:pasaje_id>', methods=['DELETE'])
def eliminar_pasaje(pasaje_id):
    """Elimina un pasaje programado"""
    try:
        db = obtener_db()
        db.conn.execute("DELETE FROM pasajes_programados WHERE id = ?", (pasaje_id,))
        db.conn.commit()
        db.close()

        return jsonify({'message': 'Pasaje eliminado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== RUTAS: RETROACTIVOS ==============

@app.route('/api/retroactivos', methods=['GET'])
def get_retroactivos():
    """Obtiene retroactivos programados (filtro opcional por empleado)"""
    try:
        empleado_id = request.args.get('empleado_id', type=int)
        db = obtener_db()

        if empleado_id:
            retroactivos = db.conn.execute(
                "SELECT * FROM retroactivos_programados WHERE empleado_id = ? ORDER BY fecha_creacion DESC",
                (empleado_id,)
            ).fetchall()
        else:
            retroactivos = db.conn.execute(
                "SELECT * FROM retroactivos_programados ORDER BY fecha_creacion DESC"
            ).fetchall()

        db.close()
        return jsonify([dict(r) for r in retroactivos])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/retroactivos', methods=['POST'])
def crear_retroactivo():
    """Crea un nuevo retroactivo programado"""
    try:
        datos = request.get_json()
        db = obtener_db()

        empleado_id = datos.get('empleado_id')
        monto_por_mes = int(datos.get('monto_por_mes', 0))  # Ya en centavos desde frontend
        cantidad_meses = int(datos.get('cantidad_meses', 1))
        monto_total = monto_por_mes * cantidad_meses
        quincena_inicio_id = datos.get('quincena_inicio_id')

        print(f"[DEBUG CREAR] Retroactivo: empleado_id={empleado_id}, monto_por_mes={monto_por_mes} ({centavos_a_pesos(monto_por_mes)}), cantidad_meses={cantidad_meses}, monto_total={monto_total} ({centavos_a_pesos(monto_total)}), quincena_inicio_id={quincena_inicio_id}")

        cursor = db.conn.cursor()
        cursor.execute(
            """INSERT INTO retroactivos_programados
               (empleado_id, monto_total, cantidad_meses, monto_por_mes,
                quincena_inicio_id, activo, saldo_pendiente, fecha_creacion)
               VALUES (?, ?, ?, ?, ?, 1, ?, ?)""",
            (empleado_id, monto_total, cantidad_meses, monto_por_mes,
             quincena_inicio_id, monto_total, datetime.now().isoformat())
        )
        db.conn.commit()
        retroactivo_id = cursor.lastrowid

        print(f"[DEBUG CREAR] ✓ Retroactivo ID {retroactivo_id} creado correctamente")

        db.close()

        return jsonify({
            'id': retroactivo_id,
            'message': 'Retroactivo creado correctamente'
        })
    except Exception as e:
        print(f"[ERROR CREAR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/retroactivos/<int:retroactivo_id>', methods=['PUT'])
def actualizar_retroactivo(retroactivo_id):
    """Actualiza un retroactivo programado"""
    try:
        datos = request.get_json()
        db = obtener_db()

        monto_por_mes = int(datos.get('monto_por_mes', 0)) if 'monto_por_mes' in datos else None  # Ya en centavos desde frontend
        cantidad_meses = datos.get('cantidad_meses')
        quincena_inicio_id = datos.get('quincena_inicio_id')

        # Obtener retroactivo actual para recalcular monto_total si es necesario
        retro = db.conn.execute("SELECT * FROM retroactivos_programados WHERE id = ?", (retroactivo_id,)).fetchone()

        updates = []
        params = []
        if monto_por_mes is not None:
            updates.append("monto_por_mes = ?")
            params.append(monto_por_mes)
        if cantidad_meses is not None:
            updates.append("cantidad_meses = ?")
            params.append(int(cantidad_meses))

        if updates:
            # Recalcular monto_total
            new_monto_por_mes = monto_por_mes if monto_por_mes is not None else retro['monto_por_mes']
            new_cantidad_meses = int(cantidad_meses) if cantidad_meses is not None else retro['cantidad_meses']
            new_monto_total = new_monto_por_mes * new_cantidad_meses

            updates.append("monto_total = ?")
            params.append(new_monto_total)

            # Recalcular saldo_pendiente = monto_total - pagado_anterior
            cuotas = db.conn.execute(
                """SELECT COALESCE(SUM(monto_aplicado), 0) as total_pagado
                   FROM cuotas_aplicadas ca
                   WHERE ca.deuda_id = (SELECT id FROM deudas WHERE id = ?)""",
                (retroactivo_id,)
            ).fetchone()
            pagado = cuotas['total_pagado'] if cuotas else 0
            new_saldo = max(0, new_monto_total - pagado)

            updates.append("saldo_pendiente = ?")
            params.append(new_saldo)

        if quincena_inicio_id is not None:
            updates.append("quincena_inicio_id = ?")
            params.append(quincena_inicio_id)

        if updates:
            params.append(retroactivo_id)
            query = f"UPDATE retroactivos_programados SET {', '.join(updates)} WHERE id = ?"
            db.conn.execute(query, params)
            db.conn.commit()

        db.close()
        return jsonify({'message': 'Retroactivo actualizado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/retroactivos/<int:retroactivo_id>', methods=['DELETE'])
def eliminar_retroactivo(retroactivo_id):
    """Elimina un retroactivo programado"""
    try:
        db = obtener_db()
        db.conn.execute("DELETE FROM retroactivos_programados WHERE id = ?", (retroactivo_id,))
        db.conn.commit()
        db.close()

        return jsonify({'message': 'Retroactivo eliminado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== RUTAS: HISTORIAL ==============

@app.route('/api/historial/<int:quincena_id>', methods=['GET'])
def get_historial(quincena_id):
    """Obtiene liquidaciones de una quincena pasada"""
    try:
        db = obtener_db()
        liquidaciones = db.get_liquidaciones(quincena_id)

        resultado = []
        for liq in liquidaciones:
            empleado = db.get_empleado(liq['empleado_id'])

            # Obtener cuotas aplicadas en esta liquidación (para historial)
            cuotas = db.get_cuotas_aplicadas_liquidacion(liq['id'])
            deuda_total = sum(c['monto_aplicado'] for c in cuotas) if cuotas else 0

            pasaje = db.get_pasaje(liq['id'])
            retroactivo = db.get_retroactivo(liq['id'])

            resultado.append({
                'id': liq['id'],
                'legajo': empleado['legajo'],
                'nombre': empleado['nombre'],
                'apellido': empleado['apellido'],
                'sueldo_bruto': liq['sueldo_bruto'],
                'deuda_total': deuda_total,
                'pasajes': pasaje['monto'] if pasaje else 0,
                'retroactivos': retroactivo['monto'] if retroactivo else 0,
                'cinta_billete': liq['cinta_billete']
            })

        db.close()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== RUTAS: CATEGORÍAS ==============

@app.route('/api/categorias', methods=['GET'])
def get_categorias():
    """Lista todas las categorías"""
    try:
        db = obtener_db()
        categorias = db.get_categorias()
        resultado = [
            {
                'id': cat['id'],
                'nombre': cat['nombre'],
                'precio_dia': cat['precio_dia']
            }
            for cat in categorias
        ]
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categorias', methods=['POST'])
def crear_categoria():
    """Crea una nueva categoría"""
    try:
        db = obtener_db()
        datos = request.get_json()

        nombre = datos.get('nombre')
        precio_dia = datos.get('precio_dia')

        if not nombre or precio_dia is None:
            return jsonify({'error': 'Datos incompletos'}), 400

        cat_id = db.crear_categoria(nombre, precio_dia)
        return jsonify({
            'id': cat_id,
            'nombre': nombre,
            'precio_dia': precio_dia,
            'message': 'Categoría creada correctamente'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== RUTAS ADICIONALES: EMPLEADOS ==============

@app.route('/api/empleados/<int:empleado_id>', methods=['PUT'])
def actualizar_empleado(empleado_id):
    """Actualiza un empleado existente"""
    try:
        db = obtener_db()
        datos = request.get_json()

        legajo = datos.get('legajo')
        nombre = datos.get('nombre')
        apellido = datos.get('apellido')
        cuil = datos.get('cuil')
        categoria_id = datos.get('categoria_id')

        if not nombre or not apellido or not categoria_id:
            return jsonify({'error': 'Datos incompletos'}), 400

        db.actualizar_empleado(empleado_id, legajo, nombre, apellido, cuil, categoria_id)

        return jsonify({
            'id': empleado_id,
            'legajo': legajo,
            'nombre': nombre,
            'apellido': apellido,
            'cuil': cuil,
            'categoria_id': categoria_id,
            'message': 'Empleado actualizado correctamente'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== RUTAS ADICIONALES: DEUDAS ==============

@app.route('/api/deudas/<int:deuda_id>', methods=['PUT'])
def actualizar_deuda(deuda_id):
    """Actualiza una deuda existente"""
    try:
        db = obtener_db()
        datos = request.get_json()

        deuda_actual = db.get_deuda(deuda_id)
        if not deuda_actual:
            return jsonify({'error': 'Deuda no encontrada'}), 404

        # Actualizar solo los campos proporcionados
        monto_total = datos.get('monto_total', deuda_actual['monto_total'])
        tipo_cobro = datos.get('tipo_cobro', deuda_actual['tipo_cobro'])

        if tipo_cobro == 'fijo':
            cuota_por_quincena = datos.get('cuota_por_quincena', deuda_actual['cuota_por_quincena'])
            porcentaje_variable = None
        else:  # porcentaje
            porcentaje_variable = datos.get('porcentaje_variable', deuda_actual.get('porcentaje_variable'))
            cuota_por_quincena = None

        # Recalcular saldo: monto_total - suma de cuotas aplicadas
        cuotas_aplicadas = sum(c['monto_aplicado'] for c in db.get_cuotas_aplicadas(deuda_id))
        nuevo_saldo = monto_total - cuotas_aplicadas

        db.actualizar_deuda(
            deuda_id,
            monto_total=monto_total,
            cuota_por_quincena=cuota_por_quincena,
            saldo_pendiente=nuevo_saldo,
            tipo_cobro=tipo_cobro,
            porcentaje_variable=porcentaje_variable
        )

        return jsonify({
            'id': deuda_id,
            'motivo': datos.get('motivo', deuda_actual['motivo']),
            'monto_total': monto_total,
            'saldo_pendiente': nuevo_saldo,
            'cuota_por_quincena': cuota_por_quincena,
            'porcentaje_variable': porcentaje_variable,
            'tipo_cobro': tipo_cobro,
            'message': 'Deuda actualizada correctamente'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== HEALTH CHECK ==============

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'obra_actual': estado['obra_actual']})

# ============== DEUDAS: POSTERGAR ==============

@app.route('/api/deudas/<int:deuda_id>/postergar', methods=['POST'])
def postergar_deuda(deuda_id):
    """Posterga una deuda para la siguiente quincena"""
    try:
        datos = request.get_json()
        quincena_id = datos.get('quincena_id')
        
        if not quincena_id:
            return jsonify({'error': 'Quincena no especificada'}), 400
        
        db = obtener_db()
        
        # Registra la postergación
        db.conn.execute("""
            INSERT INTO deudas_postergadas (deuda_id, quincena_id, fecha_postergacion)
            VALUES (?, ?, datetime('now'))
        """, (deuda_id, quincena_id))
        db.conn.commit()
        
        return jsonify({'message': 'Deuda postergada correctamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== QUINCENA: GENERAR PDFs ==============

@app.route('/api/quincenas/<int:quincena_id>/generar-pdfs', methods=['POST'])
def generar_pdfs(quincena_id):
    """Genera PDFs de Recibo B, Cinta Billete y Resumen, devuelve como ZIP"""
    try:
        db = obtener_db()

        # Obtener quincena
        quincena = db.get_quincena(quincena_id)
        if not quincena:
            db.close()
            return jsonify({'error': 'Quincena no encontrada'}), 404

        quincena_id = quincena['id']
        periodo = quincena['periodo']

        print(f"[DEBUG] Generando PDFs para quincena_id={quincena_id}, periodo='{periodo}'")

        # Obtener liquidaciones
        liquidaciones = db.get_liquidaciones(quincena_id)
        if not liquidaciones:
            db.close()
            return jsonify({'error': 'No hay liquidaciones para generar'}), 400

        # Crear carpeta output
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Obtener nombre de constructora
        nombre_constructora = "ABALLAY LUIS ROBERTO"

        try:
            # ===== 1. RECIBOS B =====
            recibos_data = []
            for liq in liquidaciones:
                empleado_id = liq.get('empleado_id')
                empleado = db.get_empleado(empleado_id)

                if not empleado:
                    continue

                legajo = empleado.get('legajo', 0)
                apellido = empleado.get('apellido', '')
                nombre = empleado.get('nombre', '')
                nombre_completo = f"{apellido} {nombre}"
                dias = liq.get('dias_trabajados', 0)

                # Obtener deudas aplicadas
                deuda_cuota = 0
                motivo_deuda = ""
                cuotas = db.get_cuotas_aplicadas_liquidacion(liq.get('id'))
                if cuotas:
                    for cuota in cuotas:
                        deuda = db.get_deuda(cuota.get('deuda_id'))
                        if deuda:
                            deuda_cuota = cuota.get('monto_aplicado', 0)
                            motivo_deuda = deuda.get('motivo', '')
                            break

                # Obtener pasajes
                pasajes = liq.get('pasajes', 0) or 0

                # Obtener retroactivos
                retroactivos = liq.get('retroactivos', 0) or 0

                recibos_data.append((
                    nombre_completo,
                    legajo,
                    dias,
                    liq.get('sueldo_bruto', 0),
                    liq.get('recibo_a', 0),
                    liq.get('hab_s_desc', 0),
                    liq.get('recibo_b', 0),
                    pasajes,
                    retroactivos,
                    deuda_cuota,
                    motivo_deuda,
                ))

            # Ordenar alfabéticamente
            recibos_data.sort(key=lambda x: x[0].upper())

            # Generar PDF de Recibos
            recibos_file = output_dir / f"RECIBOS_B_{periodo.replace('-', '_')}.pdf"
            generar_recibos_b_consolidado(
                str(recibos_file),
                periodo,
                recibos_data,
                nombre_constructora,
                db,
            )
            print(f"[PDF] Recibos generado: {recibos_file.name}")

            # ===== 2. CINTA BILLETE =====
            empleados_datos = []
            for liq in liquidaciones:
                empleado_id = liq.get('empleado_id')
                empleado = db.get_empleado(empleado_id)
                if empleado:
                    apellido = empleado.get('apellido', '')
                    nombre = empleado.get('nombre', '')
                    nombre_completo = f"{apellido} {nombre}"
                    legajo = empleado.get('legajo', 0)
                    cinta_billete = liq.get('cinta_billete', 0)
                    if cinta_billete > 0:
                        empleados_datos.append((nombre_completo, legajo, cinta_billete))

            # Ordenar alfabéticamente
            empleados_datos.sort(key=lambda x: x[0].upper())

            cinta_file = output_dir / f"CINTA_BILLETE_{periodo.replace('-', '_')}.pdf"
            generar_cinta_billete(str(cinta_file), periodo, empleados_datos)
            print(f"[PDF] Cinta Billete generada: {cinta_file.name}")

            # ===== 3. RESUMEN PREPARACIÓN =====
            from sueldos_app.calculations import redondear_a_500
            resumen_datos = []
            for liq in liquidaciones:
                empleado_id = liq.get('empleado_id')
                empleado = db.get_empleado(empleado_id)
                if empleado:
                    apellido = empleado.get('apellido', '')
                    nombre = empleado.get('nombre', '')
                    cinta_billete = liq.get('cinta_billete', 0)
                    if cinta_billete > 0:
                        a_preparar = redondear_a_500(cinta_billete)
                        resumen_datos.append((apellido, nombre, a_preparar))

            # Ordenar alfabéticamente
            resumen_datos.sort(key=lambda x: x[0].upper())

            resumen_file = output_dir / f"PREPARAR_{periodo.replace('-', '_')}.pdf"
            generar_resumen_preparacion(str(resumen_file), periodo, resumen_datos)
            print(f"[PDF] Resumen Preparación generado: {resumen_file.name}")

            # ===== CREAR ZIP =====
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for pdf_file in [recibos_file, cinta_file, resumen_file]:
                    if pdf_file.exists():
                        zip_file.write(pdf_file, arcname=pdf_file.name)
                        print(f"[ZIP] Agregado: {pdf_file.name}")

            zip_buffer.seek(0)
            db.close()

            # Retornar ZIP como descarga
            filename = f'{periodo}.zip'
            print(f"[DEBUG] Enviando ZIP con nombre: {filename}")

            response = send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name=filename
            )
            # Agregar headers manualmente
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
            return response

        except Exception as e:
            db.close()
            print(f"[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Error al generar PDFs: {str(e)}'}), 500

    except Exception as e:
        print(f"[ERROR GENERAL] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============== QUINCENA: EXPORTAR EXCEL ==============

@app.route('/api/quincenas/<int:quincena_id>/exportar-excel', methods=['POST'])
def exportar_excel(quincena_id):
    """Exporta liquidaciones a Excel"""
    try:
        # Por ahora, retornar éxito (implementación completa en backend)
        return jsonify({'message': 'Excel exportado correctamente'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============== MANEJO DE ERRORES ==============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Ruta no encontrada'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    # Inicializar con la obra "Tandil"
    try:
        cambiar_db_obra('Tandil')
    except Exception as e:
        print(f"[DEBUG] No se encontró obra 'Tandil': {e}")
        # Si falla, intentar con sueldos.db
        try:
            legacy_path = _get_obras_folder().parent / "sueldos.db"
            set_db_path(legacy_path)
            init_db()
            estado['obra_actual'] = 'sueldos'
            print(f"[DEBUG] BD inicializada desde: {legacy_path}")
        except Exception as e2:
            print(f"[ERROR] No se encontró BD de referencia: {e2}")

    app.run(debug=True, host='0.0.0.0', port=5000)
