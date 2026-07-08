DECLARE @Barkod NVARCHAR(50) = ?;
DECLARE @Baslangic DATE = ?;
DECLARE @Bitis DATE = ?;
-- Hatali/mukerrer satis entegrasyon basligi; raporlardan dislanir (config: EXCLUDED_SALE_HEADER_IND)
DECLARE @HaricIND INT = ?;

WITH Urun AS (
    SELECT TOP 1
        s.IND AS StokInd,
        s.STOKKODU AS Barkod,
        s.MALINCINSI AS UrunAdi,
        s.KOD1 AS Tedarikci,
        s.KOD2 AS AnaKategori,
        s.KOD4 AS AltKategori,
        s.KOD7 AS Marka,
        s.KALAN AS KartKalan,
        s.ALISFIYATI AS KartAlisFiyati,
        s.MALIYET AS KartMaliyet,
        s.SONALISTARIHI AS KartSonAlisTarihi,
        s.SONSATISTARIHI AS KartSonSatisTarihi
    FROM dbo.F0101TBLSTOKLAR s WITH (NOLOCK)
    WHERE s.STOKKODU = @Barkod
),

SatisHam AS (
    SELECT
        b.TARIH,
        LTRIM(RTRIM(b.FTIPI)) AS FTIPI,
        h.MIKTAR,
        h.TUTAR AS SatisKdvDahil,
        h.TUTAR / (1 + (ISNULL(h.KDV, 0) / 100.0)) AS SatisKdvHaric
    FROM dbo.F0101D0014TBLPBIENTEGREBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0014TBLPBIENTEGREHAREKET h WITH (NOLOCK)
        ON h.EVRAKNO = b.IND
    INNER JOIN Urun u
        ON h.STOKNO = u.StokInd
    WHERE b.TARIH >= @Baslangic
      AND b.TARIH <  @Bitis
      AND b.IND <> @HaricIND
      AND LTRIM(RTRIM(b.FTIPI)) IN ('FIS', 'FATURA', 'G.PUSULA')
),

Satis AS (
    SELECT
        COUNT(*) AS SatisSatirSayisi,
        SUM(MIKTAR) AS NetSatisMiktari,
        SUM(SatisKdvDahil) AS NetSatisKdvDahil,
        SUM(SatisKdvHaric) AS NetSatisKdvHaric,
        SUM(CASE WHEN FTIPI = 'G.PUSULA' THEN ABS(MIKTAR) ELSE 0 END) AS SatisIadeMiktari,
        SUM(CASE WHEN FTIPI = 'G.PUSULA' THEN ABS(SatisKdvDahil) ELSE 0 END) AS SatisIadeKdvDahil,
        SUM(CASE WHEN FTIPI = 'G.PUSULA' THEN ABS(SatisKdvHaric) ELSE 0 END) AS SatisIadeKdvHaric,
        MIN(TARIH) AS IlkSatisTarihi,
        MAX(TARIH) AS SonSatisTarihi,
        CASE WHEN SUM(MIKTAR) <> 0 THEN SUM(SatisKdvDahil) / SUM(MIKTAR) ELSE NULL END AS OrtalamaSatisKdvDahil,
        CASE WHEN SUM(MIKTAR) <> 0 THEN SUM(SatisKdvHaric) / SUM(MIKTAR) ELSE NULL END AS OrtalamaSatisKdvHaric
    FROM SatisHam
),

