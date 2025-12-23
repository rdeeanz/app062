#!/usr/bin/env python3
"""
Project Management CLI
Main entry point for database management operations.

Usage:
    python cli.py --help
    python cli.py add-project
    python cli.py list-projects
    python cli.py update-progress --id_root=123
    python cli.py update-realisasi --bulan=mei --id_root=123 --nilai=1000000
    python cli.py sync-clickhouse
    python cli.py validate
"""
import sys
from datetime import date
from decimal import Decimal
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

# Add src to path for imports
sys.path.insert(0, '.')

from src.db.postgres import db as pg_db
from src.db.clickhouse import ch_db
from src.etl.sync import sync, verify_sync
from src.utils.validators import validate_project, print_validation_report

app = typer.Typer(
    name="pm-cli",
    help="Project Management CLI - Database management for investment projects",
    add_completion=False
)
console = Console()

# ===========================================
# Health Check Commands
# ===========================================

@app.command()
def health():
    """Check database connections health."""
    console.print("\n[bold]Database Health Check[/bold]\n")
    
    # PostgreSQL
    pg_status = pg_db.test_connection()
    pg_icon = "✓" if pg_status else "✗"
    pg_color = "green" if pg_status else "red"
    console.print(f"  PostgreSQL: [{pg_color}]{pg_icon}[/{pg_color}]")
    
    # ClickHouse
    ch_status = ch_db.test_connection()
    ch_icon = "✓" if ch_status else "✗"
    ch_color = "green" if ch_status else "red"
    console.print(f"  ClickHouse: [{ch_color}]{ch_icon}[/{ch_color}]")
    
    console.print()
    
    if pg_status and ch_status:
        console.print("[bold green]All systems operational![/bold green]")
        raise typer.Exit(0)
    else:
        console.print("[bold red]Some services are down.[/bold red]")
        raise typer.Exit(1)


# ===========================================
# Project CRUD Commands
# ===========================================

