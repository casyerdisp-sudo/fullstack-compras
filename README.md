# Sistema de Solicitudes de Compra

Este repositorio contiene una **aplicación web Full‑Stack** para gestionar solicitudes de compra internas. Incluye:

- **Base de datos SQL Server** con tablas, procedimientos almacenados y vista.
- **API REST** construida con **FastAPI** que implementa autenticación JWT y control de acceso por roles.
- **Contenedor de desarrollo** con Docker Compose y un archivo `.devcontainer` para ejecutar la solución en GitHub Codespaces.

## Estructura del proyecto

```
fullstack-compras/
├── db/                 # Scripts de la base de datos
│   └── solicitudes.sql
├── api/                # Código de la API FastAPI
│   ├── app.py
│   ├── auth.py
│   ├── deps.py
│   ├── models.py
│   ├── init_db.py
│   ├── Dockerfile
│   └── requirements.txt
├── blazor/             # Front‑end (placeholder con instrucciones)
│   └── README.md
├── .devcontainer/
│   └── devcontainer.json
└── docker-compose.yml
```

## Cómo ejecutar la aplicación en Codespaces

1. **Abre este repositorio en GitHub Codespaces**. Github creará un entorno Linux con Docker instalado.
2. Ejecuta el siguiente comando en la terminal:

   ```bash
   docker compose up --build
   ```

   Este comando descargará las imágenes de SQL Server, instalará las dependencias de la API y construirá el contenedor de la interfaz (Blazor). Puede tardar algunos minutos la primera vez.

3. Cuando todos los servicios estén listos verás tres puertos expuestos en la sección Ports de Codespaces:

   - **8000**: API FastAPI (documentada en `/docs`)
   - **5000**: Aplicación Blazor (requiere ajustes adicionales, ver más abajo)
   - **1433**: SQL Server

4. Accede a `8000` para probar la API. Puedes iniciar sesión con los siguientes usuarios de prueba creados en el script de base de datos:

   | Usuario   | Contraseña | Rol        |
   |-----------|------------|------------|
   | empleado1 | empleado1  | Usuario    |
   | super1    | super1     | Supervisor |

5. La aplicación Blazor contenida en `blazor/` es solo un **placeholder**. Sigue las instrucciones del archivo `blazor/README.md` para generar la interfaz de usuario.

## Descripción resumida de los componentes

### Base de datos (`db/solicitudes.sql`)

Define las tablas **Usuarios**, **Solicitudes** y **Auditoria**, una vista y procedimientos almacenados que encapsulan la lógica de negocio (por ejemplo, solicitar comentarios para montos mayores a 5000). También inserta datos de prueba para dos usuarios.

### API (`api/`)

Implementa una API RESTful con FastAPI. Proporciona endpoints para iniciar sesión (`/auth/login`), crear y listar solicitudes (`/solicitudes`), y listar/aprobar/rechazar solicitudes pendientes (`/approvals`). Usa JWT para autenticar y proteger las rutas y emplea ODBC para comunicarse con SQL Server ejecutando los procedimientos almacenados.

### Front‑End (`blazor/`)

El directorio `blazor/` contiene únicamente documentación sobre cómo crear la interfaz de usuario con Blazor Server. Se deja a elección del desarrollador generar el proyecto y añadir páginas de inicio de sesión, creación de solicitudes, listado y panel de aprobaciones.