AlisHam AS (
    SELECT
        b.IND AS BaslikInd,
        b.TARIH,
        b.FIRMAADI,
        b.FIRMANO,
        ISNULL(b.IADE, 0) AS IADE,
        h.IND AS HareketInd,
        h.STOKNO,
        h.STOKKODU,
        h.BARKOD,
        h.MIKTAR,
        h.FIYATI,
        h.AFIYATI,
        h.GERCEKTOPLAM AS AlisKdvHaric,
        CASE WHEN ISNULL(h.KDVTUTARI, 0) <> 0 THEN h.KDVTUTARI ELSE h.GERCEKTOPLAM * (ISNULL(h.KDV, 0) / 100.0) END AS AlisKdvTutari,
        CASE WHEN ISNULL(h.KDVTUTARI, 0) <> 0 THEN h.GERCEKTOPLAM + h.KDVTUTARI ELSE h.GERCEKTOPLAM * (1 + ISNULL(h.KDV, 0) / 100.0) END AS AlisKdvDahil,
        ISNULL(h.ISK1, 0) AS ISK1,
        ISNULL(h.ISK2, 0) AS ISK2,
        ISNULL(h.ISK3, 0) AS ISK3,
        ISNULL(h.ISK4, 0) AS ISK4,
        ISNULL(h.ISK5, 0) AS ISK5,
        ISNULL(h.ISK6, 0) AS ISK6
    FROM dbo.F0101D0014TBLALFATBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0014TBLALFATHAREKET h WITH (NOLOCK)
        ON h.EVRAKNO = b.IND
    INNER JOIN Urun u
        ON (h.STOKNO = u.StokInd OR h.BARKOD = u.Barkod OR h.STOKKODU = u.Barkod)
    WHERE b.TARIH >= @Baslangic
      AND b.TARIH <  @Bitis
      AND ISNULL(b.IPTAL, 0) = 0
),

Alis AS (
    SELECT
        COUNT(*) AS AlisSatirSayisi,
        COUNT(DISTINCT BaslikInd) AS AlisFaturaSayisi,
        SUM(CASE WHEN IADE = 1 THEN MIKTAR ELSE 0 END) AS AlisIadeMiktari,
        SUM(CASE WHEN IADE = 1 THEN AlisKdvHaric ELSE 0 END) AS AlisIadeKdvHaric,
        SUM(CASE WHEN IADE = 1 THEN AlisKdvDahil ELSE 0 END) AS AlisIadeKdvDahil,
        SUM(CASE WHEN IADE = 1 THEN -MIKTAR ELSE MIKTAR END) AS NetAlisMiktari,
        SUM(CASE WHEN IADE = 1 THEN -AlisKdvHaric ELSE AlisKdvHaric END) AS NetAlisKdvHaric,
        SUM(CASE WHEN IADE = 1 THEN -AlisKdvDahil ELSE AlisKdvDahil END) AS NetAlisKdvDahil,
        SUM(CASE WHEN IADE = 0 AND MIKTAR > 0 AND (
            ISNULL(AlisKdvHaric, 0) = 0 OR ISK1 = 100 OR ISK2 = 100 OR ISK3 = 100 OR ISK4 = 100 OR ISK5 = 100 OR ISK6 = 100
        ) THEN MIKTAR ELSE 0 END) AS BedelsizMiktar,
        COUNT(CASE WHEN IADE = 0 AND MIKTAR > 0 AND (
            ISNULL(AlisKdvHaric, 0) = 0 OR ISK1 = 100 OR ISK2 = 100 OR ISK3 = 100 OR ISK4 = 100 OR ISK5 = 100 OR ISK6 = 100
        ) THEN 1 ELSE NULL END) AS BedelsizSatirSayisi,
        MIN(TARIH) AS IlkAlisTarihi,
        MAX(TARIH) AS SonAlisTarihi,
        AVG(NULLIF(FIYATI, 0)) AS OrtalamaFIYATI,
        AVG(NULLIF(AFIYATI, 0)) AS OrtalamaAFIYATI
    FROM AlisHam
)