@app.command()
def add_project(
    interactive: bool = typer.Option(True, "--interactive", "-i", help="Interactive mode"),
    id_root: Optional[str] = typer.Option(None, help="Project ID"),
    klaster_regional: str = typer.Option("Regional 2", help="Regional cluster"),
    entitas_terminal: Optional[str] = typer.Option(None, help="Terminal entity"),
    project_definition: Optional[str] = typer.Option(None, help="Project definition"),
    type_investasi: Optional[str] = typer.Option(None, help="Investment type: Murni/Multi Year/Carry Forward"),
    tahun_rkap: int = typer.Option(2025, help="RKAP year"),
):
    """Add a new project to the database."""
    if interactive:
        console.print("\n[bold]Add New Project[/bold]\n")
        
        id_root = Prompt.ask("Project ID (id_root)", default=id_root or "")
        if not id_root:
            console.print("[red]Project ID is required.[/red]")
            raise typer.Exit(1)
        
        klaster_regional = Prompt.ask("Klaster Regional", default=klaster_regional)
        entitas_terminal = Prompt.ask("Entitas Terminal", default=entitas_terminal or "")
        project_definition = Prompt.ask("Project Definition", default=project_definition or "")
        
        type_choices = ["Murni", "Multi Year", "Carry Forward"]
        console.print(f"\nType Investasi options: {', '.join(type_choices)}")
        type_investasi = Prompt.ask("Type Investasi", default=type_investasi or "Murni")
        
        tahun_rkap = int(Prompt.ask("Tahun RKAP", default=str(tahun_rkap)))
        
        # Financial data
        console.print("\n[bold cyan]Financial Data (optional, press Enter to skip)[/bold cyan]")
        rkap = Prompt.ask("RKAP (Total)", default="0")
        kebutuhan_dana = Prompt.ask("Kebutuhan Dana", default="0")
    
    else:
        if not id_root:
            console.print("[red]--id_root is required in non-interactive mode.[/red]")
            raise typer.Exit(1)
        rkap = "0"
        kebutuhan_dana = "0"
    
    # Build project data
    project_data = {
        'id_root': id_root,
        'klaster_regional': klaster_regional,
        'entitas_terminal': entitas_terminal or None,
        'project_definition': project_definition or None,
        'type_investasi': type_investasi if type_investasi in ('Murni', 'Multi Year', 'Carry Forward') else None,
        'tahun_rkap': tahun_rkap,
        'rkap': Decimal(rkap) if rkap else Decimal('0'),
        'kebutuhan_dana': Decimal(kebutuhan_dana) if kebutuhan_dana else Decimal('0'),
    }
    
    try:
        result_id = pg_db.insert_project(project_data)
        console.print(f"\n[bold green]✓ Project created successfully![/bold green]")
        console.print(f"  ID: {result_id}")
    except Exception as e:
        console.print(f"\n[bold red]✗ Error creating project: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def list_projects(
    klaster: Optional[str] = typer.Option(None, "--klaster", "-k", help="Filter by klaster regional"),
    terminal: Optional[str] = typer.Option(None, "--terminal", "-t", help="Filter by terminal"),
    tahun: Optional[int] = typer.Option(None, "--tahun", "-y", help="Filter by RKAP year"),
    status_issue: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by issue status (Open/Closed)"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of results"),
):
    """List projects with optional filters."""
    console.print("\n[bold]Project List[/bold]\n")
    
    try:
        projects = pg_db.list_projects(
            klaster_regional=klaster,
            entitas_terminal=terminal,
            tahun_rkap=tahun,
            status_issue=status_issue,
            limit=limit
        )
        
        if not projects:
            console.print("[yellow]No projects found.[/yellow]")
            return
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Regional")
        table.add_column("Terminal")
        table.add_column("Type")
        table.add_column("Tahun")
        table.add_column("RKAP", justify="right")
        table.add_column("Issue")
        
        for p in projects:
            rkap = f"Rp {p.get('rkap', 0):,.0f}" if p.get('rkap') else "-"
            table.add_row(
                str(p.get('id_root', '')),
                str(p.get('klaster_regional', '') or ''),
                str(p.get('entitas_terminal', '') or '-')[:20],
                str(p.get('type_investasi', '') or '-'),
                str(p.get('tahun_rkap', '')),
                rkap,
                str(p.get('status_issue', '') or '-')
            )
        
        console.print(table)
        console.print(f"\n[dim]Showing {len(projects)} projects[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def get_project(
    id_root: str = typer.Argument(..., help="Project ID to retrieve")
):
    """Get detailed information for a specific project."""
    try:
        project = pg_db.get_project(id_root)
        
        if not project:
            console.print(f"[yellow]Project '{id_root}' not found.[/yellow]")
            raise typer.Exit(1)
        
        # Display in panels
        console.print(f"\n[bold]Project: {id_root}[/bold]\n")
        
        # Basic info
        basic = Table(show_header=False, box=None)
        basic.add_column("Field", style="cyan")
        basic.add_column("Value")
        
        basic.add_row("Klaster Regional", str(project.get('klaster_regional', '')))
        basic.add_row("Entitas Terminal", str(project.get('entitas_terminal', '') or '-'))
        basic.add_row("Project Definition", str(project.get('project_definition', '') or '-')[:100])
        basic.add_row("Type Investasi", str(project.get('type_investasi', '') or '-'))
        basic.add_row("Tahun RKAP", str(project.get('tahun_rkap', '')))
        basic.add_row("Status Investasi", str(project.get('status_investasi', '') or '-'))
        
        console.print(Panel(basic, title="Basic Information"))
        
        # Financial info
        finance = Table(show_header=False, box=None)
        finance.add_column("Field", style="cyan")
        finance.add_column("Value", justify="right")
        
        finance.add_row("RKAP", f"Rp {project.get('rkap', 0):,.2f}")
        finance.add_row("Kebutuhan Dana", f"Rp {project.get('kebutuhan_dana', 0):,.2f}")
        finance.add_row("Nilai Kontrak", f"Rp {project.get('nilai_kontrak', 0):,.2f}")
        
        # Calculate total realisasi
        realisasi_fields = [
            'realisasi_januari', 'realisasi_februari', 'realisasi_maret',
            'realisasi_april', 'realisasi_mei', 'realisasi_juni',
            'realisasi_juli', 'realisasi_agustus', 'realisasi_september',
            'realisasi_oktober', 'realisasi_november', 'realisasi_desember'
        ]
        total_realisasi = sum(Decimal(str(project.get(f) or 0)) for f in realisasi_fields)
        finance.add_row("Total Realisasi", f"Rp {total_realisasi:,.2f}")
        
        console.print(Panel(finance, title="Financial Information"))
        
        # Issue info
        if project.get('issue_description'):
            issue = Table(show_header=False, box=None)
            issue.add_column("Field", style="cyan")
            issue.add_column("Value")
            
            issue.add_row("Status", str(project.get('status_issue', '') or '-'))
            issue.add_row("Category", str(project.get('issue_categories', '') or '-'))
            issue.add_row("Description", str(project.get('issue_description', '') or '-')[:200])
            issue.add_row("PIC", str(project.get('pic', '') or '-'))
            
            console.print(Panel(issue, title="Issue Information"))
        
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def delete_project(
    id_root: str = typer.Argument(..., help="Project ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete a project from the database."""
    if not force:
        if not Confirm.ask(f"Are you sure you want to delete project '{id_root}'?"):
            console.print("Cancelled.")
            raise typer.Exit(0)
    
    try:
        success = pg_db.delete_project(id_root)
        
        if success:
            console.print(f"[bold green]✓ Project '{id_root}' deleted successfully.[/bold green]")
        else:
            console.print(f"[yellow]Project '{id_root}' not found.[/yellow]")
            raise typer.Exit(1)
            
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)


# ===========================================
# Progress & Issue Commands
# ===========================================

@app.command()
def update_progress(
    id_root: str = typer.Argument(..., help="Project ID"),
    progres: Optional[str] = typer.Option(None, "--progres", "-p", help="Progress description"),
    issue_cat: Optional[str] = typer.Option(None, "--issue-cat", help="Issue category"),
    issue_desc: Optional[str] = typer.Option(None, "--issue-desc", help="Issue description"),
    action: Optional[str] = typer.Option(None, "--action", "-a", help="Action target"),
    pic: Optional[str] = typer.Option(None, "--pic", help="Person in charge"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Issue status (Open/Closed)"),
):
    """Update project progress and issue information."""
    
    if status and status not in ('Open', 'Closed'):
        console.print("[red]Status must be 'Open' or 'Closed'[/red]")
        raise typer.Exit(1)
    
    try:
        success = pg_db.update_progress(
            id_root=id_root,
            progres_description=progres,
            issue_categories=issue_cat,
            issue_description=issue_desc,
            action_target=action,
            pic=pic,
            status_issue=status
        )
        
        if success:
            console.print(f"[bold green]✓ Progress updated for project '{id_root}'[/bold green]")
        else:
            console.print(f"[yellow]Project '{id_root}' not found or no changes made.[/yellow]")
            
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)


# ===========================================
# Financial Update Commands
# ===========================================

@app.command()
def update_realisasi(
    id_root: str = typer.Argument(..., help="Project ID"),
    bulan: str = typer.Argument(..., help="Month (januari-desember)"),
    nilai: float = typer.Argument(..., help="Realization value"),
):
    """Update monthly realization value for a project."""
    try:
        success = pg_db.update_realisasi(id_root, bulan, Decimal(str(nilai)))
        
        if success:
            console.print(f"[bold green]✓ Realisasi {bulan} updated to Rp {nilai:,.2f}[/bold green]")
        else:
            console.print(f"[yellow]Project '{id_root}' not found.[/yellow]")
            raise typer.Exit(1)
            
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def update_prognosa(
    id_root: str = typer.Argument(..., help="Project ID"),
    bulan: str = typer.Argument(..., help="Month (januari-desember)"),
    nilai: float = typer.Argument(..., help="Prognosis value"),
):
    """Update monthly prognosis value for a project."""
    try:
        success = pg_db.update_prognosa(id_root, bulan, Decimal(str(nilai)))
        
        if success:
            console.print(f"[bold green]✓ Prognosa {bulan} updated to Rp {nilai:,.2f}[/bold green]")
        else:
            console.print(f"[yellow]Project '{id_root}' not found.[/yellow]")
            raise typer.Exit(1)
            
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def update_rkap(
    id_root: str = typer.Argument(..., help="Project ID"),
    bulan: str = typer.Argument(..., help="Month (januari-desember)"),
    nilai: float = typer.Argument(..., help="RKAP value"),
):
    """Update monthly RKAP value for a project."""
    try:
        success = pg_db.update_rkap(id_root, bulan, Decimal(str(nilai)))
        
        if success:
            console.print(f"[bold green]✓ RKAP {bulan} updated to Rp {nilai:,.2f}[/bold green]")
        else:
            console.print(f"[yellow]Project '{id_root}' not found.[/yellow]")
            raise typer.Exit(1)
            
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)


