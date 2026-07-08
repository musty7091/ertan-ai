Ertan AI v2.4 - Alis KDV Dahil Duzeltmesi

SORUN
Alis raporlarinda "Alis KDV Dahil" tutari "Alis KDV Haric" ile ayni
gorunuyordu. Sebep: ERP satir bazinda KDVTUTARI alanini doldurmuyor,
KDV belge altinda toplu hesaplaniyor. SQL ise GERCEKTOPLAM + KDVTUTARI
topladigi icin KDVTUTARI bos olunca KDV dahil = KDV haric cikiyordu.

COZUM
Uc SQL dosyasinda da KDV dahil hesabi su mantiga cevrildi:
  KDVTUTARI doluysa   -> GERCEKTOPLAM + KDVTUTARI  (eski davranis)
  KDVTUTARI bos/0 ise -> GERCEKTOPLAM x (1 + KDV orani / 100)
Boylece SINGLETON orneginde:
  165.16 x 0.85 (iskonto) = 140.39 KDV haric  (zaten dogruydu)
  140.39 x 1.20           = 168.46 KDV dahil  (artik dogru)
Iskonto zaten GERCEKTOPLAM icinde oldugu icin ekstra islem gerekmez.

DEGISEN DOSYALAR
- sql/product_360_2026.sql            (AlisKdvTutari + AlisKdvDahil)
- sql/category_profit_2026.sql        (NetAlisKdvDahil)
- sql/product_yearly_sales_purchase.sql (4 donem blogunda AlisKdvDahil)
- sql/dogrulama_alis_kdv.sql          (YENI - dogrulama sorgusu)

KURULUM
1. sql klasorundeki dosyalari uzerine yazdir.
2. Streamlit'i yeniden baslat.

TEST
[ ] "5000281065762 analiz et" -> Alis KDV Dahil, Alis KDV Haric'ten
    ~%20 buyuk olmali (252,694.80 -> ~303,233.76)
[ ] Efektif Alis KDV Haric hala 140.39 olmali (degismemeli)
[ ] Yillik raporda "Alis Hacmi KDV Dahil" kolonu da artik farkli olmali

OLASI HATA
SQL "Invalid column name 'KDV'" derse alis hareket tablosunda oran
kolonunun adi farklidir. sql/dogrulama_alis_kdv.sql dosyasini SSMS'de
calistirip sonucu bana bildir, kolon adini duzeltelim.
