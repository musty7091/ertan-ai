DECLARE @Tarih DATE = ?;
DECLARE @HaricIND INT = ?;
DECLARE @ErtesiGun DATE = DATEADD(DAY, 1, @Tarih);

WITH SatisHam AS (
    SELECT
        h.STOKNO AS StokInd,
        LTRIM(RTRIM(b.FTIPI)) AS FTIPI,
        h.MIKTAR,
        h.TUTAR AS SatisKdvDahil,
        h.TUTAR / (1 + (ISNULL(h.KDV, 0) / 100.0)) AS SatisKdvHaric
    FROM dbo.F0101D0007TBLPBIENTEGREBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0007TBLPBIENTEGREHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    WHERE b.TARIH >= @Tarih AND b.TARIH < @ErtesiGun
      AND LTRIM(RTRIM(b.FTIPI)) IN ('FIS', 'FATURA', 'G.PUSULA')

    UNION ALL

    SELECT
        h.STOKNO,
        LTRIM(RTRIM(b.FTIPI)),
        h.MIKTAR,
        h.TUTAR,
        h.TUTAR / (1 + (ISNULL(h.KDV, 0) / 100.0))
    FROM dbo.F0101D0011TBLPBIENTEGREBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0011TBLPBIENTEGREHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    WHERE b.TARIH >= @Tarih AND b.TARIH < @ErtesiGun
      AND LTRIM(RTRIM(b.FTIPI)) IN ('FIS', 'FATURA', 'G.PUSULA')

    UNION ALL

    SELECT
        h.STOKNO,
        LTRIM(RTRIM(b.FTIPI)),
        h.MIKTAR,
        h.TUTAR,
        h.TUTAR / (1 + (ISNULL(h.KDV, 0) / 100.0))
    FROM dbo.F0101D0012TBLPBIENTEGREBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0012TBLPBIENTEGREHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    WHERE b.TARIH >= @Tarih AND b.TARIH < @ErtesiGun
      AND LTRIM(RTRIM(b.FTIPI)) IN ('FIS', 'FATURA', 'G.PUSULA')

    UNION ALL

    SELECT
        h.STOKNO,
        LTRIM(RTRIM(b.FTIPI)),
        h.MIKTAR,
        h.TUTAR,
        h.TUTAR / (1 + (ISNULL(h.KDV, 0) / 100.0))
    FROM dbo.F0101D0014TBLPBIENTEGREBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0014TBLPBIENTEGREHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    WHERE b.TARIH >= @Tarih AND b.TARIH < @ErtesiGun
      AND b.IND <> @HaricIND
      AND LTRIM(RTRIM(b.FTIPI)) IN ('FIS', 'FATURA', 'G.PUSULA')
),

Satis AS (
    SELECT
        StokInd,
        COUNT(*) AS SatisSatirSayisi,
        SUM(MIKTAR) AS NetSatisMiktari,
        SUM(SatisKdvDahil) AS NetSatisKdvDahil,
        SUM(SatisKdvHaric) AS NetSatisKdvHaric,
        SUM(CASE WHEN FTIPI = 'G.PUSULA' THEN ABS(MIKTAR) ELSE 0 END) AS IadeMiktari,
        SUM(CASE WHEN FTIPI = 'G.PUSULA' THEN ABS(SatisKdvDahil) ELSE 0 END) AS IadeKdvDahil,
        SUM(CASE WHEN FTIPI = 'G.PUSULA' THEN ABS(SatisKdvHaric) ELSE 0 END) AS IadeKdvHaric
    FROM SatisHam
    GROUP BY StokInd
    HAVING ABS(SUM(MIKTAR)) > 0 OR ABS(SUM(SatisKdvDahil)) > 0
),

Urunler AS (
    SELECT
        s.StokInd,
        u.STOKKODU AS Barkod,
        u.MALINCINSI AS UrunAdi,
        u.KOD1 AS Tedarikci,
        u.KOD2 AS AnaKategori,
        u.KOD4 AS AltKategori,
        u.KOD7 AS Marka,
        u.KALAN AS KartKalan,
        NULLIF(u.MALIYET, 0) AS KartMaliyet,
        NULLIF(u.ALISFIYATI, 0) AS KartAlisFiyati
    FROM Satis s
    INNER JOIN dbo.F0101TBLSTOKLAR u WITH (NOLOCK)
        ON u.IND = s.StokInd
),

