-- ===========================================
-- ClickHouse Analytics Schema
-- Database: project_mgmt
-- ===========================================

CREATE DATABASE IF NOT EXISTS project_mgmt;

-- Main project table (synced from PostgreSQL)
CREATE TABLE IF NOT EXISTS project_mgmt.project_investasi
(
    -- Identitas & Organisasi
    id_root                     String,
    klaster_regional            String DEFAULT 'Regional 2',
    entitas_terminal            String,
    id_investasi                String,
    project_definition          String,

    -- Klasifikasi & Status
    asset_categories            String,
    type_investasi              Enum8('Murni' = 1, 'Multi Year' = 2, 'Carry Forward' = 3),
    tahun_usulan                UInt16,
    tahun_rkap                  UInt16 DEFAULT 2025,
    status_investasi            String,

    -- Progres & Issue
    progres_description         String,
    issue_categories            String,
    issue_description           String,
    action_target               String,
    head_office_support_desc    String,
    pic                         String,
    status_issue                Enum8('Open' = 1, 'Closed' = 2),

    -- Keuangan - RKAP
    kebutuhan_dana              Decimal64(2) DEFAULT 0,
    rkap                        Decimal64(2) DEFAULT 0,
    rkap_januari                Decimal64(2) DEFAULT 0,
    rkap_februari               Decimal64(2) DEFAULT 0,
    rkap_maret                  Decimal64(2) DEFAULT 0,
    rkap_april                  Decimal64(2) DEFAULT 0,
    rkap_mei                    Decimal64(2) DEFAULT 0,
    rkap_juni                   Decimal64(2) DEFAULT 0,
    rkap_juli                   Decimal64(2) DEFAULT 0,
    rkap_agustus                Decimal64(2) DEFAULT 0,
    rkap_september              Decimal64(2) DEFAULT 0,
    rkap_oktober                Decimal64(2) DEFAULT 0,
    rkap_november               Decimal64(2) DEFAULT 0,
    rkap_desember               Decimal64(2) DEFAULT 0,

    -- Kontrak
    judul_kontrak               String,
    nilai_kontrak               Decimal64(2) DEFAULT 0,
    penyerapan_sd_tahun_lalu    Decimal64(2) DEFAULT 0,
    penyedia_jasa               String,
    no_kontrak                  String,
    tanggal_kontrak             Nullable(Date),
    tgl_mulai_kontrak           Nullable(Date),
    jangka_waktu                UInt32 DEFAULT 0,
    satuan_hari                 String DEFAULT 'Hari',
    tanggal_selesai             Nullable(Date),

    -- Realisasi Bulanan
    realisasi_januari           Decimal64(2) DEFAULT 0,
    realisasi_februari          Decimal64(2) DEFAULT 0,
    realisasi_maret             Decimal64(2) DEFAULT 0,
    realisasi_april             Decimal64(2) DEFAULT 0,
    realisasi_mei               Decimal64(2) DEFAULT 0,
    realisasi_juni              Decimal64(2) DEFAULT 0,
    realisasi_juli              Decimal64(2) DEFAULT 0,
    realisasi_agustus           Decimal64(2) DEFAULT 0,
    realisasi_september         Decimal64(2) DEFAULT 0,
    realisasi_oktober           Decimal64(2) DEFAULT 0,
    realisasi_november          Decimal64(2) DEFAULT 0,
    realisasi_desember          Decimal64(2) DEFAULT 0,

    -- Prognosa Bulanan
    prognosa_januari            Decimal64(2) DEFAULT 0,
    prognosa_februari           Decimal64(2) DEFAULT 0,
    prognosa_maret              Decimal64(2) DEFAULT 0,
    prognosa_april              Decimal64(2) DEFAULT 0,
    prognosa_mei                Decimal64(2) DEFAULT 0,
    prognosa_juni               Decimal64(2) DEFAULT 0,
    prognosa_juli               Decimal64(2) DEFAULT 0,
    prognosa_agustus            Decimal64(2) DEFAULT 0,
    prognosa_september          Decimal64(2) DEFAULT 0,
    prognosa_oktober            Decimal64(2) DEFAULT 0,
    prognosa_november           Decimal64(2) DEFAULT 0,
    prognosa_sd_desember        Decimal64(2) DEFAULT 0,

    -- Lokasi
    latitude                    Nullable(Float64),
    longitude                   Nullable(Float64),

    -- Metadata
    created_at                  DateTime DEFAULT now(),
    updated_at                  DateTime DEFAULT now(),
    
    -- Calculated fields
    total_rkap_bulanan          Decimal64(2) MATERIALIZED 
        rkap_januari + rkap_februari + rkap_maret + rkap_april + 
        rkap_mei + rkap_juni + rkap_juli + rkap_agustus + 
        rkap_september + rkap_oktober + rkap_november + rkap_desember,
    
    total_realisasi             Decimal64(2) MATERIALIZED 
        realisasi_januari + realisasi_februari + realisasi_maret + realisasi_april + 
        realisasi_mei + realisasi_juni + realisasi_juli + realisasi_agustus + 
        realisasi_september + realisasi_oktober + realisasi_november + realisasi_desember,
    
    total_prognosa              Decimal64(2) MATERIALIZED 
        prognosa_januari + prognosa_februari + prognosa_maret + prognosa_april + 
        prognosa_mei + prognosa_juni + prognosa_juli + prognosa_agustus + 
        prognosa_september + prognosa_oktober + prognosa_november + prognosa_sd_desember
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (klaster_regional, entitas_terminal, id_root)
PARTITION BY tahun_rkap;

-- ===========================================
-- Materialized Views for Dashboard Queries
-- ===========================================

-- View: RKAP vs Realisasi Summary by Regional
CREATE MATERIALIZED VIEW IF NOT EXISTS project_mgmt.mv_rkap_vs_realisasi
ENGINE = SummingMergeTree()
ORDER BY (tahun_rkap, klaster_regional)
POPULATE AS
SELECT
    tahun_rkap,
    klaster_regional,
    count() AS project_count,
    sum(rkap) AS total_rkap,
    sum(realisasi_januari + realisasi_februari + realisasi_maret + realisasi_april + 
        realisasi_mei + realisasi_juni + realisasi_juli + realisasi_agustus + 
        realisasi_september + realisasi_oktober + realisasi_november + realisasi_desember) AS total_realisasi,
    sum(nilai_kontrak) AS total_nilai_kontrak
FROM project_mgmt.project_investasi
GROUP BY tahun_rkap, klaster_regional;

-- View: Progress by Regional and Terminal
CREATE MATERIALIZED VIEW IF NOT EXISTS project_mgmt.mv_progress_by_regional
ENGINE = SummingMergeTree()
ORDER BY (tahun_rkap, klaster_regional, entitas_terminal)
POPULATE AS
SELECT
    tahun_rkap,
    klaster_regional,
    entitas_terminal,
    count() AS project_count,
    countIf(status_investasi != '') AS with_status_count
FROM project_mgmt.project_investasi
GROUP BY tahun_rkap, klaster_regional, entitas_terminal;

-- View: Issue Summary
CREATE MATERIALIZED VIEW IF NOT EXISTS project_mgmt.mv_issue_summary
ENGINE = SummingMergeTree()
ORDER BY (tahun_rkap, klaster_regional, status_issue)
POPULATE AS
SELECT
    tahun_rkap,
    klaster_regional,
    status_issue,
    count() AS issue_count
FROM project_mgmt.project_investasi
WHERE issue_description != ''
GROUP BY tahun_rkap, klaster_regional, status_issue;

-- View: Monthly Realization Trend
CREATE MATERIALIZED VIEW IF NOT EXISTS project_mgmt.mv_monthly_realization
ENGINE = SummingMergeTree()
ORDER BY (tahun_rkap, klaster_regional)
POPULATE AS
SELECT
    tahun_rkap,
    klaster_regional,
    sum(realisasi_januari) AS jan,
    sum(realisasi_februari) AS feb,
    sum(realisasi_maret) AS mar,
    sum(realisasi_april) AS apr,
    sum(realisasi_mei) AS mei,
    sum(realisasi_juni) AS jun,
    sum(realisasi_juli) AS jul,
    sum(realisasi_agustus) AS agu,
    sum(realisasi_september) AS sep,
    sum(realisasi_oktober) AS okt,
    sum(realisasi_november) AS nov,
    sum(realisasi_desember) AS des
FROM project_mgmt.project_investasi
GROUP BY tahun_rkap, klaster_regional;

-- View: Investment Type Distribution
CREATE MATERIALIZED VIEW IF NOT EXISTS project_mgmt.mv_investment_type
ENGINE = SummingMergeTree()
ORDER BY (tahun_rkap, type_investasi)
POPULATE AS
SELECT
    tahun_rkap,
    type_investasi,
    count() AS project_count,
    sum(rkap) AS total_rkap,
    sum(nilai_kontrak) AS total_nilai_kontrak
FROM project_mgmt.project_investasi
GROUP BY tahun_rkap, type_investasi;
