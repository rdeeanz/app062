#!/usr/bin/env python3
"""
Real-Time Sync Daemon: PostgreSQL → ClickHouse
Listens to PostgreSQL NOTIFY events and syncs data to ClickHouse.
"""

import json
import logging
import os
import select
import signal
import sys
import time
from datetime import datetime
import decimal
from decimal import Decimal
from threading import Event

import psycopg2
import psycopg2.extensions
from clickhouse_driver import Client as ClickHouseClient

# ===========================================
# Configuration
# ===========================================
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'pm_postgres'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'database': os.getenv('POSTGRES_DB', 'project_mgmt'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres123'),
}

CLICKHOUSE_CONFIG = {
    'host': os.getenv('CLICKHOUSE_HOST', 'pm_clickhouse'),
    'port': int(os.getenv('CLICKHOUSE_PORT', '9000')),
    'database': os.getenv('CLICKHOUSE_DB', 'project_mgmt'),
    'user': os.getenv('CLICKHOUSE_USER', 'default'),
    'password': os.getenv('CLICKHOUSE_PASSWORD', 'clickhouse123'),
}

LISTEN_CHANNEL = 'project_changes'
DEBOUNCE_SECONDS = 1.0  # Batch changes within this window

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Graceful shutdown
shutdown_event = Event()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ===========================================
# ClickHouse Columns (excluding MATERIALIZED columns)
# ===========================================
SYNC_COLUMNS = [
    'id_root', 'klaster_regional', 'entitas_terminal', 'id_investasi', 'project_definition',
    'asset_categories', 'type_investasi', 'tahun_usulan', 'tahun_rkap', 'status_investasi',
    'progres_description', 'issue_categories', 'issue_description', 'action_target',
    'head_office_support_desc', 'pic', 'status_issue',
    'kebutuhan_dana', 'rkap',
    'rkap_januari', 'rkap_februari', 'rkap_maret', 'rkap_april',
    'rkap_mei', 'rkap_juni', 'rkap_juli', 'rkap_agustus',
    'rkap_september', 'rkap_oktober', 'rkap_november', 'rkap_desember',
    'judul_kontrak', 'nilai_kontrak', 'penyerapan_sd_tahun_lalu', 'penyedia_jasa',
    'no_kontrak', 'tanggal_kontrak', 'tgl_mulai_kontrak', 'jangka_waktu', 'satuan_hari', 'tanggal_selesai',
    'realisasi_januari', 'realisasi_februari', 'realisasi_maret', 'realisasi_april',
    'realisasi_mei', 'realisasi_juni', 'realisasi_juli', 'realisasi_agustus',
    'realisasi_september', 'realisasi_oktober', 'realisasi_november', 'realisasi_desember',
    'prognosa_januari', 'prognosa_februari', 'prognosa_maret', 'prognosa_april',
    'prognosa_mei', 'prognosa_juni', 'prognosa_juli', 'prognosa_agustus',
    'prognosa_september', 'prognosa_oktober', 'prognosa_november', 'prognosa_sd_desember',
    'latitude', 'longitude', 'created_at', 'updated_at'
]


