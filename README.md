# TaskSphere Enterprise REST API 🚀

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![ORM](https://img.shields.io/badge/SQLAlchemy-2.0%20Async-d71f00.svg)](https://www.sqlalchemy.org/)
[![Validation](https://img.shields.io/badge/Pydantic-V2-e92063.svg)](https://docs.pydantic.dev/)
[![Linter & Formatter](https://img.shields.io/badge/Ruff-0.7%2B-d7ff64.svg?logo=ruff&logoColor=black)](https://astral.sh/ruff)
[![Package Manager](https://img.shields.io/badge/uv-Astral-purple.svg)](https://astral.sh/uv)
[![Test Coverage](https://img.shields.io/badge/coverage-80%25%2B-brightgreen.svg)](htmlcov/index.html)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **TaskSphere Enterprise API** es una solución de nivel empresarial para la orquestación y gestión de proyectos y tareas, desarrollada siguiendo los más rigurosos estándares de la industria, **Clean Architecture (Arquitectura Limpia)**, **Domain-Driven Design (DDD)** y tipado estricto en Python 3.12+.

---

## 🏛️ Inspirado en 3 Proyectos Referentes de GitHub

Este proyecto adopta patrones arquitectónicos y de ingeniería de software probados en producción de tres de los repositorios más influyentes del ecosistema Python moderno:

| Proyecto GitHub | Patrones Adoptados en este Proyecto |
| :--- | :--- |
| **[`tiangolo/full-stack-fastapi-template`](https://github.com/tiangolo/full-stack-fastapi-template)** | • Estructura modular de endpoints en capas (`/api/v1`)<br>• Inyección de dependencias (`Depends`) para seguridad, servicios y sesiones de base de datos<br>• Autenticación OAuth2 Bearer JWT compatible con Swagger UI<br>• Ciclo de vida asíncrono (`lifespan`) con auto-migración y seed de administrador por defecto |
| **[`encode/httpx`](https://github.com/encode/httpx)** | • Jerarquía de excepciones de dominio con respuestas RFC 7807/9457 Problem Details<br>• Middleware de trazabilidad con inyección de encabezados `X-Request-ID` y medición de latencia `X-Process-Time`<br>• Pruebas de integración E2E asíncronas de alto rendimiento con `httpx.AsyncClient` y `ASGITransport` |
| **[`pydantic/pydantic`](https://github.com/pydantic/pydantic) & [`astral-sh/ruff`](https://github.com/astral-sh/ruff)** | • Validación tipada y esquemas genéricos paginados (`PaginatedResponse[T]`)<br>• Gestión de configuración fuertemente tipada con `pydantic-settings` y `.env`<br>• Configuración estandarizada PEP 621 en `pyproject.toml`, linter & formatter ultra-rápido Ruff, y suite de pruebas Pytest con cobertura automatizada |

---

## ✨ Características Principales

- 🛡️ **Seguridad y Control de Acceso (RBAC)**: Roles de usuario (`Admin`, `Manager`, `Member`) con hashing seguro de contraseñas vía `bcrypt` nativo (sin dependencias obsoletas) y tokens JWT firmados criptográficamente.
- ⚙️ **Clean Architecture**: Separación estricta entre Dominio (`models/`), Reglas de Negocio (`services/`), Acceso a Datos (`repositories/`), y Presentación (`api/`).
- 🔄 **Máquina de Estados Finitos (FSM)**: Flujo de trabajo regulado para tareas (`TODO -> IN_PROGRESS -> IN_REVIEW -> COMPLETED -> ARCHIVED`), impidiendo transiciones inválidas con validación de negocio.
- 📊 **Métricas Agregadas**: Consultas optimizadas con conteo de tareas completadas y totales en tiempo real para proyectos.
- 📜 **Trazabilidad y Auditoría**: Tabla y repositorio de `AuditLog` que registra de manera asíncrona cada evento sensible en el sistema.
- 💻 **CLI Interactiva de Operaciones**: Herramienta de línea de comandos construida con `Typer` y `Rich` para gestionar administradores, consultar el sistema y poblar datos demo.
- 🐳 **Contenedorización para Producción**: `Dockerfile` multi-etapa con usuario sin privilegios y `docker-compose.yml` orquestado con PostgreSQL 16 y comprobación de salud (`healthcheck`).

---

## 📁 Estructura del Proyecto

```text
poyecto_python/
├── .github/workflows/ci.yml         # Pipeline de Integración Continua (Linting + Tests)
├── docs/
│   └── architecture.md              # Documentación detallada y diagramas de arquitectura
├── src/
│   └── enterprise_api/
│       ├── api/                     # Capa de Presentación
│       │   ├── deps.py              # Inyección de dependencias (seguridad, servicios, BD)
│       │   └── v1/
│       │       ├── api.py           # Agregador del router maestro v1
│       │       └── endpoints/       # auth, users, projects, tasks, health
│       ├── core/                    # Núcleo del sistema
│       │   ├── config.py            # Pydantic Settings V2 y lectura de entorno
│       │   ├── database.py          # SQLAlchemy 2.0 Async Engine y sesión local
│       │   ├── exceptions.py        # Excepciones de dominio y Problem Details RFC 7807
│       │   ├── logging.py           # Logger estructurado
│       │   └── security.py          # Hashing bcrypt y gestión de tokens JWT
│       ├── middleware/
│       │   └── correlation.py       # Trazabilidad X-Request-ID y X-Process-Time
│       ├── models/                  # Entidades SQLAlchemy 2.0 ORM
│       │   ├── base.py              # DeclarativeBase y TimestampMixin
│       │   ├── enums.py             # UserRole, TaskStatus, TaskPriority, ProjectStatus
│       │   ├── user.py, project.py, task.py, audit.py
│       ├── repositories/            # Capa de Acceso a Datos (Repository Pattern)
│       │   ├── base.py              # BaseRepository genérico asíncrono
│       │   ├── user_repository.py, project_repository.py, task_repository.py, audit_repository.py
│       ├── schemas/                 # Contratos Pydantic V2 (DTOs)
│       │   ├── common.py            # PaginatedResponse[T], PaginationParams, HealthResponse
│       │   ├── user.py, project.py, task.py, audit.py
│       ├── services/                # Capa de Lógica de Negocio
│       │   ├── auth_service.py, user_service.py, project_service.py, task_service.py
│       ├── cli.py                   # CLI interactiva de consola con Typer y Rich
│       └── main.py                  # Fábrica de aplicación FastAPI y lifespan
├── tests/                           # Suite de pruebas automatizadas
│       ├── conftest.py              # Fixtures asíncronas con SQLite in-memory y HTTPX
│       ├── test_auth.py, test_users.py, test_projects.py, test_tasks.py, test_services.py, test_health.py
├── .env.example                     # Plantilla de variables de entorno documentada
├── .gitignore                       # Filtro de archivos no rastreables
├── .pre-commit-config.yaml          # Automatización de hooks git
├── Dockerfile                       # Multi-stage build optimizado
├── docker-compose.yml               # Orquestación con PostgreSQL 16
└── pyproject.toml                   # Estándar PEP 621 (Ruff, Pytest, Coverage)
```

---

## 🚀 Inicio Rápido (Quickstart)

### 1. Clonar e Instalar Dependencias
El proyecto utiliza [**uv**](https://github.com/astral-sh/uv), el gestor de paquetes ultra-rápido de Python:

```bash
# Sincronizar el entorno virtual e instalar todas las dependencias
uv sync --all-groups
```

### 2. Configurar Variables de Entorno
Copia el archivo `.env.example` a `.env`:
```bash
cp .env.example .env
```
*(Por defecto, la base de datos se configura automáticamente con SQLite asíncrono en `./tasksphere.db` para pruebas inmediatas sin configurar servicios externos).*

### 3. Poblar Datos de Demostración (Opcional)
Utiliza la CLI incluida para sembrar usuarios, proyectos y tareas de prueba:
```bash
uv run enterprise-cli seed-demo
```

### 4. Iniciar el Servidor de Desarrollo
```bash
uv run enterprise-cli run-server
# o directamente:
uv run uvicorn enterprise_api.main:app --reload --port 8000
```

Visita en tu navegador:
- 📖 **Swagger UI interactivo**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 📑 **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- 🩺 **Probe de Salud**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

## 🛠️ Comandos de la CLI (`enterprise-cli`)

La herramienta CLI proporciona utilidades operacionales con interfaz enriquecida en la terminal:

```bash
# Ver información del sistema y base de datos
uv run enterprise-cli info

# Crear un nuevo administrador
uv run enterprise-cli create-admin --email admin@tuempresa.com --password MiPasswordSeguro123! --full-name "Admin Principal"

# Poblar el dataset de demostración
uv run enterprise-cli seed-demo

# Iniciar servidor
uv run enterprise-cli run-server --port 8000
```

---

## 🧪 Pruebas Automatizadas y Calidad de Código

### Ejecutar Suite de Pruebas con Cobertura
```bash
uv run pytest
```
*Se evalúan 18 pruebas asíncronas con base de datos en memoria, garantizando más del 80% de cobertura.*

### Inspeccionar Reporte HTML de Cobertura
```bash
# Abrir el reporte visual generado en htmlcov/index.html
start htmlcov/index.html   # en Windows
```

### Linter y Formateador (Ruff)
```bash
# Verificar calidad de código y adherencia a estándares
uv run ruff check .

# Verificar formato de código
uv run ruff format --check .
```

---

## 🐳 Despliegue con Docker y PostgreSQL

Para ejecutar la solución completa en contenedores de producción con PostgreSQL 16:

```bash
# Construir e iniciar contenedores en segundo plano
docker compose up -d --build

# Consultar logs de la API
docker compose logs -f api

# Detener los servicios
docker compose down
```

---

## 👥 Credenciales de Prueba por Defecto

| Rol | Correo Electrónico | Contraseña | Permisos |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin@tasksphere.io` | `AdminSecurePass123!` | Control total, auditoría, usuarios |
| **Project Manager** | `pm@tasksphere.io` | `Password123!` | Crear proyectos, asignar tareas |
| **Developer / Miembro** | `dev@tasksphere.io` | `Password123!` | Actualizar estado de sus tareas |

---

## 📄 Licencia
Este proyecto está licenciado bajo los términos de la licencia **MIT**.
