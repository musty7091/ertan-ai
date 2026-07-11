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
    prepared["AnaKategori"] = prepared["AnaKategori"].fillna("KATEGORİ YOK").replace("", "KATEGORİ YOK")
    prepared["AltKategori"] = prepared["AltKategori"].fillna("ALT KATEGORİ YOK").replace("", "ALT KATEGORİ YOK")
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

    return display.rename(columns={
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
    })


def _show_table(df: pd.DataFrame, empty_message: str):
    if df.empty:
        st.success(empty_message)
    else:
        st.dataframe(_format_display(df), width="stretch")


def _summary_from_group(d: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if d.empty:
        return pd.DataFrame()

    total_sales = d["NetSatisKdvHaric"].sum(skipna=True)
    total_profit = d["TahminiBrutKarKdvHaric"].sum(skipna=True)

    grouped = (
        d.groupby(group_cols, dropna=False)
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
        .groupby(group_cols, dropna=False)["ZararEdenUrun"]
        .sum()
        .reset_index()
    )

    grouped = grouped.merge(loss_counts, on=group_cols, how="left")

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

    return grouped.sort_values(["NetSatisKdvHaric"], ascending=[False]).reset_index(drop=True)


def build_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    return _summary_from_group(df, ["AnaKategori"])


def build_subcategory_summary(df: pd.DataFrame) -> pd.DataFrame:
    return _summary_from_group(df, ["AnaKategori", "AltKategori"])


def _format_group_summary(df: pd.DataFrame) -> pd.DataFrame:
    display = df.copy()

    for col in ["NetSatisKdvDahil", "NetSatisKdvHaric", "TahminiMaliyet", "TahminiBrutKar", "IadeKdvDahil"]:
        if col in display.columns:
            display[col] = display[col].apply(format_tl)

    for col in [
        "UrunSayisi",
        "SatisSatiri",
        "NetSatisMiktari",
        "MaliyetiOlmayanUrun",
        "SupheliMaliyetliUrun",
        "ZararEdenUrun",
        "KontrolGereken",
    ]:
        if col in display.columns:
            display[col] = display[col].apply(format_number)

    for col in ["SatisPayiYuzde", "KarOraniYuzde", "KarPayiYuzde"]:
        if col in display.columns:
            display[col] = display[col].apply(format_percent)

    return display.rename(columns={
        "AnaKategori": "Ana Kategori",
        "AltKategori": "Alt Kategori",
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


def _sort_category_products(df: pd.DataFrame, sort_mode: str) -> pd.DataFrame:
    result = df.copy()

    if sort_mode == "En yüksek kârlılık oranı":
        return result.sort_values(["BrutKarOraniKdvHaric", "TahminiBrutKarKdvHaric"], ascending=[False, False], na_position="last")
    if sort_mode == "En düşük kârlılık oranı":
        return result.sort_values(["BrutKarOraniKdvHaric", "TahminiBrutKarKdvHaric"], ascending=[True, True], na_position="last")
    if sort_mode == "En yüksek brüt kâr":
        return result.sort_values(["TahminiBrutKarKdvHaric", "NetSatisKdvHaric"], ascending=[False, False], na_position="last")
    if sort_mode == "En düşük brüt kâr / zarar etkisi":
        return result.sort_values(["TahminiBrutKarKdvHaric", "NetSatisKdvHaric"], ascending=[True, False], na_position="last")
    if sort_mode == "En yüksek satış":
        return result.sort_values(["NetSatisKdvHaric", "TahminiBrutKarKdvHaric"], ascending=[False, False], na_position="last")
    if sort_mode == "En düşük satış":
        return result.sort_values(["NetSatisKdvHaric", "TahminiBrutKarKdvHaric"], ascending=[True, False], na_position="last")
    return result


def _render_category_profit_tree(df: pd.DataFrame, report_date: str):
    st.markdown("### Ana kategori bazlı kârlılık dağılımı")
    st.caption(
        "Ana kategoriler aşağıda açılır/kapanır başlıklar olarak gelir. "
        "Örneğin **ALKOLLU ICECK** başlığını açınca, o ana kategorinin alt kategori kârlılık dağılımını görürsün."
    )

    category_summary = build_category_summary(df)
    if category_summary.empty:
        st.warning("Ana kategori özeti oluşturulamadı.")
        return

    st.markdown("#### Ana kategori genel tablo")
    st.dataframe(_format_group_summary(category_summary), width="stretch")

    chart_df = category_summary[["AnaKategori", "NetSatisKdvHaric", "TahminiBrutKar"]].copy().set_index("AnaKategori")
    st.markdown("#### Ana kategori satış / brüt kâr grafiği")
    st.bar_chart(chart_df)

    st.markdown("#### Ana kategorileri aç/kapat")

    ordered_categories = category_summary.sort_values("NetSatisKdvHaric", ascending=False)

    for _, cat_row in ordered_categories.iterrows():
        ana = str(cat_row["AnaKategori"])
        cat_margin = cat_row["KarOraniYuzde"]
        expander_title = (
            f"{ana} | Satış: {format_tl(cat_row['NetSatisKdvHaric'])} | "
            f"Kâr: {format_tl(cat_row['TahminiBrutKar'])} | "
            f"Oran: {format_percent(cat_margin)} | "
            f"Satış Payı: {format_percent(cat_row['SatisPayiYuzde'])} | "
            f"Kontrol: {format_number(cat_row['KontrolGereken'])}"
        )

        with st.expander(expander_title, expanded=False):
            cat_df = df[df["AnaKategori"].astype(str) == ana].copy()
            sub_summary = build_subcategory_summary(cat_df)

            if not sub_summary.empty:
                sub_summary = sub_summary[sub_summary["AnaKategori"].astype(str) == ana]
                sub_summary = sub_summary.sort_values("NetSatisKdvHaric", ascending=False)

            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Alt Kategori", format_number(cat_df["AltKategori"].nunique()))
            m2.metric("Ürün", format_number(cat_df["Barkod"].nunique()))
            m3.metric("Satış KDV Hariç", format_tl(cat_row["NetSatisKdvHaric"]))
            m4.metric("Tahmini Brüt Kâr", format_tl(cat_row["TahminiBrutKar"]))
            m5.metric("Kâr Oranı", format_percent(cat_margin))
            m6.metric("Kontrol Gereken", format_number(cat_row["KontrolGereken"]))

            st.markdown(f"##### {ana} alt kategori kârlılık dağılımı")
            st.dataframe(_format_group_summary(sub_summary), width="stretch")

            if not sub_summary.empty:
                sub_chart = sub_summary[["AltKategori", "NetSatisKdvHaric", "TahminiBrutKar"]].copy().set_index("AltKategori")
                st.bar_chart(sub_chart)

            st.markdown("##### Alt kategorileri aç/kapat")
            for _, sub_row in sub_summary.sort_values("NetSatisKdvHaric", ascending=False).iterrows():
                alt = str(sub_row["AltKategori"])
                sub_title = (
                    f"{alt} | Satış: {format_tl(sub_row['NetSatisKdvHaric'])} | "
                    f"Kâr: {format_tl(sub_row['TahminiBrutKar'])} | "
                    f"Oran: {format_percent(sub_row['KarOraniYuzde'])} | "
                    f"Kontrol: {format_number(sub_row['KontrolGereken'])}"
                )
                with st.expander(sub_title, expanded=False):
                    sub_df = cat_df[cat_df["AltKategori"].astype(str) == alt].copy()

                    sort_mode = st.selectbox(
                        "Ürün sıralaması",
                        [
                            "En yüksek kârlılık oranı",
                            "En düşük kârlılık oranı",
                            "En yüksek brüt kâr",
                            "En düşük brüt kâr / zarar etkisi",
                            "En yüksek satış",
                        ],
                        index=3,
                        key=f"sub_sort_{report_date}_{ana}_{alt}",
                    )

                    sorted_products = _sort_category_products(sub_df, sort_mode)

                    p1, p2, p3, p4, p5 = st.columns(5)
                    p1.metric("Ürün", format_number(sorted_products["Barkod"].nunique()))
                    p2.metric("Satış", format_tl(sorted_products["NetSatisKdvHaric"].sum()))
                    p3.metric("Brüt Kâr", format_tl(sorted_products["TahminiBrutKarKdvHaric"].sum()))
                    ratio = (
                        sorted_products["TahminiBrutKarKdvHaric"].sum()
                        / sorted_products["NetSatisKdvHaric"].sum()
                        * 100
                    ) if sorted_products["NetSatisKdvHaric"].sum() else None
                    p4.metric("Kâr Oranı", format_percent(ratio))
                    p5.metric("Zarar Eden", format_number((sorted_products["TahminiBrutKarKdvHaric"].fillna(0) < 0).sum()))

                    cols = [
                        "Barkod",
                        "UrunAdi",
                        "Tedarikci",
                        "AltKategori",
                        "NetSatisMiktari",
                        "NetSatisKdvHaric",
                        "OrtalamaSatisFiyatiKdvHaric",
                        "KullanilanBirimMaliyetKdvHaric",
                        "TahminiSatilanMalMaliyetiKdvHaric",
                        "TahminiBrutKarKdvHaric",
                        "BrutKarOraniKdvHaric",
                        "MaliyetSaglikDurumu",
                    ]
                    existing = [c for c in cols if c in sorted_products.columns]
                    st.dataframe(_format_display(sorted_products[existing]), width="stretch")


def _render_category_filter_analysis(df: pd.DataFrame, report_date: str):
    st.markdown("### Filtreli kategori içi ürün listesi")
    st.caption(
        "Bu alan ürün listesini filtrelemek için. Ana kategori raporu için ilk sekmedeki açılır/kapanır kategori dağılımını kullan."
    )

    categories = ["TÜM ANA KATEGORİLER"] + df["AnaKategori"].astype(str).sort_values().unique().tolist()
    selected_category = st.selectbox("Ana kategori", categories, index=0, key=f"cat_filter_{report_date}_{id(df)}")

    d = df.copy()
    if selected_category != "TÜM ANA KATEGORİLER":
        d = d[d["AnaKategori"].astype(str) == selected_category]

    subcats = ["TÜM ALT KATEGORİLER"] + d["AltKategori"].astype(str).sort_values().unique().tolist()

    c1, c2, c3 = st.columns([2, 2, 1])
    selected_subcategory = c1.selectbox("Alt kategori", subcats, index=0, key=f"subcat_filter_{report_date}_{id(df)}")
    sort_mode = c2.selectbox(
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
        key=f"sort_filter_{report_date}_{id(df)}",
    )
    limit = c3.number_input("Liste", min_value=10, max_value=1000, value=100, step=10, key=f"limit_filter_{report_date}_{id(df)}")

    f1, f2, f3, f4 = st.columns(4)
    hide_missing_cost = f1.checkbox("Maliyeti olmayanları hariç tut", value=False, key=f"hide_missing_{report_date}_{id(df)}")
    only_loss = f2.checkbox("Sadece zarar edenler", value=False, key=f"only_loss_{report_date}_{id(df)}")
    only_suspicious = f3.checkbox("Sadece şüpheli maliyetler", value=False, key=f"only_suspicious_{report_date}_{id(df)}")
    only_with_sales = f4.checkbox("Satışı olanları göster", value=True, key=f"only_sales_{report_date}_{id(df)}")

    search_text = st.text_input(
        "Ürün adı / barkod içinde ara",
        value="",
        placeholder="Örnek: chivas, jack, 869...",
        key=f"search_filter_{report_date}_{id(df)}",
    ).strip().lower()

    filtered = d.copy()

    if selected_subcategory != "TÜM ALT KATEGORİLER":
        filtered = filtered[filtered["AltKategori"].astype(str) == selected_subcategory]

    if hide_missing_cost:
        filtered = filtered[filtered["MaliyetEksikMi"].fillna(0) == 0]

    if only_loss:
        filtered = filtered[filtered["TahminiBrutKarKdvHaric"].fillna(0) < 0]

    if only_suspicious:
        filtered = filtered[filtered["SupheliMaliyetMi"].fillna(0) == 1]

    if only_with_sales:
        filtered = filtered[filtered["NetSatisKdvHaric"].fillna(0) != 0]

    if search_text:
        filtered = filtered[
            filtered["UrunAdi"].fillna("").astype(str).str.lower().str.contains(search_text, na=False)
            | filtered["Barkod"].fillna("").astype(str).str.lower().str.contains(search_text, na=False)
        ]

    if filtered.empty:
        st.warning("Bu filtrelerle gösterilecek ürün bulunamadı.")
        return

    filtered = _sort_category_products(filtered, sort_mode)

    total_sales = filtered["NetSatisKdvHaric"].sum(skipna=True)
    total_profit = filtered["TahminiBrutKarKdvHaric"].sum(skipna=True)
    total_cost = filtered["TahminiSatilanMalMaliyetiKdvHaric"].sum(skipna=True)
    margin = (total_profit / total_sales * 100) if total_sales else None
    loss_count = int((filtered["TahminiBrutKarKdvHaric"].fillna(0) < 0).sum())

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Seçili Ürün", format_number(len(filtered)))
    m2.metric("Satış KDV Hariç", format_tl(total_sales))
    m3.metric("Tahmini Maliyet", format_tl(total_cost))
    m4.metric("Tahmini Brüt Kâr", format_tl(total_profit))
    m5.metric("Kâr Oranı", format_percent(margin))

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
        "MaliyetSaglikDurumu",
    ]
    existing = [c for c in cols if c in filtered.columns]
    st.dataframe(_format_display(filtered[existing].head(int(limit))), width="stretch")


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
        "Bu rapor net kâr değildir. Amaç: günlük satışları ana kategori ve alt kategori bazında ayırmak, "
        "kârlılık dağılımını ve maliyet sorunlarını denetlemek."
    )

    tabs = st.tabs([
        "Ana kategori kârlılık dağılımı",
        "Filtreli ürün listesi",
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
        _render_category_profit_tree(df, report_date)

    with tabs[1]:
        _render_category_filter_analysis(df, report_date)

    with tabs[2]:
        st.markdown("### Maliyeti olmayan ürünler")
        cols = [
            "Barkod", "UrunAdi", "Tedarikci", "AnaKategori", "AltKategori",
            "NetSatisMiktari", "NetSatisKdvDahil", "NetSatisKdvHaric",
            "KartMaliyet", "KartAlisFiyati", "SonAlisBirimMaliyetKdvHaric",
            "KullanilanMaliyetKaynak", "MaliyetSaglikDurumu",
        ]
        _show_table(missing_cost[[c for c in cols if c in missing_cost.columns]].copy(), "Maliyeti olmayan ürün yok.")

    with tabs[3]:
        st.markdown("### Zarar eden ürünler")
        cols = [
            "Barkod", "UrunAdi", "Tedarikci", "AnaKategori", "AltKategori",
            "NetSatisMiktari", "NetSatisKdvHaric", "OrtalamaSatisFiyatiKdvHaric",
            "KullanilanBirimMaliyetKdvHaric", "KullanilanMaliyetKaynak",
            "TahminiSatilanMalMaliyetiKdvHaric", "TahminiBrutKarKdvHaric",
            "BrutKarOraniKdvHaric", "KartMaliyet", "KartAlisFiyati",
            "SonAlisBirimMaliyetKdvHaric", "KullanilanMaliyetSatisOrani",
            "MaliyetSaglikDurumu",
        ]
        loss_sorted = loss_products.sort_values("TahminiBrutKarKdvHaric", ascending=True)
        _show_table(loss_sorted[[c for c in cols if c in loss_sorted.columns]].copy(), "Zarar eden ürün yok.")

    with tabs[4]:
        st.markdown("### Şüpheli maliyetler")
        cols = [
            "Barkod", "UrunAdi", "Tedarikci", "AnaKategori", "AltKategori",
            "NetSatisMiktari", "NetSatisKdvHaric", "OrtalamaSatisFiyatiKdvHaric",
            "KartMaliyet", "KartAlisFiyati", "SonAlisBirimMaliyetKdvHaric",
            "KullanilanBirimMaliyetKdvHaric", "KullanilanMaliyetKaynak",
            "KullanilanMaliyetSatisOrani", "SonAlisSatisOrani",
            "SonAlisKartMaliyetFarkYuzde", "TahminiBrutKarKdvHaric",
            "MaliyetSaglikDurumu",
        ]
        suspicious_sorted = suspicious.sort_values(["MaliyetSaglikDurumu", "TahminiBrutKarKdvHaric"], ascending=[True, True])
        _show_table(suspicious_sorted[[c for c in cols if c in suspicious_sorted.columns]].copy(), "Şüpheli maliyet işaretlenen ürün yok.")

    with tabs[5]:
        st.markdown("### Kârlılığı en çok bozan ürünler")
        _show_table(zarar, "Zarar etkisi gösterilecek ürün yok.")

    with tabs[6]:
        st.markdown("### En çok kâr bırakan ürünler")
        _show_table(top_profit, "Kâr bırakan ürün yok.")

    with tabs[7]:
        st.markdown("### Stok kartı maliyeti / son alış maliyeti kıyası")
        cols = [
            "Barkod", "UrunAdi", "NetSatisMiktari", "OrtalamaSatisFiyatiKdvHaric",
            "KartMaliyet", "KartAlisFiyati", "SonAlisBirimMaliyetKdvHaric",
            "KullanilanBirimMaliyetKdvHaric", "KullanilanMaliyetKaynak",
            "KullanilanMaliyetSatisOrani", "SonAlisSatisOrani",
            "SonAlisKartMaliyetFarkYuzde", "MaliyetSaglikDurumu",
        ]
        compare = df[[c for c in cols if c in df.columns]].copy()
        compare = compare.sort_values(["MaliyetSaglikDurumu", "KullanilanMaliyetSatisOrani"], ascending=[True, False])
        _show_table(compare, "Maliyet kıyası için veri yok.")

    with tabs[8]:
        st.markdown("### Tüm ürün detayları")
        _show_table(df, "Detay verisi yok.")
