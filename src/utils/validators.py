"""
Data Validators
Utility functions for validating project data.
"""
from decimal import Decimal
from typing import Any, Dict, List, Tuple

from rich.console import Console
from rich.table import Table

console = Console()


def validate_financial_data(project: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate financial data consistency.
    
    Checks:
    1. RKAP total matches sum of monthly RKAP
    2. Realisasi doesn't exceed RKAP (warning only)
    3. Contract value consistency
    
    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []
    
    # Calculate total monthly RKAP
    rkap_fields = [
        'rkap_januari', 'rkap_februari', 'rkap_maret', 'rkap_april',
        'rkap_mei', 'rkap_juni', 'rkap_juli', 'rkap_agustus',
        'rkap_september', 'rkap_oktober', 'rkap_november', 'rkap_desember'
    ]
    
    total_rkap_bulanan = sum(
        Decimal(str(project.get(field) or 0))
        for field in rkap_fields
    )
    
    rkap = Decimal(str(project.get('rkap') or 0))
    
    # Check RKAP consistency
    if rkap > 0 and total_rkap_bulanan > 0:
        diff = abs(rkap - total_rkap_bulanan)
        if diff > Decimal('0.01'):  # Allow small rounding errors
            issues.append(
                f"RKAP total ({rkap:,.2f}) doesn't match sum of monthly "
                f"({total_rkap_bulanan:,.2f}), diff: {diff:,.2f}"
            )
    
    # Calculate total realisasi
    realisasi_fields = [
        'realisasi_januari', 'realisasi_februari', 'realisasi_maret',
        'realisasi_april', 'realisasi_mei', 'realisasi_juni',
        'realisasi_juli', 'realisasi_agustus', 'realisasi_september',
        'realisasi_oktober', 'realisasi_november', 'realisasi_desember'
    ]
    
    total_realisasi = sum(
        Decimal(str(project.get(field) or 0))
        for field in realisasi_fields
    )
    
    # Check realisasi vs RKAP (warning)
    if rkap > 0 and total_realisasi > rkap:
        issues.append(
            f"[WARNING] Realisasi ({total_realisasi:,.2f}) exceeds RKAP ({rkap:,.2f})"
        )
    
    # Check contract value
    nilai_kontrak = Decimal(str(project.get('nilai_kontrak') or 0))
    if nilai_kontrak > 0 and rkap > 0 and nilai_kontrak > rkap * Decimal('1.1'):
        issues.append(
            f"[WARNING] Contract value ({nilai_kontrak:,.2f}) is significantly "
            f"higher than RKAP ({rkap:,.2f})"
        )
    
    is_valid = not any('[ERROR]' in issue for issue in issues)
    return is_valid, issues


def validate_date_consistency(project: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate date field consistency.
    
    Checks:
    1. Contract end date is after start date
    2. Contract dates are reasonable
    """
    issues = []
    
    tanggal_kontrak = project.get('tanggal_kontrak')
    tgl_mulai = project.get('tgl_mulai_kontrak')
    tgl_selesai = project.get('tanggal_selesai')
    
    if tgl_mulai and tgl_selesai:
        if tgl_selesai < tgl_mulai:
            issues.append("[ERROR] Contract end date is before start date")
    
    if tanggal_kontrak and tgl_mulai:
        if tgl_mulai < tanggal_kontrak:
            issues.append("[WARNING] Contract start date is before contract signing date")
    
    is_valid = not any('[ERROR]' in issue for issue in issues)
    return is_valid, issues


def validate_required_fields(project: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that required fields are present.
    """
    issues = []
    
    required_fields = ['id_root']
    
    for field in required_fields:
        if not project.get(field):
            issues.append(f"[ERROR] Required field '{field}' is missing")
    
    is_valid = len(issues) == 0
    return is_valid, issues


def validate_project(project: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Run all validations on a project.
    
    Returns:
        Tuple of (is_valid, list of all issues)
    """
    all_issues = []
    overall_valid = True
    
    # Required fields
    valid, issues = validate_required_fields(project)
    overall_valid = overall_valid and valid
    all_issues.extend(issues)
    
    # Financial validation
    valid, issues = validate_financial_data(project)
    overall_valid = overall_valid and valid
    all_issues.extend(issues)
    
    # Date validation
    valid, issues = validate_date_consistency(project)
    overall_valid = overall_valid and valid
    all_issues.extend(issues)
    
    return overall_valid, all_issues


def print_validation_report(projects: List[Dict[str, Any]]) -> None:
    """
    Print a validation report for multiple projects.
    """
    console.print("\n[bold]Validation Report[/bold]\n")
    
    total_valid = 0
    total_invalid = 0
    all_issues = []
    
    for project in projects:
        id_root = project.get('id_root', 'Unknown')
        valid, issues = validate_project(project)
        
        if valid:
            total_valid += 1
        else:
            total_invalid += 1
            for issue in issues:
                all_issues.append((id_root, issue))
    
    # Summary table
    table = Table(title="Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right")
    
    table.add_row("Total Projects", str(len(projects)))
    table.add_row("Valid", f"[green]{total_valid}[/green]")
    table.add_row("With Issues", f"[yellow]{total_invalid}[/yellow]")
    
    console.print(table)
    
    # Issues table
    if all_issues:
        console.print("\n[bold]Issues Found:[/bold]\n")
        
        issues_table = Table()
        issues_table.add_column("Project ID", style="cyan")
        issues_table.add_column("Issue")
        
        for id_root, issue in all_issues[:50]:  # Limit to 50 issues
            style = "red" if "[ERROR]" in issue else "yellow"
            issues_table.add_row(id_root, f"[{style}]{issue}[/{style}]")
        
        console.print(issues_table)
        
        if len(all_issues) > 50:
            console.print(f"\n... and {len(all_issues) - 50} more issues")


def format_currency(value: Any) -> str:
    """Format a value as Indonesian Rupiah."""
    if value is None:
        return "Rp 0"
    
    try:
        num = Decimal(str(value))
        return f"Rp {num:,.2f}".replace(',', '.')
    except:
        return str(value)


def format_percentage(value: Any, total: Any) -> str:
    """Format a percentage."""
    if not total or total == 0:
        return "0%"
    
    try:
        pct = (Decimal(str(value)) / Decimal(str(total))) * 100
        return f"{pct:.1f}%"
    except:
        return "N/A"
