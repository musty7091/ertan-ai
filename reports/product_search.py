import pandas as pd

from core.db import query_df


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
