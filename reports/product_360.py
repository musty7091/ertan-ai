import pandas as pd
import streamlit as st

from core.db import query_df
from core.formatting import format_date, format_number, format_percent, format_tl, safe_float
from core.sql_loader import load_sql


def run_product_360(conn, barkod: str) -> pd.DataFrame:
    sql = load_sql("product_360_2026.sql")
    return query_df(conn, sql, [barkod])


def render_product_360(df: pd.DataFrame):
    if df.empty:
        st.warning("Ürün için sonuç bulunamadı.")
        return

    row = df.iloc[0]

    st.subheader(f"📦 {row['UrunAdi']}")
    st.caption(
        f"Barkod: {row['Barkod']} | "
        f"Kategori: {row['AnaKategori']} / {row['AltKategori']} | "
        f"Marka: {row['Marka']}"
    )

    st.markdown("### 2026 Ürün 360")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Satış Cirosu KDV Dahil", format_tl(row["NetSatisKdvDahil"]))
    c2.metric("Satış Cirosu KDV Hariç", format_tl(row["NetSatisKdvHaric"]))
    c3.metric("Satış Adedi", format_number(row["NetSatisMiktari"]))
    c4.metric("Brüt Kâr KDV Hariç", format_tl(row["TahminiBrutKarKdvHaric_Efektif"]))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Kâr Oranı KDV Hariç", format_percent(row["BrutKarOraniKdvHaric_Efektif"]))
    c6.metric("Ort. Satış KDV Dahil", format_tl(row["OrtalamaSatisKdvDahil"]))
    c7.metric("Ort. Satış KDV Hariç", format_tl(row["OrtalamaSatisKdvHaric"]))
    c8.metric("Kart Kalan", format_number(row["KartKalan"]))

    c9, c10, c11, c12 = st.columns(4)
    c9.metric("Alış KDV Hariç", format_tl(row["NetAlisKdvHaric"]))
    c10.metric("Alış KDV Dahil", format_tl(row["NetAlisKdvDahil"]))
    c11.metric("Efektif Alış KDV Hariç", format_tl(row["EfektifAlisMaliyetiKdvHaric"]))
    c12.metric("Bedelli Alış KDV Hariç", format_tl(row["BedelliAlisOrtalamasiKdvHaric"]))

    c13, c14, c15, c16 = st.columns(4)
    c13.metric("Bedelsiz Miktar", format_number(row["BedelsizMiktar"]))
    c14.metric("Alış Miktarı", format_number(row["NetAlisMiktari"]))
    c15.metric("Gerçek Son Satış", format_date(row["SonSatisTarihi"]))
    c16.metric("Son Alış", format_date(row["SonAlisTarihi"]))

    st.divider()

    yorumlar = []

    if safe_float(row["BedelsizMiktar"]) and safe_float(row["BedelsizMiktar"]) > 0:
        yorumlar.append(
            "Bu üründe bedelsiz / %100 iskonto etkisi var. Bu nedenle efektif maliyet ve bedelli alış maliyeti ayrı yorumlanmalı."
        )

    if safe_float(row["SatisAlisMiktarFarki"]) and abs(safe_float(row["SatisAlisMiktarFarki"])) > 0:
        yorumlar.append(
            "Satış miktarı ile dönem içi alış miktarı farklı. Bu fark dönem başı stok, devir, irsaliye/fatura zaman farkı veya paket/tekli dönüşümden kaynaklanabilir."
        )

    if str(row["KartSonSatisTarihi"]) != str(row["SonSatisTarihi"]):
        yorumlar.append(
            "Stok kartındaki son satış tarihi ile gerçek satış hareketindeki son satış tarihi farklı. Raporlarda gerçek son satış tarihi satış hareketinden alınmalı."
        )

    yorumlar.append(
        "Kâr hesabında ana referans KDV hariç satış - KDV hariç alış maliyetidir. Satış KDV dahil ciro ayrıca gösterilir."
    )

    st.markdown("### Yönetici yorumu")
    for yorum in yorumlar:
        st.info(yorum)

    st.markdown("### Sonraki önerilen sorular")
    st.markdown(
        f"""
        - `{row['Barkod']} son yıllar alış satış`
        - `{row['AltKategori']} kategorisinde en kârlı ürünler`
        - `{row['AltKategori']} kategorisinde en çok satanlar`
        """
    )

    with st.expander("Detaylı tabloyu göster"):
        st.dataframe(df, width="stretch")
