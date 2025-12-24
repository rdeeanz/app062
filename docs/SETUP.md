# SETUP.md - Project Management Dashboard System

## Dokumentasi Setup untuk app062

File ini berisi panduan lengkap untuk menjalankan project **Project Management Dashboard System** di folder `/var/www/app062`. Project ini merupakan hasil clone dari repositori `app061`.

---

## 📋 Deskripsi Project

Project ini adalah **platform data terintegrasi** untuk mengelola proyek investasi, yang menampilkan dashboard real-time, analytics, dan tools manajemen data yang komprehensif.

### Fitur Utama
- **Multi-Database Architecture**: PostgreSQL (OLTP) + ClickHouse (OLAP)
- **Multiple Visualization Layers**: Plotly Dash, Grafana, Apache Superset
- **CLI Management Tool**: Python-based CLI untuk operasi CRUD dan ETL
- **Containerized Deployment**: Seluruh stack berjalan di Docker

---

## 🏗 Arsitektur Sistem

### Komponen Utama

| Service | Port | Deskripsi | Kredensial |
|---------|------|-----------|------------|
| **Dash** | `8050` | Dashboard interaktif utama dengan maps & KPI | Tidak perlu login |
| **Grafana** | `3000` | Real-time monitoring & alerting | `admin` / `admin123` |
| **Superset** | `8088` | Advanced BI analytics & data exploration | `admin` / `admin123` |
| **pgAdmin** | `5050` | Database management GUI | `admin@admin.com` / `admin123` |
| **PostgreSQL** | `5433` | Primary transactional database | `postgres` / `postgres123` |
| **ClickHouse** | `8124` (HTTP), `9001` (Native) | High-performance analytics database | `default` / `clickhouse123` |

> **Note:** Port PostgreSQL dan ClickHouse diubah dari default untuk menghindari konflik dengan service yang sudah ada di server.

### Diagram Arsitektur

```
┌─────────────────────────────────────────────────────────────────┐
│                    VISUALIZATION LAYER                          │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Plotly Dash   │     Grafana     │       Apache Superset       │
│    (Port 8050)  │   (Port 3000)   │        (Port 8088)          │
└────────┬────────┴────────┬────────┴────────────┬────────────────┘
         │                 │                      │
         ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                              │
├──────────────────────────┬──────────────────────────────────────┤
│       PostgreSQL         │           ClickHouse                 │
│      (OLTP - Port 5432)  │         (OLAP - Port 9000)           │
│   Source of Truth        │      Analytics Engine                │
└──────────────────────────┴──────────────────────────────────────┘
         ▲                              ▲
         │                              │
         └──────────── ETL Sync ────────┘
                    (cli.py sync-clickhouse)
```

---

## 📁 Struktur Direktori

```
/var/www/app062/
├── cli.py                      # Main Python CLI entry point (516 baris)
├── docker-compose.yml          # Orchestrasi 6 container services
├── requirements.txt            # Python dependencies (12 packages)
├── README.md                   # Dokumentasi ringkas project
│
├── src/                        # Source code aplikasi
│   ├── __init__.py
│   ├── db/                     # Database abstraction layers
│   │   ├── postgres.py         # PostgreSQL handler (344 baris)
│   │   └── clickhouse.py       # ClickHouse handler (222 baris)
│   ├── models/                 # Data models & Pydantic schemas
│   │   └── project.py          # Project models (167 baris)
│   ├── etl/                    # Extract-Transform-Load logic
│   │   └── sync.py             # Sync PostgreSQL → ClickHouse (153 baris)
│   └── utils/                  # Helper functions
│       └── validators.py       # Data validators (224 baris)
│
├── dashboards/                 # Dashboard configurations
│   ├── dash_app/               # Custom Plotly Dash application
│   │   ├── Dockerfile          # Python 3.11-slim image
│   │   ├── app.py              # Main dashboard app (493 baris)
│   │   └── requirements.txt    # Dash dependencies
│   ├── grafana/                # Grafana provisioning
│   │   └── provisioning/
│   │       ├── datasources/    # ClickHouse datasource config
│   │       └── dashboards/     # Pre-built dashboards
│   └── superset/               # Superset configuration
│       ├── superset_config.py  # Session & security config
│       └── setup.sh            # Manual setup instructions
│
├── db/                         # Database initialization scripts
│   ├── init/                   # PostgreSQL schemas
│   │   ├── 001_schema.sql      # Main table definition (135 baris)
│   │   └── 002_indexes.sql     # Database indexes (60 baris)
│   └── clickhouse/             # ClickHouse schemas
│       └── 001_schema.sql      # Analytics views (203 baris)
│
├── tests/                      # Unit tests
│   └── test_cli.py             # CLI & validator tests (216 baris)
│
└── docs/                       # Documentation
    ├── DOCUMENTATION.md        # Technical documentation
    └── SETUP.md                # File ini
```

---

## 🛠 Tech Stack

### Backend & CLI
| Teknologi | Versi | Fungsi |
|-----------|-------|--------|
| Python | 3.9+ | Core language |
| Typer | 0.9.0 | CLI framework |
| Pydantic | 2.5.0 | Data validation |
| Rich | 13.7.0 | Terminal formatting |

