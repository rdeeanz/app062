"""
ClickHouse Database Operations
Handles all ClickHouse connections for analytics.
"""
import os
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from clickhouse_driver import Client
from dotenv import load_dotenv

load_dotenv()


class ClickHouseDB:
    """ClickHouse database handler for analytics."""
    
    def __init__(self):
        self.config = {
            'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
            'port': int(os.getenv('CLICKHOUSE_NATIVE_PORT', 9000)),
            'database': os.getenv('CLICKHOUSE_DB', 'project_mgmt'),
            'user': os.getenv('CLICKHOUSE_USER', 'default'),
            'password': os.getenv('CLICKHOUSE_PASSWORD', 'clickhouse123'),
        }
    
    def get_client(self) -> Client:
        """Get ClickHouse client."""
        return Client(**self.config)
    
    @contextmanager
    def connection(self):
        """Context manager for ClickHouse connections."""
        client = self.get_client()
        try:
            yield client
        finally:
            client.disconnect()
    
    # ===========================================
    # Data Sync Operations
    # ===========================================
    
    def insert_projects(self, projects: List[Dict[str, Any]]) -> int:
        """Insert or update projects in ClickHouse."""
        if not projects:
            return 0
        
        # Prepare data for insertion
        columns = [
            'id_root', 'klaster_regional', 'entitas_terminal', 'id_investasi',
            'project_definition', 'asset_categories', 'type_investasi',
            'tahun_usulan', 'tahun_rkap', 'status_investasi',
            'progres_description', 'issue_categories', 'issue_description',
            'action_target', 'head_office_support_desc', 'pic', 'status_issue',
            'kebutuhan_dana', 'rkap',
            'rkap_januari', 'rkap_februari', 'rkap_maret', 'rkap_april',
            'rkap_mei', 'rkap_juni', 'rkap_juli', 'rkap_agustus',
            'rkap_september', 'rkap_oktober', 'rkap_november', 'rkap_desember',
            'judul_kontrak', 'nilai_kontrak', 'penyerapan_sd_tahun_lalu',
            'penyedia_jasa', 'no_kontrak', 'tanggal_kontrak', 'tgl_mulai_kontrak',
            'jangka_waktu', 'satuan_hari', 'tanggal_selesai',
            'realisasi_januari', 'realisasi_februari', 'realisasi_maret',
            'realisasi_april', 'realisasi_mei', 'realisasi_juni',
            'realisasi_juli', 'realisasi_agustus', 'realisasi_september',
            'realisasi_oktober', 'realisasi_november', 'realisasi_desember',
            'prognosa_januari', 'prognosa_februari', 'prognosa_maret',
            'prognosa_april', 'prognosa_mei', 'prognosa_juni',
            'prognosa_juli', 'prognosa_agustus', 'prognosa_september',
            'prognosa_oktober', 'prognosa_november', 'prognosa_sd_desember',
            'latitude', 'longitude', 'created_at', 'updated_at'
        ]
        
        # Convert projects to tuples
        data = []
        for project in projects:
            row = []
            for col in columns:
                value = project.get(col)
                
                # Handle type conversions
                if col == 'type_investasi':
                    value = value if value in ('Murni', 'Multi Year', 'Carry Forward') else 'Murni'
                elif col == 'status_issue':
                    value = value if value in ('Open', 'Closed') else 'Open'
                elif col in ('tahun_usulan', 'tahun_rkap'):
                    value = int(value) if value else 2025
                elif col == 'jangka_waktu':
                    value = int(value) if value else 0
                elif 'rkap_' in col or 'realisasi_' in col or 'prognosa_' in col or col in ('kebutuhan_dana', 'rkap', 'nilai_kontrak', 'penyerapan_sd_tahun_lalu'):
                    value = float(value) if value else 0.0
                elif col in ('latitude', 'longitude'):
                    value = float(value) if value else None
                elif col in ('tanggal_kontrak', 'tgl_mulai_kontrak', 'tanggal_selesai'):
                    # Keep as date or None
                    pass
                elif col in ('created_at', 'updated_at'):
                    # Handle timezone-aware datetimes
                    if value is not None:
                        if hasattr(value, 'tzinfo') and value.tzinfo is not None:
                            value = value.replace(tzinfo=None)
                else:
                    value = str(value) if value else ''
                
                row.append(value)
            data.append(tuple(row))
        
        column_str = ', '.join(columns)
        query = f"INSERT INTO project_investasi ({column_str}) VALUES"
        
        with self.connection() as client:
            client.execute(query, data)
        
        return len(data)
    
    def truncate_table(self, table: str = 'project_investasi') -> None:
        """Truncate a table (for full sync)."""
        with self.connection() as client:
            client.execute(f"TRUNCATE TABLE {table}")
    
    # ===========================================
    # Analytics Queries
    # ===========================================
    
    def get_rkap_vs_realisasi(self, tahun_rkap: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get RKAP vs Realisasi summary from materialized view."""
        where_clause = f"WHERE tahun_rkap = {tahun_rkap}" if tahun_rkap else ""
        
        query = f"""
            SELECT 
                tahun_rkap,
                klaster_regional,
                project_count,
                total_rkap,
                total_realisasi,
                total_nilai_kontrak,
                if(total_rkap > 0, total_realisasi / total_rkap * 100, 0) as persen_serapan
            FROM mv_rkap_vs_realisasi
            {where_clause}
            ORDER BY tahun_rkap, klaster_regional
        """
        
        with self.connection() as client:
            result = client.execute(query, with_column_types=True)
            columns = [col[0] for col in result[1]]
            return [dict(zip(columns, row)) for row in result[0]]
    
    def get_issue_summary(self, tahun_rkap: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get issue summary from materialized view."""
        where_clause = f"WHERE tahun_rkap = {tahun_rkap}" if tahun_rkap else ""
        
        query = f"""
            SELECT 
                tahun_rkap,
                klaster_regional,
                status_issue,
                issue_count
            FROM mv_issue_summary
            {where_clause}
            ORDER BY tahun_rkap, klaster_regional
        """
        
        with self.connection() as client:
            result = client.execute(query, with_column_types=True)
            columns = [col[0] for col in result[1]]
            return [dict(zip(columns, row)) for row in result[0]]
    
    def get_monthly_realization(self, tahun_rkap: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get monthly realization trend."""
        where_clause = f"WHERE tahun_rkap = {tahun_rkap}" if tahun_rkap else ""
        
        query = f"""
            SELECT *
            FROM mv_monthly_realization
            {where_clause}
        """
        
        with self.connection() as client:
            result = client.execute(query, with_column_types=True)
            columns = [col[0] for col in result[1]]
            return [dict(zip(columns, row)) for row in result[0]]
    
    def get_investment_type_distribution(self, tahun_rkap: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get investment type distribution."""
        where_clause = f"WHERE tahun_rkap = {tahun_rkap}" if tahun_rkap else ""
        
        query = f"""
            SELECT 
                tahun_rkap,
                type_investasi,
                project_count,
                total_rkap,
                total_nilai_kontrak
            FROM mv_investment_type
            {where_clause}
            ORDER BY tahun_rkap, type_investasi
        """
        
        with self.connection() as client:
            result = client.execute(query, with_column_types=True)
            columns = [col[0] for col in result[1]]
            return [dict(zip(columns, row)) for row in result[0]]
    
    def get_project_count(self) -> int:
        """Get total project count."""
        with self.connection() as client:
            result = client.execute("SELECT count() FROM project_investasi")
            return result[0][0]
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.connection() as client:
                client.execute("SELECT 1")
                return True
        except Exception:
            return False


# Singleton instance
ch_db = ClickHouseDB()
