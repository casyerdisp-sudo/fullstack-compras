import os
import time
import pyodbc
import pathlib

# Cadena de conexión a SQL Server obtenida de la variable de entorno
conn_str = os.getenv("SQLSERVER_CONN")
# Ruta al archivo SQL que inicializa la base de datos
sql_path = pathlib.Path(__file__).resolve().parent.parent / "db" / "solicitudes.sql"

# Esperar a que SQL Server esté disponible
for _ in range(60):
    try:
        with pyodbc.connect(conn_str, timeout=2) as conn:
            break
    except Exception:
        time.sleep(2)
else:
    raise RuntimeError("No se pudo conectar a SQL Server")

# Leer el contenido del script SQL
with open(sql_path, "r", encoding="utf-8") as f:
    sql = f.read()

# Dividir el script en comandos individuales utilizando 'GO'
chunks = []
acc = []
for line in sql.splitlines():
    if line.strip().upper() == "GO":
        if acc:
            chunks.append("\n".join(acc))
            acc = []
    else:
        acc.append(line)
# Agregar último segmento
if acc:
    chunks.append("\n".join(acc))

# Ejecutar cada comando en la base de datos
with pyodbc.connect(conn_str, autocommit=True) as conn:
    cursor = conn.cursor()
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            cursor.execute(chunk)
        except Exception:
            # Ignorar errores por re-ejecución (idempotencia)
            pass
