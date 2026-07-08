-- Dogrulama sorgusu: alis hareket tablosunda KDV alanlarini kontrol eder.
-- SSMS'de yasemin (read-only) kullanicisiyla calistir.
-- Beklenti: KDV kolonu 20 gibi bir oran, KDVTUTARI ise 0 veya NULL olmali.
-- "Invalid column name 'KDV'" hatasi alirsan kolon adi farklidir; bana bildir.

SELECT TOP 10
    h.STOKKODU,
    h.BARKOD,
    h.MIKTAR,
    h.FIYATI,
    h.GERCEKTOPLAM,
    h.KDV,
    h.KDVTUTARI,
    h.GERCEKTOPLAM * (1 + ISNULL(h.KDV, 0) / 100.0) AS HesaplananKdvDahil
FROM dbo.F0101D0014TBLALFATHAREKET h WITH (NOLOCK)
WHERE h.BARKOD = '5000281065762'
ORDER BY h.IND DESC;
