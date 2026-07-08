DECLARE @Barkod NVARCHAR(50) = ?;
-- Hatali/mukerrer satis entegrasyon basligi; raporlardan dislanir (config: EXCLUDED_SALE_HEADER_IND)
DECLARE @HaricIND INT = ?;
-- NOT: Tarih araliklari fiziksel donem tablolarina (D0007/D0011/D0012/D0014) baglidir.
-- Yeni donem tablosu (or. D0015) acilirsa buraya yeni bir UNION ALL blogu eklenmelidir.
-- D0014 ust siniri bilerek genis tutuldu ki yil devrinde rapor sessizce bos kalmasin.

WITH Urun AS (
    SELECT TOP 1
        IND AS StokInd,
        STOKKODU AS Barkod,
        MALINCINSI AS UrunAdi,
        KOD1 AS Tedarikci,
        KOD2 AS AnaKategori,
        KOD4 AS AltKategori,
        KOD7 AS Marka
    FROM dbo.F0101TBLSTOKLAR WITH (NOLOCK)
    WHERE STOKKODU = @Barkod
),

SatisHam AS (
    SELECT
        YEAR(b.TARIH) AS Yil,
        h.MIKTAR,
        h.TUTAR AS SatisKdvDahil,
        h.TUTAR / (1 + (ISNULL(h.KDV, 0) / 100.0)) AS SatisKdvHaric
    FROM dbo.F0101D0007TBLPBIENTEGREBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0007TBLPBIENTEGREHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    INNER JOIN Urun u ON (h.STOKNO = u.StokInd OR h.BARKOD = u.Barkod)
    WHERE b.TARIH >= '2019-01-01' AND b.TARIH < '2023-01-01'
      AND LTRIM(RTRIM(b.FTIPI)) IN ('FIS', 'FATURA', 'G.PUSULA')

    UNION ALL

    SELECT
        YEAR(b.TARIH),
        h.MIKTAR,
        h.TUTAR,
        h.TUTAR / (1 + (ISNULL(h.KDV, 0) / 100.0))
    FROM dbo.F0101D0011TBLPBIENTEGREBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0011TBLPBIENTEGREHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    INNER JOIN Urun u ON (h.STOKNO = u.StokInd OR h.BARKOD = u.Barkod)
    WHERE b.TARIH >= '2023-01-01' AND b.TARIH < '2024-01-01'
      AND LTRIM(RTRIM(b.FTIPI)) IN ('FIS', 'FATURA', 'G.PUSULA')

    UNION ALL

    SELECT
        YEAR(b.TARIH),
        h.MIKTAR,
        h.TUTAR,
        h.TUTAR / (1 + (ISNULL(h.KDV, 0) / 100.0))
    FROM dbo.F0101D0012TBLPBIENTEGREBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0012TBLPBIENTEGREHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    INNER JOIN Urun u ON (h.STOKNO = u.StokInd OR h.BARKOD = u.Barkod)
    WHERE b.TARIH >= '2024-01-01' AND b.TARIH < '2026-01-01'
      AND LTRIM(RTRIM(b.FTIPI)) IN ('FIS', 'FATURA', 'G.PUSULA')

    UNION ALL

    SELECT
        YEAR(b.TARIH),
        h.MIKTAR,
        h.TUTAR,
        h.TUTAR / (1 + (ISNULL(h.KDV, 0) / 100.0))
    FROM dbo.F0101D0014TBLPBIENTEGREBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0014TBLPBIENTEGREHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    INNER JOIN Urun u ON (h.STOKNO = u.StokInd OR h.BARKOD = u.Barkod)
    WHERE b.TARIH >= '2026-01-01' AND b.TARIH < '2100-01-01'
      AND b.IND <> @HaricIND
      AND LTRIM(RTRIM(b.FTIPI)) IN ('FIS', 'FATURA', 'G.PUSULA')
),

