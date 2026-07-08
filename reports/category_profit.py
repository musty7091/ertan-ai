import pandas as pd
import streamlit as st

from core.db import query_df
from core.formatting import format_tl
from core.config import get_excluded_sale_header_ind, get_report_date_range, get_report_year
from core.sql_loader import load_sql


def run_category_profit(conn, category: str, limit: int = 50) -> pd.DataFrame:
    sql = load_sql("category_profit_2026.sql")
    baslangic, bitis = get_report_date_range()
    return query_df(conn, sql, [category, limit, baslangic, bitis, get_excluded_sale_header_ind()])


def render_category_profit(df: pd.DataFrame, category: str):
    if df.empty:
        st.warning(f"{category} kategorisi için sonuç bulunamadı.")
        return

    st.subheader(f"🏷️ {category} - {get_report_year()} Kategori Kârlılık Raporu")

    total_sales = df["NetSatisKdvHaric"].sum()
    total_profit = df["TahminiBrutKarKdvHaric"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ürün Sayısı", f"{len(df)}")
    c2.metric("Satış KDV Hariç", format_tl(total_sales))
    c3.metric("Tahmini Brüt Kâr", format_tl(total_profit))

    profit_rate = None
    if total_sales:
        profit_rate = total_profit / total_sales * 100
    c4.metric(
        "Kategori Kâr Oranı",
        f"%{profit_rate:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if profit_rate is not None else "-"
    )

    st.markdown("### En kârlı ürünler")
    st.dataframe(df, width="stretch")

    st.markdown("### Grafik")
    chart_df = df.head(15)[["UrunAdi", "TahminiBrutKarKdvHaric"]].copy()
    chart_df = chart_df.set_index("UrunAdi")
    st.bar_chart(chart_df)

    st.info(f"Kategori raporu {get_report_year()} satış ve alış faturası verilerine göre hesaplanır. Brüt kâr KDV hariç mantıkla gösterilir.")