AlisHam AS (
    SELECT
        b.TARIH,
        h.IND AS HareketInd,
        h.STOKNO,
        h.STOKKODU,
        h.BARKOD,
        h.MIKTAR,
        h.GERCEKTOPLAM,
        CASE WHEN h.MIKTAR <> 0 THEN h.GERCEKTOPLAM / h.MIKTAR ELSE NULL END AS SonAlisBirimMaliyetKdvHaric
    FROM dbo.F0101D0007TBLALFATBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0007TBLALFATHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    INNER JOIN Urunler u ON (h.STOKNO = u.StokInd OR h.BARKOD = u.Barkod OR h.STOKKODU = u.Barkod)
    WHERE b.TARIH <= @Tarih
      AND ISNULL(b.IPTAL, 0) = 0
      AND ISNULL(b.IADE, 0) = 0
      AND h.MIKTAR > 0
      AND h.GERCEKTOPLAM > 0

    UNION ALL

    SELECT
        b.TARIH,
        h.IND,
        h.STOKNO,
        h.STOKKODU,
        h.BARKOD,
        h.MIKTAR,
        h.GERCEKTOPLAM,
        CASE WHEN h.MIKTAR <> 0 THEN h.GERCEKTOPLAM / h.MIKTAR ELSE NULL END
    FROM dbo.F0101D0011TBLALFATBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0011TBLALFATHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    INNER JOIN Urunler u ON (h.STOKNO = u.StokInd OR h.BARKOD = u.Barkod OR h.STOKKODU = u.Barkod)
    WHERE b.TARIH <= @Tarih
      AND ISNULL(b.IPTAL, 0) = 0
      AND ISNULL(b.IADE, 0) = 0
      AND h.MIKTAR > 0
      AND h.GERCEKTOPLAM > 0

    UNION ALL

    SELECT
        b.TARIH,
        h.IND,
        h.STOKNO,
        h.STOKKODU,
        h.BARKOD,
        h.MIKTAR,
        h.GERCEKTOPLAM,
        CASE WHEN h.MIKTAR <> 0 THEN h.GERCEKTOPLAM / h.MIKTAR ELSE NULL END
    FROM dbo.F0101D0012TBLALFATBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0012TBLALFATHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    INNER JOIN Urunler u ON (h.STOKNO = u.StokInd OR h.BARKOD = u.Barkod OR h.STOKKODU = u.Barkod)
    WHERE b.TARIH <= @Tarih
      AND ISNULL(b.IPTAL, 0) = 0
      AND ISNULL(b.IADE, 0) = 0
      AND h.MIKTAR > 0
      AND h.GERCEKTOPLAM > 0

    UNION ALL

    SELECT
        b.TARIH,
        h.IND,
        h.STOKNO,
        h.STOKKODU,
        h.BARKOD,
        h.MIKTAR,
        h.GERCEKTOPLAM,
        CASE WHEN h.MIKTAR <> 0 THEN h.GERCEKTOPLAM / h.MIKTAR ELSE NULL END
    FROM dbo.F0101D0014TBLALFATBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0014TBLALFATHAREKET h WITH (NOLOCK) ON h.EVRAKNO = b.IND
    INNER JOIN Urunler u ON (h.STOKNO = u.StokInd OR h.BARKOD = u.Barkod OR h.STOKKODU = u.Barkod)
    WHERE b.TARIH <= @Tarih
      AND ISNULL(b.IPTAL, 0) = 0
      AND ISNULL(b.IADE, 0) = 0
      AND h.MIKTAR > 0
      AND h.GERCEKTOPLAM > 0
),

