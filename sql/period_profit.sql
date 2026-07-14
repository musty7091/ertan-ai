DECLARE @Baslangic DATE = ?;
DECLARE @RaporTarihi DATE = @Baslangic;
DECLARE @BitisHaric DATE = DATEADD(DAY, 1, CAST(? AS DATE));
DECLARE @HaricIND INT = ?;

/*
    v3.16.2 - Yazarkasa / POS brüt kârlılık

    Esas karar:
    - Satış evreni sadece PBIENTEGRE yazarkasa/POS satırlarıdır.
      FIS + FATURA - G.PUSULA
    - Ofis/toptan faturalar stok hareketinden körlemesine alınmaz.
    - Maliyet, POS satırındaki STOKNO için son bilinen gerçek SATISBIRIMMALIYETI üzerinden bulunur.
    - 13/07/2026 gibi günlerde IZAHAT=101 içinde SATISBIRIMMALIYETI boş geldiği için aynı gün 101 maliyetine bağımlı kalınmaz.
*/

WITH HeaderSummary AS (
    SELECT
        COUNT(*) AS PosBelgeSayisi,
        SUM(CASE WHEN LTRIM(RTRIM(b.FTIPI)) = 'FIS' THEN 1 ELSE 0 END) AS FisBelgeSayisi,
        SUM(CASE WHEN LTRIM(RTRIM(b.FTIPI)) = 'FATURA' THEN 1 ELSE 0 END) AS FaturaBelgeSayisi,
        SUM(CASE WHEN LTRIM(RTRIM(b.FTIPI)) = 'G.PUSULA' THEN 1 ELSE 0 END) AS IadeBelgeSayisi,
        SUM(CASE WHEN LTRIM(RTRIM(b.FTIPI)) IN ('FIS', 'FATURA') THEN 1 ELSE 0 END) AS PosSatisBelgeSayisi,
        SUM(
            CASE
                WHEN LTRIM(RTRIM(b.FTIPI)) = 'G.PUSULA' THEN -ABS(ISNULL(b.TOPLAM, 0))
                WHEN LTRIM(RTRIM(b.FTIPI)) IN ('FIS', 'FATURA') THEN ISNULL(b.TOPLAM, 0)
                ELSE 0
            END
        ) AS PosBaslikNetCiroKdvDahil,
        SUM(CASE WHEN LTRIM(RTRIM(b.FTIPI)) = 'FIS' THEN ISNULL(b.TOPLAM, 0) ELSE 0 END) AS PosBaslikFisCiroKdvDahil,
        SUM(CASE WHEN LTRIM(RTRIM(b.FTIPI)) = 'FATURA' THEN ISNULL(b.TOPLAM, 0) ELSE 0 END) AS PosBaslikFaturaCiroKdvDahil,
        SUM(CASE WHEN LTRIM(RTRIM(b.FTIPI)) = 'G.PUSULA' THEN ABS(ISNULL(b.TOPLAM, 0)) ELSE 0 END) AS PosBaslikIadeKdvDahil
    FROM dbo.F0101D0014TBLPBIENTEGREBASLIK b WITH (NOLOCK)
    WHERE
        b.TARIH >= @Baslangic
        AND b.TARIH < @BitisHaric
        AND b.IND <> @HaricIND
        AND LTRIM(RTRIM(b.FTIPI)) IN ('FIS', 'FATURA', 'G.PUSULA')
),

PbiSatir AS (
    SELECT
        b.IND AS BaslikInd,
        LTRIM(RTRIM(b.FTIPI)) AS FTIPI,
        CAST(h.STOKNO AS INT) AS StokInd,
        h.BARKOD AS BarkodHareket,
        ISNULL(h.MIKTAR, 0) AS MIKTAR,
        ISNULL(h.TUTAR, 0) AS KdvDahilTutar,
        CASE
            WHEN ISNULL(h.KDV, 0) = 0 THEN ISNULL(h.TUTAR, 0)
            ELSE ISNULL(h.TUTAR, 0) / (1 + (ISNULL(h.KDV, 0) / 100.0))
        END AS KdvHaricTutar
    FROM dbo.F0101D0014TBLPBIENTEGREBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0014TBLPBIENTEGREHAREKET h WITH (NOLOCK)
        ON h.EVRAKNO = b.IND
    WHERE
        b.TARIH >= @Baslangic
        AND b.TARIH < @BitisHaric
        AND b.IND <> @HaricIND
        AND LTRIM(RTRIM(b.FTIPI)) IN ('FIS', 'FATURA', 'G.PUSULA')
),

