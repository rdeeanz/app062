-- ===========================================
-- Indexes for Query Optimization
-- ===========================================

-- Index for regional queries
CREATE INDEX IF NOT EXISTS idx_project_klaster_regional 
    ON project_investasi(klaster_regional);

-- Index for terminal queries
CREATE INDEX IF NOT EXISTS idx_project_entitas_terminal 
    ON project_investasi(entitas_terminal);

-- Index for year-based queries
CREATE INDEX IF NOT EXISTS idx_project_tahun_rkap 
    ON project_investasi(tahun_rkap);

CREATE INDEX IF NOT EXISTS idx_project_tahun_usulan 
    ON project_investasi(tahun_usulan);

-- Index for status queries
CREATE INDEX IF NOT EXISTS idx_project_status_investasi 
    ON project_investasi(status_investasi);

CREATE INDEX IF NOT EXISTS idx_project_status_issue 
    ON project_investasi(status_issue);

-- Index for investment type
CREATE INDEX IF NOT EXISTS idx_project_type_investasi 
    ON project_investasi(type_investasi);

-- Index for asset categories
CREATE INDEX IF NOT EXISTS idx_project_asset_categories 
    ON project_investasi(asset_categories);

-- Composite index for common filter patterns
CREATE INDEX IF NOT EXISTS idx_project_regional_year 
    ON project_investasi(klaster_regional, tahun_rkap);

CREATE INDEX IF NOT EXISTS idx_project_terminal_year 
    ON project_investasi(entitas_terminal, tahun_rkap);

-- Index for contract queries
CREATE INDEX IF NOT EXISTS idx_project_tanggal_kontrak 
    ON project_investasi(tanggal_kontrak);

CREATE INDEX IF NOT EXISTS idx_project_tanggal_selesai 
    ON project_investasi(tanggal_selesai);

-- Index for updated_at (useful for incremental sync)
CREATE INDEX IF NOT EXISTS idx_project_updated_at 
    ON project_investasi(updated_at);

-- GIN index for JSONB metadata queries
CREATE INDEX IF NOT EXISTS idx_project_metadata 
    ON project_investasi USING GIN (metadata);

-- Geospatial index (for location-based queries if PostGIS installed)
-- CREATE INDEX IF NOT EXISTS idx_project_location 
--     ON project_investasi USING GIST (ST_MakePoint(longitude, latitude));
