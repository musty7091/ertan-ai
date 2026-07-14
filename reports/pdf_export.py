from __future__ import annotations

import io
import os
import re
from datetime import datetime
from math import cos, sin, radians

import pandas as pd


# v3.16.5 - Tek sayfa lüks POS özet PDF
# Amaç: Ciro - Maliyet - Karlılık + kategori dağılımı + kategori içi kar oranları
# Not: Bu PDF tek sayfa landscape A4 olarak canvas ile çizilir; uzun ürün listeleri içermez.


def safe_filename(label: str) -> str:
    clean = re.sub(r"[^0-9A-Za-zğüşöçıİĞÜŞÖÇ_-]+", "_", str(label)).strip("_")
    return f"ertan_pos_ozet_{clean or 'rapor'}.pdf"


def _num(value, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _series_sum(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns or df.empty:
        return 0.0
    return pd.to_numeric(df[col], errors="coerce").fillna(0).sum()


def _first_numeric(df: pd.DataFrame, col: str, default: float = 0.0) -> float:
    if col not in df.columns or df.empty:
        return default
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    if s.empty:
        return default
    return float(s.iloc[0])


def fmt_tl(value) -> str:
    try:
        return f"{float(value):,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "-"


def fmt_num(value) -> str:
    try:
        return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "-"


def fmt_pct(value) -> str:
    try:
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
        try:
            pdfmetrics.registerFont(TTFont("ErtanRegular", regular))
            regular_name = "ErtanRegular"
        except Exception:
            regular_name = "Helvetica"
    else:
        regular_name = "Helvetica"

    if bold:
        try:
            pdfmetrics.registerFont(TTFont("ErtanBold", bold))
            bold_name = "ErtanBold"
        except Exception:
            bold_name = "Helvetica-Bold"
    else:
        bold_name = "Helvetica-Bold"

    return regular_name, bold_name


def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    if d.empty:
        return d

    d = d.loc[:, ~d.columns.duplicated()].copy()

    numeric_cols = [
        "PosBaslikNetCiroKdvDahil", "NetSatisKdvDahil", "NetSatisKdvHaric",
        "TahminiSatilanMalMaliyetiKdvHaric", "TahminiBrutKarKdvHaric",
        "NetSatisMiktari", "FisBelgeSayisi", "FaturaBelgeSayisi", "IadeBelgeSayisi",
        "FisKdvHaric", "FaturaKdvHaric", "IadeKdvHaric",
        "MaliyetEksikMi", "MiktarUyumsuzMu", "SupheliMaliyetMi",
    ]
    if "MiktarUyumsuzMi" in d.columns and "MiktarUyumsuzMu" not in d.columns:
        d["MiktarUyumsuzMu"] = d["MiktarUyumsuzMi"]

    for col in numeric_cols:
        if col not in d.columns:
            d[col] = 0
        d[col] = pd.to_numeric(d[col], errors="coerce").fillna(0)

    for col in ["AnaKategori", "AltKategori", "Barkod", "UrunAdi"]:
        if col not in d.columns:
            d[col] = ""
        d[col] = d[col].fillna("").astype(str)

    d["AnaKategori"] = d["AnaKategori"].replace("", "KATEGORI YOK")
    d["AltKategori"] = d["AltKategori"].replace("", "ALT KATEGORI YOK")
    return d


def _category_summary(d: pd.DataFrame) -> pd.DataFrame:
    if d.empty:
        return pd.DataFrame(columns=[
            "AnaKategori", "UrunSayisi", "Ciro", "Pay", "Maliyet", "BrutKar", "KarOrani", "Kontrol"
        ])
    total = _series_sum(d, "NetSatisKdvHaric")
    grouped = (
        d.groupby("AnaKategori", dropna=False)
        .agg(
            UrunSayisi=("Barkod", "nunique"),
            Miktar=("NetSatisMiktari", "sum"),
            Ciro=("NetSatisKdvHaric", "sum"),
            Maliyet=("TahminiSatilanMalMaliyetiKdvHaric", "sum"),
            KontrolEksik=("MaliyetEksikMi", "sum"),
            KontrolMiktar=("MiktarUyumsuzMu", "sum"),
            KontrolSupheli=("SupheliMaliyetMi", "sum"),
        )
        .reset_index()
    )
    grouped["BrutKar"] = grouped["Ciro"] - grouped["Maliyet"]
    grouped["Pay"] = grouped["Ciro"].apply(lambda x: x / total * 100 if total else 0)
    grouped["KarOrani"] = grouped.apply(lambda r: r["BrutKar"] / r["Ciro"] * 100 if r["Ciro"] else 0, axis=1)
    grouped["Kontrol"] = grouped[["KontrolEksik", "KontrolMiktar", "KontrolSupheli"]].fillna(0).sum(axis=1)
    return grouped.sort_values("Ciro", ascending=False).reset_index(drop=True)


def _fit_text(c, text: str, x: float, y: float, max_width: float, font: str, size: float, min_size: float = 6.0):
    from reportlab.pdfbase.pdfmetrics import stringWidth

    text = str(text or "")
    s = size
    while s > min_size and stringWidth(text, font, s) > max_width:
        s -= 0.5
    c.setFont(font, s)
    c.drawString(x, y, text)


def _draw_round_rect(c, x, y, w, h, fill, stroke=None, radius=10, stroke_width=0.5):
    c.saveState()
    c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(stroke_width)
        c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
    else:
        c.roundRect(x, y, w, h, radius, fill=1, stroke=0)
    c.restoreState()


def _draw_kpi(c, x, y, w, h, title, value, accent, font_regular, font_bold):
    from reportlab.lib import colors

    _draw_round_rect(c, x, y, w, h, colors.HexColor("#FFFFFF"), colors.HexColor("#D8DEE9"), radius=12)
    c.setFillColor(accent)
    c.roundRect(x + 8, y + h - 13, 30, 5, 2.5, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#64748B"))
    c.setFont(font_regular, 7.4)
    c.drawString(x + 10, y + h - 27, title)
    c.setFillColor(colors.HexColor("#0F172A"))
    _fit_text(c, value, x + 10, y + 14, w - 20, font_bold, 13, min_size=8)


def _draw_donut(c, cx, cy, r, values, labels, colors_list, font_regular, font_bold):
    from reportlab.lib import colors

    total = sum(max(0, _num(v)) for v in values)
    if total <= 0:
        c.setFont(font_regular, 8)
        c.setFillColor(colors.HexColor("#64748B"))
        c.drawCentredString(cx, cy, "Veri yok")
        return

    start = 90
    for i, v in enumerate(values):
        val = max(0, _num(v))
        extent = 360 * val / total
        c.setFillColor(colors_list[i % len(colors_list)])
        c.wedge(cx - r, cy - r, cx + r, cy + r, start, extent, stroke=0, fill=1)
        start += extent

    # inner circle
    c.setFillColor(colors.HexColor("#FFFFFF"))
    c.circle(cx, cy, r * 0.58, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont(font_bold, 14)
    c.drawCentredString(cx, cy + 3, fmt_pct(100))
    c.setFont(font_regular, 6.8)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(cx, cy - 9, "Kategori payı")

    lx = cx + r + 18
    ly = cy + r - 6
    for i, (label, val) in enumerate(zip(labels, values)):
        if i >= 7:
            break
        pct = val / total * 100 if total else 0
        yy = ly - i * 16
        c.setFillColor(colors_list[i % len(colors_list)])
        c.roundRect(lx, yy - 2, 8, 8, 2, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#0F172A"))
        _fit_text(c, str(label)[:22], lx + 12, yy, 92, font_regular, 7.2, min_size=5.8)
        c.setFillColor(colors.HexColor("#475569"))
        c.setFont(font_bold, 7.2)
        c.drawRightString(lx + 155, yy, fmt_pct(pct))


def _draw_margin_bars(c, x, y, w, h, summary: pd.DataFrame, font_regular, font_bold):
    from reportlab.lib import colors

    if summary.empty:
        return
    top = summary.sort_values("Ciro", ascending=False).head(6).copy()
    max_margin = max(20, top["KarOrani"].max())
    row_h = h / max(1, len(top))
    for i, (_, r) in enumerate(top.iterrows()):
        yy = y + h - (i + 1) * row_h + 4
        label = str(r["AnaKategori"])[:20]
        margin = _num(r["KarOrani"])
        c.setFillColor(colors.HexColor("#0F172A"))
        _fit_text(c, label, x, yy + row_h - 13, 95, font_regular, 7.2, min_size=5.8)
        bar_x = x + 105
        bar_y = yy + row_h - 15
        bar_w = w - 155
        c.setFillColor(colors.HexColor("#E5E7EB"))
        c.roundRect(bar_x, bar_y, bar_w, 8, 4, fill=1, stroke=0)
        ratio = max(0, min(1, margin / max_margin))
        col = colors.HexColor("#B08D57") if margin >= 8 else colors.HexColor("#A16207")
        if margin < 3:
            col = colors.HexColor("#B91C1C")
        c.setFillColor(col)
        c.roundRect(bar_x, bar_y, bar_w * ratio, 8, 4, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#0F172A"))
        c.setFont(font_bold, 7.2)
        c.drawRightString(x + w, bar_y, fmt_pct(margin))


def _draw_category_table(c, x, y, w, h, summary: pd.DataFrame, font_regular, font_bold):
    from reportlab.lib import colors

    header_h = 20
    row_h = 18
    cols = [
        ("Kategori", 0.23),
        ("Ciro", 0.17),
        ("Pay", 0.10),
        ("Maliyet", 0.17),
        ("Brüt Kâr", 0.17),
        ("Kâr Ort.", 0.10),
        ("Kontrol", 0.06),
    ]
    col_x = [x]
    for _, frac in cols[:-1]:
        col_x.append(col_x[-1] + w * frac)

    c.setFillColor(colors.HexColor("#0F172A"))
    c.roundRect(x, y + h - header_h, w, header_h, 8, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#FFFFFF"))
    c.setFont(font_bold, 7.2)
    for i, (title, frac) in enumerate(cols):
        xx = col_x[i] + 5
        c.drawString(xx, y + h - 13, title)

    top = summary.head(7).copy()
    y0 = y + h - header_h - row_h
    for idx, (_, r) in enumerate(top.iterrows()):
        yy = y0 - idx * row_h
        c.setFillColor(colors.HexColor("#FFFFFF") if idx % 2 == 0 else colors.HexColor("#F8FAFC"))
        c.rect(x, yy, w, row_h, fill=1, stroke=0)
        c.setStrokeColor(colors.HexColor("#E5E7EB"))
        c.line(x, yy, x + w, yy)
        c.setFillColor(colors.HexColor("#0F172A"))
        c.setFont(font_regular, 6.9)
        values = [
            str(r["AnaKategori"])[:23],
            fmt_tl(r["Ciro"]),
            fmt_pct(r["Pay"]),
            fmt_tl(r["Maliyet"]),
            fmt_tl(r["BrutKar"]),
            fmt_pct(r["KarOrani"]),
            fmt_num(r["Kontrol"]),
        ]
        for i, text in enumerate(values):
            xx = col_x[i] + 5
            max_w = w * cols[i][1] - 8
            if i in [1, 2, 3, 4, 5, 6]:
                # right aligned numeric columns
                right_x = col_x[i] + w * cols[i][1] - 5
                c.drawRightString(right_x, yy + 6, text)
            else:
                _fit_text(c, text, xx, yy + 6, max_w, font_regular, 6.9, min_size=5.5)


def _draw_footer(c, width, margin, font_regular):
    from reportlab.lib import colors

    c.setFillColor(colors.HexColor("#64748B"))
    c.setFont(font_regular, 6.5)
    c.drawString(
        margin,
        18,
        "Not: Bu rapor yazarkasa/POS satışları içindir. Ofis/toptan faturalar dahil değildir. Brüt kâr = KDV hariç satış - KDV hariç satış maliyeti. Net kâr değildir.",
    )
    c.drawRightString(width - margin, 18, datetime.now().strftime("%d.%m.%Y %H:%M"))


def build_profit_pdf(df: pd.DataFrame, report_label: str) -> bytes:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors

    font_regular, font_bold = _register_fonts()
    d = _prepare_df(df)

    buffer = io.BytesIO()
    page_w, page_h = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=(page_w, page_h))

    # Palette
    navy = colors.HexColor("#0F172A")
    navy2 = colors.HexColor("#111827")
    slate = colors.HexColor("#64748B")
    bg = colors.HexColor("#F4F6FA")
    gold = colors.HexColor("#B08D57")
    green = colors.HexColor("#16803C")
    red = colors.HexColor("#B91C1C")
    blue = colors.HexColor("#2563EB")
    purple = colors.HexColor("#7C3AED")
    teal = colors.HexColor("#0F766E")
    orange = colors.HexColor("#EA580C")
    pink = colors.HexColor("#DB2777")
    chart_colors = [gold, blue, green, purple, orange, teal, pink, colors.HexColor("#475569")]

    # Background
    c.setFillColor(bg)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    margin = 28
    content_w = page_w - 2 * margin

    # Header
    c.setFillColor(navy)
    c.roundRect(margin, page_h - 78, content_w, 54, 16, fill=1, stroke=0)
    c.setFillColor(gold)
    c.roundRect(margin + 18, page_h - 43, 72, 4, 2, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(font_bold, 19)
    c.drawString(margin + 18, page_h - 57, "Ertan Market - Yazarkasa / POS Brüt Kârlılık Özeti")
    c.setFont(font_regular, 8.5)
    c.setFillColor(colors.HexColor("#CBD5E1"))
    c.drawRightString(page_w - margin - 18, page_h - 43, f"Rapor tarihi: {report_label}")
    c.drawRightString(page_w - margin - 18, page_h - 58, "Tek sayfa yönetim özeti")

    # Totals
    official_sales_inc = _first_numeric(d, "PosBaslikNetCiroKdvDahil", _series_sum(d, "NetSatisKdvDahil"))
    sales_exc = _series_sum(d, "NetSatisKdvHaric")
    cost = _series_sum(d, "TahminiSatilanMalMaliyetiKdvHaric")
    profit = sales_exc - cost
    margin_pct = profit / sales_exc * 100 if sales_exc else 0
    products = d["Barkod"].nunique() if "Barkod" in d.columns else len(d)
    control = _series_sum(d, "MaliyetEksikMi") + _series_sum(d, "MiktarUyumsuzMu") + _series_sum(d, "SupheliMaliyetMi")

    # KPI cards
    top_y = page_h - 142
    card_gap = 10
    card_w = (content_w - card_gap * 4) / 5
    cards = [
        ("Ciro KDV Dahil", fmt_tl(official_sales_inc), blue),
        ("Ciro KDV Hariç", fmt_tl(sales_exc), purple),
        ("Maliyet KDV Hariç", fmt_tl(cost), orange),
        ("Brüt Kâr", fmt_tl(profit), green if profit >= 0 else red),
        ("Brüt Kâr Oranı", fmt_pct(margin_pct), gold),
    ]
    for i, (title, value, accent) in enumerate(cards):
        _draw_kpi(c, margin + i * (card_w + card_gap), top_y, card_w, 52, title, value, accent, font_regular, font_bold)

    # Summary small strip
    strip_y = top_y - 34
    _draw_round_rect(c, margin, strip_y, content_w, 24, colors.HexColor("#FFFFFF"), colors.HexColor("#E2E8F0"), radius=9)
    c.setFillColor(slate)
    c.setFont(font_regular, 7.6)
    fis = _first_numeric(d, "FisBelgeSayisi")
    fat = _first_numeric(d, "FaturaBelgeSayisi")
    iad = _first_numeric(d, "IadeBelgeSayisi")
    qty = _series_sum(d, "NetSatisMiktari")
    c.drawString(margin + 12, strip_y + 8, f"Fiş: {fmt_num(fis)}   POS Fatura: {fmt_num(fat)}   İade Fişi: {fmt_num(iad)}")
    c.drawCentredString(page_w / 2, strip_y + 8, f"Net miktar: {fmt_num(qty)}   Ürün sayısı: {fmt_num(products)}")
    c.drawRightString(page_w - margin - 12, strip_y + 8, f"Kontrol gereken: {fmt_num(control)}")

    summary = _category_summary(d)
    top_for_donut = summary.head(6).copy()
    if len(summary) > 6:
        other = pd.DataFrame([{
            "AnaKategori": "DİĞER",
            "Ciro": summary.iloc[6:]["Ciro"].sum(),
            "Pay": summary.iloc[6:]["Ciro"].sum() / sales_exc * 100 if sales_exc else 0,
            "Maliyet": summary.iloc[6:]["Maliyet"].sum(),
            "BrutKar": summary.iloc[6:]["BrutKar"].sum(),
            "KarOrani": 0,
            "Kontrol": summary.iloc[6:]["Kontrol"].sum(),
            "UrunSayisi": summary.iloc[6:]["UrunSayisi"].sum(),
        }])
        top_for_donut = pd.concat([top_for_donut, other], ignore_index=True)

    # Chart panels
    panel_y = 222
    panel_h = 174
    left_w = 382
    right_w = content_w - left_w - 14
    _draw_round_rect(c, margin, panel_y, left_w, panel_h, colors.HexColor("#FFFFFF"), colors.HexColor("#D8DEE9"), radius=14)
    _draw_round_rect(c, margin + left_w + 14, panel_y, right_w, panel_h, colors.HexColor("#FFFFFF"), colors.HexColor("#D8DEE9"), radius=14)

    c.setFillColor(navy2)
    c.setFont(font_bold, 10)
    c.drawString(margin + 16, panel_y + panel_h - 22, "Satışların ana kategori dağılımı")
    _draw_donut(
        c,
        margin + 110,
        panel_y + 82,
        58,
        list(top_for_donut["Ciro"]),
        list(top_for_donut["AnaKategori"]),
        chart_colors,
        font_regular,
        font_bold,
    )

    c.setFillColor(navy2)
    c.setFont(font_bold, 10)
    c.drawString(margin + left_w + 30, panel_y + panel_h - 22, "Kategorilerin kendi içindeki kâr ortalamaları")
    _draw_margin_bars(c, margin + left_w + 30, panel_y + 22, right_w - 55, panel_h - 52, summary, font_regular, font_bold)

    # Bottom category table panel
    table_y = 44
    table_h = 160
    _draw_round_rect(c, margin, table_y, content_w, table_h, colors.HexColor("#FFFFFF"), colors.HexColor("#D8DEE9"), radius=14)
    c.setFillColor(navy2)
    c.setFont(font_bold, 10)
    c.drawString(margin + 16, table_y + table_h - 18, "Ana kategori özet tablosu - ciro, maliyet ve kârlılık")
    _draw_category_table(c, margin + 16, table_y + 10, content_w - 32, table_h - 36, summary, font_regular, font_bold)

    _draw_footer(c, page_w, margin, font_regular)
    c.showPage()
    c.save()
    return buffer.getvalue()
