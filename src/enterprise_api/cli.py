"""Interactive developer and operational CLI built with Typer and Rich."""

import asyncio

import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from enterprise_api.core.config import settings
from enterprise_api.core.database import AsyncSessionLocal, engine
from enterprise_api.core.security import hash_password
from enterprise_api.models import Base, Project, Task, User
from enterprise_api.models.enums import ProjectStatus, TaskPriority, TaskStatus, UserRole
from enterprise_api.repositories.user_repository import UserRepository

app = typer.Typer(
    name="enterprise-cli",
    help="Enterprise Task Orchestrator Management CLI",
    add_completion=False,
)
console = Console()


@app.command()
def info() -> None:
    """Show system configuration and operational status."""
    table = Table(
        title="Enterprise Task API Environment", show_header=True, header_style="bold cyan"
    )
    table.add_column("Parameter", style="dim", width=25)
    table.add_column("Value", style="bold green")

    table.add_row("Application Name", settings.APP_NAME)
    table.add_row("Version", settings.APP_VERSION)
    table.add_row("Environment", settings.ENVIRONMENT)
    table.add_row("Database Dialect", settings.DATABASE_URL.split("://")[0])
    table.add_row("API Prefix", settings.API_V1_PREFIX)
    table.add_row("Default Bind", f"{settings.HOST}:{settings.PORT}")

    console.print(
        Panel.fit(table, title="[bold white]System Info[/bold white]", border_style="blue")
    )


@app.command()
def run_server(
    host: str = typer.Option(settings.HOST, help="Bind host address"),
    port: int = typer.Option(settings.PORT, help="Bind port number"),
    reload: bool = typer.Option(True, help="Enable auto-reload on file changes"),
) -> None:
    """Start the Uvicorn ASGI development server."""
    console.print(
        f"[bold green]Starting {settings.APP_NAME} server on [cyan]http://{host}:{port}[/cyan] ...[/bold green]"
    )
    console.print(
        f"[bold yellow]OpenAPI Documentation available at: [cyan]http://{host}:{port}/docs[/cyan][/bold yellow]"
    )
    uvicorn.run("enterprise_api.main:app", host=host, port=port, reload=reload)


async def _create_admin_async(email: str, password: str, full_name: str) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        existing = await user_repo.get_by_email(email)
        if existing:
            console.print(f"[bold red]User with email '{email}' already exists![/bold red]")
            return

        admin = User(
            email=email.lower().strip(),
            full_name=full_name.strip(),
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        console.print(f"[bold green]Admin account created successfully:[/bold green] {email}")


@app.command()
def create_admin(
    email: str = typer.Option(..., prompt=True, help="Admin email address"),
    password: str = typer.Option(..., prompt=True, hide_input=True, help="Admin password"),
    full_name: str = typer.Option("Admin User", prompt=True, help="Full display name"),
) -> None:
    """Create a new superuser administrator account."""
    asyncio.run(_create_admin_async(email, password, full_name))


async def _seed_demo_async() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        user_repo = UserRepository(session)
        if await user_repo.get_by_email("pm@tasksphere.io"):
            console.print("[bold yellow]Demo data already exists in database.[/bold yellow]")
            return

        console.print("[cyan]Seeding demo users, projects and tasks...[/cyan]")

        # 1. Users
        pm = User(
            email="pm@tasksphere.io",
            full_name="Sarah Connor",
            hashed_password=hash_password("Password123!"),
            role=UserRole.MANAGER,
            is_active=True,
        )
        dev = User(
            email="dev@tasksphere.io",
            full_name="Alex Murphy",
            hashed_password=hash_password("Password123!"),
            role=UserRole.MEMBER,
            is_active=True,
        )
        session.add_all([pm, dev])
        await session.flush()

        # 2. Project
        project = Project(
            title="Cloud Migration 2026",
            slug="cloud-migration-2026",
            description="Migrate mission-critical services from legacy on-prem to Kubernetes cloud cluster.",
            status=ProjectStatus.ACTIVE,
            owner_id=pm.id,
        )
        session.add(project)
        await session.flush()

        # 3. Tasks
        tasks = [
            Task(
                title="Design Terraform Infrastructure Modules",
                description="Write reproducible HCL for VPC, EKS/GKE cluster and IAM roles.",
                status=TaskStatus.COMPLETED,
                priority=TaskPriority.HIGH,
                project_id=project.id,
                creator_id=pm.id,
                assignee_id=dev.id,
            ),
            Task(
                title="Implement CI/CD GitHub Actions Workflow",
                description="Automate linting, testing, Docker image building and registry push.",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.CRITICAL,
                project_id=project.id,
                creator_id=pm.id,
                assignee_id=dev.id,
            ),
            Task(
                title="Zero-downtime Database Cutover Runbook",
                description="Draft dual-write replication and failover test procedures.",
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                project_id=project.id,
                creator_id=pm.id,
                assignee_id=pm.id,
            ),
        ]
        session.add_all(tasks)
        await session.commit()

        console.print("[bold green]Demo dataset seeded successfully![/bold green]")
        console.print(
            "  - Manager: [cyan]pm@tasksphere.io[/cyan] (Password: [cyan]Password123![/cyan])"
        )
        console.print(
            "  - Developer: [cyan]dev@tasksphere.io[/cyan] (Password: [cyan]Password123![/cyan])"
        )


@app.command()
def seed_demo() -> None:
    """Populate database with rich enterprise demo data."""
    asyncio.run(_seed_demo_async())


if __name__ == "__main__":
    app()
