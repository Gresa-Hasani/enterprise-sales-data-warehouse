"""
Executes a .sql file (statements separated by ';') against Oracle
using the given schema-owner credentials.
"""

import os

import oracledb
from dotenv import load_dotenv

load_dotenv()

DSN = f"{os.getenv('ORACLE_HOST')}:{os.getenv('ORACLE_PORT')}/{os.getenv('ORACLE_SERVICE_NAME')}"


def run_sql_file(filepath: str, user: str, password: str):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    statements = [s.strip() for s in content.split(";") if s.strip()]

    conn = oracledb.connect(user=user, password=password, dsn=DSN)
    cur = conn.cursor()
    try:
        for stmt in statements:
            cur.execute(stmt)
        conn.commit()
    finally:
        cur.close()
        conn.close()

    print(f"Executed {len(statements)} statements from {filepath} as {user}")