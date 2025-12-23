#!/bin/bash
# ===========================================
# Superset Setup Script
# Run this after Superset container is up
# ===========================================

set -e

echo "=== Superset Setup ==="

# Wait for Superset to be ready
echo "Waiting for Superset..."
sleep 10

# Configure ClickHouse database connection
echo "Configuring ClickHouse connection..."

# The database connection will be added via the Superset UI or API
# This script provides the connection string for reference

cat << 'EOF'
===========================================
Manual Setup Instructions:
===========================================

1. Access Superset at http://localhost:8088
   - Username: admin
   - Password: admin

2. Add ClickHouse Database Connection:
   - Go to: Data > Databases > + Database
   - Select: ClickHouse
   - SQLAlchemy URI: clickhousedb://default:clickhouse123@clickhouse:8123/project_mgmt
   - Display Name: Project Management Analytics

3. Add PostgreSQL Database Connection:
   - Go to: Data > Databases > + Database
   - Select: PostgreSQL
   - SQLAlchemy URI: postgresql://postgres:postgres123@postgres:5432/project_mgmt
   - Display Name: Project Management

4. Create Datasets:
   - Go to: Data > Datasets > + Dataset
   - Select database and table: project_investasi

5. Create Charts and Dashboards:
   - Create charts using the SQL Lab or Chart Builder
   - Combine charts into dashboards

===========================================
Example SQL Queries for Charts:
===========================================

-- Total RKAP vs Realisasi by Regional
SELECT 
    klaster_regional,
    SUM(rkap) as total_rkap,
    SUM(realisasi_januari + realisasi_februari + realisasi_maret +
        realisasi_april + realisasi_mei + realisasi_juni +
        realisasi_juli + realisasi_agustus + realisasi_september +
        realisasi_oktober + realisasi_november + realisasi_desember) as total_realisasi
FROM project_investasi
GROUP BY klaster_regional
ORDER BY klaster_regional;

-- Investment Type Distribution
SELECT 
    type_investasi,
    COUNT(*) as project_count,
    SUM(rkap) as total_rkap
FROM project_investasi
GROUP BY type_investasi;

-- Issue Status Summary
SELECT 
    status_issue,
    COUNT(*) as issue_count
FROM project_investasi
WHERE issue_description IS NOT NULL AND issue_description != ''
GROUP BY status_issue;

-- Monthly Realization Trend
SELECT 
    'Januari' as month, 1 as month_order, SUM(realisasi_januari) as value FROM project_investasi
UNION ALL
SELECT 'Februari', 2, SUM(realisasi_februari) FROM project_investasi
UNION ALL
SELECT 'Maret', 3, SUM(realisasi_maret) FROM project_investasi
UNION ALL
SELECT 'April', 4, SUM(realisasi_april) FROM project_investasi
UNION ALL
SELECT 'Mei', 5, SUM(realisasi_mei) FROM project_investasi
UNION ALL
SELECT 'Juni', 6, SUM(realisasi_juni) FROM project_investasi
UNION ALL
SELECT 'Juli', 7, SUM(realisasi_juli) FROM project_investasi
UNION ALL
SELECT 'Agustus', 8, SUM(realisasi_agustus) FROM project_investasi
UNION ALL
SELECT 'September', 9, SUM(realisasi_september) FROM project_investasi
UNION ALL
SELECT 'Oktober', 10, SUM(realisasi_oktober) FROM project_investasi
UNION ALL
SELECT 'November', 11, SUM(realisasi_november) FROM project_investasi
UNION ALL
SELECT 'Desember', 12, SUM(realisasi_desember) FROM project_investasi
ORDER BY month_order;

-- Top Projects by RKAP
SELECT 
    id_root,
    project_definition,
    klaster_regional,
    rkap,
    nilai_kontrak
FROM project_investasi
ORDER BY rkap DESC
LIMIT 10;

EOF

echo "=== Setup Complete ==="
echo "Access Superset at http://localhost:8088"
