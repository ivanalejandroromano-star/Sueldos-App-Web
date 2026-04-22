import base64
import os

def init_database():
    """Descodifica sueldos.db desde base64 si es necesario"""
    db_path = '/var/task/sueldos.db'
    b64_path = '/var/task/sueldos.db.b64'
    
    # Si el archivo binario existe pero no es válido, recrearlo desde base64
    if os.path.exists(b64_path):
        try:
            with open(b64_path, 'r') as f:
                b64_content = f.read()
            
            db_bytes = base64.b64decode(b64_content)
            
            with open(db_path, 'wb') as f:
                f.write(db_bytes)
            
            print(f"[INIT] BD recreada desde base64: {len(db_bytes)} bytes")
            return db_path
        except Exception as e:
            print(f"[ERROR] No se pudo recrear BD: {e}")
    
    return db_path if os.path.exists(db_path) else None

# Ejecutar al importar
db = init_database()
