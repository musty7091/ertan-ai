DECLARE @AltKategori NVARCHAR(100) = ?;
DECLARE @Limit INT = ?;
DECLARE @Baslangic DATE = '2026-01-01';
DECLARE @Bitis DATE = '2027-01-01';

WITH Urunler AS (
    SELECT
        IND AS StokInd,
        STOKKODU AS Barkod,
        MALINCINSI AS UrunAdi,
        KOD1 AS Tedarikci,
        KOD2 AS AnaKategori,
        KOD4 AS AltKategori,
        KOD7 AS Marka,
        KALAN AS KartKalan
    FROM dbo.F0101TBLSTOKLAR WITH (NOLOCK)
    WHERE KOD4 = @AltKategori
      AND ISNULL(DELETED, 0) = 0
),

Satis AS (
    SELECT
        u.StokInd,
        SUM(h.MIKTAR) AS NetSatisMiktari,
        SUM(h.TUTAR) AS NetSatisKdvDahil,
        SUM(h.TUTAR / (1 + (ISNULL(h.KDV, 0) / 100.0))) AS NetSatisKdvHaric,
        MAX(b.TARIH) AS SonSatisTarihi
    FROM dbo.F0101D0014TBLPBIENTEGREBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0014TBLPBIENTEGREHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    INNER JOIN Urunler u ON h.STOKNO = u.StokInd
    WHERE b.TARIH >= @Baslangic
      AND b.TARIH < @Bitis
      AND b.IND <> 166576
      AND LTRIM(RTRIM(b.FTIPI)) IN ('FIS', 'FATURA', 'G.PUSULA')
    GROUP BY u.StokInd
),

Alis AS (
    SELECT
        u.StokInd,
        SUM(CASE WHEN ISNULL(b.IADE, 0) = 1 THEN -h.MIKTAR ELSE h.MIKTAR END) AS NetAlisMiktari,
        SUM(CASE WHEN ISNULL(b.IADE, 0) = 1 THEN -h.GERCEKTOPLAM ELSE h.GERCEKTOPLAM END) AS NetAlisKdvHaric,
        SUM(CASE WHEN ISNULL(b.IADE, 0) = 1 THEN -(h.GERCEKTOPLAM + ISNULL(h.KDVTUTARI, 0)) ELSE h.GERCEKTOPLAM + ISNULL(h.KDVTUTARI, 0) END) AS NetAlisKdvDahil,
        SUM(CASE WHEN ISNULL(b.IADE, 0) = 0 AND h.MIKTAR > 0 AND (
            ISNULL(h.GERCEKTOPLAM, 0) = 0
            OR ISNULL(h.ISK1, 0) = 100 OR ISNULL(h.ISK2, 0) = 100 OR ISNULL(h.ISK3, 0) = 100
            OR ISNULL(h.ISK4, 0) = 100 OR ISNULL(h.ISK5, 0) = 100 OR ISNULL(h.ISK6, 0) = 100
        ) THEN h.MIKTAR ELSE 0 END) AS BedelsizMiktar
    FROM dbo.F0101D0014TBLALFATBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0014TBLALFATHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    INNER JOIN Urunler u ON (h.STOKNO = u.StokInd OR h.BARKOD = u.Barkod OR h.STOKKODU = u.Barkod)
    WHERE b.TARIH >= @Baslangic
      AND b.TARIH < @Bitis
      AND ISNULL(b.IPTAL, 0) = 0
    GROUP BY u.StokInd
)

SELECT TOP (@Limit)
    u.Barkod,
    u.UrunAdi,
    u.Tedarikci,
    u.AnaKategori,
    u.AltKategori,
    u.Marka,
    u.KartKalan,
    ISNULL(s.NetSatisMiktari, 0) AS NetSatisMiktari,
    ISNULL(s.NetSatisKdvDahil, 0) AS NetSatisKdvDahil,
    ISNULL(s.NetSatisKdvHaric, 0) AS NetSatisKdvHaric,
    ISNULL(a.NetAlisMiktari, 0) AS NetAlisMiktari,
    ISNULL(a.NetAlisKdvHaric, 0) AS NetAlisKdvHaric,
    ISNULL(a.NetAlisKdvDahil, 0) AS NetAlisKdvDahil,
    ISNULL(a.BedelsizMiktar, 0) AS BedelsizMiktar,
    CASE WHEN ISNULL(a.NetAlisMiktari, 0) <> 0 THEN a.NetAlisKdvHaric / a.NetAlisMiktari ELSE NULL END AS EfektifAlisMaliyetiKdvHaric,
    CASE WHEN ISNULL(s.NetSatisMiktari, 0) <> 0 THEN s.NetSatisKdvHaric / s.NetSatisMiktari ELSE NULL END AS OrtalamaSatisKdvHaric,
    CASE WHEN ISNULL(a.NetAlisMiktari, 0) <> 0 THEN s.NetSatisKdvHaric - (s.NetSatisMiktari * (a.NetAlisKdvHaric / a.NetAlisMiktari)) ELSE NULL END AS TahminiBrutKarKdvHaric,
    CASE WHEN ISNULL(s.NetSatisKdvHaric, 0) <> 0 AND ISNULL(a.NetAlisMiktari, 0) <> 0 THEN (s.NetSatisKdvHaric - (s.NetSatisMiktari * (a.NetAlisKdvHaric / a.NetAlisMiktari))) / s.NetSatisKdvHaric * 100 ELSE NULL END AS BrutKarOraniKdvHaric,
    s.SonSatisTarihi
FROM Urunler u
LEFT JOIN Satis s ON s.StokInd = u.StokInd
LEFT JOIN Alis a ON a.StokInd = u.StokInd
WHERE ISNULL(s.NetSatisKdvHaric, 0) > 0
ORDER BY TahminiBrutKarKdvHaric DESC, NetSatisKdvHaric DESC;