def convert_value(value, column_name):
    """Convert PostgreSQL values to ClickHouse-compatible format."""
    # List of decimal/numeric columns
    DECIMAL_COLUMNS = [
        'kebutuhan_dana', 'rkap', 'nilai_kontrak', 'penyerapan_sd_tahun_lalu',
        'rkap_januari', 'rkap_februari', 'rkap_maret', 'rkap_april',
        'rkap_mei', 'rkap_juni', 'rkap_juli', 'rkap_agustus',
        'rkap_september', 'rkap_oktober', 'rkap_november', 'rkap_desember',
        'realisasi_januari', 'realisasi_februari', 'realisasi_maret', 'realisasi_april',
        'realisasi_mei', 'realisasi_juni', 'realisasi_juli', 'realisasi_agustus',
        'realisasi_september', 'realisasi_oktober', 'realisasi_november', 'realisasi_desember',
        'prognosa_januari', 'prognosa_februari', 'prognosa_maret', 'prognosa_april',
        'prognosa_mei', 'prognosa_juni', 'prognosa_juli', 'prognosa_agustus',
        'prognosa_september', 'prognosa_oktober', 'prognosa_november', 'prognosa_sd_desember',
    ]
    
    # Handle Enum columns - ClickHouse Enum8 doesn't accept empty strings
    if column_name == 'type_investasi':
        if value is None or value == '':
            return 'Murni'  # Default to 'Murni'
        return value
    
    if column_name == 'status_issue':
        if value is None or value == '':
            return 'Open'  # Default to 'Open'
        return value
    
    # Handle decimal/numeric columns - return 0.0 for NULL or invalid values
    if column_name in DECIMAL_COLUMNS:
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError, decimal.InvalidOperation):
            return 0.0
    
    if value is None:
        # Handle nullable columns
        if column_name in ['tanggal_kontrak', 'tgl_mulai_kontrak', 'tanggal_selesai', 'latitude', 'longitude']:
            return None
        if column_name in ['tahun_usulan', 'tahun_rkap', 'jangka_waktu']:
            return 0
        return None if column_name in ['created_at', 'updated_at'] else ''
    
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value
    if isinstance(value, dict):
        return json.dumps(value)
    return value


def get_postgres_connection():
    """Create a new PostgreSQL connection with autocommit for LISTEN."""
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def get_clickhouse_client():
    """Create a new ClickHouse client connection."""
    return ClickHouseClient(**CLICKHOUSE_CONFIG)


def optimize_table(ch_client):
    """Run OPTIMIZE TABLE to deduplicate ReplacingMergeTree records."""
    try:
        ch_client.execute("OPTIMIZE TABLE project_investasi FINAL")
        logger.debug("✓ Table optimized (deduplicated)")
    except Exception as e:
        logger.warning(f"OPTIMIZE TABLE failed: {e}")


def sync_record_to_clickhouse(ch_client, pg_conn, id_root: str):
    """Sync a single record from PostgreSQL to ClickHouse by id_root."""
    cursor = pg_conn.cursor()
    
    # Fetch the record from PostgreSQL
    columns_str = ', '.join(SYNC_COLUMNS)
    cursor.execute(f"SELECT {columns_str} FROM project_investasi WHERE id_root = %s", (id_root,))
    row = cursor.fetchone()
    cursor.close()
    
    if row is None:
        logger.warning(f"Record not found in PostgreSQL for id_root: {id_root}")
        return False
    
    # Convert values
    converted_row = tuple(convert_value(row[i], SYNC_COLUMNS[i]) for i in range(len(row)))
    
    # Insert into ClickHouse (ReplacingMergeTree will handle duplicates)
    columns_str = ', '.join(SYNC_COLUMNS)
    placeholders = ', '.join(['%s'] * len(SYNC_COLUMNS))
    insert_query = f"INSERT INTO project_investasi ({columns_str}) VALUES"
    
    try:
        ch_client.execute(insert_query, [converted_row])
        logger.info(f"✓ Synced record: {id_root}")
        return True
    except Exception as e:
        logger.error(f"Failed to sync {id_root}: {e}")
        return False


def delete_from_clickhouse(ch_client, id_root: str):
    """
    Handle DELETE operation for ClickHouse.
    Since ClickHouse doesn't support direct DELETE easily, we use lightweight delete.
    """
    try:
        # Use ALTER TABLE ... DELETE for ReplacingMergeTree
        ch_client.execute(f"ALTER TABLE project_investasi DELETE WHERE id_root = '{id_root}'")
        logger.info(f"✓ Deleted record: {id_root}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete {id_root}: {e}")
        return False