SELECT
    u.StokInd,
    u.Barkod,
    u.UrunAdi,
    u.Tedarikci,
    u.AnaKategori,
    u.AltKategori,
    u.Marka,
    u.KartKalan,
    u.KartAlisFiyati,
    u.KartMaliyet,
    u.KartSonAlisTarihi,
    u.KartSonSatisTarihi,
    s.IlkSatisTarihi,
    s.SonSatisTarihi,
    ISNULL(s.SatisSatirSayisi, 0) AS SatisSatirSayisi,
    ISNULL(s.NetSatisMiktari, 0) AS NetSatisMiktari,
    ISNULL(s.NetSatisKdvDahil, 0) AS NetSatisKdvDahil,
    ISNULL(s.NetSatisKdvHaric, 0) AS NetSatisKdvHaric,
    ISNULL(s.SatisIadeMiktari, 0) AS SatisIadeMiktari,
    ISNULL(s.SatisIadeKdvDahil, 0) AS SatisIadeKdvDahil,
    ISNULL(s.SatisIadeKdvHaric, 0) AS SatisIadeKdvHaric,
    s.OrtalamaSatisKdvDahil,
    s.OrtalamaSatisKdvHaric,
    a.IlkAlisTarihi,
    a.SonAlisTarihi,
    ISNULL(a.AlisFaturaSayisi, 0) AS AlisFaturaSayisi,
    ISNULL(a.AlisSatirSayisi, 0) AS AlisSatirSayisi,
    ISNULL(a.NetAlisMiktari, 0) AS NetAlisMiktari,
    ISNULL(a.NetAlisKdvHaric, 0) AS NetAlisKdvHaric,
    ISNULL(a.NetAlisKdvDahil, 0) AS NetAlisKdvDahil,
    ISNULL(a.AlisIadeMiktari, 0) AS AlisIadeMiktari,
    ISNULL(a.AlisIadeKdvHaric, 0) AS AlisIadeKdvHaric,
    ISNULL(a.AlisIadeKdvDahil, 0) AS AlisIadeKdvDahil,
    ISNULL(a.BedelsizMiktar, 0) AS BedelsizMiktar,
    ISNULL(a.BedelsizSatirSayisi, 0) AS BedelsizSatirSayisi,
    CASE WHEN ISNULL(a.NetAlisMiktari, 0) <> 0 THEN a.NetAlisKdvHaric / a.NetAlisMiktari ELSE NULL END AS EfektifAlisMaliyetiKdvHaric,
    CASE WHEN (ISNULL(a.NetAlisMiktari, 0) - ISNULL(a.BedelsizMiktar, 0)) <> 0 THEN a.NetAlisKdvHaric / (a.NetAlisMiktari - a.BedelsizMiktar) ELSE NULL END AS BedelliAlisOrtalamasiKdvHaric,
    a.OrtalamaFIYATI,
    a.OrtalamaAFIYATI,
    CASE WHEN ISNULL(a.NetAlisMiktari, 0) <> 0 THEN s.NetSatisKdvHaric - (s.NetSatisMiktari * (a.NetAlisKdvHaric / a.NetAlisMiktari)) ELSE NULL END AS TahminiBrutKarKdvHaric_Efektif,
    CASE WHEN (ISNULL(a.NetAlisMiktari, 0) - ISNULL(a.BedelsizMiktar, 0)) <> 0 THEN s.NetSatisKdvHaric - (s.NetSatisMiktari * (a.NetAlisKdvHaric / (a.NetAlisMiktari - a.BedelsizMiktar))) ELSE NULL END AS TahminiBrutKarKdvHaric_Bedelli,
    CASE WHEN ISNULL(s.NetSatisKdvHaric, 0) <> 0 AND ISNULL(a.NetAlisMiktari, 0) <> 0 THEN (s.NetSatisKdvHaric - (s.NetSatisMiktari * (a.NetAlisKdvHaric / a.NetAlisMiktari))) / s.NetSatisKdvHaric * 100 ELSE NULL END AS BrutKarOraniKdvHaric_Efektif,
    CASE WHEN ISNULL(s.NetSatisKdvHaric, 0) <> 0 AND (ISNULL(a.NetAlisMiktari, 0) - ISNULL(a.BedelsizMiktar, 0)) <> 0 THEN (s.NetSatisKdvHaric - (s.NetSatisMiktari * (a.NetAlisKdvHaric / (a.NetAlisMiktari - a.BedelsizMiktar)))) / s.NetSatisKdvHaric * 100 ELSE NULL END AS BrutKarOraniKdvHaric_Bedelli,
    ISNULL(s.NetSatisMiktari, 0) - ISNULL(a.NetAlisMiktari, 0) AS SatisAlisMiktarFarki
FROM Urun u
CROSS JOIN Satis s
CROSS JOIN Alis a;
