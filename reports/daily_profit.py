import pandas as pd
import streamlit as st

from core.config import get_excluded_sale_header_ind
from core.db import query_df
from core.formatting import format_number, format_percent, format_tl
from core.sql_loader import load_sql


NUMERIC_COLUMNS = [
    "PosBelgeSayisi", "FisBelgeSayisi", "FaturaBelgeSayisi", "IadeBelgeSayisi", "PosSatisBelgeSayisi",
    "PosBaslikNetCiroKdvDahil", "PosBaslikFisCiroKdvDahil", "PosBaslikFaturaCiroKdvDahil", "PosBaslikIadeKdvDahil",
    "SatisSatirSayisi", "SatisBelgeSayisi", "NetSatisMiktari", "NetSatisKdvDahil", "NetSatisKdvHaric",
    "OrtalamaSatisFiyatiKdvHaric", "FisMiktar", "FisKdvDahil", "FisKdvHaric", "FaturaMiktar",
    "FaturaKdvDahil", "FaturaKdvHaric", "IadeMiktari", "IadeKdvDahil", "IadeKdvHaric",
    "KartMaliyet", "KartAlisFiyati", "KartKalan", "Stok101CikisMiktari", "Stok101SatisKdvHaric",
    "Stok101Maliyet", "Stok101AgirlikliBirimMaliyet", "Stok21CikisMiktari", "Stok21SatisKdvHaric",
    "Stok21Maliyet", "Stok21AgirlikliBirimMaliyet", "Stok102GirisMiktari", "Stok102IadeKdvHaric",
    "IadeBirimMaliyet", "FisMaliyet", "FaturaMaliyet", "IadeMaliyet",
    "TahminiSatilanMalMaliyetiKdvHaric", "TahminiBrutKarKdvHaric", "BrutKarOraniKdvHaric",
    "KullanilanBirimMaliyetKdvHaric", "StokHareketNetCikisMiktari", "StokHareketSatisTutari",
    "KullanilanMaliyetSatisOrani", "SonAlisSatisOrani", "SonAlisKartMaliyetFarkYuzde",
    "MaliyetEksikMi", "MiktarUyumsuzMu", "SupheliMaliyetMi",
]

MONEY_COLUMNS = [
    "PosBaslikNetCiroKdvDahil", "PosBaslikFisCiroKdvDahil", "PosBaslikFaturaCiroKdvDahil", "PosBaslikIadeKdvDahil",
    "NetSatisKdvDahil", "NetSatisKdvHaric", "OrtalamaSatisFiyatiKdvHaric",
    "FisKdvDahil", "FisKdvHaric", "FaturaKdvDahil", "FaturaKdvHaric", "IadeKdvDahil", "IadeKdvHaric",
    "KartMaliyet", "KartAlisFiyati", "Stok101SatisKdvHaric", "Stok101Maliyet", "Stok101AgirlikliBirimMaliyet",
    "Stok21SatisKdvHaric", "Stok21Maliyet", "Stok21AgirlikliBirimMaliyet", "Stok102IadeKdvHaric",
    "IadeBirimMaliyet", "FisMaliyet", "FaturaMaliyet", "IadeMaliyet",
    "TahminiSatilanMalMaliyetiKdvHaric", "TahminiBrutKarKdvHaric", "KullanilanBirimMaliyetKdvHaric",
    "StokHareketSatisTutari", "TahminiMaliyetSonAlisKdvHaric", "TahminiKarSonAlisKdvHaric",
]

NUMBER_COLUMNS = [
    "PosBelgeSayisi", "FisBelgeSayisi", "FaturaBelgeSayisi", "IadeBelgeSayisi", "PosSatisBelgeSayisi",
    "SatisSatirSayisi", "SatisBelgeSayisi", "NetSatisMiktari", "FisMiktar", "FaturaMiktar", "IadeMiktari",
    "KartKalan", "Stok101CikisMiktari", "Stok21CikisMiktari", "Stok102GirisMiktari", "StokHareketNetCikisMiktari",
    "MaliyetEksikMi", "MiktarUyumsuzMu", "SupheliMaliyetMi",
]

