"""
PostgreSQL Database Operations
Handles all PostgreSQL connections and CRUD operations.
"""
import os
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


class PostgresDB:
    """PostgreSQL database handler for project management."""
    
    def __init__(self):
        self.config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'project_mgmt'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres123'),
        }
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = psycopg2.connect(**self.config)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """Context manager for database cursors."""
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    
    # ===========================================
    # Project CRUD Operations
    # ===========================================
    
    def insert_project(self, project_data: Dict[str, Any]) -> str:
        """Insert a new project into the database."""
        columns = list(project_data.keys())
        values = list(project_data.values())
        placeholders = ', '.join(['%s'] * len(values))
        column_names = ', '.join(columns)
        
        query = f"""
            INSERT INTO project_investasi ({column_names})
            VALUES ({placeholders})
            RETURNING id_root
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, values)
            result = cursor.fetchone()
            return result['id_root']
    
    def update_project(self, id_root: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing project."""
        if not update_data:
            return False
        
        set_clauses = ', '.join([f"{key} = %s" for key in update_data.keys()])
        values = list(update_data.values()) + [id_root]
        
        query = f"""
            UPDATE project_investasi
            SET {set_clauses}
            WHERE id_root = %s
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, values)
            return cursor.rowcount > 0
    
    def delete_project(self, id_root: str) -> bool:
        """Delete a project from the database."""
        query = "DELETE FROM project_investasi WHERE id_root = %s"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, (id_root,))
            return cursor.rowcount > 0
    
    def get_project(self, id_root: str) -> Optional[Dict[str, Any]]:
        """Get a single project by ID."""
        query = "SELECT * FROM project_investasi WHERE id_root = %s"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, (id_root,))
            return cursor.fetchone()
    
    def list_projects(
        self,
        klaster_regional: Optional[str] = None,
        entitas_terminal: Optional[str] = None,
        tahun_rkap: Optional[int] = None,
        status_issue: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List projects with optional filters."""
        conditions = []
        params = []
        
        if klaster_regional:
            conditions.append("klaster_regional = %s")
            params.append(klaster_regional)
        
        if entitas_terminal:
            conditions.append("entitas_terminal ILIKE %s")
            params.append(f"%{entitas_terminal}%")
        
        if tahun_rkap:
            conditions.append("tahun_rkap = %s")
            params.append(tahun_rkap)
        
        if status_issue:
            conditions.append("status_issue = %s")
            params.append(status_issue)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.extend([limit, offset])
        
        query = f"""
            SELECT id_root, klaster_regional, entitas_terminal, project_definition,
                   type_investasi, tahun_rkap, status_investasi, status_issue,
                   rkap, nilai_kontrak, updated_at
            FROM project_investasi
            WHERE {where_clause}
            ORDER BY updated_at DESC
            LIMIT %s OFFSET %s
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def count_projects(self, **filters) -> int:
        """Count projects with optional filters."""
        conditions = []
        params = []
        
        for key, value in filters.items():
            if value is not None:
                conditions.append(f"{key} = %s")
                params.append(value)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"SELECT COUNT(*) as count FROM project_investasi WHERE {where_clause}"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()['count']
    
    # ===========================================
    # Progress & Issue Operations
    # ===========================================
    
    def update_progress(
        self,
        id_root: str,
        progres_description: Optional[str] = None,
        issue_categories: Optional[str] = None,
        issue_description: Optional[str] = None,
        action_target: Optional[str] = None,
        head_office_support_desc: Optional[str] = None,
        pic: Optional[str] = None,
        status_issue: Optional[str] = None
    ) -> bool:
        """Update project progress and issue information."""
        update_data = {}
        
        if progres_description is not None:
            update_data['progres_description'] = progres_description
        if issue_categories is not None:
            update_data['issue_categories'] = issue_categories
        if issue_description is not None:
            update_data['issue_description'] = issue_description
        if action_target is not None:
            update_data['action_target'] = action_target
        if head_office_support_desc is not None:
            update_data['head_office_support_desc'] = head_office_support_desc
        if pic is not None:
            update_data['pic'] = pic
        if status_issue is not None:
            update_data['status_issue'] = status_issue
        
        return self.update_project(id_root, update_data)
    
    # ===========================================
    # Financial Operations
    # ===========================================
    
    def update_realisasi(self, id_root: str, bulan: str, nilai: float) -> bool:
        """Update monthly realization value."""
        bulan_map = {
            'januari': 'realisasi_januari',
            'februari': 'realisasi_februari',
            'maret': 'realisasi_maret',
            'april': 'realisasi_april',
            'mei': 'realisasi_mei',
            'juni': 'realisasi_juni',
            'juli': 'realisasi_juli',
            'agustus': 'realisasi_agustus',
            'september': 'realisasi_september',
            'oktober': 'realisasi_oktober',
            'november': 'realisasi_november',
            'desember': 'realisasi_desember'
        }
        
        column = bulan_map.get(bulan.lower())
        if not column:
            raise ValueError(f"Invalid month: {bulan}")
        
        return self.update_project(id_root, {column: nilai})
    
    def update_prognosa(self, id_root: str, bulan: str, nilai: float) -> bool:
        """Update monthly prognosis value."""
        bulan_map = {
            'januari': 'prognosa_januari',
            'februari': 'prognosa_februari',
            'maret': 'prognosa_maret',
            'april': 'prognosa_april',
            'mei': 'prognosa_mei',
            'juni': 'prognosa_juni',
            'juli': 'prognosa_juli',
            'agustus': 'prognosa_agustus',
            'september': 'prognosa_september',
            'oktober': 'prognosa_oktober',
            'november': 'prognosa_november',
            'desember': 'prognosa_sd_desember'
        }
        
        column = bulan_map.get(bulan.lower())
        if not column:
            raise ValueError(f"Invalid month: {bulan}")
        
        return self.update_project(id_root, {column: nilai})
    
    def update_rkap(self, id_root: str, bulan: str, nilai: float) -> bool:
        """Update monthly RKAP value."""
        bulan_map = {
            'januari': 'rkap_januari',
            'februari': 'rkap_februari',
            'maret': 'rkap_maret',
            'april': 'rkap_april',
            'mei': 'rkap_mei',
            'juni': 'rkap_juni',
            'juli': 'rkap_juli',
            'agustus': 'rkap_agustus',
            'september': 'rkap_september',
            'oktober': 'rkap_oktober',
            'november': 'rkap_november',
            'desember': 'rkap_desember'
        }
        
        column = bulan_map.get(bulan.lower())
        if not column:
            raise ValueError(f"Invalid month: {bulan}")
        
        return self.update_project(id_root, {column: nilai})
    
    # ===========================================
    # Analytics Queries
    # ===========================================
    
    def get_summary_by_regional(self, tahun_rkap: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get summary statistics grouped by regional."""
        params = []
        where_clause = ""
        
        if tahun_rkap:
            where_clause = "WHERE tahun_rkap = %s"
            params.append(tahun_rkap)
        
        query = f"""
            SELECT 
                klaster_regional,
                COUNT(*) as project_count,
                SUM(rkap) as total_rkap,
                SUM(nilai_kontrak) as total_nilai_kontrak,
                SUM(
                    realisasi_januari + realisasi_februari + realisasi_maret +
                    realisasi_april + realisasi_mei + realisasi_juni +
                    realisasi_juli + realisasi_agustus + realisasi_september +
                    realisasi_oktober + realisasi_november + realisasi_desember
                ) as total_realisasi,
                COUNT(*) FILTER (WHERE status_issue = 'Open') as open_issues,
                COUNT(*) FILTER (WHERE status_issue = 'Closed') as closed_issues
            FROM project_investasi
            {where_clause}
            GROUP BY klaster_regional
            ORDER BY klaster_regional
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_projects_for_sync(self, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all projects for ClickHouse sync, optionally filtered by update time."""
        params = []
        where_clause = ""
        
        if since:
            where_clause = "WHERE updated_at > %s"
            params.append(since)
        
        query = f"SELECT * FROM project_investasi {where_clause} ORDER BY updated_at"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False


# Singleton instance
db = PostgresDB()
