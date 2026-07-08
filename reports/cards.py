# -*- coding: utf-8 -*-
"""
Net cevap karti: her rapor icin 4-5 kilit sayi + kisa yorum + katlanir detay.
Kartlar sohbet gecmisinde saklanip yeniden cizilebilir (df kartin icinde tasinir).
"""

import streamlit as st

from core.comments import comment_category, comment_product_360, comment_product_yearly
from core.config import get_report_year
from core.formatting import format_number, format_percent, format_tl, safe_float


def build_product_360_card(df) -> dict:
    row = df.iloc[0]
    return {
        "report_type": "product_360",
        "title": f"📦 {row['UrunAdi']}",
        "subtitle": f"{get_report_year()} Ürün 360 · Barkod {row['Barkod']} · {row['AnaKategori'] or ''} / {row['AltKategori'] or ''}",
        "metrics": [
            ("Satış", f"{format_number(row['NetSatisMiktari'])} adet"),
            ("Ciro (KDV Hariç)", format_tl(row["NetSatisKdvHaric"])),
            ("Brüt Kâr", format_tl(row["TahminiBrutKarKdvHaric_Efektif"])),
            ("Kâr Oranı", format_percent(row["BrutKarOraniKdvHaric_Efektif"])),
            ("Stok", format_number(row["KartKalan"])),
        ],
        "comments": comment_product_360(row),
        "df": df,
        "extra": {},
    }


def build_product_yearly_card(df) -> dict:
    first = df.iloc[0]
    d = df[df["SatisMiktari"].fillna(0) > 0].sort_values("Yil")
    son = d.iloc[-1] if not d.empty else None
    metrics = []
    if son is not None:
        metrics = [
            (f"{int(son['Yil'])} Satış", f"{format_number(son['SatisMiktari'])} adet"),
            (f"{int(son['Yil'])} Ciro", format_tl(son["SatisKdvHaric"])),
            (f"{int(son['Yil'])} Brüt Kâr", format_tl(son["BrutKarKdvHaric"])),
            (f"{int(son['Yil'])} Kâr Oranı", format_percent(son["BrutKarOraniKdvHaric"])),
            ("Veri Yılı", f"{len(d)} yıl"),
        ]
    return {
        "report_type": "product_yearly",
        "title": f"📈 {first['UrunAdi']}",
        "subtitle": f"Son Yıllar Alış / Satış · Barkod {first['Barkod']}",
        "metrics": metrics,
        "comments": comment_product_yearly(df),
        "df": df,
        "extra": {},
    }


def build_category_card(df, category: str) -> dict:
    toplam_satis = df["NetSatisKdvHaric"].sum()
    toplam_kar = df["TahminiBrutKarKdvHaric"].sum()
    oran = (safe_float(toplam_kar) / safe_float(toplam_satis) * 100) if safe_float(toplam_satis) else None
    lider = df.iloc[0]["UrunAdi"] if not df.empty else "-"
    return {
        "report_type": "category_profit",
        "title": f"🏷️ {category}",
        "subtitle": f"{get_report_year()} Kategori Kârlılık · {len(df)} ürün",
        "metrics": [
            ("Satış (KDV Hariç)", format_tl(toplam_satis)),
            ("Brüt Kâr", format_tl(toplam_kar)),
            ("Kâr Oranı", format_percent(oran)),
            ("En Kârlı", str(lider)[:22]),
        ],
        "comments": comment_category(df, category),
        "df": df,
        "extra": {"category": category},
    }


def render_card(card: dict):
    from reports.category_profit import render_category_profit
    from reports.product_360 import render_product_360
    from reports.product_yearly import render_product_yearly

    with st.container(border=True):
        st.markdown(f"**{card['title']}**")
        st.caption(card["subtitle"])

        if card["metrics"]:
            cols = st.columns(len(card["metrics"]))
            for col, (label, value) in zip(cols, card["metrics"]):
                col.metric(label, value)

        for level, text in card.get("comments", []):
            icon = {"success": "✅", "warning": "⚠️", "info": "💬"}.get(level, "💬")
            st.markdown(f"{icon} {text}")

        with st.expander("🔎 Tüm detaylar"):
            if card["report_type"] == "product_360":
                render_product_360(card["df"])
            elif card["report_type"] == "product_yearly":
                render_product_yearly(card["df"])
            elif card["report_type"] == "category_profit":
                render_category_profit(card["df"], card["extra"].get("category", ""))