PERCENT_COLUMNS = [
    "BrutKarOraniKdvHaric", "KullanilanMaliyetSatisOrani", "SonAlisSatisOrani", "SonAlisKartMaliyetFarkYuzde",
]

RENAME_MAP = {
    "RaporTarihi": "Rapor Tarihi",
    "Barkod": "Barkod",
    "UrunAdi": "Ürün Adı",
    "Tedarikci": "Tedarikçi",
    "AnaKategori": "Ana Kategori",
    "AltKategori": "Alt Kategori",
    "Marka": "Marka",
    "PosBelgeSayisi": "POS Belge",
    "FisBelgeSayisi": "Fiş",
    "FaturaBelgeSayisi": "POS Fatura",
    "IadeBelgeSayisi": "İade Fişi",
    "PosSatisBelgeSayisi": "Satış Belgesi",
    "PosBaslikNetCiroKdvDahil": "POS Ciro KDV Dahil",
    "PosBaslikFisCiroKdvDahil": "Fiş Ciro KDV Dahil",
    "PosBaslikFaturaCiroKdvDahil": "Fatura Ciro KDV Dahil",
    "PosBaslikIadeKdvDahil": "İade KDV Dahil",
    "SatisSatirSayisi": "Satış Satırı",
    "SatisBelgeSayisi": "Belge Sayısı",
    "NetSatisMiktari": "Net Miktar",
    "NetSatisKdvDahil": "Satış KDV Dahil",
    "NetSatisKdvHaric": "Satış KDV Hariç",
    "OrtalamaSatisFiyatiKdvHaric": "Ort. Satış KDV Hariç",
    "FisMiktar": "Fiş Miktarı",
    "FisKdvHaric": "Fiş KDV Hariç",
    "FaturaMiktar": "Fatura Miktarı",
    "FaturaKdvHaric": "Fatura KDV Hariç",
    "IadeMiktari": "İade Miktarı",
    "IadeKdvHaric": "İade KDV Hariç",
    "KartMaliyet": "Kart Maliyet",
    "KartAlisFiyati": "Kart Alış",
    "KartKalan": "Kart Kalan",
    "FisMaliyet": "Fiş Maliyeti",
    "FaturaMaliyet": "Fatura Maliyeti",
    "IadeMaliyet": "İade Maliyeti",
    "TahminiSatilanMalMaliyetiKdvHaric": "Satılan Mal Maliyeti",
    "TahminiBrutKarKdvHaric": "Brüt Kâr",
    "BrutKarOraniKdvHaric": "Brüt Kâr Oranı",
    "KullanilanBirimMaliyetKdvHaric": "Kullanılan Birim Maliyet",
    "StokHareketNetCikisMiktari": "Stok Hareket Net Miktar",
    "KullanilanMaliyetKaynak": "Maliyet Kaynağı",
    "KullanilanMaliyetSatisOrani": "Maliyet / Satış",
    "MaliyetEksikMi": "Maliyet Eksik",
    "MiktarUyumsuzMu": "Miktar Uyumsuz",
    "SupheliMaliyetMi": "Şüpheli",
    "MaliyetSaglikDurumu": "Kontrol Durumu",
}


def run_daily_profit(conn, report_date: str) -> pd.DataFrame:
    sql = load_sql("daily_profit.sql")
    return query_df(conn, sql, [report_date, get_excluded_sale_header_ind()])


def _dedupe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """SQL Server result sets can accidentally return duplicate aliases.
    Pandas then returns a DataFrame instead of a Series for df[column], which
    breaks pd.to_numeric. Keep the first occurrence so the report does not crash.
    """
    if df.empty:
        return df.copy()
    return df.loc[:, ~df.columns.duplicated()].copy()


def _series(df: pd.DataFrame, column: str):
    if column not in df.columns:
        return pd.Series(dtype="float64")
    value = df[column]
    if isinstance(value, pd.DataFrame):
        value = value.iloc[:, 0]
    return value


