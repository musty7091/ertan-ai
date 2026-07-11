from __future__ import annotations

import io
import os
import re
from datetime import datetime

import pandas as pd


MONEY_COLUMNS = [
    "NetSatisKdvDahil",
    "NetSatisKdvHaric",
    "TahminiSatilanMalMaliyetiKdvHaric",
    "TahminiBrutKarKdvHaric",
    "IadeKdvDahil",
    "KartMaliyet",
    "KartAlisFiyati",
    "KullanilanBirimMaliyetKdvHaric",
    "OrtalamaSatisFiyatiKdvHaric",
]

NUMERIC_COLUMNS = [
    "NetSatisMiktari",
    "SatisSatirSayisi",
    "MaliyetEksikMi",
    "SupheliMaliyetMi",
]

PERCENT_COLUMNS = [
    "BrutKarOraniKdvHaric",
    "KullanilanMaliyetSatisOrani",
]


def safe_filename(label: str) -> str:
    clean = re.sub(r"[^0-9A-Za-zğüşöçıİĞÜŞÖÇ_-]+", "_", str(label)).strip("_")
    return f"ertan_karlilik_raporu_{clean or 'rapor'}.pdf"


def _to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    for col in MONEY_COLUMNS + NUMERIC_COLUMNS + PERCENT_COLUMNS:
        if col in d.columns:
            d[col] = _to_number(d[col])

    if "AnaKategori" in d.columns:
        d["AnaKategori"] = d["AnaKategori"].fillna("KATEGORI YOK").replace("", "KATEGORI YOK")
    else:
        d["AnaKategori"] = "KATEGORI YOK"

    if "AltKategori" in d.columns:
        d["AltKategori"] = d["AltKategori"].fillna("ALT KATEGORI YOK").replace("", "ALT KATEGORI YOK")
    else:
        d["AltKategori"] = "ALT KATEGORI YOK"

    for col in ["Barkod", "UrunAdi", "Tedarikci", "Marka", "MaliyetSaglikDurumu", "KullanilanMaliyetKaynak"]:
        if col not in d.columns:
            d[col] = ""
        d[col] = d[col].fillna("").astype(str)

    return d


def fmt_tl(value) -> str:
    try:
        if pd.isna(value):
            return "-"
        return f"{float(value):,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "-"


def fmt_num(value) -> str:
    try:
        if pd.isna(value):
            return "-"
        return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "-"


def fmt_int(value) -> str:
    try:
        if pd.isna(value):
            return "0"
        return f"{int(round(float(value))):,}".replace(",", ".")
    except Exception:
        return "0"


def fmt_pct(value) -> str:
    try:
        if pd.isna(value):
            return "-"
        return f"%{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "-"