CostedSatir AS (
    SELECT
        p.*,
        u.STOKKODU AS Barkod,
        u.MALINCINSI AS UrunAdi,
        u.KOD1 AS Tedarikci,
        u.KOD2 AS AnaKategori,
        u.KOD4 AS AltKategori,
        u.KOD7 AS Marka,
        NULLIF(u.MALIYET, 0) AS KartMaliyet,
        NULLIF(u.ALISFIYATI, 0) AS KartAlisFiyati,
        u.KALAN AS KartKalan,
        son.SonSatisBirimMaliyeti,
        COALESCE(son.SonSatisBirimMaliyeti, NULLIF(u.MALIYET, 0), NULLIF(u.ALISFIYATI, 0)) AS KullanilanBirimMaliyet,
        CASE
            WHEN son.SonSatisBirimMaliyeti IS NOT NULL THEN 'Son satış maliyeti'
            WHEN NULLIF(u.MALIYET, 0) IS NOT NULL THEN 'Kart maliyet'
            WHEN NULLIF(u.ALISFIYATI, 0) IS NOT NULL THEN 'Kart alış fiyatı'
            ELSE 'Maliyet bulunamadı'
        END AS MaliyetKaynakSatir
    FROM PbiSatir p
    INNER JOIN dbo.F0101TBLSTOKLAR u WITH (NOLOCK)
        ON u.IND = p.StokInd
    OUTER APPLY (
        SELECT TOP 1
            sh2.SATISBIRIMMALIYETI AS SonSatisBirimMaliyeti
        FROM dbo.F0101D0014TBLSTOKHAREKETLERI sh2 WITH (NOLOCK)
        WHERE
            sh2.STOKNO = p.StokInd
            AND sh2.TARIH < @BitisHaric
            AND LTRIM(RTRIM(sh2.IZAHAT)) IN ('101', '21', '23', '33')
            AND ISNULL(sh2.SATISBIRIMMALIYETI, 0) > 0
        ORDER BY
            sh2.TARIH DESC,
            sh2.IND DESC
    ) son
),