def prepare_numeric_df(df: pd.DataFrame) -> pd.DataFrame:
    prepared = _dedupe_columns(df)

    # v3.16.4 güvenlik katmanı:
    # Eski SQL dosyası / kolon adı farkı / boş sonuç yüzünden rapor ekranı çökmesin.
    # Eksik kontrol kolonlarını 0 kabul ediyoruz; finansal hesap kolonları SQL'den gelmelidir,
    # gelmezse ekranda hatalı KeyError üretmek yerine 0 görünür ve kontrol edilebilir.
    if "MiktarUyumsuzMi" in prepared.columns and "MiktarUyumsuzMu" not in prepared.columns:
        prepared["MiktarUyumsuzMu"] = prepared["MiktarUyumsuzMi"]

    for column in NUMERIC_COLUMNS:
        if column not in prepared.columns:
            prepared[column] = 0
        prepared[column] = pd.to_numeric(_series(prepared, column), errors="coerce").fillna(0)

    for column in ["AnaKategori", "AltKategori", "UrunAdi", "Barkod", "Tedarikci", "Marka"]:
        if column not in prepared.columns:
            prepared[column] = ""

    for column in ["KullanilanMaliyetKaynak", "MaliyetSaglikDurumu"]:
        if column not in prepared.columns:
            prepared[column] = ""

    return prepared


def _first_value(df: pd.DataFrame, column: str, default=0):
    if column not in df.columns or df.empty:
        return default
    series = pd.to_numeric(_series(df, column), errors="coerce").dropna()
    if series.empty:
        return default
    return series.iloc[0]


def _safe_sum(df: pd.DataFrame, column: str) -> float:
    if column not in df.columns or df.empty:
        return 0.0
    return pd.to_numeric(_series(df, column), errors="coerce").fillna(0).sum()


def _format_display(df: pd.DataFrame) -> pd.DataFrame:
    display = df.copy()

    for col in MONEY_COLUMNS:
        if col in display.columns:
            display[col] = display[col].apply(format_tl)

    for col in NUMBER_COLUMNS:
        if col in display.columns:
            display[col] = display[col].apply(format_number)

    for col in PERCENT_COLUMNS:
        if col in display.columns:
            display[col] = display[col].apply(format_percent)

    return display.rename(columns=RENAME_MAP)


def _show_table(df: pd.DataFrame, empty_message: str):
    if df.empty:
        st.success(empty_message)
    else:
        st.dataframe(_format_display(df), width="stretch")


def build_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    d = df.copy()
    d["AnaKategori"] = d["AnaKategori"].fillna("KATEGORİ YOK").replace("", "KATEGORİ YOK")

    total_sales = _safe_sum(d, "NetSatisKdvHaric")
    total_profit = _safe_sum(d, "TahminiBrutKarKdvHaric")
    total_sales_inc = _safe_sum(d, "NetSatisKdvDahil")

    grouped = (
        d.groupby("AnaKategori", dropna=False)
        .agg(
            UrunSayisi=("Barkod", "nunique"),
            SatisSatiri=("SatisSatirSayisi", "sum"),
            NetSatisMiktari=("NetSatisMiktari", "sum"),
            NetSatisKdvDahil=("NetSatisKdvDahil", "sum"),
            NetSatisKdvHaric=("NetSatisKdvHaric", "sum"),
            FisKdvHaric=("FisKdvHaric", "sum"),
            FaturaKdvHaric=("FaturaKdvHaric", "sum"),
            IadeKdvHaric=("IadeKdvHaric", "sum"),
            Maliyet=("TahminiSatilanMalMaliyetiKdvHaric", "sum"),
            BrutKar=("TahminiBrutKarKdvHaric", "sum"),
            MaliyetEksik=("MaliyetEksikMi", "sum"),
            MiktarUyumsuz=("MiktarUyumsuzMu", "sum"),
            Supheli=("SupheliMaliyetMi", "sum"),
        )
        .reset_index()
    )

    grouped["CiroPayiYuzde"] = grouped["NetSatisKdvHaric"].apply(lambda v: (v / total_sales * 100) if total_sales else None)
    grouped["KdvDahilCiroPayiYuzde"] = grouped["NetSatisKdvDahil"].apply(lambda v: (v / total_sales_inc * 100) if total_sales_inc else None)
    grouped["KarOraniYuzde"] = grouped.apply(
        lambda r: (r["BrutKar"] / r["NetSatisKdvHaric"] * 100) if r["NetSatisKdvHaric"] else None,
        axis=1,
    )
    grouped["BrutKarPayiYuzde"] = grouped["BrutKar"].apply(lambda v: (v / total_profit * 100) if total_profit else None)
    grouped["KontrolGereken"] = grouped[["MaliyetEksik", "MiktarUyumsuz", "Supheli"]].fillna(0).sum(axis=1)

    return grouped.sort_values("NetSatisKdvHaric", ascending=False).reset_index(drop=True)


