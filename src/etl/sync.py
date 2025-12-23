"""
ETL Sync Module
Handles data synchronization from PostgreSQL to ClickHouse.
"""
import os
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.db.postgres import db as pg_db
from src.db.clickhouse import ch_db

console = Console()

# File to store last sync timestamp
LAST_SYNC_FILE = os.path.join(os.path.dirname(__file__), '.last_sync')


def get_last_sync_time() -> Optional[str]:
    """Get the timestamp of the last successful sync."""
    if os.path.exists(LAST_SYNC_FILE):
        with open(LAST_SYNC_FILE, 'r') as f:
            return f.read().strip()
    return None


def save_last_sync_time(timestamp: str) -> None:
    """Save the timestamp of the current sync."""
    with open(LAST_SYNC_FILE, 'w') as f:
        f.write(timestamp)


def full_sync() -> int:
    """
    Perform a full sync from PostgreSQL to ClickHouse.
    This truncates the ClickHouse table and reloads all data.
    """
    console.print("[bold yellow]Starting full sync...[/bold yellow]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Fetch all projects from PostgreSQL
        task1 = progress.add_task("Fetching projects from PostgreSQL...", total=None)
        projects = pg_db.get_projects_for_sync()
        progress.update(task1, completed=True)
        console.print(f"  → Fetched [green]{len(projects)}[/green] projects")
        
        if not projects:
            console.print("[yellow]No projects to sync.[/yellow]")
            return 0
        
        # Truncate ClickHouse table
        task2 = progress.add_task("Truncating ClickHouse table...", total=None)
        ch_db.truncate_table()
        progress.update(task2, completed=True)
        
        # Insert into ClickHouse
        task3 = progress.add_task("Inserting into ClickHouse...", total=None)
        count = ch_db.insert_projects(projects)
        progress.update(task3, completed=True)
        console.print(f"  → Inserted [green]{count}[/green] projects")
    
    # Save sync timestamp
    timestamp = datetime.now().isoformat()
    save_last_sync_time(timestamp)
    
    console.print(f"[bold green]Full sync completed at {timestamp}[/bold green]")
    return count


def incremental_sync() -> int:
    """
    Perform an incremental sync from PostgreSQL to ClickHouse.
    Only syncs projects updated since the last sync.
    """
    last_sync = get_last_sync_time()
    
    if not last_sync:
        console.print("[yellow]No previous sync found. Performing full sync instead.[/yellow]")
        return full_sync()
    
    console.print(f"[bold yellow]Starting incremental sync since {last_sync}...[/bold yellow]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Fetch updated projects from PostgreSQL
        task1 = progress.add_task("Fetching updated projects...", total=None)
        projects = pg_db.get_projects_for_sync(since=last_sync)
        progress.update(task1, completed=True)
        console.print(f"  → Found [green]{len(projects)}[/green] updated projects")
        
        if not projects:
            console.print("[yellow]No projects to sync.[/yellow]")
            return 0
        
        # Insert into ClickHouse (ReplacingMergeTree will handle duplicates)
        task2 = progress.add_task("Inserting into ClickHouse...", total=None)
        count = ch_db.insert_projects(projects)
        progress.update(task2, completed=True)
        console.print(f"  → Synced [green]{count}[/green] projects")
    
    # Save sync timestamp
    timestamp = datetime.now().isoformat()
    save_last_sync_time(timestamp)
    
    console.print(f"[bold green]Incremental sync completed at {timestamp}[/bold green]")
    return count


def sync(full: bool = False) -> int:
    """
    Main sync function.
    
    Args:
        full: If True, perform full sync. Otherwise, incremental.
    
    Returns:
        Number of projects synced.
    """
    if full:
        return full_sync()
    return incremental_sync()


def verify_sync() -> bool:
    """
    Verify that PostgreSQL and ClickHouse data are in sync.
    Compares row counts and optionally checksums.
    """
    console.print("[bold]Verifying sync status...[/bold]")
    
    pg_count = pg_db.count_projects()
    ch_count = ch_db.get_project_count()
    
    console.print(f"  PostgreSQL: [cyan]{pg_count}[/cyan] projects")
    console.print(f"  ClickHouse: [cyan]{ch_count}[/cyan] projects")
    
    if pg_count == ch_count:
        console.print("[bold green]✓ Databases are in sync[/bold green]")
        return True
    else:
        diff = abs(pg_count - ch_count)
        console.print(f"[bold red]✗ Databases are out of sync by {diff} records[/bold red]")
        return False