Satis AS (
    SELECT
        Yil,
        SUM(MIKTAR) AS SatisMiktari,
        SUM(SatisKdvDahil) AS SatisKdvDahil,
        SUM(SatisKdvHaric) AS SatisKdvHaric
    FROM SatisHam
    GROUP BY Yil
),

AlisHam AS (
    SELECT
        YEAR(b.TARIH) AS Yil,
        CASE WHEN ISNULL(b.IADE, 0) = 1 THEN -h.MIKTAR ELSE h.MIKTAR END AS AlisMiktari,
        CASE WHEN ISNULL(b.IADE, 0) = 1 THEN -h.GERCEKTOPLAM ELSE h.GERCEKTOPLAM END AS AlisKdvHaric,
        CASE WHEN ISNULL(b.IADE, 0) = 1 THEN -(CASE WHEN ISNULL(h.KDVTUTARI, 0) <> 0 THEN h.GERCEKTOPLAM + h.KDVTUTARI ELSE h.GERCEKTOPLAM * (1 + ISNULL(h.KDV, 0) / 100.0) END) ELSE (CASE WHEN ISNULL(h.KDVTUTARI, 0) <> 0 THEN h.GERCEKTOPLAM + h.KDVTUTARI ELSE h.GERCEKTOPLAM * (1 + ISNULL(h.KDV, 0) / 100.0) END) END AS AlisKdvDahil,
        CASE
            WHEN ISNULL(b.IADE, 0) = 0 AND h.MIKTAR > 0 AND (
                ISNULL(h.GERCEKTOPLAM, 0) = 0
                OR ISNULL(h.ISK1, 0) = 100 OR ISNULL(h.ISK2, 0) = 100 OR ISNULL(h.ISK3, 0) = 100
                OR ISNULL(h.ISK4, 0) = 100 OR ISNULL(h.ISK5, 0) = 100 OR ISNULL(h.ISK6, 0) = 100
            )
            THEN h.MIKTAR
            ELSE 0
        END AS BedelsizMiktar
    FROM dbo.F0101D0007TBLALFATBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0007TBLALFATHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    INNER JOIN Urun u ON (h.STOKNO = u.StokInd OR h.BARKOD = u.Barkod OR h.STOKKODU = u.Barkod)
    WHERE b.TARIH >= '2019-01-01' AND b.TARIH < '2023-01-01'
      AND ISNULL(b.IPTAL, 0) = 0

    UNION ALL

    SELECT
        YEAR(b.TARIH),
        CASE WHEN ISNULL(b.IADE, 0) = 1 THEN -h.MIKTAR ELSE h.MIKTAR END,
        CASE WHEN ISNULL(b.IADE, 0) = 1 THEN -h.GERCEKTOPLAM ELSE h.GERCEKTOPLAM END,
        CASE WHEN ISNULL(b.IADE, 0) = 1 THEN -(CASE WHEN ISNULL(h.KDVTUTARI, 0) <> 0 THEN h.GERCEKTOPLAM + h.KDVTUTARI ELSE h.GERCEKTOPLAM * (1 + ISNULL(h.KDV, 0) / 100.0) END) ELSE (CASE WHEN ISNULL(h.KDVTUTARI, 0) <> 0 THEN h.GERCEKTOPLAM + h.KDVTUTARI ELSE h.GERCEKTOPLAM * (1 + ISNULL(h.KDV, 0) / 100.0) END) END,
        CASE
            WHEN ISNULL(b.IADE, 0) = 0 AND h.MIKTAR > 0 AND (
                ISNULL(h.GERCEKTOPLAM, 0) = 0
                OR ISNULL(h.ISK1, 0) = 100 OR ISNULL(h.ISK2, 0) = 100 OR ISNULL(h.ISK3, 0) = 100
                OR ISNULL(h.ISK4, 0) = 100 OR ISNULL(h.ISK5, 0) = 100 OR ISNULL(h.ISK6, 0) = 100
            )
            THEN h.MIKTAR
            ELSE 0
        END
    FROM dbo.F0101D0011TBLALFATBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0011TBLALFATHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    INNER JOIN Urun u ON (h.STOKNO = u.StokInd OR h.BARKOD = u.Barkod OR h.STOKKODU = u.Barkod)
    WHERE b.TARIH >= '2023-01-01' AND b.TARIH < '2024-01-01'
      AND ISNULL(b.IPTAL, 0) = 0

    UNION ALL

    SELECT
        YEAR(b.TARIH),
        CASE WHEN ISNULL(b.IADE, 0) = 1 THEN -h.MIKTAR ELSE h.MIKTAR END,
        CASE WHEN ISNULL(b.IADE, 0) = 1 THEN -h.GERCEKTOPLAM ELSE h.GERCEKTOPLAM END,
        CASE WHEN ISNULL(b.IADE, 0) = 1 THEN -(CASE WHEN ISNULL(h.KDVTUTARI, 0) <> 0 THEN h.GERCEKTOPLAM + h.KDVTUTARI ELSE h.GERCEKTOPLAM * (1 + ISNULL(h.KDV, 0) / 100.0) END) ELSE (CASE WHEN ISNULL(h.KDVTUTARI, 0) <> 0 THEN h.GERCEKTOPLAM + h.KDVTUTARI ELSE h.GERCEKTOPLAM * (1 + ISNULL(h.KDV, 0) / 100.0) END) END,
        CASE
            WHEN ISNULL(b.IADE, 0) = 0 AND h.MIKTAR > 0 AND (
                ISNULL(h.GERCEKTOPLAM, 0) = 0
                OR ISNULL(h.ISK1, 0) = 100 OR ISNULL(h.ISK2, 0) = 100 OR ISNULL(h.ISK3, 0) = 100
                OR ISNULL(h.ISK4, 0) = 100 OR ISNULL(h.ISK5, 0) = 100 OR ISNULL(h.ISK6, 0) = 100
            )
            THEN h.MIKTAR
            ELSE 0
        END
    FROM dbo.F0101D0012TBLALFATBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0012TBLALFATHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    INNER JOIN Urun u ON (h.STOKNO = u.StokInd OR h.BARKOD = u.Barkod OR h.STOKKODU = u.Barkod)
    WHERE b.TARIH >= '2024-01-01' AND b.TARIH < '2026-01-01'
      AND ISNULL(b.IPTAL, 0) = 0

    UNION ALL

    SELECT
        YEAR(b.TARIH),
        CASE WHEN ISNULL(b.IADE, 0) = 1 THEN -h.MIKTAR ELSE h.MIKTAR END,
        CASE WHEN ISNULL(b.IADE, 0) = 1 THEN -h.GERCEKTOPLAM ELSE h.GERCEKTOPLAM END,
        CASE WHEN ISNULL(b.IADE, 0) = 1 THEN -(CASE WHEN ISNULL(h.KDVTUTARI, 0) <> 0 THEN h.GERCEKTOPLAM + h.KDVTUTARI ELSE h.GERCEKTOPLAM * (1 + ISNULL(h.KDV, 0) / 100.0) END) ELSE (CASE WHEN ISNULL(h.KDVTUTARI, 0) <> 0 THEN h.GERCEKTOPLAM + h.KDVTUTARI ELSE h.GERCEKTOPLAM * (1 + ISNULL(h.KDV, 0) / 100.0) END) END,
        CASE
            WHEN ISNULL(b.IADE, 0) = 0 AND h.MIKTAR > 0 AND (
                ISNULL(h.GERCEKTOPLAM, 0) = 0
                OR ISNULL(h.ISK1, 0) = 100 OR ISNULL(h.ISK2, 0) = 100 OR ISNULL(h.ISK3, 0) = 100
                OR ISNULL(h.ISK4, 0) = 100 OR ISNULL(h.ISK5, 0) = 100 OR ISNULL(h.ISK6, 0) = 100
            )
            THEN h.MIKTAR
            ELSE 0
        END
    FROM dbo.F0101D0014TBLALFATBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0014TBLALFATHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    INNER JOIN Urun u ON (h.STOKNO = u.StokInd OR h.BARKOD = u.Barkod OR h.STOKKODU = u.Barkod)
    WHERE b.TARIH >= '2026-01-01' AND b.TARIH < '2100-01-01'
      AND ISNULL(b.IPTAL, 0) = 0
),