def build_subcategory_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    d = df.copy()
    d["AnaKategori"] = d["AnaKategori"].fillna("KATEGORİ YOK").replace("", "KATEGORİ YOK")
    d["AltKategori"] = d["AltKategori"].fillna("ALT KATEGORİ YOK").replace("", "ALT KATEGORİ YOK")
    grouped = (
        d.groupby(["AnaKategori", "AltKategori"], dropna=False)
        .agg(
            UrunSayisi=("Barkod", "nunique"),
            NetSatisMiktari=("NetSatisMiktari", "sum"),
            NetSatisKdvHaric=("NetSatisKdvHaric", "sum"),
            Maliyet=("TahminiSatilanMalMaliyetiKdvHaric", "sum"),
            BrutKar=("TahminiBrutKarKdvHaric", "sum"),
            Supheli=("SupheliMaliyetMi", "sum"),
        )
        .reset_index()
    )
    grouped["KarOraniYuzde"] = grouped.apply(
        lambda r: (r["BrutKar"] / r["NetSatisKdvHaric"] * 100) if r["NetSatisKdvHaric"] else None,
        axis=1,
    )
    return grouped.sort_values(["AnaKategori", "NetSatisKdvHaric"], ascending=[True, False]).reset_index(drop=True)


def _format_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    display = df.copy()
    money_cols = ["NetSatisKdvDahil", "NetSatisKdvHaric", "FisKdvHaric", "FaturaKdvHaric", "IadeKdvHaric", "Maliyet", "BrutKar"]
    number_cols = ["UrunSayisi", "SatisSatiri", "NetSatisMiktari", "MaliyetEksik", "MiktarUyumsuz", "Supheli", "KontrolGereken"]
    percent_cols = ["CiroPayiYuzde", "KdvDahilCiroPayiYuzde", "KarOraniYuzde", "BrutKarPayiYuzde"]

    for col in money_cols:
        if col in display.columns:
            display[col] = display[col].apply(format_tl)
    for col in number_cols:
        if col in display.columns:
            display[col] = display[col].apply(format_number)
    for col in percent_cols:
        if col in display.columns:
            display[col] = display[col].apply(format_percent)

    return display.rename(columns={
        "AnaKategori": "Ana Kategori",
        "AltKategori": "Alt Kategori",
        "UrunSayisi": "Ürün Sayısı",
        "SatisSatiri": "Satış Satırı",
        "NetSatisMiktari": "Satış Miktarı",
        "NetSatisKdvDahil": "Ciro KDV Dahil",
        "NetSatisKdvHaric": "Ciro KDV Hariç",
        "FisKdvHaric": "Fiş Ciro",
        "FaturaKdvHaric": "Fatura Ciro",
        "IadeKdvHaric": "İade",
        "CiroPayiYuzde": "Ciro Payı",
        "KdvDahilCiroPayiYuzde": "KDV Dahil Ciro Payı",
        "Maliyet": "Maliyet",
        "BrutKar": "Brüt Kâr",
        "KarOraniYuzde": "Brüt Kâr Oranı",
        "BrutKarPayiYuzde": "Brüt Kâr Payı",
        "MaliyetEksik": "Maliyet Eksik",
        "MiktarUyumsuz": "Miktar Uyumsuz",
        "Supheli": "Şüpheli",
        "KontrolGereken": "Kontrol Gereken",
    })