SonAlis AS (
    SELECT
        u.StokInd,
        son.TARIH AS SonAlisTarihi,
        son.SonAlisBirimMaliyetKdvHaric
    FROM Urunler u
    OUTER APPLY (
        SELECT TOP 1
            ah.TARIH,
            ah.SonAlisBirimMaliyetKdvHaric
        FROM AlisHam ah
        WHERE
               ah.STOKNO = u.StokInd
            OR ah.BARKOD = u.Barkod
            OR ah.STOKKODU = u.Barkod
        ORDER BY ah.TARIH DESC, ah.HareketInd DESC
    ) son
),

Hesap AS (
    SELECT
        CONVERT(date, @Tarih) AS RaporTarihi,
        u.Barkod,
        u.UrunAdi,
        u.Tedarikci,
        u.AnaKategori,
        u.AltKategori,
        u.Marka,

        s.SatisSatirSayisi,
        s.NetSatisMiktari,
        s.NetSatisKdvDahil,
        s.NetSatisKdvHaric,
        CASE WHEN s.NetSatisMiktari <> 0 THEN s.NetSatisKdvHaric / s.NetSatisMiktari ELSE NULL END AS OrtalamaSatisFiyatiKdvHaric,
        s.IadeMiktari,
        s.IadeKdvDahil,
        s.IadeKdvHaric,

        u.KartMaliyet,
        u.KartAlisFiyati,
        sa.SonAlisBirimMaliyetKdvHaric,
        sa.SonAlisTarihi,

        COALESCE(u.KartMaliyet, u.KartAlisFiyati, sa.SonAlisBirimMaliyetKdvHaric) AS KullanilanBirimMaliyetKdvHaric,

        CASE
            WHEN u.KartMaliyet IS NOT NULL THEN 'Stok kartı MALIYET'
            WHEN u.KartAlisFiyati IS NOT NULL THEN 'Stok kartı ALISFIYATI'
            WHEN sa.SonAlisBirimMaliyetKdvHaric IS NOT NULL THEN 'Son alış faturası'
            ELSE 'Maliyet yok'
        END AS KullanilanMaliyetKaynak,

        u.KartKalan
    FROM Satis s
    INNER JOIN Urunler u ON u.StokInd = s.StokInd
    LEFT JOIN SonAlis sa ON sa.StokInd = s.StokInd
)

