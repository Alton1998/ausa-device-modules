import asyncio
import os
import uuid
import threading
import logging

import pyrqlite.dbapi2 as dbapi2


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

Tables = {
    "data_sync": {
        "columns": ["data"],
        "data_type": [],
        "interval": 10  # seconds
    },
    "data_sync_1": {
        "columns": ["data"],
        "data_type": [],
        "interval": 20  # seconds
    }
}

HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", 4001))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 10))

TASKS = {}

class RqliteConnectionSingleton:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_connection(cls):
        with cls._lock:
            if cls._instance is None or not cls._is_connection_alive(cls._instance):
                logger.debug("Creating new rqlite connection")
                cls._instance = dbapi2.connect(host=HOST, port=PORT)
            return cls._instance

    @staticmethod
    def _is_connection_alive(conn):
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            return True
        except Exception as e:
            logger.warning("Rqlite connection is not alive: %s", e)
            return False

def perform_migrations():
    logger.info("Performing migrations...")
    connection = RqliteConnectionSingleton.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_sync (
                    id TEXT PRIMARY KEY NOT NULL,
                    data TEXT,
                    synced BOOLEAN DEFAULT FALSE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_sync_1 (
                    id TEXT PRIMARY KEY NOT NULL,
                    data TEXT,
                    synced BOOLEAN DEFAULT FALSE
                )
            """)
            data_value = "This is a test record"
            synced_value = False
            for _ in range(100):
                cursor.execute("""
                    INSERT INTO data_sync (id, data, synced)
                    VALUES (?, ?, ?)
                """, (str(uuid.uuid4()), data_value, synced_value))
            for _ in range(100):
                cursor.execute("""
                    INSERT INTO data_sync_1 (id, data, synced)
                    VALUES (?, ?, ?)
                """, (str(uuid.uuid4()), data_value, synced_value))
        logger.info("Migrations and data seeding complete.")
    except Exception as e:
        logger.exception("Migration error: %s", e)
    finally:
        connection.close()

async def send_to_cloud(*args, **kwargs):
    table = kwargs["table"]
    columns = kwargs.get("columns", [])
    interval = kwargs.get("interval", 10)
    batch_size = BATCH_SIZE

    while True:
        offset = 0
        rows_fetched = 0
        connection = RqliteConnectionSingleton.get_connection()

        try:
            with connection.cursor() as cursor:
                more_rows = True
                while more_rows:
                    if not columns:
                        query = f"""
                            SELECT * FROM {table}
                            WHERE synced = false
                            LIMIT {batch_size} OFFSET {offset}
                        """
                    else:
                        col_string = ", ".join(f"`{col}`" for col in columns)
                        query = f"""
                            SELECT {col_string} FROM {table}
                            WHERE synced = false
                            LIMIT {batch_size} OFFSET {offset}
                        """

                    cursor.execute(query)
                    rows = cursor.fetchall()

                    if not rows:
                        more_rows = False
                        break

                    logger.info(f"[{table}] Fetched {len(rows)} rows from offset {offset}")
                    rows_fetched += len(rows)
                    offset += batch_size

                    # Simulate cloud upload delay
                    await asyncio.sleep(0.1)

        except Exception as e:
            logger.exception(f"Error in send_to_cloud for {table}: {e}")
        finally:
            connection.close()

        logger.info(f"[{table}] Sync cycle complete. Total rows processed: {rows_fetched}")
        await asyncio.sleep(interval)

async def main():
    logger.info("Starting background sync tasks...")
    for table, value in Tables.items():
        TASKS[table] = asyncio.create_task(send_to_cloud(
            table=table,
            columns=value.get("columns", []),
            interval=value.get("interval", 10)
        ))
    await asyncio.gather(*TASKS.values())

if __name__ == "__main__":
    perform_migrations()
    asyncio.run(main())
