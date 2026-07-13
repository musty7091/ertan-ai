DECLARE @RaporTarihi DATE = ?;
DECLARE @Baslangic DATE = @RaporTarihi;
DECLARE @BitisHaric DATE = DATEADD(DAY, 1, @RaporTarihi);
DECLARE @HaricIND INT = ?;

WITH PbiSatis AS (
    SELECT
        CAST(h.STOKNO AS INT) AS StokInd,
        COUNT(*) AS SatisSatirSayisi,
        SUM(h.MIKTAR) AS NetSatisMiktari,
        SUM(h.TUTAR) AS NetSatisKdvDahil,
        SUM(
            CASE
                WHEN ISNULL(h.KDV, 0) = 0 THEN h.TUTAR
                ELSE h.TUTAR / (1 + (ISNULL(h.KDV, 0) / 100.0))
            END
        ) AS NetSatisKdvHaric,
        SUM(CASE WHEN LTRIM(RTRIM(b.FTIPI)) = 'G.PUSULA' THEN ABS(h.MIKTAR) ELSE 0 END) AS IadeMiktari,
        SUM(CASE WHEN LTRIM(RTRIM(b.FTIPI)) = 'G.PUSULA' THEN ABS(h.TUTAR) ELSE 0 END) AS IadeKdvDahil,
        SUM(
            CASE
                WHEN LTRIM(RTRIM(b.FTIPI)) = 'G.PUSULA'
                THEN ABS(
                    CASE
                        WHEN ISNULL(h.KDV, 0) = 0 THEN h.TUTAR
                        ELSE h.TUTAR / (1 + (ISNULL(h.KDV, 0) / 100.0))
                    END
                )
                ELSE 0
            END
        ) AS IadeKdvHaric
    FROM dbo.F0101D0014TBLPBIENTEGREBASLIK b WITH (NOLOCK)
    INNER JOIN dbo.F0101D0014TBLPBIENTEGREHAREKET h WITH (NOLOCK)
        ON h.EVRAKNO = b.IND
    WHERE
        b.TARIH >= @Baslangic
        AND b.TARIH < @BitisHaric
        AND b.IND <> @HaricIND
        AND LTRIM(RTRIM(b.FTIPI)) IN ('FIS', 'FATURA', 'G.PUSULA')
    GROUP BY
        CAST(h.STOKNO AS INT)
    HAVING
        ABS(SUM(h.MIKTAR)) > 0
        OR ABS(SUM(h.TUTAR)) > 0
),

StokHareketMaliyet AS (
    SELECT
        sh.STOKNO AS StokInd,
        SUM(
            ISNULL(sh.CIKAN, 0)
            - CASE WHEN ISNULL(sh.IADE, 0) = 1 THEN ISNULL(sh.GIREN, 0) ELSE 0 END
        ) AS StokHareketNetCikisMiktari,
        SUM(
            (
                ISNULL(sh.CIKAN, 0)
                - CASE WHEN ISNULL(sh.IADE, 0) = 1 THEN ISNULL(sh.GIREN, 0) ELSE 0 END
            )
            * NULLIF(sh.SATISBIRIMMALIYETI, 0)
        ) AS StokHareketMaliyetKdvHaric,
        SUM(
            (
                ISNULL(sh.CIKAN, 0)
                - CASE WHEN ISNULL(sh.IADE, 0) = 1 THEN ISNULL(sh.GIREN, 0) ELSE 0 END
            )
            * NULLIF(sh.SATISBIRIMMALIYETIKDVLI, 0)
        ) AS StokHareketMaliyetKdvli,
        SUM(sh.TUTAR) AS StokHareketSatisTutari,
        CASE
            WHEN SUM(
                ISNULL(sh.CIKAN, 0)
                - CASE WHEN ISNULL(sh.IADE, 0) = 1 THEN ISNULL(sh.GIREN, 0) ELSE 0 END
            ) <> 0
            THEN
                SUM(
                    (
                        ISNULL(sh.CIKAN, 0)
                        - CASE WHEN ISNULL(sh.IADE, 0) = 1 THEN ISNULL(sh.GIREN, 0) ELSE 0 END
                    )
                    * NULLIF(sh.SATISBIRIMMALIYETI, 0)
                )
                /
                SUM(
                    ISNULL(sh.CIKAN, 0)
                    - CASE WHEN ISNULL(sh.IADE, 0) = 1 THEN ISNULL(sh.GIREN, 0) ELSE 0 END
                )
            ELSE NULL
        END AS StokHareketAgirlikliBirimMaliyetKdvHaric,
        AVG(NULLIF(sh.SATISBIRIMMALIYETI, 0)) AS OrtalamaSatisBirimMaliyeti,
        AVG(NULLIF(sh.SATISBIRIMMALIYETIKDVLI, 0)) AS OrtalamaSatisBirimMaliyetiKdvli,
        COUNT(*) AS StokHareketSatirSayisi
    FROM dbo.F0101D0014TBLSTOKHAREKETLERI sh WITH (NOLOCK)
    INNER JOIN PbiSatis p
        ON p.StokInd = sh.STOKNO
    WHERE
        sh.TARIH >= @Baslangic
        AND sh.TARIH < @BitisHaric
        AND LTRIM(RTRIM(sh.IZAHAT)) = '101'
        AND (
            ISNULL(sh.CIKAN, 0) > 0
            OR (ISNULL(sh.IADE, 0) = 1 AND ISNULL(sh.GIREN, 0) > 0)
        )
        AND NULLIF(sh.SATISBIRIMMALIYETI, 0) IS NOT NULL
    GROUP BY
        sh.STOKNO
),

