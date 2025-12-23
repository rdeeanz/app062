-- ===========================================
-- Project Management Investment Database
-- Table: project_investasi
-- ===========================================

CREATE TABLE IF NOT EXISTS project_investasi (
    -- =====================
    -- Identitas & Organisasi
    -- =====================
    id_root                     VARCHAR(50) PRIMARY KEY,
    klaster_regional            VARCHAR(100) DEFAULT 'Regional 2',
    entitas_terminal            VARCHAR(200),
    id_investasi                VARCHAR(100),
    project_definition          TEXT,

    -- =====================
    -- Klasifikasi & Status
    -- =====================
    asset_categories            VARCHAR(200),
    type_investasi              VARCHAR(50) CHECK (type_investasi IN ('Murni', 'Multi Year', 'Carry Forward')),
    tahun_usulan                INTEGER,
    tahun_rkap                  INTEGER DEFAULT 2025,
    status_investasi            VARCHAR(100),

    -- =====================
    -- Progres & Issue
    -- =====================
    progres_description         TEXT,
    issue_categories            VARCHAR(200),
    issue_description           TEXT,
    action_target               TEXT,
    head_office_support_desc    TEXT,
    pic                         VARCHAR(200),
    status_issue                VARCHAR(20) CHECK (status_issue IN ('Open', 'Closed')),

    -- =====================
    -- Keuangan - RKAP
    -- =====================
    kebutuhan_dana              NUMERIC(18, 2) DEFAULT 0,
    rkap                        NUMERIC(18, 2) DEFAULT 0,
    rkap_januari                NUMERIC(18, 2) DEFAULT 0,
    rkap_februari               NUMERIC(18, 2) DEFAULT 0,
    rkap_maret                  NUMERIC(18, 2) DEFAULT 0,
    rkap_april                  NUMERIC(18, 2) DEFAULT 0,
    rkap_mei                    NUMERIC(18, 2) DEFAULT 0,
    rkap_juni                   NUMERIC(18, 2) DEFAULT 0,
    rkap_juli                   NUMERIC(18, 2) DEFAULT 0,
    rkap_agustus                NUMERIC(18, 2) DEFAULT 0,
    rkap_september              NUMERIC(18, 2) DEFAULT 0,
    rkap_oktober                NUMERIC(18, 2) DEFAULT 0,
    rkap_november               NUMERIC(18, 2) DEFAULT 0,
    rkap_desember               NUMERIC(18, 2) DEFAULT 0,

    -- =====================
    -- Kontrak
    -- =====================
    judul_kontrak               TEXT,
    nilai_kontrak               NUMERIC(18, 2) DEFAULT 0,
    penyerapan_sd_tahun_lalu    NUMERIC(18, 2) DEFAULT 0,
    penyedia_jasa               VARCHAR(300),
    no_kontrak                  VARCHAR(200),
    tanggal_kontrak             DATE,
    tgl_mulai_kontrak           DATE,
    jangka_waktu                INTEGER,
    satuan_hari                 VARCHAR(20) DEFAULT 'Hari',
    tanggal_selesai             DATE,

    -- =====================
    -- Realisasi Bulanan
    -- =====================
    realisasi_januari           NUMERIC(18, 2) DEFAULT 0,
    realisasi_februari          NUMERIC(18, 2) DEFAULT 0,
    realisasi_maret             NUMERIC(18, 2) DEFAULT 0,
    realisasi_april             NUMERIC(18, 2) DEFAULT 0,
    realisasi_mei               NUMERIC(18, 2) DEFAULT 0,
    realisasi_juni              NUMERIC(18, 2) DEFAULT 0,
    realisasi_juli              NUMERIC(18, 2) DEFAULT 0,
    realisasi_agustus           NUMERIC(18, 2) DEFAULT 0,
    realisasi_september         NUMERIC(18, 2) DEFAULT 0,
    realisasi_oktober           NUMERIC(18, 2) DEFAULT 0,
    realisasi_november          NUMERIC(18, 2) DEFAULT 0,
    realisasi_desember          NUMERIC(18, 2) DEFAULT 0,

    -- =====================
    -- Prognosa Bulanan
    -- =====================
    prognosa_januari            NUMERIC(18, 2) DEFAULT 0,
    prognosa_februari           NUMERIC(18, 2) DEFAULT 0,
    prognosa_maret              NUMERIC(18, 2) DEFAULT 0,
    prognosa_april              NUMERIC(18, 2) DEFAULT 0,
    prognosa_mei                NUMERIC(18, 2) DEFAULT 0,
    prognosa_juni               NUMERIC(18, 2) DEFAULT 0,
    prognosa_juli               NUMERIC(18, 2) DEFAULT 0,
    prognosa_agustus            NUMERIC(18, 2) DEFAULT 0,
    prognosa_september          NUMERIC(18, 2) DEFAULT 0,
    prognosa_oktober            NUMERIC(18, 2) DEFAULT 0,
    prognosa_november           NUMERIC(18, 2) DEFAULT 0,
    prognosa_sd_desember        NUMERIC(18, 2) DEFAULT 0,

    -- =====================
    -- Lokasi
    -- =====================
    latitude                    NUMERIC(10, 7),
    longitude                   NUMERIC(10, 7),

    -- =====================
    -- Metadata
    -- =====================
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata                    JSONB DEFAULT '{}'::jsonb
);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_project_investasi
    BEFORE UPDATE ON project_investasi
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE project_investasi IS 'Main table for investment project management';
COMMENT ON COLUMN project_investasi.id_root IS 'Primary key - unique project identifier';
COMMENT ON COLUMN project_investasi.klaster_regional IS 'Regional cluster (default: Regional 2)';
COMMENT ON COLUMN project_investasi.type_investasi IS 'Investment type: Murni, Multi Year, or Carry Forward';
COMMENT ON COLUMN project_investasi.status_issue IS 'Issue status: Open or Closed';
COMMENT ON COLUMN project_investasi.metadata IS 'JSONB column for extensible metadata';
