import os

PORT = int(os.getenv("DATAQUALITYX_PORT", "8000"))
DB_PATH = os.getenv("DATAQUALITYX_DB_PATH", "backend/data/dataqualityx.db")
