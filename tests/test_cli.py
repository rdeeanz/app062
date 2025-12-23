"""
CLI Tests
Unit tests for the Project Management CLI.
"""
import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, '.')

from src.models.project import ProjectCreate, ProjectFinance, ProjectRealisasi
from src.utils.validators import (
    validate_financial_data,
    validate_date_consistency,
    validate_required_fields,
    validate_project,
    format_currency,
    format_percentage
)


class TestProjectModels:
    """Test Pydantic models."""
    
    def test_project_create_valid(self):
        """Test valid project creation."""
        project = ProjectCreate(
            id_root="TEST001",
            klaster_regional="Regional 2",
            entitas_terminal="Terminal A",
            type_investasi="Murni",
            tahun_rkap=2025
        )
        
        assert project.id_root == "TEST001"
        assert project.klaster_regional == "Regional 2"
        assert project.type_investasi == "Murni"
    
    def test_project_create_defaults(self):
        """Test project creation with defaults."""
        project = ProjectCreate(id_root="TEST002")
        
        assert project.klaster_regional == "Regional 2"
        assert project.tahun_rkap == 2025
    
    def test_project_finance_defaults(self):
        """Test financial model defaults."""
        finance = ProjectFinance()
        
        assert finance.rkap == Decimal('0')
        assert finance.kebutuhan_dana == Decimal('0')
        assert finance.rkap_januari == Decimal('0')
    
    def test_project_realisasi_total(self):
        """Test realisasi total calculation."""
        realisasi = ProjectRealisasi(
            realisasi_januari=Decimal('100'),
            realisasi_februari=Decimal('200'),
            realisasi_maret=Decimal('300')
        )
        
        assert realisasi.total == Decimal('600')


class TestValidators:
    """Test validation utilities."""
    
    def test_validate_required_fields_valid(self):
        """Test required fields validation with valid data."""
        project = {'id_root': 'TEST001'}
        is_valid, issues = validate_required_fields(project)
        
        assert is_valid
        assert len(issues) == 0
    
    def test_validate_required_fields_missing(self):
        """Test required fields validation with missing data."""
        project = {}
        is_valid, issues = validate_required_fields(project)
        
        assert not is_valid
        assert len(issues) == 1
        assert "[ERROR]" in issues[0]
    
    def test_validate_financial_data_consistent(self):
        """Test financial validation with consistent data."""
        project = {
            'id_root': 'TEST001',
            'rkap': Decimal('1000'),
            'rkap_januari': Decimal('500'),
            'rkap_februari': Decimal('500'),
            'realisasi_januari': Decimal('400')
        }
        is_valid, issues = validate_financial_data(project)
        
        assert is_valid
    
    def test_validate_financial_data_mismatch(self):
        """Test financial validation with mismatched totals."""
        project = {
            'id_root': 'TEST001',
            'rkap': Decimal('1000'),
            'rkap_januari': Decimal('100'),
            'rkap_februari': Decimal('100')
        }
        is_valid, issues = validate_financial_data(project)
        
        # Should have warning about mismatch
        assert any('doesn\'t match' in issue for issue in issues)
    
    def test_validate_date_consistency_valid(self):
        """Test date validation with valid dates."""
        project = {
            'tanggal_kontrak': date(2025, 1, 1),
            'tgl_mulai_kontrak': date(2025, 1, 15),
            'tanggal_selesai': date(2025, 12, 31)
        }
        is_valid, issues = validate_date_consistency(project)
        
        assert is_valid
        assert len(issues) == 0
    
    def test_validate_date_consistency_invalid(self):
        """Test date validation with end before start."""
        project = {
            'tgl_mulai_kontrak': date(2025, 12, 31),
            'tanggal_selesai': date(2025, 1, 1)
        }
        is_valid, issues = validate_date_consistency(project)
        
        assert not is_valid
        assert any('[ERROR]' in issue for issue in issues)
    
    def test_format_currency(self):
        """Test currency formatting."""
        result = format_currency(1000000)
        assert 'Rp' in result
        assert '1' in result
    
    def test_format_currency_none(self):
        """Test currency formatting with None."""
        result = format_currency(None)
        assert result == "Rp 0"
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        result = format_percentage(50, 100)
        assert result == "50.0%"
    
    def test_format_percentage_zero_total(self):
        """Test percentage formatting with zero total."""
        result = format_percentage(50, 0)
        assert result == "0%"


class TestProjectValidation:
    """Test complete project validation."""
    
    def test_validate_project_valid(self):
        """Test validation on valid project."""
        project = {
            'id_root': 'TEST001',
            'rkap': Decimal('0'),
            'nilai_kontrak': Decimal('0')
        }
        is_valid, issues = validate_project(project)
        
        assert is_valid
    
    def test_validate_project_multiple_issues(self):
        """Test validation with multiple issues."""
        project = {
            # Missing id_root
            'rkap': Decimal('1000'),
            'rkap_januari': Decimal('100'),  # Mismatch
            'tgl_mulai_kontrak': date(2025, 12, 31),
            'tanggal_selesai': date(2025, 1, 1)  # End before start
        }
        is_valid, issues = validate_project(project)
        
        assert not is_valid
        assert len(issues) >= 2


class TestDatabaseOperations:
    """Test database operations with mocks."""
    
    @patch('src.db.postgres.psycopg2.connect')
    def test_postgres_connection(self, mock_connect):
        """Test PostgreSQL connection."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        from src.db.postgres import PostgresDB
        db = PostgresDB()
        
        assert db.config['database'] == 'project_mgmt'
    
    @patch('src.db.clickhouse.Client')
    def test_clickhouse_connection(self, mock_client):
        """Test ClickHouse connection."""
        from src.db.clickhouse import ClickHouseDB
        db = ClickHouseDB()
        
        assert db.config['database'] == 'project_mgmt'


# ===========================================
# Run Tests
# ===========================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
