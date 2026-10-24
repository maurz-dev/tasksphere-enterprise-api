# TaskSphere Enterprise REST API

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com)
[![ORM](https://img.shields.io/badge/SQLAlchemy-2.0%20Async-d71f00.svg)](https://www.sqlalchemy.org/)
[![Validation](https://img.shields.io/badge/Pydantic-V2-e92063.svg)](https://docs.pydantic.dev/)
[![Linter & Formatter](https://img.shields.io/badge/Ruff-0.7%2B-d7ff64.svg)](https://astral.sh/ruff)
[![Package Manager](https://img.shields.io/badge/uv-Astral-purple.svg)](https://astral.sh/uv)
[![Test Coverage](https://img.shields.io/badge/coverage-80%25%2B-brightgreen.svg)](htmlcov/index.html)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

TaskSphere Enterprise API es una plataforma de servicios REST para la orquestacion de proyectos, gestion de tareas y trazabilidad de eventos empresariales. Esta desarrollada bajo principios de Arquitectura Limpia (Clean Architecture), Diseno Guiado por el Dominio (DDD) y tipado estricto en Python 3.12+.

---

## Caracteristicas Principales

- **Control de Acceso Basado en Roles (RBAC)**: Jerarquia de acceso multi-rol (Administrador, Gerente de Proyecto, Miembro) con funciones criptograficas seguras mediante bcrypt nativo y JSON Web Tokens (JWT) conformes al estandar RFC 7519.
- **Arquitectura Limpia**: Desacoplamiento riguroso entre capas de Dominio, Logica de Negocio (Servicios), Persistencia (Repositorios) e Interfaz HTTP (Controladores/Routers).
- **Maquina de Estados Finitos (FSM)**: Transiciones de estado estrictas y controladas para tareas (`TODO -> IN_PROGRESS -> IN_REVIEW -> COMPLETED -> ARCHIVED`), impidiendo estados inconsistentes y emitiendo errores estandarizados RFC 7807/9457 en transiciones no autorizadas.
- **Auditoria Transaccional Integrada**: Modulo persistente de auditoria que registra operaciones criticas (altas, bajas, modificaciones de estado y autenticaciones).
- **Procesamiento Asincrono Completo**: Motor de base de datos basado en SQLAlchemy 2.0 AsyncIO con compatibilidad nativa para SQLite en desarrollo y PostgreSQL en entornos productivos.
- **Instrumentacion y Trazabilidad**: Middleware de contexto que asocia correlacion unívoca via encabezado `X-Request-ID` y medicion de latencia en encabezado `X-Process-Time`.
- **Interfaz de Linea de Comandos (CLI)**: Herramienta de administracion y mantenimiento construida con Typer y Rich para la gestion de credenciales y sembrado de datos de prueba.
- **Contenedorizacion de Produccion**: Configuracion Dockerfile multi-etapa con usuario no privilegiado y composicion Docker Compose con PostgreSQL 16 y sondeos de salud (healthchecks).

---

## Arquitectura del Sistema

```text
+---------------------------------------------------------------------+
| Capa de Presentacion (src/enterprise_api/api/)                       |
|  - Enrutadores modulares versionados (/api/v1)                      |
|  - Dependencias de autenticacion y verificacion de roles            |
|  - Middleware de correlacion y tiempos de respuesta                 |
+----------------------------------+----------------------------------+
                                   |
                                   v
+---------------------------------------------------------------------+
| Capa de Logica de Negocio (src/enterprise_api/services/)            |
|  - Validacion de reglas de negocio y transiciones FSM               |
|  - Generacion deterministica de identificadores unicos              |
|  - Emision de registros en log de auditoria                         |
+----------------------------------+----------------------------------+
                                   |
                                   v
+---------------------------------------------------------------------+
| Capa de Acceso a Datos (src/enterprise_api/repositories/)            |
|  - BaseRepository generico tipado                                   |
|  - Consultas optimizadas con carga ansiosa (selectinload)           |
+----------------------------------+----------------------------------+
                                   |
                                   v
+---------------------------------------------------------------------+
| Capa de Dominio y Persistencia (src/enterprise_api/models & core/)  |
|  - DeclarativeBase SQLAlchemy 2.0 con control de marcas de tiempo   |
|  - Modelos relacionales: User, Project, Task, AuditLog              |
|  - Configuracion declarativa con Pydantic Settings                  |
+---------------------------------------------------------------------+
```

---

## Estructura de Directorios

```text
enterprise-task-api/
├── .github/workflows/ci.yml         # Pipeline de Integracion Continua
├── docs/
│   └── architecture.md              # Especificacion formal de la arquitectura
├── src/
│   └── enterprise_api/
│       ├── api/
│       │   ├── deps.py              # Inyeccion de dependencias
│       │   └── v1/
│       │       ├── api.py           # Agregador del router v1
│       │       └── endpoints/       # Controladores de recursos
│       ├── core/
│       │   ├── config.py            # Configuracion de entorno
│       │   ├── database.py          # Conexion asincrona a base de datos
│       │   ├── exceptions.py        # Jerarquia de excepciones RFC 7807
│       │   ├── logging.py           # Configuración de logging estructurado
│       │   └── security.py          # Criptografia, hashing y JWT
│       ├── middleware/
│       │   └── correlation.py       # Trazabilidad de peticiones
│       ├── models/                  # Entidades ORM relacionales
│       ├── repositories/            # Implementacion de patron repositorio
│       ├── schemas/                 # Contratos de datos Pydantic V2
│       ├── services/                # Servicios de aplicacion y FSM
│       ├── cli.py                   # Interfaz de linea de comandos
│       └── main.py                  # Punto de entrada de la aplicacion ASGI
├── tests/                           # Suite de pruebas unitarias y de integracion
├── .env.example                     # Plantilla de configuracion de entorno
├── .gitignore                       # Reglas de exclusion de control de versiones
├── .pre-commit-config.yaml          # Configuracion de hooks de pre-confirmacion
├── Dockerfile                       # Definicion de imagen de contenedor multi-etapa
├── docker-compose.yml               # Orquestacion de servicios (API + PostgreSQL)
└── pyproject.toml                   # Especificacion de dependencias y herramientas PEP 621
```

---

## Requisitos Previos e Instalacion

El proyecto utiliza **uv** para la gestion deterministica de dependencias y entornos virtuales:

```bash
# Instalacion de dependencias y configuracion del entorno virtual
uv sync --all-groups
```

### Configuracion de Variables de Entorno

Crear el archivo de variables locales a partir de la plantilla:

```bash
cp .env.example .env
```

Por defecto, la aplicacion utiliza una base de datos local SQLite asincrona (`tasksphere.db`), permitiendo su ejecucion inmediata sin dependencias externas.

---

## Ejecucion del Servidor

### Modo Desarrollo

```bash
uv run enterprise-cli run-server --port 8000
```

Alternativamente, es posible invocar Uvicorn de forma directa:

```bash
uv run uvicorn enterprise_api.main:app --reload --port 8000
```

### Documentacion Interactiva de la API

Una vez iniciado el servicio, los esquemas y contratos OpenAPI estan disponibles en:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Sondeo de Salud: `http://127.0.0.1:8000/api/v1/health`

---

## Interfaz de Linea de Comandos (CLI)

El proyecto incluye comandos de gestion administrativa a traves del comando `enterprise-cli`:

```bash
# Consultar estado operacional y variables del entorno
uv run enterprise-cli info

# Registrar un nuevo usuario con rol de Administrador
uv run enterprise-cli create-admin --email admin@empresa.com --password PasswordSeguro123! --full-name "Administrador General"

# Poblar el sistema con datos de demostracion (usuarios, proyectos y tareas)
uv run enterprise-cli seed-demo

# Iniciar servidor Uvicorn con parametros configurables
uv run enterprise-cli run-server --host 127.0.0.1 --port 8000
```

---

## Pruebas Automatizadas y Calidad de Codigo

### Ejecucion de Pruebas Unitarias y de Integracion

La suite incluye 18 pruebas asincronas que validan autenticacion, roles, paginacion y maquinas de estado sobre una base de datos SQLite en memoria:

```bash
uv run pytest
```

El reporte de cobertura en formato HTML se genera en el directorio `htmlcov/`:

```bash
# Abrir reporte de cobertura en Windows
start htmlcov/index.html
```

### Analisis Estatico y Formato con Ruff

```bash
# Comprobacion de reglas de linter
uv run ruff check .

# Validacion de formato de codigo
uv run ruff format --check .
```

---

## Despliegue con Docker y PostgreSQL

Para levantar el entorno completo de produccion con PostgreSQL 16 y comprobaciones de estado de conexion:

```bash
# Compilacion y arranque de servicios en segundo plano
docker compose up -d --build

# Visualizacion de logs de la aplicacion
docker compose logs -f api

# Parada de servicios
docker compose down
```

---

## Credenciales por Defecto (Entorno de Desarrollo)

| Rol | Correo Electronico | Contrasena | Alcance de Permisos |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin@tasksphere.io` | `AdminSecurePass123!` | Administracion de usuarios, proyectos, tareas y auditoria |
| **Gerente de Proyecto** | `pm@tasksphere.io` | `Password123!` | Creacion de proyectos y asignacion de tareas |
| **Miembro** | `dev@tasksphere.io` | `Password123!` | Visualizacion y transicion de estados de tareas asignadas |

---

## Licencia

Este proyecto se distribuye bajo los terminos de la licencia MIT. Consulte el archivo LICENSE para mas detalles.
