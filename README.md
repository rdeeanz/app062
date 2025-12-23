# Project Management Dashboard System

An integrated data platform for managing investment projects, featuring real-time dashboards, analytics, and comprehensive data management tools.

## 🏗 Architecture

The system consists of several integrated components running in Docker containers:

| Service | Port | Description | Login Credentials |
|---------|------|-------------|-------------------|
| **Dash** | `8050` | Main interactive dashboard with maps & KPIs | No login required |
| **Grafana** | `3000` | Real-time monitoring & alerting | `admin` / `admin123` |
| **Superset** | `8088` | Advanced BI analytics & data exploration | `admin` / `admin123` |
| **pgAdmin** | `5050` | Database management GUI | `admin@admin.com` / `admin123` |
| **PostgreSQL** | `5432` | Primary transactional database | `postgres` / `postgres123` |
| **ClickHouse** | `8123` | High-performance analytics database | `default` / `clickhouse123` |

## 🚀 Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.9+ (for CLI usage outside Docker)

### 2. Setup & Run
```bash
# 1. Clone repository
git clone <repository-url>
cd app061

# 2. Configure Environment
cp .env.example .env
# Edit .env if needed (ports, passwords)

# 3. Start Services
docker-compose up -d

# 4. Verify Services
docker-compose ps
```

### 3. Initialize Data (CLI)
The project includes a Python CLI for managing data:

```bash
# Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Check connection health
python cli.py health

# Add sample data
python cli.py add-sample-project

# Sync to ClickHouse (for analytics)
python cli.py sync-clickhouse --full
```

## 📊 Dashboard Access

### 1. Plotly Dash (http://localhost:8050)
- **Features:** Interactive maps, project details, S-Curve charts.
- **Best for:** Stakeholder presentations, project tracking.

### 2. Grafana (http://localhost:3000)
- **Features:** Real-time metrics, system health monitoring.
- **Best for:** Technical monitoring, quick stats.

### 3. Apache Superset (http://localhost:8088)
- **Features:** Deep dive analytics, ad-hoc SQL queries.
- **Best for:** Business analysts, custom report generation.
- **Note:** Login session configured with server-side storage for stability.

### 4. pgAdmin (http://localhost:5050)
- **Features:** Web-based database management.
- **Usage:** Connect to server using Host: `postgres`.

## 🛠 Tech Stack
- **Backend:** Python (Typer, Pydantic, Pandas)
- **Databases:** PostgreSQL (OLTP), ClickHouse (OLAP)
- **Visualization:** Plotly Dash, Grafana, Apache Superset
- **Infrastructure:** Docker, Docker Compose
- **Tools:** pgAdmin, Gunicorn, Nginx (optional reverse proxy)

## 📄 Documentation
Full technical documentation is available in [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md).