Hesap AS (
    SELECT
        CONVERT(varchar(10), @Baslangic, 120) + ' / ' + CONVERT(varchar(10), DATEADD(DAY, -1, @BitisHaric), 120) AS RaporTarihi,
        u.STOKKODU AS Barkod,
        u.MALINCINSI AS UrunAdi,
        u.KOD1 AS Tedarikci,
        u.KOD2 AS AnaKategori,
        u.KOD4 AS AltKategori,
        u.KOD7 AS Marka,
        p.SatisSatirSayisi,
        p.NetSatisMiktari,
        p.NetSatisKdvDahil,
        p.NetSatisKdvHaric,
        CASE WHEN p.NetSatisMiktari <> 0 THEN p.NetSatisKdvHaric / p.NetSatisMiktari ELSE NULL END AS OrtalamaSatisFiyatiKdvHaric,
        p.IadeMiktari,
        p.IadeKdvDahil,
        p.IadeKdvHaric,
        NULLIF(u.MALIYET, 0) AS KartMaliyet,
        NULLIF(u.ALISFIYATI, 0) AS KartAlisFiyati,
        u.KALAN AS KartKalan,
        sm.StokHareketNetCikisMiktari,
        sm.StokHareketSatisTutari,
        sm.StokHareketMaliyetKdvHaric,
        sm.StokHareketMaliyetKdvli,
        sm.StokHareketAgirlikliBirimMaliyetKdvHaric,
        sm.OrtalamaSatisBirimMaliyeti,
        sm.OrtalamaSatisBirimMaliyetiKdvli,
        sm.StokHareketSatirSayisi,
        sm.StokHareketAgirlikliBirimMaliyetKdvHaric AS KullanilanBirimMaliyetKdvHaric,
        CASE
            WHEN sm.StokHareketMaliyetKdvHaric IS NOT NULL THEN 'Stok hareketi SATISBIRIMMALIYETI'
            ELSE 'Maliyet bulunamadı'
        END AS KullanilanMaliyetKaynak
    FROM PbiSatis p
    INNER JOIN dbo.F0101TBLSTOKLAR u WITH (NOLOCK)
        ON u.IND = p.StokInd
    LEFT JOIN StokHareketMaliyet sm
        ON sm.StokInd = p.StokInd
)

