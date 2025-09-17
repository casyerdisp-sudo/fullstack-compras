from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List
import os
import pyodbc
import jwt
import datetime

app = FastAPI()

# Obtener configuración de variables de entorno
JWT_SECRET = os.getenv("JWT_SECRET", "super-secreto-123")
SQL_CONN = os.getenv("SQLSERVER_CONN")

# OAuth2 scheme para obtener el token desde el header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Modelos Pydantic
class User(BaseModel):
    id: int
    username: str
    rol: str

class SolicitudCreate(BaseModel):
    descripcion: str
    monto: float
    fecha_esperada: datetime.date

class ApproveRequest(BaseModel):
    comentario: Optional[str] = None

class RejectRequest(BaseModel):
    comentario: str

# Conexión a la base de datos

def get_conn():
    return pyodbc.connect(SQL_CONN)

# Obtener el usuario actual a partir del token JWT

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return User(**payload)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Autenticación de usuarios. Devuelve un JWT si las credenciales son correctas."""
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_login ?, ?", form_data.username, form_data.password)
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
        user_data = {"id": row[0], "username": row[1], "rol": row[2]}
        token = jwt.encode(user_data, JWT_SECRET, algorithm="HS256")
        return {"access_token": token, "token_type": "bearer"}

@app.post("/solicitudes")
def crear_solicitud(solicitud: SolicitudCreate, user: User = Depends(get_current_user)):
    """Crear una nueva solicitud de compra."""
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_crear_solicitud ?, ?, ?, ?", user.id, solicitud.descripcion, solicitud.monto, solicitud.fecha_esperada)
        row = cursor.fetchone()
        solicitud_id = row[0] if row else None
        return {"id": solicitud_id}

@app.get("/solicitudes")
def listar_solicitudes(user: User = Depends(get_current_user)):
    """Listar solicitudes. Los usuarios ven las propias y el supervisor ve todas."""
    with get_conn() as conn:
        cursor = conn.cursor()
        if user.rol == "Supervisor":
            cursor.execute("EXEC sp_listar_solicitudes NULL")
        else:
            cursor.execute("EXEC sp_listar_solicitudes ?", user.id)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results

@app.post("/approvals/{solicitud_id}/approve")
def aprobar_solicitud(solicitud_id: int, body: ApproveRequest, user: User = Depends(get_current_user)):
    """Aprobar una solicitud. Solo el supervisor puede hacerlo."""
    if user.rol != "Supervisor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    with get_conn() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("EXEC sp_aprobar_solicitud ?, ?, ?", user.id, solicitud_id, body.comentario)
            return {"detail": "Solicitud aprobada"}
        except Exception as e:
            # Devolver el mensaje del procedimiento almacenado
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.post("/approvals/{solicitud_id}/reject")
def rechazar_solicitud(solicitud_id: int, body: RejectRequest, user: User = Depends(get_current_user)):
    """Rechazar una solicitud. Solo el supervisor puede hacerlo y el comentario es obligatorio."""
    if user.rol != "Supervisor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    with get_conn() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("EXEC sp_rechazar_solicitud ?, ?, ?", user.id, solicitud_id, body.comentario)
            return {"detail": "Solicitud rechazada"}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