PbiSatis AS (
    SELECT
        c.StokInd,
        MAX(CONVERT(varchar(10), @RaporTarihi, 120)) AS RaporTarihi,
        MAX(c.Barkod) AS Barkod,
        MAX(c.UrunAdi) AS UrunAdi,
        MAX(c.Tedarikci) AS Tedarikci,
        MAX(c.AnaKategori) AS AnaKategori,
        MAX(c.AltKategori) AS AltKategori,
        MAX(c.Marka) AS Marka,
        MAX(c.KartMaliyet) AS KartMaliyet,
        MAX(c.KartAlisFiyati) AS KartAlisFiyati,
        MAX(c.KartKalan) AS KartKalan,

        COUNT(*) AS SatisSatirSayisi,
        COUNT(DISTINCT c.BaslikInd) AS SatisBelgeSayisi,
        SUM(c.MIKTAR) AS NetSatisMiktari,
        SUM(c.KdvDahilTutar) AS NetSatisKdvDahil,
        SUM(c.KdvHaricTutar) AS NetSatisKdvHaric,
        CASE WHEN SUM(c.MIKTAR) <> 0 THEN SUM(c.KdvHaricTutar) / SUM(c.MIKTAR) ELSE NULL END AS OrtalamaSatisFiyatiKdvHaric,

        SUM(CASE WHEN c.FTIPI = 'FIS' THEN c.MIKTAR ELSE 0 END) AS FisMiktar,
        SUM(CASE WHEN c.FTIPI = 'FIS' THEN c.KdvDahilTutar ELSE 0 END) AS FisKdvDahil,
        SUM(CASE WHEN c.FTIPI = 'FIS' THEN c.KdvHaricTutar ELSE 0 END) AS FisKdvHaric,

        SUM(CASE WHEN c.FTIPI = 'FATURA' THEN c.MIKTAR ELSE 0 END) AS FaturaMiktar,
        SUM(CASE WHEN c.FTIPI = 'FATURA' THEN c.KdvDahilTutar ELSE 0 END) AS FaturaKdvDahil,
        SUM(CASE WHEN c.FTIPI = 'FATURA' THEN c.KdvHaricTutar ELSE 0 END) AS FaturaKdvHaric,

        SUM(CASE WHEN c.FTIPI = 'G.PUSULA' THEN ABS(c.MIKTAR) ELSE 0 END) AS IadeMiktari,
        SUM(CASE WHEN c.FTIPI = 'G.PUSULA' THEN ABS(c.KdvDahilTutar) ELSE 0 END) AS IadeKdvDahil,
        SUM(CASE WHEN c.FTIPI = 'G.PUSULA' THEN ABS(c.KdvHaricTutar) ELSE 0 END) AS IadeKdvHaric,

        SUM(CASE WHEN c.FTIPI = 'FIS' THEN c.MIKTAR * ISNULL(c.KullanilanBirimMaliyet, 0) ELSE 0 END) AS FisMaliyet,
        SUM(CASE WHEN c.FTIPI = 'FATURA' THEN c.MIKTAR * ISNULL(c.KullanilanBirimMaliyet, 0) ELSE 0 END) AS FaturaMaliyet,
        SUM(CASE WHEN c.FTIPI = 'G.PUSULA' THEN ABS(c.MIKTAR) * ISNULL(c.KullanilanBirimMaliyet, 0) ELSE 0 END) AS IadeMaliyet,

        MAX(c.KullanilanBirimMaliyet) AS KullanilanBirimMaliyetKdvHaric,
        MAX(c.MaliyetKaynakSatir) AS KullanilanMaliyetKaynak,
        SUM(CASE WHEN c.KullanilanBirimMaliyet IS NULL THEN 1 ELSE 0 END) AS MaliyetEksikSatirSayisi
    FROM CostedSatir c
    GROUP BY c.StokInd
    HAVING
        ABS(SUM(c.MIKTAR)) > 0
        OR ABS(SUM(c.KdvDahilTutar)) > 0
),

Stok101 AS (
    SELECT
        sh.STOKNO AS StokInd,
        SUM(ISNULL(sh.CIKAN, 0)) AS Stok101CikisMiktari,
        SUM(ISNULL(sh.TUTAR, 0)) AS Stok101SatisKdvHaric,
        SUM(ISNULL(sh.CIKAN, 0) * ISNULL(sh.SATISBIRIMMALIYETI, 0)) AS Stok101Maliyet
    FROM dbo.F0101D0014TBLSTOKHAREKETLERI sh WITH (NOLOCK)
    INNER JOIN PbiSatis p ON p.StokInd = sh.STOKNO
    WHERE
        sh.TARIH >= @Baslangic
        AND sh.TARIH < @BitisHaric
        AND LTRIM(RTRIM(sh.IZAHAT)) = '101'
        AND ISNULL(sh.CIKAN, 0) > 0
    GROUP BY sh.STOKNO
),

Stok102 AS (
    SELECT
        sh.STOKNO AS StokInd,
        SUM(ISNULL(sh.GIREN, 0)) AS Stok102GirisMiktari,
        SUM(ISNULL(sh.TUTAR, 0)) AS Stok102IadeKdvHaric
    FROM dbo.F0101D0014TBLSTOKHAREKETLERI sh WITH (NOLOCK)
    INNER JOIN PbiSatis p ON p.StokInd = sh.STOKNO
    WHERE
        sh.TARIH >= @Baslangic
        AND sh.TARIH < @BitisHaric
        AND LTRIM(RTRIM(sh.IZAHAT)) = '102'
        AND ISNULL(sh.GIREN, 0) > 0
    GROUP BY sh.STOKNO
),

