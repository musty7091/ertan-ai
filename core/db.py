import os

import pandas as pd
import pyodbc
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    server = os.getenv("SQL_SERVER")
    database = os.getenv("SQL_DATABASE")
    driver = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    username = os.getenv("SQL_USERNAME")
    password = os.getenv("SQL_PASSWORD")

    missing = [
        key
        for key, value in {
            "SQL_SERVER": server,
            "SQL_DATABASE": database,
            "SQL_USERNAME": username,
            "SQL_PASSWORD": password,
        }.items()
        if not value
    ]

    if missing:
        raise RuntimeError(f".env içinde eksik alan var: {', '.join(missing)}")

    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(conn_str, timeout=30)


def query_df(conn, sql: str, params=None) -> pd.DataFrame:
    # pandas.read_sql + pyodbc uyarısını önlemek için güvenli DataFrame yardımcı fonksiyonu.
    # DECLARE gibi ifadelerden sonra asıl SELECT result set'ine ilerler.
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or [])

        while cursor.description is None:
            if not cursor.nextset():
                return pd.DataFrame()

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        data = [tuple(row) for row in rows]

        return pd.DataFrame(data, columns=columns)

    finally:
        cursor.close()
