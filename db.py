import os
import re

import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

load_dotenv()

_DB_NAME_SAFE = re.compile(r"^[a-zA-Z0-9_]+$")


def get_db_config():
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "password"),
        "database": os.getenv("MYSQL_DATABASE", "car_rental"),
    }


def ensure_database_exists():
    """Create the configured database if MySQL returns 1049. Safe for repeated calls."""
    cfg = get_db_config()
    name = cfg["database"]
    if not _DB_NAME_SAFE.match(name):
        raise ValueError("MYSQL_DATABASE must contain only letters, digits, and underscores")

    conn = pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["root"],
        password=cfg["password"],
        cursorclass=DictCursor,
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE DATABASE IF NOT EXISTS `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                % name.replace("`", "")
            )
    finally:
        conn.close()


def get_connection():
    cfg = get_db_config()
    return pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        cursorclass=DictCursor,
        autocommit=False,
    )


def ping_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return True
    finally:
        conn.close()