Hesap AS (
    SELECT
        p.RaporTarihi,
        p.Barkod,
        p.UrunAdi,
        p.Tedarikci,
        p.AnaKategori,
        p.AltKategori,
        p.Marka,

        hs.PosBelgeSayisi,
        hs.FisBelgeSayisi,
        hs.FaturaBelgeSayisi,
        hs.IadeBelgeSayisi,
        hs.PosSatisBelgeSayisi,
        hs.PosBaslikNetCiroKdvDahil,
        hs.PosBaslikFisCiroKdvDahil,
        hs.PosBaslikFaturaCiroKdvDahil,
        hs.PosBaslikIadeKdvDahil,

        p.SatisSatirSayisi,
        p.SatisBelgeSayisi,
        p.NetSatisMiktari,
        p.NetSatisKdvDahil,
        p.NetSatisKdvHaric,
        p.OrtalamaSatisFiyatiKdvHaric,
        p.FisMiktar,
        p.FisKdvDahil,
        p.FisKdvHaric,
        p.FaturaMiktar,
        p.FaturaKdvDahil,
        p.FaturaKdvHaric,
        p.IadeMiktari,
        p.IadeKdvDahil,
        p.IadeKdvHaric,

        p.KartMaliyet,
        p.KartAlisFiyati,
        p.KartKalan,

        s101.Stok101CikisMiktari,
        s101.Stok101SatisKdvHaric,
        s101.Stok101Maliyet,
        CASE WHEN s101.Stok101CikisMiktari <> 0 THEN s101.Stok101Maliyet / s101.Stok101CikisMiktari ELSE NULL END AS Stok101AgirlikliBirimMaliyet,

        p.FaturaMiktar AS Stok21CikisMiktari,
        p.FaturaKdvHaric AS Stok21SatisKdvHaric,
        p.FaturaMaliyet AS Stok21Maliyet,
        CASE WHEN p.FaturaMiktar <> 0 THEN p.FaturaMaliyet / p.FaturaMiktar ELSE NULL END AS Stok21AgirlikliBirimMaliyet,

        s102.Stok102GirisMiktari,
        s102.Stok102IadeKdvHaric,
        p.KullanilanBirimMaliyetKdvHaric AS IadeBirimMaliyet,

        p.FisMaliyet,
        p.FaturaMaliyet,
        p.IadeMaliyet,
        p.MaliyetEksikSatirSayisi,
        p.KullanilanBirimMaliyetKdvHaric,
        p.KullanilanMaliyetKaynak,

        CASE WHEN p.MaliyetEksikSatirSayisi > 0 THEN 1 ELSE 0 END AS MaliyetEksikMi,
        CASE
            WHEN ABS(ISNULL(p.FisMiktar, 0) - ISNULL(s101.Stok101CikisMiktari, 0)) > 0.01 THEN 1
            WHEN ABS(ISNULL(p.IadeMiktari, 0) - ISNULL(s102.Stok102GirisMiktari, 0)) > 0.01 THEN 1
            ELSE 0
        END AS MiktarUyumsuzMu
    FROM PbiSatis p
    CROSS JOIN HeaderSummary hs
    LEFT JOIN Stok101 s101 ON s101.StokInd = p.StokInd
    LEFT JOIN Stok102 s102 ON s102.StokInd = p.StokInd
)