# ===========================================
# ETL & Sync Commands
# ===========================================

@app.command()
def sync_clickhouse(
    full: bool = typer.Option(False, "--full", "-f", help="Force full sync (truncate and reload)")
):
    """Sync data from PostgreSQL to ClickHouse."""
    try:
        count = sync(full=full)
        console.print(f"\n[bold green]Sync completed: {count} projects synced.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Sync failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def verify():
    """Verify that PostgreSQL and ClickHouse are in sync."""
    try:
        is_synced = verify_sync()
        raise typer.Exit(0 if is_synced else 1)
    except Exception as e:
        console.print(f"[bold red]Verification failed: {e}[/bold red]")
        raise typer.Exit(1)


# ===========================================
# Validation Commands
# ===========================================

@app.command()
def validate(
    limit: int = typer.Option(100, "--limit", "-l", help="Number of projects to validate")
):
    """Validate data integrity for all projects."""
    try:
        projects = pg_db.list_projects(limit=limit)
        
        if not projects:
            console.print("[yellow]No projects to validate.[/yellow]")
            return
        
        # Get full project data for validation
        full_projects = []
        for p in projects:
            full = pg_db.get_project(p['id_root'])
            if full:
                full_projects.append(full)
        
        print_validation_report(full_projects)
        
    except Exception as e:
        console.print(f"[bold red]Validation failed: {e}[/bold red]")
        raise typer.Exit(1)


# ===========================================
# Analytics Commands
# ===========================================

@app.command()
def summary(
    tahun: Optional[int] = typer.Option(None, "--tahun", "-y", help="Filter by RKAP year")
):
    """Show summary statistics by regional."""
    try:
        data = pg_db.get_summary_by_regional(tahun_rkap=tahun)
        
        if not data:
            console.print("[yellow]No data found.[/yellow]")
            return
        
        console.print(f"\n[bold]Summary by Regional{f' (Tahun {tahun})' if tahun else ''}[/bold]\n")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Regional")
        table.add_column("Projects", justify="right")
        table.add_column("Total RKAP", justify="right")
        table.add_column("Total Realisasi", justify="right")
        table.add_column("Serapan %", justify="right")
        table.add_column("Open Issues", justify="right")
        
        for row in data:
            rkap = row.get('total_rkap') or 0
            realisasi = row.get('total_realisasi') or 0
            serapan = (realisasi / rkap * 100) if rkap > 0 else 0
            
            table.add_row(
                str(row.get('klaster_regional', '')),
                str(row.get('project_count', 0)),
                f"Rp {rkap:,.0f}",
                f"Rp {realisasi:,.0f}",
                f"{serapan:.1f}%",
                str(row.get('open_issues', 0))
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(1)


# ===========================================
# Main Entry Point
# ===========================================

if __name__ == "__main__":
    app()
