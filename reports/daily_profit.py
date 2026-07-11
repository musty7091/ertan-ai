import pandas as pd
import streamlit as st

from core.config import get_excluded_sale_header_ind
from core.db import query_df
from core.formatting import format_number, format_percent, format_tl
from core.sql_loader import load_sql


NUMERIC_COLUMNS = [
    "SatisSatirSayisi",
    "NetSatisMiktari",
    "NetSatisKdvDahil",
    "NetSatisKdvHaric",
    "OrtalamaSatisFiyatiKdvHaric",
    "IadeMiktari",
    "IadeKdvDahil",
    "IadeKdvHaric",
    "KartMaliyet",
    "KartAlisFiyati",
    "SonAlisBirimMaliyetKdvHaric",
    "KullanilanBirimMaliyetKdvHaric",
    "TahminiSatilanMalMaliyetiKdvHaric",
    "TahminiBrutKarKdvHaric",
    "BrutKarOraniKdvHaric",
    "TahminiMaliyetSonAlisKdvHaric",
    "TahminiKarSonAlisKdvHaric",
    "KullanilanMaliyetSatisOrani",
    "SonAlisSatisOrani",
    "SonAlisKartMaliyetFarkYuzde",
    "KartKalan",
    "MaliyetEksikMi",
    "SupheliMaliyetMi",
]


def run_daily_profit(conn, report_date: str) -> pd.DataFrame:
    sql = load_sql("daily_profit.sql")
    return query_df(conn, sql, [report_date, get_excluded_sale_header_ind()])


def prepare_numeric_df(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    for column in NUMERIC_COLUMNS:
        if column in prepared.columns:
            prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    return prepared


def _format_display(df: pd.DataFrame) -> pd.DataFrame:
    display = df.copy()

    money_cols = [
        "NetSatisKdvDahil",
        "NetSatisKdvHaric",
        "OrtalamaSatisFiyatiKdvHaric",
        "IadeKdvDahil",
        "IadeKdvHaric",
        "KartMaliyet",
        "KartAlisFiyati",
        "SonAlisBirimMaliyetKdvHaric",
        "KullanilanBirimMaliyetKdvHaric",
        "TahminiSatilanMalMaliyetiKdvHaric",
        "TahminiBrutKarKdvHaric",
        "TahminiMaliyetSonAlisKdvHaric",
        "TahminiKarSonAlisKdvHaric",
    ]
    number_cols = [
        "SatisSatirSayisi",
        "NetSatisMiktari",
        "IadeMiktari",
        "KartKalan",
    ]
    percent_cols = [
        "BrutKarOraniKdvHaric",
        "KullanilanMaliyetSatisOrani",
        "SonAlisSatisOrani",
        "SonAlisKartMaliyetFarkYuzde",
    ]

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
        "RaporTarihi": "Rapor Tarihi",
        "Barkod": "Barkod",
        "UrunAdi": "Ürün Adı",
        "Tedarikci": "Tedarikçi",
        "AnaKategori": "Ana Kategori",
        "AltKategori": "Alt Kategori",
        "Marka": "Marka",
        "SatisSatirSayisi": "Satış Satırı",
        "NetSatisMiktari": "Net Satış Miktarı",
        "NetSatisKdvDahil": "Net Satış KDV Dahil",
        "NetSatisKdvHaric": "Net Satış KDV Hariç",
        "OrtalamaSatisFiyatiKdvHaric": "Ort. Satış KDV Hariç",
        "IadeMiktari": "İade Miktarı",
        "IadeKdvDahil": "İade KDV Dahil",
        "IadeKdvHaric": "İade KDV Hariç",
        "KartMaliyet": "Stok Kartı Maliyet",
        "KartAlisFiyati": "Stok Kartı Alış",
        "SonAlisBirimMaliyetKdvHaric": "Son Alış Birim Maliyet",
        "SonAlisTarihi": "Son Alış Tarihi",
        "KullanilanBirimMaliyetKdvHaric": "Kullanılan Birim Maliyet",
        "KullanilanMaliyetKaynak": "Kullanılan Kaynak",
        "TahminiSatilanMalMaliyetiKdvHaric": "Stok Kartı Bazlı Tahmini Maliyet",
        "TahminiBrutKarKdvHaric": "Stok Kartı Bazlı Tahmini Brüt Kâr",
        "BrutKarOraniKdvHaric": "Tahmini Kâr Oranı",
        "TahminiMaliyetSonAlisKdvHaric": "Son Alış Bazlı Maliyet",
        "TahminiKarSonAlisKdvHaric": "Son Alış Bazlı Kâr",
        "KullanilanMaliyetSatisOrani": "Kullanılan Maliyet / Satış",
        "SonAlisSatisOrani": "Son Alış / Satış",
        "SonAlisKartMaliyetFarkYuzde": "Son Alış - Kart Maliyet Farkı",
        "KartKalan": "Kart Kalan",
        "MaliyetEksikMi": "Maliyet Eksik Mi",
        "SupheliMaliyetMi": "Şüpheli Mi",
        "MaliyetSaglikDurumu": "Maliyet Sağlık Durumu",
    }

    return display.rename(columns=rename_map)