def _register_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates_regular = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    candidates_bold = [
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\Arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    regular = next((p for p in candidates_regular if os.path.exists(p)), None)
    bold = next((p for p in candidates_bold if os.path.exists(p)), None)

    if regular:
        pdfmetrics.registerFont(TTFont("ErtanRegular", regular))
        regular_name = "ErtanRegular"
    else:
        regular_name = "Helvetica"

    if bold:
        pdfmetrics.registerFont(TTFont("ErtanBold", bold))
        bold_name = "ErtanBold"
    else:
        bold_name = "Helvetica-Bold"

    return regular_name, bold_name


def _para(text: str, style):
    from reportlab.platypus import Paragraph

    text = str(text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(text, style)


def _table(data, col_widths, styles, repeat_rows=1):
    from reportlab.platypus import Table
    from reportlab.lib import colors

    table = Table(data, colWidths=col_widths, repeatRows=repeat_rows, hAlign="LEFT")
    table.setStyle(styles)
    return table


def _base_table_style(font_regular: str, font_bold: str, font_size: int = 7):
    from reportlab.platypus import TableStyle
    from reportlab.lib import colors

    return TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_regular),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("FONTNAME", (0, 0), (-1, 0), font_bold),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAECEF")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ])


def _build_category_summary(d: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    total_sales = d["NetSatisKdvHaric"].sum(skipna=True)
    total_profit = d["TahminiBrutKarKdvHaric"].sum(skipna=True)

    grouped = (
        d.groupby(group_cols, dropna=False)
        .agg(
            UrunSayisi=("Barkod", "nunique"),
            NetSatisKdvDahil=("NetSatisKdvDahil", "sum"),
            NetSatisKdvHaric=("NetSatisKdvHaric", "sum"),
            TahminiMaliyet=("TahminiSatilanMalMaliyetiKdvHaric", "sum"),
            TahminiBrutKar=("TahminiBrutKarKdvHaric", "sum"),
            IadeKdvDahil=("IadeKdvDahil", "sum"),
            MaliyetiOlmayan=("MaliyetEksikMi", "sum"),
            Supheli=("SupheliMaliyetMi", "sum"),
        )
        .reset_index()
    )

    loss_counts = (
        d.assign(ZararEden=(d["TahminiBrutKarKdvHaric"].fillna(0) < 0).astype(int))
        .groupby(group_cols, dropna=False)["ZararEden"]
        .sum()
        .reset_index()
    )
    grouped = grouped.merge(loss_counts, on=group_cols, how="left")

    grouped["SatisPayi"] = grouped["NetSatisKdvHaric"].apply(lambda x: x / total_sales * 100 if total_sales else None)
    grouped["KarOrani"] = grouped.apply(
        lambda r: r["TahminiBrutKar"] / r["NetSatisKdvHaric"] * 100 if r["NetSatisKdvHaric"] else None,
        axis=1,
    )
    grouped["KarPayi"] = grouped["TahminiBrutKar"].apply(lambda x: x / total_profit * 100 if total_profit else None)
    grouped["Kontrol"] = grouped["MaliyetiOlmayan"].fillna(0) + grouped["Supheli"].fillna(0) + grouped["ZararEden"].fillna(0)

    return grouped.sort_values("NetSatisKdvHaric", ascending=False).reset_index(drop=True)


def _add_summary_table(story, d, styles, font_regular, font_bold):
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer

    sales_inc = d["NetSatisKdvDahil"].sum(skipna=True)
    sales_exc = d["NetSatisKdvHaric"].sum(skipna=True)
    cost = d["TahminiSatilanMalMaliyetiKdvHaric"].sum(skipna=True)
    profit = d["TahminiBrutKarKdvHaric"].sum(skipna=True)
    margin = profit / sales_exc * 100 if sales_exc else None
    missing = int(d["MaliyetEksikMi"].fillna(0).sum()) if "MaliyetEksikMi" in d.columns else 0
    suspicious = int(d["SupheliMaliyetMi"].fillna(0).sum()) if "SupheliMaliyetMi" in d.columns else 0
    loss_count = int((d["TahminiBrutKarKdvHaric"].fillna(0) < 0).sum()) if "TahminiBrutKarKdvHaric" in d.columns else 0

    rows = [
        ["Gösterge", "Değer", "Gösterge", "Değer"],
        ["Satış KDV Dahil", fmt_tl(sales_inc), "Satış KDV Hariç", fmt_tl(sales_exc)],
        ["Tahmini Maliyet", fmt_tl(cost), "Tahmini Brüt Kâr", fmt_tl(profit)],
        ["Tahmini Kâr Oranı", fmt_pct(margin), "Ürün Sayısı", fmt_int(d["Barkod"].nunique())],
        ["Maliyeti Olmayan", fmt_int(missing), "Şüpheli Maliyet", fmt_int(suspicious)],
        ["Zarar Eden Ürün", fmt_int(loss_count), "Satır Sayısı", fmt_int(len(d))],
    ]

    story.append(_table(rows, [4.3*cm, 4.1*cm, 4.3*cm, 4.1*cm], _base_table_style(font_regular, font_bold, 8)))
    story.append(Spacer(1, 0.35*cm))


def _add_category_table(story, title, summary, styles, font_regular, font_bold, level="category", max_rows=60):
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer

    if summary.empty:
        return

    story.append(_para(title, styles["Heading2"]))

    rows = []
    if level == "category":
        rows.append(["Ana Kategori", "Ürün", "Satış", "Satış Payı", "Maliyet", "Brüt Kâr", "Kâr Oranı", "Kontrol"])
        for _, r in summary.head(max_rows).iterrows():
            rows.append([
                r["AnaKategori"],
                fmt_int(r["UrunSayisi"]),
                fmt_tl(r["NetSatisKdvHaric"]),
                fmt_pct(r["SatisPayi"]),
                fmt_tl(r["TahminiMaliyet"]),
                fmt_tl(r["TahminiBrutKar"]),
                fmt_pct(r["KarOrani"]),
                fmt_int(r["Kontrol"]),
            ])
        widths = [4.4*cm, 1.2*cm, 2.6*cm, 1.8*cm, 2.6*cm, 2.6*cm, 1.8*cm, 1.3*cm]
    else:
        rows.append(["Ana Kategori", "Alt Kategori", "Ürün", "Satış", "Maliyet", "Brüt Kâr", "Kâr Oranı", "Kontrol"])
        for _, r in summary.head(max_rows).iterrows():
            rows.append([
                r["AnaKategori"],
                r["AltKategori"],
                fmt_int(r["UrunSayisi"]),
                fmt_tl(r["NetSatisKdvHaric"]),
                fmt_tl(r["TahminiMaliyet"]),
                fmt_tl(r["TahminiBrutKar"]),
                fmt_pct(r["KarOrani"]),
                fmt_int(r["Kontrol"]),
            ])
        widths = [3.5*cm, 3.5*cm, 1.1*cm, 2.5*cm, 2.5*cm, 2.5*cm, 1.6*cm, 1.2*cm]

    story.append(_table(rows, widths, _base_table_style(font_regular, font_bold, 6.5)))
    story.append(Spacer(1, 0.35*cm))


def _add_product_table(story, title, products, styles, font_regular, font_bold, max_rows=40):
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer

    if products.empty:
        return

    story.append(_para(title, styles["Heading2"]))

    rows = [["Barkod", "Ürün", "Ana Kat.", "Alt Kat.", "Satış", "Maliyet", "Brüt Kâr", "Oran", "Durum"]]
    for _, r in products.head(max_rows).iterrows():
        rows.append([
            r.get("Barkod", ""),
            r.get("UrunAdi", "")[:42],
            r.get("AnaKategori", "")[:18],
            r.get("AltKategori", "")[:18],
            fmt_tl(r.get("NetSatisKdvHaric")),
            fmt_tl(r.get("TahminiSatilanMalMaliyetiKdvHaric")),
            fmt_tl(r.get("TahminiBrutKarKdvHaric")),
            fmt_pct(r.get("BrutKarOraniKdvHaric")),
            r.get("MaliyetSaglikDurumu", "")[:28],
        ])

    widths = [2.5*cm, 5.0*cm, 2.3*cm, 2.3*cm, 2.2*cm, 2.2*cm, 2.2*cm, 1.4*cm, 3.0*cm]
    story.append(_table(rows, widths, _base_table_style(font_regular, font_bold, 5.8)))
    story.append(Spacer(1, 0.35*cm))


def build_profit_pdf(df: pd.DataFrame, report_label: str) -> bytes:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

    font_regular, font_bold = _register_fonts()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.0*cm,
        rightMargin=1.0*cm,
        topMargin=1.0*cm,
        bottomMargin=1.0*cm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ErtanTitle",
        parent=styles["Title"],
        fontName=font_bold,
        fontSize=17,
        leading=20,
        alignment=TA_LEFT,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="ErtanSub",
        parent=styles["Normal"],
        fontName=font_regular,
        fontSize=8,
        leading=10,
        textColor="#4B5563",
        spaceAfter=8,
    ))
    styles["Heading2"].fontName = font_bold
    styles["Heading2"].fontSize = 10
    styles["Heading2"].leading = 12
    styles["Normal"].fontName = font_regular
    styles["Normal"].fontSize = 8
    styles["Normal"].leading = 10

    d = _prepare_df(df)

    story = []
    story.append(_para(f"Ertan Market - Kârlılık Raporu", styles["ErtanTitle"]))
    story.append(_para(f"Rapor dönemi: {report_label}", styles["ErtanSub"]))
    story.append(_para(
        f"Oluşturma zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M')} | "
        "Not: Bu rapor muhasebe net kârı değildir; stok kartı bazlı tahmini brüt kârlılık ve maliyet sağlık kontrolüdür.",
        styles["ErtanSub"],
    ))
    story.append(Spacer(1, 0.2*cm))

    _add_summary_table(story, d, styles, font_regular, font_bold)

    category_summary = _build_category_summary(d, ["AnaKategori"])
    _add_category_table(story, "Ana kategori kârlılık özeti", category_summary, styles, font_regular, font_bold, "category", 80)

    subcategory_summary = _build_category_summary(d, ["AnaKategori", "AltKategori"])
    _add_category_table(story, "Alt kategori kârlılık özeti", subcategory_summary, styles, font_regular, font_bold, "subcategory", 120)

    story.append(PageBreak())

    loss_products = d[d["TahminiBrutKarKdvHaric"].fillna(0) < 0].sort_values("TahminiBrutKarKdvHaric", ascending=True)
    missing_cost = d[d["MaliyetEksikMi"].fillna(0) == 1].sort_values("NetSatisKdvHaric", ascending=False)
    suspicious = d[d["SupheliMaliyetMi"].fillna(0) == 1].sort_values(["MaliyetSaglikDurumu", "TahminiBrutKarKdvHaric"], ascending=[True, True])
    top_profit = d.sort_values("TahminiBrutKarKdvHaric", ascending=False)

    _add_product_table(story, "Zarar eden ürünler - ilk 40", loss_products, styles, font_regular, font_bold, 40)
    _add_product_table(story, "Maliyeti olmayan ürünler - ilk 40", missing_cost, styles, font_regular, font_bold, 40)
    _add_product_table(story, "Şüpheli maliyetli ürünler - ilk 40", suspicious, styles, font_regular, font_bold, 40)
    _add_product_table(story, "En çok kâr bırakan ürünler - ilk 40", top_profit, styles, font_regular, font_bold, 40)

    doc.build(story)
    return buffer.getvalue()
