Ertan AI v2.3 - Faz 0: Saglamlastirma Paketi

BU PATCH NE YAPAR?

1. KRITIK HATA DUZELTMESI (sql/product_360_2026.sql)
   BrutKarOraniKdvHaric_Bedelli hesabinda bir kapanis parantezi eksikti.
   Repodaki haliyle Urun 360 raporu SQL Server'da sozdizimi hatasi veriyordu.
   Duzeltildi. (Not: Lokalde calisiyorsa lokal kopyan repodan farkliydi demektir;
   bu patch sonrasi repo ve lokal ayni olacak.)

2. RAPOR YILI ARTIK SABIT DEGIL
   SQL dosyalarindaki '2026-01-01' / '2027-01-01' sabitleri kaldirildi.
   Tarihler artik Python'dan parametre olarak gonderiliyor.
   Yil, .env icindeki REPORT_YEAR degerinden okunur; bos birakilirsa
   otomatik olarak icinde bulunulan yil kullanilir. 2027'de sessizce
   bos rapor gelme riski ortadan kalkti.

3. SIHIRLI SAYI 166576 CONFIG'E TASINDI
   Hatali/mukerrer satis entegrasyon basligi artik .env icindeki
   EXCLUDED_SALE_HEADER_IND degerinden okunur ve SQL'e parametre olarak
   gecilir. SQL dosyalarina neden dislandigini anlatan yorum eklendi.

4. YILLIK RAPORDA YIL DEVRI GUVENLIGI
   D0014 (guncel donem) tablosunun ust tarih siniri genis tutuldu.
   Boylece 2027'ye girildiginde rapor kirilmaz. Yeni donem tablosu
   (or. D0015) acilirsa SQL'e yeni bir UNION ALL blogu eklenmesi
   gerektigi yorum olarak not edildi.

5. URUN ARAMA ONBELLEGI
   find_product_cached: ayni urun aramasi 5 dakika icinde tekrarlanirsa
   veritabanina gidilmez (st.cache_data, ttl=300).

DEGISEN / YENI DOSYALAR
- core/config.py                          (YENI)
- app.py
- reports/product_360.py
- reports/category_profit.py
- reports/product_yearly.py
- reports/product_search.py
- sql/product_360_2026.sql
- sql/category_profit_2026.sql
- sql/product_yearly_sales_purchase.sql
- .env.example

KURULUM
1. Zip icerigini C:\ertan-ai icine cikar, mevcut dosyalarin uzerine yazdir.
2. .env dosyana su iki satiri ekle (dosya sende, zip'te yok):
   REPORT_YEAR=2026
   EXCLUDED_SALE_HEADER_IND=166576
3. .env icindeki SQL_USERNAME / SQL_PASSWORD alanlarini READ-ONLY
   kullanicinla guncelle. Sifreyi sadece .env'de tut, hicbir sohbete
   veya dosyaya yazma. Mumkunse sifreyi SQL Server'da yenile.
4. Streamlit'i yeniden baslat.

TEST LISTESI (sirayla dene)
[ ] "5099873090183 analiz et"  -> Urun 360 raporu acilmali (parantez fixi testi)
[ ] "Chivas 12 son yillar"     -> Yillik rapor, 2019-2026 yillari gorunmeli
[ ] "Whiskey kategorisinde en karli urunler" -> Kategori raporu, baslikta 2026
[ ] Ayni urunu 1 dk icinde iki kez ara -> Ikincisi aninda gelmeli (cache)
[ ] .env'de REPORT_YEAR=2025 yap, yeniden baslat -> Basliklar 2025 olmali,
    360 ve kategori raporlari 2025 verisi gostermeli. Sonra 2026'ya geri al.

NOT: Read-only kullanici ile INSERT/UPDATE calismayacagi icin uygulama
guvenli tarafta. Bu paket tamamlaninca Faz 1'e (Claude API ile dogal dil
anlama katmani) geciyoruz.
