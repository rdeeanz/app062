# Project Management Dashboard Documentation

## Overview
This system is an integrated platform designed to manage, track, and visualize investment projects. It combines transactional data management (PostgreSQL) with high-performance analytics (ClickHouse) and multiple visualization layers (Dash, Grafana, Superset) to provide comprehensive insights.

## directory Structure
```
/var/www/app061/
├── cli.py                  # Main Python CLI entry point
├── docker-compose.yml      # Service orchestration
├── .env                    # Environment variables (secrets)
├── requirements.txt        # Python dependencies
├── src/                    # Source code
│   ├── db/                 # Database abstraction layers (PG & ClickHouse)
│   ├── models/             # Data models & Pydantic schemas
│   ├── etl/                # Extract-Transform-Load logic
│   └── utils/              # Helper functions
├── dashboards/             # Dashboard source codes & configs
│   ├── dash_app/           # Custom Plotly Dash application
│   ├── grafana/            # Grafana provisioning configs
│   └── superset/           # Superset setup scripts
└── db/                     # Database initialization scripts
```

## System Architecture

### 1. Database Layer
- **PostgreSQL (v15)**: Acts as the primary source of truth (OLTP). Stores project details, status, and transactional updates.
  - **Schema**: `public.project_investasi`
  - **Key Fields**: `id_root`, `entitas`, `rkap`, `realisasi`, `status_issue`
- **ClickHouse (v23.8)**: Acts as the analytics engine (OLAP). Optimized for aggregation and fast querying.
  - **Engine**: MergeTree
  - **Sync**: Data is synchronized from PostgreSQL to ClickHouse via CLI ETL commands.

### 2. Application Layer (CLI)
Built with **Typer** and **Pydantic**:
- **CRUD Operations**: Create, Read, Update projects in PostgreSQL.
- **Data Validation**: Ensures integrity of investment types, status, and financial figures.
- **ETL Sync**: Synchronizes data to ClickHouse for dashboard consumption.

### 3. Visualization Layer
- **Plotly Dash (Port 8050)**: Custom Python web app. Best for detailed project views and maps.
- **Grafana (Port 3000)**: Monitoring dashboard. Uses ClickHouse datasource for real-time metrics.
- **Apache Superset (Port 8088)**: Self-service BI. Allows users to create custom charts and datasets.

### 4. Management Layer
- **pgAdmin (Port 5050)**: Web interface for managing the PostgreSQL database effectively.

## Installation & Configuration

### Prerequisites
- Docker & Docker Compose
- Python 3.9+ (optional, for local CLI)

### Deployment Steps
1. **Prepare Environment**:
   ```bash
   cp .env.example .env
   # Update passwords in .env
   ```

2. **Start Services**:
   ```bash
   docker-compose up -d
   ```

3. **Initialize Database**:
   The `db/init/001_schema.sql` script runs automatically on first startup.

4. **Load Data**:
   ```bash
   # Enter CLI environment
   python3 -m venv .venv
   source .venv/bin/activate
   
   # Add sample data
   python cli.py add-sample-project
   ```

## API / CLI Reference

### `cli.py` Commands

| Command | Description | Example |
|---------|-------------|---------|
| `list-projects` | Display all projects in a table | `python cli.py list-projects` |
| `add-project` | Interactive wizard to add a project | `python cli.py add-project` |
| `summary` | Show aggregated stats per regional | `python cli.py summary` |
| `health` | Check connection to Postgres & ClickHouse | `python cli.py health` |
| `sync-clickhouse` | Run ETL process to update analytics | `python cli.py sync-clickhouse --full` |

## Troubleshooting

### Superset Login Issues
If you experience session loops (login page reloading):
1. Use **Firefox** or **Chrome** (avoid Brave/Safari strict tracking protection).
2. The system uses **server-side sessions** (Redis/SQLAlchemy) backed by Gunicorn.
3. Check logs: `docker logs pm_superset`.

### Database Connection
- **Internal Docker Network**: Services communicate via `pm_network`. Use hostname `postgres` or `clickhouse`.
- **External Access**: Use `localhost` or server IP with mapped ports (5432, 8123).

### Data Not Appearing in Dashboards
1. Ensure you ran the sync command: `python cli.py sync-clickhouse`
2. Check Grafana datasources in Configuration.
3. Refresh the dashboard browser page.

## Data Dictionary
**Table: `project_investasi`**

| Column | Type | Description |
|--------|------|-------------|
| `id_root` | VARCHAR | Unique Project ID (PK) |
| `klaster_regional` | VARCHAR | Project Region |
| `entitas_terminal` | VARCHAR | Terminal Name |
| `type_investasi` | VARCHAR | Murni / Multi Year / Carry Forward |
| `rkap` | NUMERIC | Budget Plan (Rencana Kerja Anggaran Perusahaan) |
| `total_realisasi` | NUMERIC | Actual spending realized |
| `status_issue` | VARCHAR | Open / Closed |
| `latitude/longitude` | NUMERIC | Geo-coordinates for map visualization |

---
**Maintained by:** Development Team
**Last Updated:** December 2025
