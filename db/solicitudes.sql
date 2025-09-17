-- Script de base de datos para el sistema de solicitudes

-- Tabla de usuarios
CREATE TABLE Usuarios (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(50) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL,
    rol NVARCHAR(20) NOT NULL
);

-- Tabla de solicitudes
CREATE TABLE Solicitudes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    usuario_id INT NOT NULL,
    descripcion NVARCHAR(255) NOT NULL,
    monto DECIMAL(18, 2) NOT NULL,
    fecha_esperada DATE NOT NULL,
    estado NVARCHAR(20) NOT NULL DEFAULT 'Pendiente',
    comentario NVARCHAR(255) NULL,
    fecha_creacion DATETIME NOT NULL DEFAULT GETDATE(),
    fecha_actualizacion DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT fk_solicitud_usuario FOREIGN KEY(usuario_id) REFERENCES Usuarios(id)
);

-- Tabla de auditoría
CREATE TABLE Auditoria (
    id INT IDENTITY(1,1) PRIMARY KEY,
    usuario_id INT NOT NULL,
    fecha DATETIME NOT NULL DEFAULT GETDATE(),
    accion NVARCHAR(50) NOT NULL,
    detalle NVARCHAR(255) NOT NULL,
    CONSTRAINT fk_auditoria_usuario FOREIGN KEY(usuario_id) REFERENCES Usuarios(id)
);

-- Vista para consultar solicitudes por usuario y estado
CREATE VIEW v_solicitudes_por_usuario_estado AS
SELECT s.id, u.username AS usuario, s.descripcion, s.monto, s.fecha_esperada, s.estado, s.comentario, s.fecha_creacion, s.fecha_actualizacion
FROM Solicitudes s
JOIN Usuarios u ON s.usuario_id = u.id;

GO

-- Procedimiento para autenticación (login)
CREATE OR ALTER PROCEDURE sp_login
    @Username NVARCHAR(50),
    @Password NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT id, username, rol FROM Usuarios
    WHERE username = @Username AND password_hash = @Password;
END;
GO

-- Procedimiento para crear una solicitud
CREATE OR ALTER PROCEDURE sp_crear_solicitud
    @UsuarioId INT,
    @Descripcion NVARCHAR(255),
    @Monto DECIMAL(18, 2),
    @FechaEsperada DATE
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO Solicitudes (usuario_id, descripcion, monto, fecha_esperada)
    VALUES (@UsuarioId, @Descripcion, @Monto, @FechaEsperada);

    DECLARE @SolicitudId INT = SCOPE_IDENTITY();

    -- Registrar en auditoría
    INSERT INTO Auditoria (usuario_id, accion, detalle)
    VALUES (@UsuarioId, 'CrearSolicitud', CONCAT('Solicitud ', @SolicitudId, ' creada'));

    SELECT @SolicitudId AS SolicitudId;
END;
GO

-- Procedimiento para aprobar una solicitud
CREATE OR ALTER PROCEDURE sp_aprobar_solicitud
    @SupervisorId INT,
    @SolicitudId INT,
    @Comentario NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Monto DECIMAL(18,2);
    SELECT @Monto = monto FROM Solicitudes WHERE id = @SolicitudId;

    -- Validación de comentario obligatorio si monto > 5000
    IF (@Monto > 5000 AND ( @Comentario IS NULL OR LTRIM(RTRIM(@Comentario)) = '' ))
    BEGIN
        RAISERROR('Comentario obligatorio para montos mayores a 5000', 16, 1);
        RETURN;
    END;

    UPDATE Solicitudes
    SET estado = 'Aprobada', comentario = @Comentario, fecha_actualizacion = GETDATE()
    WHERE id = @SolicitudId;

    -- Registrar en auditoría
    INSERT INTO Auditoria (usuario_id, accion, detalle)
    VALUES (@SupervisorId, 'AprobarSolicitud', CONCAT('Solicitud ', @SolicitudId, ' aprobada'));
END;
GO

-- Procedimiento para rechazar una solicitud
CREATE OR ALTER PROCEDURE sp_rechazar_solicitud
    @SupervisorId INT,
    @SolicitudId INT,
    @Comentario NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    IF ( @Comentario IS NULL OR LTRIM(RTRIM(@Comentario)) = '' )
    BEGIN
        RAISERROR('Comentario obligatorio al rechazar una solicitud', 16, 1);
        RETURN;
    END;

    UPDATE Solicitudes
    SET estado = 'Rechazada', comentario = @Comentario, fecha_actualizacion = GETDATE()
    WHERE id = @SolicitudId;

    -- Registrar en auditoría
    INSERT INTO Auditoria (usuario_id, accion, detalle)
    VALUES (@SupervisorId, 'RechazarSolicitud', CONCAT('Solicitud ', @SolicitudId, ' rechazada'));
END;
GO

-- Procedimiento para listar solicitudes
CREATE OR ALTER PROCEDURE sp_listar_solicitudes
    @UsuarioId INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF @UsuarioId IS NULL
    BEGIN
        -- Supervisor: listar todas
        SELECT * FROM v_solicitudes_por_usuario_estado;
    END
    ELSE
    BEGIN
        -- Usuario: listar sus propias solicitudes
        SELECT * FROM v_solicitudes_por_usuario_estado WHERE usuario = (SELECT username FROM Usuarios WHERE id = @UsuarioId);
    END;
END;
GO

-- Datos de prueba
INSERT INTO Usuarios (username, password_hash, rol)
VALUES ('empleado1', 'empleado1', 'Usuario'),
       ('super1', 'super1', 'Supervisor');