def full_sync(ch_client, pg_conn):
    """Perform a full sync from PostgreSQL to ClickHouse."""
    logger.info("Starting full sync...")
    cursor = pg_conn.cursor()
    
    columns_str = ', '.join(SYNC_COLUMNS)
    cursor.execute(f"SELECT {columns_str} FROM project_investasi")
    rows = cursor.fetchall()
    cursor.close()
    
    if not rows:
        logger.info("No records to sync")
        return
    
    # Convert all rows
    converted_rows = []
    for row in rows:
        converted_row = tuple(convert_value(row[i], SYNC_COLUMNS[i]) for i in range(len(row)))
        converted_rows.append(converted_row)
    
    # Truncate and insert
    ch_client.execute("TRUNCATE TABLE project_investasi")
    
    insert_query = f"INSERT INTO project_investasi ({columns_str}) VALUES"
    ch_client.execute(insert_query, converted_rows)
    
    logger.info(f"✓ Full sync completed: {len(converted_rows)} records")


def process_notifications(pg_listen_conn, pg_data_conn, ch_client):
    """Process pending notifications with debouncing."""
    pending_ids = {}  # id_root -> operation
    
    # Collect all pending notifications
    pg_listen_conn.poll()
    while pg_listen_conn.notifies:
        notify = pg_listen_conn.notifies.pop(0)
        try:
            payload = json.loads(notify.payload)
            id_root = payload.get('id_root')
            operation = payload.get('operation')
            if id_root:
                pending_ids[id_root] = operation
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in notification: {notify.payload}")
    
    # Process collected changes
    synced = False
    for id_root, operation in pending_ids.items():
        if operation == 'DELETE':
            delete_from_clickhouse(ch_client, id_root)
            synced = True
        else:  # INSERT or UPDATE
            if sync_record_to_clickhouse(ch_client, pg_data_conn, id_root):
                synced = True
    
    # Run OPTIMIZE to deduplicate immediately for real-time accuracy
    if synced:
        optimize_table(ch_client)


def main():
    """Main daemon loop."""
    logger.info("=" * 50)
    logger.info("Real-Time Sync Daemon Starting...")
    logger.info(f"PostgreSQL: {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
    logger.info(f"ClickHouse: {CLICKHOUSE_CONFIG['host']}:{CLICKHOUSE_CONFIG['port']}")
    logger.info("=" * 50)
    
    retry_count = 0
    max_retries = 30
    
    while not shutdown_event.is_set() and retry_count < max_retries:
        try:
            # Create connections
            pg_listen_conn = get_postgres_connection()
            pg_data_conn = psycopg2.connect(**POSTGRES_CONFIG)
            ch_client = get_clickhouse_client()
            
            logger.info("✓ Connected to PostgreSQL and ClickHouse")
            
            # Subscribe to notifications
            cursor = pg_listen_conn.cursor()
            cursor.execute(f"LISTEN {LISTEN_CHANNEL};")
            logger.info(f"✓ Listening on channel: {LISTEN_CHANNEL}")
            
            # Perform initial full sync
            full_sync(ch_client, pg_data_conn)
            
            # Main event loop
            retry_count = 0  # Reset on successful connection
            while not shutdown_event.is_set():
                # Wait for notifications with timeout
                if select.select([pg_listen_conn], [], [], DEBOUNCE_SECONDS)[0]:
                    process_notifications(pg_listen_conn, pg_data_conn, ch_client)
            
        except psycopg2.OperationalError as e:
            retry_count += 1
            wait_time = min(30, 2 ** retry_count)
            logger.error(f"PostgreSQL connection error: {e}")
            logger.info(f"Retrying in {wait_time}s... ({retry_count}/{max_retries})")
            time.sleep(wait_time)
            
        except Exception as e:
            retry_count += 1
            wait_time = min(30, 2 ** retry_count)
            logger.error(f"Unexpected error: {e}")
            logger.info(f"Retrying in {wait_time}s... ({retry_count}/{max_retries})")
            time.sleep(wait_time)
            
        finally:
            # Clean up connections
            try:
                pg_listen_conn.close()
            except:
                pass
            try:
                pg_data_conn.close()
            except:
                pass
    
    logger.info("Sync daemon shutdown complete")


if __name__ == "__main__":
    main()
