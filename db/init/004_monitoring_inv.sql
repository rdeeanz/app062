-- ===========================================
-- Monitoring Investment Table
-- Related to project_investasi via id_root
-- ===========================================

CREATE TABLE IF NOT EXISTS monitoring_inv (
    -- Primary Key
    id                          SERIAL PRIMARY KEY,
    
    -- Foreign Key to project_investasi (only -001 suffix allowed)
    id_root                     VARCHAR(50) NOT NULL 
                                REFERENCES project_investasi(id_root) ON DELETE CASCADE ON UPDATE CASCADE
                                CHECK (id_root LIKE '%-001'),
    
    -- Monitoring Details
    tanggal_monitoring          DATE NOT NULL DEFAULT CURRENT_DATE,
    progres_fisik               NUMERIC(5, 2) DEFAULT 0 CHECK (progres_fisik >= 0 AND progres_fisik <= 100),
    progres_keuangan            NUMERIC(5, 2) DEFAULT 0 CHECK (progres_keuangan >= 0 AND progres_keuangan <= 100),
    
    -- Status & Notes
    status_monitoring           VARCHAR(50) CHECK (status_monitoring IN ('On Track', 'Delayed', 'At Risk', 'Completed')),
    catatan                     TEXT,
    kendala                     TEXT,
    tindak_lanjut               TEXT,
    
    -- PIC & Dokumentasi
    pic_monitoring              VARCHAR(200),
    foto_dokumentasi            TEXT,  -- URL or path to documentation photos
    
    -- Metadata
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trigger for updated_at
CREATE TRIGGER trigger_update_monitoring_inv
    BEFORE UPDATE ON monitoring_inv
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Indexes for performance
CREATE INDEX idx_monitoring_inv_id_root ON monitoring_inv(id_root);
CREATE INDEX idx_monitoring_inv_tanggal ON monitoring_inv(tanggal_monitoring);
CREATE INDEX idx_monitoring_inv_status ON monitoring_inv(status_monitoring);

-- Comments
COMMENT ON TABLE monitoring_inv IS 'Monitoring table for investment projects, linked to project_investasi';
COMMENT ON COLUMN monitoring_inv.id_root IS 'Foreign key referencing project_investasi.id_root';
COMMENT ON COLUMN monitoring_inv.progres_fisik IS 'Physical progress percentage (0-100)';
COMMENT ON COLUMN monitoring_inv.progres_keuangan IS 'Financial progress percentage (0-100)';
COMMENT ON COLUMN monitoring_inv.status_monitoring IS 'Monitoring status: On Track, Delayed, At Risk, or Completed';