def _show_table(df: pd.DataFrame, empty_message: str):
    if df.empty:
        st.success(empty_message)
    else:
        st.dataframe(_format_display(df), width="stretch")


def _metric_money(value):
    return format_tl(value if pd.notna(value) else None)


def build_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Günlük satışları ana kategori bazında toplar."""
    if df.empty:
        return pd.DataFrame()

    d = df.copy()
    d["AnaKategori"] = d["AnaKategori"].fillna("KATEGORİ YOK").replace("", "KATEGORİ YOK")

    total_sales = d["NetSatisKdvHaric"].sum(skipna=True)
    total_profit = d["TahminiBrutKarKdvHaric"].sum(skipna=True)

    grouped = (
        d.groupby("AnaKategori", dropna=False)
        .agg(
            UrunSayisi=("Barkod", "nunique"),
            SatisSatiri=("SatisSatirSayisi", "sum"),
            NetSatisMiktari=("NetSatisMiktari", "sum"),
            NetSatisKdvDahil=("NetSatisKdvDahil", "sum"),
            NetSatisKdvHaric=("NetSatisKdvHaric", "sum"),
            TahminiMaliyet=("TahminiSatilanMalMaliyetiKdvHaric", "sum"),
            TahminiBrutKar=("TahminiBrutKarKdvHaric", "sum"),
            IadeKdvDahil=("IadeKdvDahil", "sum"),
            MaliyetiOlmayanUrun=("MaliyetEksikMi", "sum"),
            SupheliMaliyetliUrun=("SupheliMaliyetMi", "sum"),
        )
        .reset_index()
    )

    loss_counts = (
        d.assign(ZararEdenUrun=(d["TahminiBrutKarKdvHaric"].fillna(0) < 0).astype(int))
        .groupby("AnaKategori", dropna=False)["ZararEdenUrun"]
        .sum()
        .reset_index()
    )

    grouped = grouped.merge(loss_counts, on="AnaKategori", how="left")

    grouped["SatisPayiYuzde"] = grouped["NetSatisKdvHaric"].apply(
        lambda v: (v / total_sales * 100) if total_sales else None
    )
    grouped["KarOraniYuzde"] = grouped.apply(
        lambda r: (r["TahminiBrutKar"] / r["NetSatisKdvHaric"] * 100)
        if r["NetSatisKdvHaric"]
        else None,
        axis=1,
    )
    grouped["KarPayiYuzde"] = grouped["TahminiBrutKar"].apply(
        lambda v: (v / total_profit * 100) if total_profit else None
    )

    grouped["KontrolGereken"] = (
        grouped["MaliyetiOlmayanUrun"].fillna(0)
        + grouped["SupheliMaliyetliUrun"].fillna(0)
        + grouped["ZararEdenUrun"].fillna(0)
    )

    return grouped.sort_values(
        ["TahminiBrutKar", "NetSatisKdvHaric"],
        ascending=[True, False],
    ).reset_index(drop=True)


def _format_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    display = df.copy()

    money_cols = [
        "NetSatisKdvDahil",
        "NetSatisKdvHaric",
        "TahminiMaliyet",
        "TahminiBrutKar",
        "IadeKdvDahil",
    ]
    number_cols = [
        "UrunSayisi",
        "SatisSatiri",
        "NetSatisMiktari",
        "MaliyetiOlmayanUrun",
        "SupheliMaliyetliUrun",
        "ZararEdenUrun",
        "KontrolGereken",
    ]
    percent_cols = ["SatisPayiYuzde", "KarOraniYuzde", "KarPayiYuzde"]

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
        "UrunSayisi": "Ürün Sayısı",
        "SatisSatiri": "Satış Satırı",
        "NetSatisMiktari": "Satış Miktarı",
        "NetSatisKdvDahil": "Satış KDV Dahil",
        "NetSatisKdvHaric": "Satış KDV Hariç",
        "SatisPayiYuzde": "Satış Payı",
        "TahminiMaliyet": "Tahmini Maliyet",
        "TahminiBrutKar": "Tahmini Brüt Kâr",
        "KarOraniYuzde": "Kâr Oranı",
        "KarPayiYuzde": "Kâr Payı",
        "MaliyetiOlmayanUrun": "Maliyeti Olmayan",
        "ZararEdenUrun": "Zarar Eden",
        "SupheliMaliyetliUrun": "Şüpheli Maliyet",
        "KontrolGereken": "Kontrol Gereken",
        "IadeKdvDahil": "İade KDV Dahil",
    })



def _category_options(df: pd.DataFrame) -> list[str]:
    categories = (
        df["AnaKategori"]
        .fillna("KATEGORİ YOK")
        .replace("", "KATEGORİ YOK")
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )
    return ["TÜM KATEGORİLER"] + categories


def _sort_category_products(df: pd.DataFrame, sort_mode: str) -> pd.DataFrame:
    result = df.copy()

    if sort_mode == "En yüksek kârlılık oranı":
        result = result.sort_values(
            ["BrutKarOraniKdvHaric", "TahminiBrutKarKdvHaric"],
            ascending=[False, False],
            na_position="last",
        )
    elif sort_mode == "En düşük kârlılık oranı":
        result = result.sort_values(
            ["BrutKarOraniKdvHaric", "TahminiBrutKarKdvHaric"],
            ascending=[True, True],
            na_position="last",
        )
    elif sort_mode == "En yüksek brüt kâr":
        result = result.sort_values(
            ["TahminiBrutKarKdvHaric", "NetSatisKdvHaric"],
            ascending=[False, False],
            na_position="last",
        )
    elif sort_mode == "En düşük brüt kâr / zarar etkisi":
        result = result.sort_values(
            ["TahminiBrutKarKdvHaric", "NetSatisKdvHaric"],
            ascending=[True, False],
            na_position="last",
        )
    elif sort_mode == "En yüksek satış":
        result = result.sort_values(
            ["NetSatisKdvHaric", "TahminiBrutKarKdvHaric"],
            ascending=[False, False],
            na_position="last",
        )
    elif sort_mode == "En düşük satış":
        result = result.sort_values(
            ["NetSatisKdvHaric", "TahminiBrutKarKdvHaric"],
            ascending=[True, False],
            na_position="last",
        )

    return result


def _render_category_filter_analysis(df: pd.DataFrame, report_date: str):
    st.markdown("### Kategori içi ürün kârlılık analizi")
    st.caption(
        "Burada seçtiğin ana kategorinin içindeki ürünleri kendi içinde sıralayabilirsin. "
        "Örneğin ALKOLLU ICECK seçip en yüksek veya en düşük kârlılık oranını görebilirsin."
    )

    category_col, sort_col, limit_col = st.columns([2.2, 2.2, 1])

    categories = _category_options(df)
    selected_category = category_col.selectbox(
        "Ana kategori",
        categories,
        index=0,
        key=f"daily_category_select_{report_date}",
    )

    sort_mode = sort_col.selectbox(
        "Sıralama",
        [
            "En yüksek kârlılık oranı",
            "En düşük kârlılık oranı",
            "En yüksek brüt kâr",
            "En düşük brüt kâr / zarar etkisi",
            "En yüksek satış",
            "En düşük satış",
        ],
        index=0,
        key=f"daily_category_sort_{report_date}",
    )

    limit = limit_col.number_input(
        "Liste adedi",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
        key=f"daily_category_limit_{report_date}",
    )

    f1, f2, f3, f4 = st.columns(4)
    hide_missing_cost = f1.checkbox(
        "Maliyeti olmayanları hariç tut",
        value=False,
        key=f"daily_hide_missing_{report_date}",
    )
    only_loss = f2.checkbox(
        "Sadece zarar edenler",
        value=False,
        key=f"daily_only_loss_{report_date}",
    )
    only_suspicious = f3.checkbox(
        "Sadece şüpheli maliyetler",
        value=False,
        key=f"daily_only_suspicious_{report_date}",
    )
    only_with_sales = f4.checkbox(
        "Satışı olanları göster",
        value=True,
        key=f"daily_only_sales_{report_date}",
    )

    filtered = df.copy()
    filtered["AnaKategori"] = filtered["AnaKategori"].fillna("KATEGORİ YOK").replace("", "KATEGORİ YOK")

    if selected_category != "TÜM KATEGORİLER":
        filtered = filtered[filtered["AnaKategori"].astype(str) == selected_category]

    if hide_missing_cost:
        filtered = filtered[filtered["MaliyetEksikMi"].fillna(0) == 0]

    if only_loss:
        filtered = filtered[filtered["TahminiBrutKarKdvHaric"].fillna(0) < 0]

    if only_suspicious:
        filtered = filtered[filtered["SupheliMaliyetMi"].fillna(0) == 1]

    if only_with_sales:
        filtered = filtered[filtered["NetSatisKdvHaric"].fillna(0) != 0]

    if filtered.empty:
        st.warning("Bu filtrelerle gösterilecek ürün bulunamadı.")
        return

    filtered = _sort_category_products(filtered, sort_mode)

    total_sales = filtered["NetSatisKdvHaric"].sum(skipna=True)
    total_profit = filtered["TahminiBrutKarKdvHaric"].sum(skipna=True)
    total_cost = filtered["TahminiSatilanMalMaliyetiKdvHaric"].sum(skipna=True)
    margin = (total_profit / total_sales * 100) if total_sales else None
    missing_count = int(filtered["MaliyetEksikMi"].fillna(0).sum())
    loss_count = int((filtered["TahminiBrutKarKdvHaric"].fillna(0) < 0).sum())
    suspicious_count = int(filtered["SupheliMaliyetMi"].fillna(0).sum())

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Seçili Ürün", format_number(len(filtered)))
    m2.metric("Satış KDV Hariç", format_tl(total_sales))
    m3.metric("Tahmini Maliyet", format_tl(total_cost))
    m4.metric("Tahmini Brüt Kâr", format_tl(total_profit))
    m5.metric("Kâr Oranı", format_percent(margin))
    m6.metric("Zarar Eden", format_number(loss_count))

    m7, m8, m9 = st.columns(3)
    m7.metric("Maliyeti Olmayan", format_number(missing_count))
    m8.metric("Şüpheli Maliyet", format_number(suspicious_count))
    m9.metric("Seçilen Kategori", selected_category[:28])

    cols = [
        "Barkod",
        "UrunAdi",
        "Tedarikci",
        "AnaKategori",
        "AltKategori",
        "Marka",
        "NetSatisMiktari",
        "NetSatisKdvDahil",
        "NetSatisKdvHaric",
        "OrtalamaSatisFiyatiKdvHaric",
        "KullanilanBirimMaliyetKdvHaric",
        "KullanilanMaliyetKaynak",
        "TahminiSatilanMalMaliyetiKdvHaric",
        "TahminiBrutKarKdvHaric",
        "BrutKarOraniKdvHaric",
        "KullanilanMaliyetSatisOrani",
        "MaliyetSaglikDurumu",
        "MaliyetEksikMi",
        "SupheliMaliyetMi",
    ]
    existing = [c for c in cols if c in filtered.columns]

    st.dataframe(_format_display(filtered[existing].head(int(limit))), width="stretch")

    chart_source = filtered.head(min(int(limit), 50)).copy()
    if not chart_source.empty:
        chart_df = chart_source[["UrunAdi", "NetSatisKdvHaric", "TahminiBrutKarKdvHaric"]].copy()
        chart_df = chart_df.set_index("UrunAdi")
        st.markdown("### Seçili liste satış / brüt kâr grafiği")
        st.bar_chart(chart_df)

def render_daily_profit(df: pd.DataFrame, report_date: str, show_summary: bool = True):
    if df.empty:
        st.warning(f"{report_date} tarihi için satış verisi bulunamadı.")
        return

    df = prepare_numeric_df(df)

    total_sales_inc = df["NetSatisKdvDahil"].sum(skipna=True)
    total_sales_exc = df["NetSatisKdvHaric"].sum(skipna=True)
    total_qty = df["NetSatisMiktari"].sum(skipna=True)
    total_cogs = df["TahminiSatilanMalMaliyetiKdvHaric"].sum(skipna=True)
    total_profit = df["TahminiBrutKarKdvHaric"].sum(skipna=True)
    total_refund = df["IadeKdvDahil"].sum(skipna=True)

    missing_cost = df[df["MaliyetEksikMi"].fillna(0) == 1].copy()
    suspicious = df[df["SupheliMaliyetMi"].fillna(0) == 1].copy()
    loss_products = df[df["TahminiBrutKarKdvHaric"].fillna(0) < 0].copy()
    profitable_products = df[df["TahminiBrutKarKdvHaric"].fillna(0) > 0].copy()

    missing_cost_count = len(missing_cost)
    suspicious_count = len(suspicious)
    loss_count = len(loss_products)
    profitable_count = len(profitable_products)

    total_loss_effect = loss_products["TahminiBrutKarKdvHaric"].sum(skipna=True) if not loss_products.empty else 0
    total_positive_profit = profitable_products["TahminiBrutKarKdvHaric"].sum(skipna=True) if not profitable_products.empty else 0
    profit_rate = (total_profit / total_sales_exc * 100) if total_sales_exc else None

    category_summary = build_category_summary(df)
    worst_category = None
    best_category = None
    if not category_summary.empty:
        worst_category = category_summary.sort_values("TahminiBrutKar", ascending=True).iloc[0]
        best_category = category_summary.sort_values("TahminiBrutKar", ascending=False).iloc[0]

    if show_summary:
        st.subheader(f"🧾 {report_date} Günlük Satış ve Maliyet Sağlık Kontrolü")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Satış KDV Dahil", format_tl(total_sales_inc))
        c2.metric("Satış KDV Hariç", format_tl(total_sales_exc))
        c3.metric("Satış Miktarı", format_number(total_qty))
        c4.metric("Ürün Sayısı", format_number(len(df)))

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Stok Kartı Bazlı Maliyet", format_tl(total_cogs))
        c6.metric("Tahmini Brüt Kâr", format_tl(total_profit))
        c7.metric("Tahmini Kâr Oranı", format_percent(profit_rate))
        c8.metric("İade KDV Dahil", format_tl(total_refund))

        c9, c10, c11, c12 = st.columns(4)
        c9.metric("Maliyeti Olmayan Ürün", format_number(missing_cost_count))
        c10.metric("Zarar Eden Ürün", format_number(loss_count))
        c11.metric("Şüpheli Maliyet", format_number(suspicious_count))
        c12.metric("Kârlı Ürün", format_number(profitable_count))

        c13, c14, c15, c16 = st.columns(4)
        c13.metric("Toplam Zarar Etkisi", format_tl(total_loss_effect))
        c14.metric("Pozitif Kâr Toplamı", format_tl(total_positive_profit))
        c15.metric("Kontrol Gereken", format_number(missing_cost_count + suspicious_count + loss_count))
        c16.metric("Normal Görünen", format_number(max(len(df) - suspicious_count - missing_cost_count - loss_count, 0)))

        if worst_category is not None and best_category is not None:
            c17, c18, c19, c20 = st.columns(4)
            c17.metric("En Zayıf Ana Kategori", str(worst_category["AnaKategori"])[:22])
            c18.metric("Kategori Brüt Kârı", format_tl(worst_category["TahminiBrutKar"]))
            c19.metric("En Güçlü Ana Kategori", str(best_category["AnaKategori"])[:22])
            c20.metric("Kategori Brüt Kârı", format_tl(best_category["TahminiBrutKar"]))

    st.warning(
        "Bu rapor net kâr değildir. Şu anda amaç: günlük satışları, maliyeti olmayan ürünleri, zarar eden ürünleri "
        "ve şüpheli maliyetleri ayrı ayrı denetlemek. Tahmini kâr, stok kartı MALIYET / ALISFIYATI baz alınarak hesaplanır. "
        "Son alış maliyeti sadece kıyas ve şüpheli maliyet tespiti için gösterilir."
    )

    tabs = st.tabs([
        "Ana kategori özeti",
        "Kategori içi analiz",
        f"Maliyeti olmayanlar ({missing_cost_count})",
        f"Zarar eden ürünler ({loss_count})",
        f"Şüpheli maliyetler ({suspicious_count})",
        "En çok zarar etkisi",
        "En çok kâr",
        "Maliyet kıyası",
        "Tüm detay",
    ])

    zarar = df.sort_values("TahminiBrutKarKdvHaric", ascending=True).head(50)
    top_profit = df.sort_values("TahminiBrutKarKdvHaric", ascending=False).head(50)

    with tabs[0]:
        st.markdown("### Ana kategori bazlı günlük satış ve kârlılık")
        st.caption(
            "Bu tablo, günlük satışı ana kategoriye göre ayırır. "
            "Satış payı ve kâr oranı sayesinde hangi kategorinin günü taşıdığını veya bozduğunu görürüz."
        )
        if category_summary.empty:
            st.warning("Ana kategori özeti oluşturulamadı.")
        else:
            st.dataframe(_format_category_summary(category_summary), width="stretch")

            chart_df = category_summary[["AnaKategori", "NetSatisKdvHaric", "TahminiBrutKar"]].copy()
            chart_df = chart_df.set_index("AnaKategori")
            st.markdown("### Ana kategori satış / brüt kâr grafiği")
            st.bar_chart(chart_df)

    with tabs[1]:
        _render_category_filter_analysis(df, report_date)

    with tabs[2]:
        st.markdown("### Maliyeti olmayan ürünler")
        st.caption("Bu ürünlerde stok kartı maliyet, stok kartı alış fiyatı ve son alış faturası maliyeti bulunamadı.")
        cols = [
            "Barkod",
            "UrunAdi",
            "Tedarikci",
            "AnaKategori",
            "AltKategori",
            "NetSatisMiktari",
            "NetSatisKdvDahil",
            "NetSatisKdvHaric",
            "KartMaliyet",
            "KartAlisFiyati",
            "SonAlisBirimMaliyetKdvHaric",
            "KullanilanMaliyetKaynak",
            "MaliyetSaglikDurumu",
        ]
        existing = [c for c in cols if c in missing_cost.columns]
        _show_table(missing_cost[existing].copy() if existing else missing_cost, "Maliyeti olmayan ürün yok.")

    with tabs[3]:
        st.markdown("### Zarar eden ürünler")
        st.caption("Stok kartı bazlı tahmini brüt kârı negatif olan ürünler.")
        cols = [
            "Barkod",
            "UrunAdi",
            "Tedarikci",
            "AnaKategori",
            "AltKategori",
            "NetSatisMiktari",
            "NetSatisKdvHaric",
            "OrtalamaSatisFiyatiKdvHaric",
            "KullanilanBirimMaliyetKdvHaric",
            "KullanilanMaliyetKaynak",
            "TahminiSatilanMalMaliyetiKdvHaric",
            "TahminiBrutKarKdvHaric",
            "BrutKarOraniKdvHaric",
            "KartMaliyet",
            "KartAlisFiyati",
            "SonAlisBirimMaliyetKdvHaric",
            "KullanilanMaliyetSatisOrani",
            "MaliyetSaglikDurumu",
        ]
        existing = [c for c in cols if c in loss_products.columns]
        loss_sorted = loss_products.sort_values("TahminiBrutKarKdvHaric", ascending=True)
        _show_table(loss_sorted[existing].copy() if existing else loss_sorted, "Zarar eden ürün yok.")

    with tabs[4]:
        st.markdown("### Şüpheli maliyetler")
        st.caption("Maliyet satış fiyatından yüksek / satış fiyatına çok yakın / son alış ile stok kartı maliyeti çok farklı olan ürünler.")
        cols = [
            "Barkod",
            "UrunAdi",
            "Tedarikci",
            "AnaKategori",
            "AltKategori",
            "NetSatisMiktari",
            "NetSatisKdvHaric",
            "OrtalamaSatisFiyatiKdvHaric",
            "KartMaliyet",
            "KartAlisFiyati",
            "SonAlisBirimMaliyetKdvHaric",
            "KullanilanBirimMaliyetKdvHaric",
            "KullanilanMaliyetKaynak",
            "KullanilanMaliyetSatisOrani",
            "SonAlisSatisOrani",
            "SonAlisKartMaliyetFarkYuzde",
            "TahminiBrutKarKdvHaric",
            "MaliyetSaglikDurumu",
        ]
        existing = [c for c in cols if c in suspicious.columns]
        suspicious_sorted = suspicious.sort_values(
            ["MaliyetSaglikDurumu", "TahminiBrutKarKdvHaric"],
            ascending=[True, True],
        )
        _show_table(suspicious_sorted[existing].copy() if existing else suspicious_sorted, "Şüpheli maliyet işaretlenen ürün yok.")

    with tabs[5]:
        st.markdown("### Kârlılığı en çok bozan ürünler")
        st.caption("Tüm ürünler içinden tahmini brüt kârı en düşük olan ilk 50 ürün.")
        _show_table(zarar, "Zarar etkisi gösterilecek ürün yok.")

    with tabs[6]:
        st.markdown("### En çok kâr bırakan ürünler")
        _show_table(top_profit, "Kâr bırakan ürün yok.")

    with tabs[7]:
        st.markdown("### Stok kartı maliyeti / son alış maliyeti kıyası")
        cols = [
            "Barkod",
            "UrunAdi",
            "NetSatisMiktari",
            "OrtalamaSatisFiyatiKdvHaric",
            "KartMaliyet",
            "KartAlisFiyati",
            "SonAlisBirimMaliyetKdvHaric",
            "KullanilanBirimMaliyetKdvHaric",
            "KullanilanMaliyetKaynak",
            "KullanilanMaliyetSatisOrani",
            "SonAlisSatisOrani",
            "SonAlisKartMaliyetFarkYuzde",
            "MaliyetSaglikDurumu",
        ]
        existing = [c for c in cols if c in df.columns]
        compare = df[existing].copy()
        compare = compare.sort_values(
            ["MaliyetSaglikDurumu", "KullanilanMaliyetSatisOrani"],
            ascending=[True, False],
        )
        _show_table(compare, "Maliyet kıyası için veri yok.")

    with tabs[8]:
        st.markdown("### Tüm ürün detayları")
        _show_table(df, "Detay verisi yok.")