SELECT
    h.*,

    CASE
        WHEN h.KullanilanBirimMaliyetKdvHaric IS NOT NULL AND h.KullanilanBirimMaliyetKdvHaric > 0
        THEN h.NetSatisMiktari * h.KullanilanBirimMaliyetKdvHaric
        ELSE NULL
    END AS TahminiSatilanMalMaliyetiKdvHaric,

    CASE
        WHEN h.KullanilanBirimMaliyetKdvHaric IS NOT NULL AND h.KullanilanBirimMaliyetKdvHaric > 0
        THEN h.NetSatisKdvHaric - (h.NetSatisMiktari * h.KullanilanBirimMaliyetKdvHaric)
        ELSE NULL
    END AS TahminiBrutKarKdvHaric,

    CASE
        WHEN h.NetSatisKdvHaric <> 0
         AND h.KullanilanBirimMaliyetKdvHaric IS NOT NULL
         AND h.KullanilanBirimMaliyetKdvHaric > 0
        THEN
            (
                h.NetSatisKdvHaric - (h.NetSatisMiktari * h.KullanilanBirimMaliyetKdvHaric)
            ) / h.NetSatisKdvHaric * 100
        ELSE NULL
    END AS BrutKarOraniKdvHaric,

    CASE
        WHEN h.SonAlisBirimMaliyetKdvHaric IS NOT NULL AND h.SonAlisBirimMaliyetKdvHaric > 0
        THEN h.NetSatisMiktari * h.SonAlisBirimMaliyetKdvHaric
        ELSE NULL
    END AS TahminiMaliyetSonAlisKdvHaric,

    CASE
        WHEN h.SonAlisBirimMaliyetKdvHaric IS NOT NULL AND h.SonAlisBirimMaliyetKdvHaric > 0
        THEN h.NetSatisKdvHaric - (h.NetSatisMiktari * h.SonAlisBirimMaliyetKdvHaric)
        ELSE NULL
    END AS TahminiKarSonAlisKdvHaric,

    CASE
        WHEN h.OrtalamaSatisFiyatiKdvHaric > 0 AND h.KullanilanBirimMaliyetKdvHaric IS NOT NULL
        THEN h.KullanilanBirimMaliyetKdvHaric / h.OrtalamaSatisFiyatiKdvHaric * 100
        ELSE NULL
    END AS KullanilanMaliyetSatisOrani,

    CASE
        WHEN h.OrtalamaSatisFiyatiKdvHaric > 0 AND h.SonAlisBirimMaliyetKdvHaric IS NOT NULL
        THEN h.SonAlisBirimMaliyetKdvHaric / h.OrtalamaSatisFiyatiKdvHaric * 100
        ELSE NULL
    END AS SonAlisSatisOrani,

    CASE
        WHEN h.KartMaliyet IS NOT NULL AND h.SonAlisBirimMaliyetKdvHaric IS NOT NULL AND h.KartMaliyet > 0
        THEN ABS(h.SonAlisBirimMaliyetKdvHaric - h.KartMaliyet) / h.KartMaliyet * 100
        ELSE NULL
    END AS SonAlisKartMaliyetFarkYuzde,

    CASE
        WHEN h.KullanilanBirimMaliyetKdvHaric IS NULL OR h.KullanilanBirimMaliyetKdvHaric <= 0
        THEN 1
        ELSE 0
    END AS MaliyetEksikMi,

    CASE
        WHEN h.KullanilanBirimMaliyetKdvHaric IS NULL OR h.KullanilanBirimMaliyetKdvHaric <= 0 THEN 1
        WHEN h.OrtalamaSatisFiyatiKdvHaric IS NOT NULL
         AND h.OrtalamaSatisFiyatiKdvHaric > 0
         AND h.KullanilanBirimMaliyetKdvHaric > h.OrtalamaSatisFiyatiKdvHaric * 1.10 THEN 1
        WHEN h.OrtalamaSatisFiyatiKdvHaric IS NOT NULL
         AND h.OrtalamaSatisFiyatiKdvHaric > 0
         AND h.KullanilanBirimMaliyetKdvHaric > h.OrtalamaSatisFiyatiKdvHaric * 0.90 THEN 1
        WHEN h.KartMaliyet IS NOT NULL
         AND h.SonAlisBirimMaliyetKdvHaric IS NOT NULL
         AND h.KartMaliyet > 0
         AND ABS(h.SonAlisBirimMaliyetKdvHaric - h.KartMaliyet) / h.KartMaliyet > 0.50 THEN 1
        ELSE 0
    END AS SupheliMaliyetMi,

    CASE
        WHEN h.KullanilanBirimMaliyetKdvHaric IS NULL OR h.KullanilanBirimMaliyetKdvHaric <= 0
            THEN 'Maliyet yok'
        WHEN h.OrtalamaSatisFiyatiKdvHaric IS NOT NULL
         AND h.OrtalamaSatisFiyatiKdvHaric > 0
         AND h.KullanilanBirimMaliyetKdvHaric > h.OrtalamaSatisFiyatiKdvHaric * 1.10
            THEN 'Kritik: maliyet satış fiyatından yüksek'
        WHEN h.OrtalamaSatisFiyatiKdvHaric IS NOT NULL
         AND h.OrtalamaSatisFiyatiKdvHaric > 0
         AND h.KullanilanBirimMaliyetKdvHaric > h.OrtalamaSatisFiyatiKdvHaric * 0.90
            THEN 'Dikkat: maliyet satış fiyatına çok yakın'
        WHEN h.KartMaliyet IS NOT NULL
         AND h.SonAlisBirimMaliyetKdvHaric IS NOT NULL
         AND h.KartMaliyet > 0
         AND ABS(h.SonAlisBirimMaliyetKdvHaric - h.KartMaliyet) / h.KartMaliyet > 0.50
            THEN 'Dikkat: son alış ile stok kartı maliyeti çok farklı'
        ELSE 'Normal'
    END AS MaliyetSaglikDurumu

FROM Hesap h
ORDER BY SupheliMaliyetMi DESC, TahminiBrutKarKdvHaric ASC, NetSatisKdvHaric DESC;