SELECT
    h.*,
    (ISNULL(h.FisMaliyet, 0) + ISNULL(h.FaturaMaliyet, 0) - ISNULL(h.IadeMaliyet, 0)) AS TahminiSatilanMalMaliyetiKdvHaric,
    h.NetSatisKdvHaric - (ISNULL(h.FisMaliyet, 0) + ISNULL(h.FaturaMaliyet, 0) - ISNULL(h.IadeMaliyet, 0)) AS TahminiBrutKarKdvHaric,
    CASE
        WHEN h.NetSatisKdvHaric <> 0
        THEN (h.NetSatisKdvHaric - (ISNULL(h.FisMaliyet, 0) + ISNULL(h.FaturaMaliyet, 0) - ISNULL(h.IadeMaliyet, 0))) / h.NetSatisKdvHaric * 100
        ELSE NULL
    END AS BrutKarOraniKdvHaric,
    (ISNULL(h.FisMiktar, 0) + ISNULL(h.FaturaMiktar, 0) - ISNULL(h.IadeMiktari, 0)) AS StokHareketNetCikisMiktari,
    (ISNULL(h.FisKdvHaric, 0) + ISNULL(h.FaturaKdvHaric, 0) - ISNULL(h.IadeKdvHaric, 0)) AS StokHareketSatisTutari,
    NULL AS SonAlisBirimMaliyetKdvHaric,
    NULL AS TahminiMaliyetSonAlisKdvHaric,
    NULL AS TahminiKarSonAlisKdvHaric,
    CASE
        WHEN h.NetSatisKdvHaric <> 0
        THEN (ISNULL(h.FisMaliyet, 0) + ISNULL(h.FaturaMaliyet, 0) - ISNULL(h.IadeMaliyet, 0)) / h.NetSatisKdvHaric * 100
        ELSE NULL
    END AS KullanilanMaliyetSatisOrani,
    CASE
        WHEN h.NetSatisKdvHaric <> 0
        THEN (ISNULL(h.FisMaliyet, 0) + ISNULL(h.FaturaMaliyet, 0) - ISNULL(h.IadeMaliyet, 0)) / h.NetSatisKdvHaric * 100
        ELSE NULL
    END AS SonAlisSatisOrani,
    CASE
        WHEN h.KartMaliyet IS NOT NULL AND h.KartMaliyet > 0 AND h.KullanilanBirimMaliyetKdvHaric IS NOT NULL
        THEN ABS(h.KullanilanBirimMaliyetKdvHaric - h.KartMaliyet) / h.KartMaliyet * 100
        ELSE NULL
    END AS SonAlisKartMaliyetFarkYuzde,
    CASE
        WHEN h.MaliyetEksikMi = 1 THEN 1
        WHEN h.NetSatisKdvHaric <> 0 AND (ISNULL(h.FisMaliyet, 0) + ISNULL(h.FaturaMaliyet, 0) - ISNULL(h.IadeMaliyet, 0)) > h.NetSatisKdvHaric THEN 1
        WHEN h.NetSatisKdvHaric <> 0 AND (ISNULL(h.FisMaliyet, 0) + ISNULL(h.FaturaMaliyet, 0) - ISNULL(h.IadeMaliyet, 0)) > h.NetSatisKdvHaric * 0.95 THEN 1
        ELSE 0
    END AS SupheliMaliyetMi,
    CASE
        WHEN h.MaliyetEksikMi = 1 THEN 'Maliyet eksik: ürün için son satış maliyeti/kart maliyeti bulunamadı'
        WHEN h.NetSatisKdvHaric <> 0 AND (ISNULL(h.FisMaliyet, 0) + ISNULL(h.FaturaMaliyet, 0) - ISNULL(h.IadeMaliyet, 0)) > h.NetSatisKdvHaric THEN 'Kritik: POS maliyeti satıştan yüksek'
        WHEN h.NetSatisKdvHaric <> 0 AND (ISNULL(h.FisMaliyet, 0) + ISNULL(h.FaturaMaliyet, 0) - ISNULL(h.IadeMaliyet, 0)) > h.NetSatisKdvHaric * 0.95 THEN 'Dikkat: POS marjı çok düşük'
        ELSE 'Normal'
    END AS MaliyetSaglikDurumu
FROM Hesap h
ORDER BY
    SupheliMaliyetMi DESC,
    TahminiBrutKarKdvHaric ASC,
    NetSatisKdvDahil DESC;
