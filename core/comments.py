# -*- coding: utf-8 -*-
"""
Kural tabanli yorum motoru.
"""

from datetime import date

from core.config import get_report_year
from core.formatting import safe_float


MARJ_COK_DUSUK = 5.0
MARJ_DUSUK = 12.0
MARJ_GUCLU = 25.0
STOK_YUKSEK_GUN = 365
STOK_DUSUK_GUN = 14
HAREKETSIZ_GUN = 30


def _elapsed_days() -> int:
    year = get_report_year()
    today = date.today()
    if year == today.year:
        return max((today - date(year, 1, 1)).days, 1)
    return 365


def comment_product_360(row) -> list[tuple[str, str]]:
    yorumlar: list[tuple[str, str]] = []

    satis_adet = safe_float(row.get("NetSatisMiktari")) or 0
    marj = safe_float(row.get("BrutKarOraniKdvHaric_Efektif"))
    kalan = safe_float(row.get("KartKalan")) or 0
    alis_haric = safe_float(row.get("NetAlisKdvHaric")) or 0
    alis_dahil = safe_float(row.get("NetAlisKdvDahil")) or 0
    bedelsiz = safe_float(row.get("BedelsizMiktar")) or 0

    if satis_adet <= 0:
        yorumlar.append(("warning", "Bu yil hic satis gorunmuyor. Urun rafta mi, fiyati dogru mu kontrol edilmeli."))
        return yorumlar[:3]

    if marj is not None:
        if marj < 0:
            yorumlar.append(("warning", f"Urun zararda gorunuyor (marj %{marj:.1f}). Satis fiyati veya alis maliyeti gozden gecirilmeli."))
        elif marj < MARJ_COK_DUSUK:
            yorumlar.append(("warning", f"Kar marji cok dusuk (%{marj:.1f}). Fiyat guncellemesi dusunulebilir."))
        elif marj < MARJ_DUSUK:
            yorumlar.append(("info", f"Kar marji dusuk tarafta (%{marj:.1f})."))
        elif marj > MARJ_GUCLU:
            yorumlar.append(("success", f"Kar marji guclu (%{marj:.1f})."))

    gunluk = satis_adet / _elapsed_days()
    if gunluk > 0 and kalan > 0:
        kapsama = kalan / gunluk
        if kapsama > STOK_YUKSEK_GUN:
            yorumlar.append(("warning", f"Stok yuksek: mevcut satis hiziyla yaklasik {kapsama/365:.1f} yillik stok var ({kalan:.0f} adet)."))
        elif kapsama < STOK_DUSUK_GUN:
            yorumlar.append(("warning", f"Stok azaliyor: mevcut hizla yaklasik {kapsama:.0f} gunluk stok kaldi. Siparis planlanmali."))

    son_satis = row.get("SonSatisTarihi")
    try:
        gecen = (date.today() - son_satis.date()).days if hasattr(son_satis, "date") else None
        if gecen is not None and gecen > HAREKETSIZ_GUN:
            yorumlar.append(("warning", f"Son satistan {gecen} gun gecmis. Urun hareketsizlesmis olabilir."))
    except Exception:
        pass

    if alis_haric > 0 and abs(alis_dahil - alis_haric) < 0.01:
        yorumlar.append(("info", "Alis KDV dahil ile haric ayni: alis faturalarinda satir KDV'si girilmemis olabilir."))

    if bedelsiz > 0:
        yorumlar.append(("info", f"{bedelsiz:.0f} adet bedelsiz alis var; efektif maliyet bu sayede dusuk."))

    if not yorumlar:
        yorumlar.append(("success", "Genel gorunum dengeli: marj ve stok seviyesi normal aralikta."))

    return yorumlar[:3]


