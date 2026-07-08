import pandas as pd
import streamlit as st

from core.db import query_df
from core.formatting import format_number, format_percent, format_tl
from core.config import get_excluded_sale_header_ind
from core.sql_loader import load_sql


NUMERIC_COLUMNS = [
    "SatisMiktari",
    "SatisKdvDahil",
    "SatisKdvHaric",
    "AlisMiktari",
    "AlisKdvHaric",
    "AlisKdvDahil",
    "BedelsizMiktar",
    "OrtalamaSatisKdvDahil",
    "OrtalamaSatisKdvHaric",
    "OrtalamaAlisKdvHaric",
    "TahminiSatilanMalMaliyetiKdvHaric",
    "BrutKarKdvHaric",
    "BrutKarOraniKdvHaric",
    "AlisSatisMiktarFarki",
]


def run_product_yearly(conn, barkod: str) -> pd.DataFrame:
    sql = load_sql("product_yearly_sales_purchase.sql")
    return query_df(conn, sql, [barkod, get_excluded_sale_header_ind()])


def prepare_numeric_df(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()

    for column in NUMERIC_COLUMNS:
        if column in prepared.columns:
            prepared[column] = pd.to_numeric(prepared[column], errors="coerce")

    if "Yil" in prepared.columns:
        prepared["Yil"] = pd.to_numeric(prepared["Yil"], errors="coerce").astype("Int64")

    return prepared


def render_product_yearly(df: pd.DataFrame):
    if df.empty:
        st.warning("Ürün için yıllık alış-satış sonucu bulunamadı.")
        return

    df = prepare_numeric_df(df)
    first = df.iloc[0]

    st.subheader(f"📈 {first['UrunAdi']} - Son Yıllar Alış / Satış")
    st.caption(
        f"Barkod: {first['Barkod']} | "
        f"Kategori: {first['AnaKategori']} / {first['AltKategori']} | "
        f"Marka: {first['Marka']}"
    )

    total_sales_qty = df["SatisMiktari"].sum(skipna=True)
    total_purchase_qty = df["AlisMiktari"].sum(skipna=True)
    total_sales_vat_inc = df["SatisKdvDahil"].sum(skipna=True)
    total_sales_vat_exc = df["SatisKdvHaric"].sum(skipna=True)
    total_purchase_vat_exc = df["AlisKdvHaric"].sum(skipna=True)
    total_cogs = df["TahminiSatilanMalMaliyetiKdvHaric"].sum(skipna=True)
    total_profit = df["BrutKarKdvHaric"].sum(skipna=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Satış Adedi", format_number(total_sales_qty))
    c2.metric("Satış KDV Dahil", format_tl(total_sales_vat_inc))
    c3.metric("Satış KDV Hariç", format_tl(total_sales_vat_exc))
    c4.metric("Tahmini Brüt Kâr", format_tl(total_profit))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Toplam Alış Adedi", format_number(total_purchase_qty))
    c6.metric("Alış Hacmi KDV Hariç", format_tl(total_purchase_vat_exc))
    c7.metric("Tahmini Satılan Mal Maliyeti", format_tl(total_cogs))
    c8.metric(
        "Tahmini Kâr Oranı",
        format_percent((total_profit / total_sales_vat_exc * 100) if total_sales_vat_exc else None),
    )

    st.divider()

    st.info(
        "Bu raporda alış toplamı ayrı, satılan mal maliyeti ayrı gösterilir. "
        "Brüt kâr; toplam alıştan değil, satılan miktarın tahmini maliyetinden hesaplanır."
    )

    chart_df = df[["Yil", "SatisMiktari", "AlisMiktari"]].copy()
    chart_df = chart_df.fillna(0)
    chart_df["Yil"] = chart_df["Yil"].astype(str)
    chart_df = chart_df.set_index("Yil")

    st.markdown("### Yıllık miktar trendi")
    st.line_chart(chart_df)

    amount_df = df[
        [
            "Yil",
            "SatisKdvHaric",
            "AlisKdvHaric",
            "TahminiSatilanMalMaliyetiKdvHaric",
            "BrutKarKdvHaric",
        ]
    ].copy()
    amount_df = amount_df.fillna(0)
    amount_df["Yil"] = amount_df["Yil"].astype(str)
    amount_df = amount_df.set_index("Yil")

    st.markdown("### Yıllık tutar trendi KDV hariç")
    st.line_chart(amount_df)

    display = df.copy()

    money_cols = [
        "SatisKdvDahil",
        "SatisKdvHaric",
        "AlisKdvHaric",
        "AlisKdvDahil",
        "OrtalamaSatisKdvDahil",
        "OrtalamaSatisKdvHaric",
        "OrtalamaAlisKdvHaric",
        "TahminiSatilanMalMaliyetiKdvHaric",
        "BrutKarKdvHaric",
    ]
    number_cols = [
        "SatisMiktari",
        "AlisMiktari",
        "BedelsizMiktar",
        "AlisSatisMiktarFarki",
    ]
    percent_cols = ["BrutKarOraniKdvHaric"]

    for col in money_cols:
        if col in display.columns:
            display[col] = display[col].apply(format_tl)

    for col in number_cols:
        if col in display.columns:
            display[col] = display[col].apply(format_number)

    for col in percent_cols:
        if col in display.columns:
            display[col] = display[col].apply(format_percent)

    rename_map = {
        "SatisMiktari": "Satış Miktarı",
        "SatisKdvDahil": "Satış KDV Dahil",
        "SatisKdvHaric": "Satış KDV Hariç",
        "AlisMiktari": "Alış Miktarı",
        "AlisKdvHaric": "Alış Hacmi KDV Hariç",
        "AlisKdvDahil": "Alış Hacmi KDV Dahil",
        "BedelsizMiktar": "Bedelsiz Miktar",
        "OrtalamaSatisKdvDahil": "Ort. Satış KDV Dahil",
        "OrtalamaSatisKdvHaric": "Ort. Satış KDV Hariç",
        "OrtalamaAlisKdvHaric": "Ort. Alış KDV Hariç",
        "TahminiSatilanMalMaliyetiKdvHaric": "Tahmini Satılan Mal Maliyeti",
        "BrutKarKdvHaric": "Tahmini Brüt Kâr",
        "BrutKarOraniKdvHaric": "Tahmini Kâr Oranı",
        "AlisSatisMiktarFarki": "Satış - Alış Miktar Farkı",
    }

    display = display.rename(columns=rename_map)

    st.markdown("### Yıllık detay")
    st.dataframe(display, width="stretch")

    st.warning(
        "Not: Aynı yıl içinde alış kaydı olmayan fakat satış olan yıllarda kâr hesabı eksik kalabilir. "
        "Bir sonraki aşamada stok devir maliyeti / dönem başı stok mantığını da eklemeliyiz."
    )