SELECT
    h.*,
    h.StokHareketMaliyetKdvHaric AS TahminiSatilanMalMaliyetiKdvHaric,
    CASE
        WHEN h.StokHareketMaliyetKdvHaric IS NOT NULL
        THEN h.NetSatisKdvHaric - h.StokHareketMaliyetKdvHaric
        ELSE NULL
    END AS TahminiBrutKarKdvHaric,
    CASE
        WHEN h.NetSatisKdvHaric <> 0 AND h.StokHareketMaliyetKdvHaric IS NOT NULL
        THEN (h.NetSatisKdvHaric - h.StokHareketMaliyetKdvHaric) / h.NetSatisKdvHaric * 100
        ELSE NULL
    END AS BrutKarOraniKdvHaric,
    h.StokHareketMaliyetKdvHaric AS TahminiMaliyetSonAlisKdvHaric,
    CASE
        WHEN h.StokHareketMaliyetKdvHaric IS NOT NULL
        THEN h.NetSatisKdvHaric - h.StokHareketMaliyetKdvHaric
        ELSE NULL
    END AS TahminiKarSonAlisKdvHaric,
    CASE
        WHEN h.OrtalamaSatisFiyatiKdvHaric > 0 AND h.KullanilanBirimMaliyetKdvHaric IS NOT NULL
        THEN h.KullanilanBirimMaliyetKdvHaric / h.OrtalamaSatisFiyatiKdvHaric * 100
        ELSE NULL
    END AS KullanilanMaliyetSatisOrani,
    CASE
        WHEN h.OrtalamaSatisFiyatiKdvHaric > 0 AND h.KullanilanBirimMaliyetKdvHaric IS NOT NULL
        THEN h.KullanilanBirimMaliyetKdvHaric / h.OrtalamaSatisFiyatiKdvHaric * 100
        ELSE NULL
    END AS SonAlisSatisOrani,
    CASE
        WHEN h.KartMaliyet IS NOT NULL AND h.KullanilanBirimMaliyetKdvHaric IS NOT NULL AND h.KartMaliyet > 0
        THEN ABS(h.KullanilanBirimMaliyetKdvHaric - h.KartMaliyet) / h.KartMaliyet * 100
        ELSE NULL
    END AS SonAlisKartMaliyetFarkYuzde,
    CASE WHEN h.StokHareketMaliyetKdvHaric IS NULL THEN 1 ELSE 0 END AS MaliyetEksikMi,
    CASE
        WHEN h.StokHareketNetCikisMiktari IS NULL THEN 1
        WHEN ABS(ISNULL(h.StokHareketNetCikisMiktari, 0) - ISNULL(h.NetSatisMiktari, 0)) > 0.01 THEN 1
        ELSE 0
    END AS MiktarUyumsuzMu,
    CASE
        WHEN h.StokHareketMaliyetKdvHaric IS NULL THEN 1
        WHEN ABS(ISNULL(h.StokHareketNetCikisMiktari, 0) - ISNULL(h.NetSatisMiktari, 0)) > 0.01 THEN 1
        WHEN h.NetSatisKdvHaric <> 0 AND h.StokHareketMaliyetKdvHaric > h.NetSatisKdvHaric THEN 1
        WHEN h.NetSatisKdvHaric <> 0 AND h.StokHareketMaliyetKdvHaric > h.NetSatisKdvHaric * 0.95 THEN 1
        ELSE 0
    END AS SupheliMaliyetMi,
    CASE
        WHEN h.StokHareketMaliyetKdvHaric IS NULL
            THEN 'Maliyet yok: stok hareketi SATISBIRIMMALIYETI bulunamadı'
        WHEN ABS(ISNULL(h.StokHareketNetCikisMiktari, 0) - ISNULL(h.NetSatisMiktari, 0)) > 0.01
            THEN 'Kontrol: POS miktarı ile stok çıkış miktarı farklı'
        WHEN h.NetSatisKdvHaric <> 0 AND h.StokHareketMaliyetKdvHaric > h.NetSatisKdvHaric
            THEN 'Kritik: stok hareket maliyeti satıştan yüksek'
        WHEN h.NetSatisKdvHaric <> 0 AND h.StokHareketMaliyetKdvHaric > h.NetSatisKdvHaric * 0.95
            THEN 'Dikkat: marj çok düşük'
        ELSE 'Normal'
    END AS MaliyetSaglikDurumu
FROM Hesap h
ORDER BY
    SupheliMaliyetMi DESC,
    TahminiBrutKarKdvHaric ASC,
    NetSatisKdvDahil DESC;
