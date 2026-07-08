import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

from core.db import query_df
from core.turkce import normalize


def find_product(conn, barcode: str | None = None, product_text: str | None = None) -> pd.DataFrame:
    if barcode:
        sql = """
        SELECT TOP 1
            IND AS StokInd,
            STOKKODU AS Barkod,
            MALINCINSI AS UrunAdi,
            KOD1 AS Tedarikci,
            KOD2 AS AnaKategori,
            KOD4 AS AltKategori,
            KOD7 AS Marka
        FROM dbo.F0101TBLSTOKLAR WITH (NOLOCK)
        WHERE STOKKODU = ?
        """
        return query_df(conn, sql, [barcode])

    if product_text:
        words = [w.strip() for w in product_text.split() if len(w.strip()) >= 2]
        if not words:
            return pd.DataFrame()

        where_parts = []
        params = []

        for word in words:
            where_parts.append("MALINCINSI LIKE ?")
            params.append(f"%{word}%")

        sql = f"""
        SELECT TOP 15
            IND AS StokInd,
            STOKKODU AS Barkod,
            MALINCINSI AS UrunAdi,
            KOD1 AS Tedarikci,
            KOD2 AS AnaKategori,
            KOD4 AS AltKategori,
            KOD7 AS Marka,
            AKTIF
        FROM dbo.F0101TBLSTOKLAR WITH (NOLOCK)
        WHERE {" AND ".join(where_parts)}
          AND ISNULL(DELETED, 0) = 0
        ORDER BY AKTIF DESC, MALINCINSI
        """
        return query_df(conn, sql, params)

    return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def find_product_cached(_conn, barcode: str | None = None, product_text: str | None = None) -> pd.DataFrame:
    """5 dakikalik onbellek: ayni urun aramasi tekrarlandiginda veritabanina gidilmez.
    _conn parametresi alt cizgi ile basladigi icin cache anahtarina dahil edilmez."""
    return find_product(_conn, barcode=barcode, product_text=product_text)


@st.cache_data(ttl=600, show_spinner=False)
def _load_product_index(_conn) -> pd.DataFrame:
    """Aktif urun listesi 10 dakikalik onbellege alinir; bulanik arama bunun uzerinde calisir."""
    sql = """
    SELECT
        IND AS StokInd,
        STOKKODU AS Barkod,
        MALINCINSI AS UrunAdi,
        KOD1 AS Tedarikci,
        KOD2 AS AnaKategori,
        KOD4 AS AltKategori,
        KOD7 AS Marka,
        AKTIF
    FROM dbo.F0101TBLSTOKLAR WITH (NOLOCK)
    WHERE ISNULL(DELETED, 0) = 0
    """
    df = query_df(_conn, sql)
    if not df.empty:
        df["_norm"] = df["UrunAdi"].apply(normalize)
    return df


def _token_score(query_norm: str, name_norm: str) -> float:
    """Sorgudaki her kelimeyi urun adindaki en yakin kelimeyle eslestirir,
    ortalamasini dondurur. 'sivas 12' -> CHIVAS 12'yi dogru bulur,
    '12' gibi rakamlarin yanlis urunu kazandirmasini engeller."""
    q_tokens = [tok for tok in query_norm.split() if tok]
    n_tokens = [tok for tok in name_norm.split() if tok]
    if not q_tokens or not n_tokens:
        return 0.0
    total = 0.0
    for q_tok in q_tokens:
        total += max(fuzz.ratio(q_tok, n_tok) for n_tok in n_tokens)
    return total / len(q_tokens)


def fuzzy_find(conn, product_text: str, limit: int = 10, cutoff: float = 70.0) -> pd.DataFrame:
    """Yazim hatalarina dayanikli urun arama (rapidfuzz).
    LIKE aramasi bos dondugunde devreye girer."""
    index = _load_product_index(conn)
    if index.empty or not product_text:
        return pd.DataFrame()

    query = normalize(product_text)
    scores = [_token_score(query, name) for name in index["_norm"].tolist()]

    index = index.copy()
    index["Benzerlik"] = [round(s) for s in scores]
    result = index[index["Benzerlik"] >= cutoff]
    if result.empty:
        return pd.DataFrame()

    result = result.sort_values(["Benzerlik", "AKTIF"], ascending=[False, False]).head(limit)
    return result.drop(columns=["_norm"]).reset_index(drop=True)