def _executive_comment(category_summary: pd.DataFrame, total_sales_exc: float, total_profit: float) -> str:
    if category_summary.empty:
        return "Kategori özeti oluşturulamadı."
    top_sales = category_summary.sort_values("NetSatisKdvHaric", ascending=False).iloc[0]
    top_profit = category_summary.sort_values("BrutKar", ascending=False).iloc[0]
    weak = category_summary.sort_values("KarOraniYuzde", ascending=True).iloc[0]
    return (
        f"Bugün POS cirosunu en çok **{top_sales['AnaKategori']}** taşıdı "
        f"({format_percent(top_sales.get('CiroPayiYuzde'))} ciro payı). "
        f"Brüt kâr katkısında en güçlü ana kategori **{top_profit['AnaKategori']}** oldu "
        f"({format_tl(top_profit.get('BrutKar'))}). "
        f"Marjı en zayıf kategori **{weak['AnaKategori']}** görünüyor "
        f"({format_percent(weak.get('KarOraniYuzde'))}). "
        f"Toplam KDV hariç POS satış {format_tl(total_sales_exc)}, brüt kâr {format_tl(total_profit)}."
    )


def render_daily_profit(df: pd.DataFrame, report_date: str, show_summary: bool = True):
    if df.empty:
        st.warning(f"{report_date} tarihi için POS satış verisi bulunamadı.")
        return

    df = prepare_numeric_df(df)

    official_sales_inc = _first_value(df, "PosBaslikNetCiroKdvDahil", _safe_sum(df, "NetSatisKdvDahil"))
    total_sales_inc = _safe_sum(df, "NetSatisKdvDahil")
    total_sales_exc = _safe_sum(df, "NetSatisKdvHaric")
    total_qty = _safe_sum(df, "NetSatisMiktari")
    total_cost = _safe_sum(df, "TahminiSatilanMalMaliyetiKdvHaric")
    total_profit = _safe_sum(df, "TahminiBrutKarKdvHaric")
    profit_rate = (total_profit / total_sales_exc * 100) if total_sales_exc else None
    profit_rate_inc = (total_profit / official_sales_inc * 100) if official_sales_inc else None

    fis_count = _first_value(df, "FisBelgeSayisi")
    fatura_count = _first_value(df, "FaturaBelgeSayisi")
    iade_count = _first_value(df, "IadeBelgeSayisi")
    sales_doc_count = _first_value(df, "PosSatisBelgeSayisi")
    avg_receipt = official_sales_inc / sales_doc_count if sales_doc_count else None

    total_fis = _safe_sum(df, "FisKdvHaric")
    total_fatura = _safe_sum(df, "FaturaKdvHaric")
    total_iade = _safe_sum(df, "IadeKdvHaric")
    total_fis_cost = _safe_sum(df, "FisMaliyet")
    total_fatura_cost = _safe_sum(df, "FaturaMaliyet")
    total_iade_cost = _safe_sum(df, "IadeMaliyet")

    missing_cost = df[df["MaliyetEksikMi"].fillna(0) == 1].copy()
    mismatch = df[df["MiktarUyumsuzMu"].fillna(0) == 1].copy()
    suspicious = df[df["SupheliMaliyetMi"].fillna(0) == 1].copy()
    loss_products = df[df["TahminiBrutKarKdvHaric"].fillna(0) < 0].copy()

    category_summary = build_category_summary(df)
    subcategory_summary = build_subcategory_summary(df)

    if show_summary:
        st.subheader(f"🧾 {report_date} Yazarkasa / POS Brüt Kârlılık Raporu")
        st.caption("Kapsam: yazarkasa/POS sisteminden geçen FİŞ + FATURA - İADE FİŞİ. Maliyet motoru v3.16.4: POS PBI satırları + son bilinen ürün maliyeti + çakışan kolon düzeltmesi. Ofis/toptan faturalar dahil değildir.")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Net POS Ciro KDV Dahil", format_tl(official_sales_inc))
        c2.metric("Net POS Ciro KDV Hariç", format_tl(total_sales_exc))
        c3.metric("Satış Maliyeti", format_tl(total_cost))
        c4.metric("Brüt Kâr", format_tl(total_profit))

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Brüt Kâr Oranı", format_percent(profit_rate))
        c6.metric("KDV Dahil Ciroya Göre", format_percent(profit_rate_inc))
        c7.metric("Net Satış Miktarı", format_number(total_qty))
        c8.metric("Ortalama Belge", format_tl(avg_receipt))

        c9, c10, c11, c12 = st.columns(4)
        c9.metric("Fiş", format_number(fis_count))
        c10.metric("POS Fatura", format_number(fatura_count))
        c11.metric("İade Fişi", format_number(iade_count))
        c12.metric("Ürün Sayısı", format_number(len(df)))

        c13, c14, c15, c16 = st.columns(4)
        c13.metric("Fiş Ciro KDV Hariç", format_tl(total_fis))
        c14.metric("Fatura Ciro KDV Hariç", format_tl(total_fatura))
        c15.metric("İade KDV Hariç", format_tl(total_iade))
        c16.metric("Kontrol Gereken", format_number(len(missing_cost) + len(mismatch) + len(suspicious)))

        with st.container(border=True):
            st.markdown("### Yönetici yorumu")
            st.markdown(_executive_comment(category_summary, total_sales_exc, total_profit))

    if abs(official_sales_inc - total_sales_inc) > 5:
        st.warning(
            "Başlık POS cirosu ile ürün satır toplamı arasında fark var. "
            f"Başlık: {format_tl(official_sales_inc)}, Ürün hareket toplamı: {format_tl(total_sales_inc)}."
        )

    st.info(
        "Bu rapor net kâr değildir; personel, kira, elektrik, fire, finansman ve operasyon giderleri dahil değildir. "
        "Gösterilen sonuç yazarkasa/POS satışları için stok hareketlerinden hesaplanan brüt kârdır."
    )

    tabs = st.tabs([
        "Ana kategori lüks özet",
        "Kategori içi kârlılık",
        "Kanal kırılımı",
        "En çok ciro",
        "En çok brüt kâr",
        "Zayıf / zarar edenler",
        "Kontrol uyarıları",
        "Tüm ürün detayları",
    ])

    with tabs[0]:
        st.markdown("### Ana kategori ciro dağılımı ve kârlılık")
        if category_summary.empty:
            st.warning("Ana kategori özeti oluşturulamadı.")
        else:
            st.dataframe(_format_category_summary(category_summary), width="stretch")
            chart_df = category_summary[["AnaKategori", "NetSatisKdvHaric", "BrutKar"]].copy().set_index("AnaKategori")
            st.markdown("### Ciro ve brüt kâr grafiği")
            st.bar_chart(chart_df)
            pay_df = category_summary[["AnaKategori", "CiroPayiYuzde", "KarOraniYuzde"]].copy().set_index("AnaKategori")
            st.markdown("### Ciro payı ve kategori içi kâr oranı")
            st.bar_chart(pay_df)

    with tabs[1]:
        st.markdown("### Alt kategori / kategori içi kârlılık")
        if subcategory_summary.empty:
            st.warning("Alt kategori özeti oluşturulamadı.")
        else:
            st.dataframe(_format_category_summary(subcategory_summary), width="stretch")

    with tabs[2]:
        st.markdown("### POS kanal kırılımı")
        channel = pd.DataFrame([
            {"Kanal": "Fiş", "Ciro KDV Hariç": total_fis, "Maliyet": total_fis_cost, "Brüt Kâr": total_fis - total_fis_cost},
            {"Kanal": "POS Fatura", "Ciro KDV Hariç": total_fatura, "Maliyet": total_fatura_cost, "Brüt Kâr": total_fatura - total_fatura_cost},
            {"Kanal": "İade Etkisi", "Ciro KDV Hariç": -total_iade, "Maliyet": -total_iade_cost, "Brüt Kâr": -(total_iade - total_iade_cost)},
        ])
        channel["Brüt Kâr Oranı"] = channel.apply(
            lambda r: (r["Brüt Kâr"] / r["Ciro KDV Hariç"] * 100) if r["Ciro KDV Hariç"] else None,
            axis=1,
        )
        display_channel = channel.copy()
        for col in ["Ciro KDV Hariç", "Maliyet", "Brüt Kâr"]:
            display_channel[col] = display_channel[col].apply(format_tl)
        display_channel["Brüt Kâr Oranı"] = display_channel["Brüt Kâr Oranı"].apply(format_percent)
        st.dataframe(display_channel, width="stretch")

    with tabs[3]:
        st.markdown("### En çok ciro yapan ürünler")
        cols = [
            "Barkod", "UrunAdi", "Tedarikci", "AnaKategori", "AltKategori", "NetSatisMiktari",
            "NetSatisKdvDahil", "NetSatisKdvHaric", "TahminiSatilanMalMaliyetiKdvHaric",
            "TahminiBrutKarKdvHaric", "BrutKarOraniKdvHaric", "MaliyetSaglikDurumu",
        ]
        existing = [c for c in cols if c in df.columns]
        _show_table(df.sort_values("NetSatisKdvHaric", ascending=False).head(75)[existing], "Ciro ürünü yok.")

    with tabs[4]:
        st.markdown("### En çok brüt kâr bırakan ürünler")
        cols = [
            "Barkod", "UrunAdi", "Tedarikci", "AnaKategori", "AltKategori", "NetSatisMiktari",
            "NetSatisKdvHaric", "TahminiSatilanMalMaliyetiKdvHaric", "TahminiBrutKarKdvHaric",
            "BrutKarOraniKdvHaric", "KullanilanBirimMaliyetKdvHaric", "MaliyetSaglikDurumu",
        ]
        existing = [c for c in cols if c in df.columns]
        _show_table(df.sort_values("TahminiBrutKarKdvHaric", ascending=False).head(75)[existing], "Brüt kâr ürünü yok.")

    with tabs[5]:
        st.markdown("### Zayıf marjlı / zarar eden ürünler")
        weak = df[(df["TahminiBrutKarKdvHaric"].fillna(0) < 0) | (df["BrutKarOraniKdvHaric"].fillna(999) < 3)].copy()
        cols = [
            "Barkod", "UrunAdi", "AnaKategori", "AltKategori", "NetSatisMiktari", "NetSatisKdvHaric",
            "TahminiSatilanMalMaliyetiKdvHaric", "TahminiBrutKarKdvHaric", "BrutKarOraniKdvHaric",
            "FisMaliyet", "FaturaMaliyet", "IadeMaliyet", "MaliyetSaglikDurumu",
        ]
        existing = [c for c in cols if c in weak.columns]
        _show_table(weak.sort_values("TahminiBrutKarKdvHaric", ascending=True).head(100)[existing] if not weak.empty else weak, "Zarar veya çok zayıf marj görünen ürün yok.")

    with tabs[6]:
        st.markdown("### Kontrol uyarıları")
        control = pd.concat([missing_cost, mismatch, suspicious]).drop_duplicates(subset=["Barkod"], keep="first") if not df.empty else pd.DataFrame()
        cols = [
            "Barkod", "UrunAdi", "AnaKategori", "AltKategori", "NetSatisMiktari", "FisMiktar", "FaturaMiktar", "IadeMiktari",
            "Stok101CikisMiktari", "Stok21CikisMiktari", "Stok102GirisMiktari", "NetSatisKdvHaric",
            "TahminiSatilanMalMaliyetiKdvHaric", "TahminiBrutKarKdvHaric", "MaliyetEksikMi", "MiktarUyumsuzMu", "SupheliMaliyetMi", "MaliyetSaglikDurumu",
        ]
        existing = [c for c in cols if c in control.columns]
        _show_table(control.sort_values("NetSatisKdvHaric", ascending=False)[existing] if not control.empty else control, "Kontrol uyarısı yok.")

    with tabs[7]:
        st.markdown("### Tüm POS ürün detayları")
        _show_table(df, "Detay verisi yok.")