def comment_product_yearly(df) -> list[tuple[str, str]]:
    yorumlar: list[tuple[str, str]] = []
    year_now = get_report_year()

    d = df.copy()
    d = d[(d["SatisMiktari"].fillna(0) > 0)]
    if d.empty or "Yil" not in d.columns:
        return [("warning", "Yillik satis verisi bulunamadi.")]

    d = d.sort_values("Yil")
    son = d.iloc[-1]
    son_yil = int(son["Yil"])

    if "BrutKarKdvHaric" in d.columns and d["BrutKarKdvHaric"].notna().any():
        best = d.loc[d["BrutKarKdvHaric"].idxmax()]
        yorumlar.append(("info", f"En karli yil {int(best['Yil'])} ({safe_float(best['BrutKarKdvHaric']):,.0f} TL brut kar)."))

    if len(d) >= 2:
        onceki = d.iloc[-2]
        m1, m0 = safe_float(son["SatisMiktari"]), safe_float(onceki["SatisMiktari"])
        if m0 and m1 is not None:
            degisim = (m1 - m0) / m0 * 100
            kisim = f"{int(onceki['Yil'])} -> {son_yil} satis miktari"
            not_ek = " (yil henuz bitmedi)" if son_yil == year_now and date.today().year == year_now else ""
            if degisim <= -20:
                yorumlar.append(("warning", f"{kisim} %{abs(degisim):.0f} dusmus{not_ek}."))
            elif degisim >= 20:
                yorumlar.append(("success", f"{kisim} %{degisim:.0f} artmis{not_ek}."))
            else:
                yorumlar.append(("info", f"{kisim} yatay seyrediyor (%{degisim:+.0f}){not_ek}."))

        o_marj, s_marj = safe_float(onceki.get("BrutKarOraniKdvHaric")), safe_float(son.get("BrutKarOraniKdvHaric"))
        if o_marj is not None and s_marj is not None and abs(s_marj - o_marj) >= 3:
            yon = "dusmus" if s_marj < o_marj else "yukselmis"
            seviye = "warning" if s_marj < o_marj else "success"
            yorumlar.append((seviye, f"Kar marji %{o_marj:.1f}'den %{s_marj:.1f}'e {yon}."))

    return yorumlar[:3]


def comment_category(df, category: str) -> list[tuple[str, str]]:
    yorumlar: list[tuple[str, str]] = []
    if df.empty:
        return yorumlar

    toplam_satis = safe_float(df["NetSatisKdvHaric"].sum()) or 0
    toplam_kar = safe_float(df["TahminiBrutKarKdvHaric"].sum()) or 0

    if toplam_satis > 0:
        marj = toplam_kar / toplam_satis * 100
        if marj < MARJ_DUSUK:
            yorumlar.append(("warning", f"Kategori geneli marj dusuk (%{marj:.1f})."))
        else:
            yorumlar.append(("info", f"Kategori geneli marj %{marj:.1f}."))

    if toplam_kar > 0:
        lider = df.iloc[0]
        pay = (safe_float(lider["TahminiBrutKarKdvHaric"]) or 0) / toplam_kar * 100
        if pay >= 25:
            yorumlar.append(("info", f"Karin %{pay:.0f}'i tek urunden geliyor: {lider['UrunAdi']}. Stok surekliligi kritik."))

    negatif = df[df["TahminiBrutKarKdvHaric"].apply(lambda v: (safe_float(v) or 0) < 0)]
    if len(negatif) > 0:
        yorumlar.append(("warning", f"{len(negatif)} urun zararda satiliyor. Detay tablosunun sonuna bak."))

    return yorumlar[:3]


def comment_daily_profit(df, report_date: str) -> list[tuple[str, str]]:
    yorumlar: list[tuple[str, str]] = []
    if df.empty:
        return [("warning", "Bu tarih için satış verisi bulunamadı.")]

    satis = safe_float(df["NetSatisKdvHaric"].sum()) or 0
    kar = safe_float(df["TahminiBrutKarKdvHaric"].sum()) or 0
    maliyet_eksik = int(df["MaliyetEksikMi"].fillna(0).sum()) if "MaliyetEksikMi" in df.columns else 0
    supheli = int(df["SupheliMaliyetMi"].fillna(0).sum()) if "SupheliMaliyetMi" in df.columns else 0
    zarar_eden = int((df["TahminiBrutKarKdvHaric"].fillna(0) < 0).sum()) if "TahminiBrutKarKdvHaric" in df.columns else 0

    yorumlar.append(("info", "Bu ekran önce ana kategori özetini, maliyeti olmayanları, zarar edenleri ve şüpheli maliyetleri ayırmak için kullanılmalı."))

    if satis > 0:
        marj = kar / satis * 100
        yorumlar.append(("info", f"Stok kartı bazlı tahmini brüt kâr oranı %{marj:.1f}. Maliyet doğruluğu teyit edilmeden nihai karar verilmemeli."))

    if maliyet_eksik > 0:
        yorumlar.append(("warning", f"{maliyet_eksik} üründe maliyet yok. Öncelik bu ürünlerin kart maliyetlerini düzeltmek olmalı."))

    if zarar_eden > 0:
        yorumlar.append(("warning", f"{zarar_eden} ürün zarar ediyor görünüyor. Zarar eden ürünler sekmesini kontrol et."))

    if supheli > 0:
        yorumlar.append(("warning", f"{supheli} üründe maliyet şüpheli işaretlendi."))

    return yorumlar[:5]
