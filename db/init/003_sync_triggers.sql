-- ===========================================
-- Real-Time Sync Triggers for PostgreSQL → ClickHouse
-- This creates triggers that notify a sync daemon when data changes
-- ===========================================

-- ===========================================
-- Notification Function
-- ===========================================
CREATE OR REPLACE FUNCTION notify_project_changes()
RETURNS TRIGGER AS $$
DECLARE
    payload JSON;
BEGIN
    IF (TG_OP = 'DELETE') THEN
        payload = json_build_object(
            'operation', TG_OP,
            'id_root', OLD.id_root,
            'timestamp', CURRENT_TIMESTAMP
        );
    ELSE
        payload = json_build_object(
            'operation', TG_OP,
            'id_root', NEW.id_root,
            'timestamp', CURRENT_TIMESTAMP
        );
    END IF;
    
    PERFORM pg_notify('project_changes', payload::text);
    
    IF (TG_OP = 'DELETE') THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- Trigger for INSERT, UPDATE, DELETE
-- ===========================================
DROP TRIGGER IF EXISTS project_investasi_sync_trigger ON project_investasi;

CREATE TRIGGER project_investasi_sync_trigger
    AFTER INSERT OR UPDATE OR DELETE ON project_investasi
    FOR EACH ROW EXECUTE FUNCTION notify_project_changes();

-- Add comment for documentation
COMMENT ON FUNCTION notify_project_changes() IS 'Sends NOTIFY event to project_changes channel on INSERT/UPDATE/DELETE';