### Database
| Teknologi | Versi | Fungsi |
|-----------|-------|--------|
| PostgreSQL | 15-alpine | OLTP database (transactional) |
| ClickHouse | 23.8 | OLAP database (analytics) |
| psycopg2-binary | 2.9.9 | PostgreSQL driver |
| clickhouse-driver | 0.2.6 | ClickHouse driver |

### Visualization
| Teknologi | Versi | Fungsi |
|-----------|-------|--------|
| Plotly Dash | 2.14.0 | Custom interactive dashboard |
| Dash Bootstrap | 1.5.0 | UI components |
| Grafana | 10.2.0 | Real-time monitoring |
| Apache Superset | 3.0.0 | BI & SQL analytics |
| pgAdmin | latest | PostgreSQL GUI |

### Infrastructure
| Teknologi | Fungsi |
|-----------|--------|
| Docker | Container runtime |
| Docker Compose | Multi-container orchestration |
| Gunicorn | WSGI HTTP Server |

---

## 🚀 Langkah-langkah Setup

### Prerequisites

1. **Docker & Docker Compose** terinstall
   ```bash
   docker --version
   docker-compose --version
   ```

2. **Python 3.9+** (untuk menjalankan CLI di luar Docker)
   ```bash
   python3 --version
   ```

3. **Port yang tersedia:**
   - 3000 (Grafana)
   - 5050 (pgAdmin)
   - 5432 (PostgreSQL)
   - 8050 (Dash)
   - 8088 (Superset)
   - 8123 & 9000 (ClickHouse)

### Step 1: Navigasi ke Direktori Project

```bash
cd /var/www/app062
```

### Step 2: Konfigurasi Environment (Opsional)

Buat file `.env` jika ingin override default values:

```bash
# Buat file .env
cat > .env << 'EOF'
# PostgreSQL
POSTGRES_DB=project_mgmt
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_PORT=5432

# ClickHouse
CLICKHOUSE_DB=project_mgmt
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=clickhouse123
CLICKHOUSE_HTTP_PORT=8123
CLICKHOUSE_NATIVE_PORT=9000

# Superset
SUPERSET_SECRET_KEY=supersecretkey123
SUPERSET_PORT=8088

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin123
GRAFANA_PORT=3000

# Dash
DASH_PORT=8050

# pgAdmin
PGADMIN_PORT=5050
EOF
```

### Step 3: Start Semua Services

```bash
# Start dalam mode detached
docker-compose up -d

# Pantau logs (opsional)
docker-compose logs -f
```

### Step 4: Verifikasi Services

```bash
# Cek status semua container
docker-compose ps

# Hasil yang diharapkan:
# NAME           STATUS          PORTS
# pm_postgres    Up (healthy)    5432/tcp
# pm_clickhouse  Up (healthy)    8123/tcp, 9000/tcp
# pm_superset    Up              8088/tcp
# pm_grafana     Up              3000/tcp
# pm_dash        Up              8050/tcp
# pm_pgadmin     Up              5050/tcp
```

### Step 5: Setup Python CLI (Opsional)

```bash
# Buat virtual environment
python3 -m venv .venv

# Aktifkan virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test koneksi database
python cli.py health
```

### Step 6: Inisialisasi Data (Opsional)

```bash
# Tambah sample project
python cli.py add-project

# List semua project
python cli.py list-projects

# Sync ke ClickHouse untuk analytics
python cli.py sync-clickhouse --full
```

---

## 📊 Akses Dashboard

### 1. Plotly Dash (http://localhost:8050)
- **Fitur:** Interactive maps, project details, S-Curve charts, KPI cards
- **Best for:** Presentasi stakeholder, project tracking
- **Login:** Tidak diperlukan

### 2. Grafana (http://localhost:3000)
- **Fitur:** Real-time metrics, system health monitoring, alerting
- **Best for:** Technical monitoring, quick stats
- **Login:** `admin` / `admin123`
- **Datasource:** ClickHouse (pre-configured)

### 3. Apache Superset (http://localhost:8088)
- **Fitur:** Deep dive analytics, ad-hoc SQL queries, custom charts
- **Best for:** Business analysts, custom report generation
- **Login:** `admin` / `admin123`
- **Note:** Gunakan Firefox/Chrome untuk menghindari session issues

### 4. pgAdmin (http://localhost:5050)
- **Fitur:** Web-based PostgreSQL management
- **Login:** `admin@admin.com` / `admin123`
- **Server Connection:**
  - Host: `postgres` (dalam Docker network) atau `localhost` (dari host)
  - Port: `5432`
  - Username: `postgres`
  - Password: `postgres123`

---

## 💻 CLI Commands Reference

### Health Check
```bash
python cli.py health          # Cek koneksi semua database
```

### Project CRUD
```bash
python cli.py add-project              # Tambah project (interactive)
python cli.py add-project --no-interactive --id_root=PRJ001  # Non-interactive
python cli.py list-projects            # List semua project
python cli.py list-projects --klaster="Regional 2" --limit=50
python cli.py get-project PRJ001       # Detail satu project
python cli.py delete-project PRJ001    # Hapus project
```