Alis AS (
    SELECT
        Yil,
        SUM(AlisMiktari) AS AlisMiktari,
        SUM(AlisKdvHaric) AS AlisKdvHaric,
        SUM(AlisKdvDahil) AS AlisKdvDahil,
        SUM(BedelsizMiktar) AS BedelsizMiktar
    FROM AlisHam
    GROUP BY Yil
),

Yillar AS (
    SELECT Yil FROM Satis
    UNION
    SELECT Yil FROM Alis
)

SELECT
    u.Barkod,
    u.UrunAdi,
    u.Tedarikci,
    u.AnaKategori,
    u.AltKategori,
    u.Marka,
    y.Yil,

    ISNULL(s.SatisMiktari, 0) AS SatisMiktari,
    ISNULL(s.SatisKdvDahil, 0) AS SatisKdvDahil,
    ISNULL(s.SatisKdvHaric, 0) AS SatisKdvHaric,

    ISNULL(a.AlisMiktari, 0) AS AlisMiktari,
    ISNULL(a.AlisKdvHaric, 0) AS AlisKdvHaric,
    ISNULL(a.AlisKdvDahil, 0) AS AlisKdvDahil,
    ISNULL(a.BedelsizMiktar, 0) AS BedelsizMiktar,

    CASE
        WHEN ISNULL(s.SatisMiktari, 0) <> 0
        THEN s.SatisKdvDahil / s.SatisMiktari
        ELSE NULL
    END AS OrtalamaSatisKdvDahil,

    CASE
        WHEN ISNULL(s.SatisMiktari, 0) <> 0
        THEN s.SatisKdvHaric / s.SatisMiktari
        ELSE NULL
    END AS OrtalamaSatisKdvHaric,

    CASE
        WHEN ISNULL(a.AlisMiktari, 0) <> 0
        THEN a.AlisKdvHaric / a.AlisMiktari
        ELSE NULL
    END AS OrtalamaAlisKdvHaric,

    CASE
        WHEN ISNULL(a.AlisMiktari, 0) <> 0
        THEN s.SatisMiktari * (a.AlisKdvHaric / a.AlisMiktari)
        ELSE NULL
    END AS TahminiSatilanMalMaliyetiKdvHaric,

    CASE
        WHEN ISNULL(a.AlisMiktari, 0) <> 0
        THEN s.SatisKdvHaric - (s.SatisMiktari * (a.AlisKdvHaric / a.AlisMiktari))
        ELSE NULL
    END AS BrutKarKdvHaric,

    CASE
        WHEN ISNULL(s.SatisKdvHaric, 0) <> 0 AND ISNULL(a.AlisMiktari, 0) <> 0
        THEN
            (
                s.SatisKdvHaric - (s.SatisMiktari * (a.AlisKdvHaric / a.AlisMiktari))
            ) / s.SatisKdvHaric * 100
        ELSE NULL
    END AS BrutKarOraniKdvHaric,

    ISNULL(s.SatisMiktari, 0) - ISNULL(a.AlisMiktari, 0) AS AlisSatisMiktarFarki

FROM Urun u
CROSS JOIN Yillar y
LEFT JOIN Satis s ON s.Yil = y.Yil
LEFT JOIN Alis a ON a.Yil = y.Yil
ORDER BY y.Yil;
