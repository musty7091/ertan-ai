import pandas as pd

from core.config import get_excluded_sale_header_ind
from core.db import query_df
from core.sql_loader import load_sql


def run_period_profit(conn, start_date: str, end_date: str) -> pd.DataFrame:
    sql = load_sql("period_profit.sql")
    return query_df(conn, sql, [start_date, end_date, get_excluded_sale_header_ind()])