### Financial Updates
```bash
python cli.py update-realisasi PRJ001 januari 1000000
python cli.py update-prognosa PRJ001 februari 2000000
python cli.py update-rkap PRJ001 maret 3000000
```

### Progress & Issues
```bash
python cli.py update-progress PRJ001 --progres="50% complete" --status=Open
```

### ETL & Sync
```bash
python cli.py sync-clickhouse          # Incremental sync
python cli.py sync-clickhouse --full   # Full sync (truncate + reload)
python cli.py verify                   # Verify PostgreSQL & ClickHouse in sync
```

### Analytics
```bash
python cli.py summary                  # Summary by regional
python cli.py summary --tahun=2025     # Filter by year
python cli.py validate                 # Validate data integrity
```

---

## 🗃 Database Schema

### PostgreSQL: `project_investasi` Table

| Kategori | Kolom | Tipe |
|----------|-------|------|
| **Identitas** | `id_root` (PK), `klaster_regional`, `entitas_terminal`, `id_investasi`, `project_definition` | VARCHAR/TEXT |
| **Klasifikasi** | `asset_categories`, `type_investasi`, `tahun_usulan`, `tahun_rkap`, `status_investasi` | VARCHAR/INT |
| **Progress** | `progres_description`, `issue_categories`, `issue_description`, `action_target`, `pic`, `status_issue` | TEXT/VARCHAR |
| **Keuangan** | `kebutuhan_dana`, `rkap`, `rkap_januari`...`rkap_desember` | NUMERIC(18,2) |
| **Kontrak** | `judul_kontrak`, `nilai_kontrak`, `penyedia_jasa`, `no_kontrak`, `tanggal_*`, `jangka_waktu` | TEXT/DATE/INT |
| **Realisasi** | `realisasi_januari`...`realisasi_desember` | NUMERIC(18,2) |
| **Prognosa** | `prognosa_januari`...`prognosa_sd_desember` | NUMERIC(18,2) |
| **Lokasi** | `latitude`, `longitude` | NUMERIC(10,7) |
| **Metadata** | `created_at`, `updated_at`, `metadata` | TIMESTAMP/JSONB |

### ClickHouse: Materialized Views

| View | Fungsi |
|------|--------|
| `mv_rkap_vs_realisasi` | RKAP vs Realisasi summary by regional |
| `mv_progress_by_regional` | Progress by regional & terminal |
| `mv_issue_summary` | Issue count by status |
| `mv_monthly_realization` | Monthly realization trend |
| `mv_investment_type` | Investment type distribution |

---

## 🔧 Troubleshooting

### 1. Container Tidak Start

```bash
# Cek logs container yang bermasalah
docker-compose logs postgres
docker-compose logs superset

# Restart specific container
docker-compose restart superset
```

### 2. Database Connection Failed

```bash
# Pastikan container PostgreSQL healthy
docker exec pm_postgres pg_isready -U postgres

# Test koneksi dari host
psql -h localhost -p 5432 -U postgres -d project_mgmt
```

### 3. Superset Login Loop

- Gunakan browser **Firefox** atau **Chrome**
- Clear cookies dan cache
- Cek logs: `docker logs pm_superset`

### 4. ClickHouse Sync Error

```bash
# Full sync untuk reset
python cli.py sync-clickhouse --full

# Verify sync status
python cli.py verify
```

### 5. Port Already in Use

```bash
# Cek port yang digunakan
sudo lsof -i :5432

# Ubah port di .env atau docker-compose.yml
POSTGRES_PORT=5433
```

---

## 🛑 Stop & Cleanup

### Stop Services (Retain Data)
```bash
docker-compose down
```

### Stop & Remove Volumes (Delete All Data)
```bash
docker-compose down -v
```

### Remove Images
```bash
docker-compose down --rmi all
```

---

## 📝 Catatan Penting

1. **Data Persistence**: Semua data disimpan di Docker volumes. Gunakan `docker-compose down` tanpa flag `-v` untuk mempertahankan data.

2. **Network**: Semua services berkomunikasi melalui Docker network `pm_network`. Gunakan hostname container (e.g., `postgres`, `clickhouse`) untuk koneksi internal.

3. **Scalability**: Untuk production, pertimbangkan:
   - Menggunakan external PostgreSQL/ClickHouse
   - Menambahkan reverse proxy (Nginx)
   - Mengkonfigurasi SSL/TLS

4. **Backup**: 
   ```bash
   # Backup PostgreSQL
   docker exec pm_postgres pg_dump -U postgres project_mgmt > backup.sql
   
   # Restore
   docker exec -i pm_postgres psql -U postgres project_mgmt < backup.sql
   ```

---

## 📚 Referensi

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [ClickHouse Documentation](https://clickhouse.com/docs/en/)
- [Plotly Dash Documentation](https://dash.plotly.com/)
- [Apache Superset Documentation](https://superset.apache.org/docs/intro)
- [Grafana Documentation](https://grafana.com/docs/)
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

**Dibuat oleh:** Development Team  
**Tanggal:** Desember 2025  
**Project:** app062 (clone dari app061)
