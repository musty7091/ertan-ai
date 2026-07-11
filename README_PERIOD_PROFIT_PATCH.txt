Ertan AI v3.10 - İki Tarih Arası / Aylık Net Kârlılık Raporu

Bu patch günlük kârlılık mantığını dönem bazlı çalıştırır.

Yeni desteklenen sorular:
- 2026 haziran ayı net karlılık
- Haziran 2026 net kârlılık
- 2026-06 net karlılık
- 01.06.2026 - 30.06.2026 net karlılık
- 2026-06-01 / 2026-06-30 karlılık
- bu ay net karlılık
- geçen ay net karlılık

Rapor mantığı:
- Seçilen tarih aralığındaki tüm satışlar alınır.
- Ana kategori / alt kategori / ürün kırılımı günlük rapordaki gibi çalışır.
- Maliyet ana kaynağı yine stok kartı MALIYET / ALISFIYATI olur.
- Son alış maliyeti sadece kıyas ve maliyet sağlığı kontrolü için gösterilir.

Önemli:
Bu rapor muhasebe anlamında net kâr değildir.
Genel giderler, POS komisyonu, fire, personel, kira vb. dahil değildir.
Doğru ad: dönem bazlı tahmini brüt kârlılık / maliyet sağlık kontrolü.

Güncellenen / eklenen dosyalar:
- app.py
- core/intent.py
- reports/period_profit.py
- sql/period_profit.sql

Kurulum:
1. Zip içeriğini C:\ertan-ai içine çıkar.
2. Dosyaların üzerine yazdır.
3. Streamlit'i tamamen kapatıp yeniden başlat.

Komut:
cd C:\ertan-ai
.\.venv\Scripts\activate
streamlit run app.py

Test:
2026 haziran ayı net karlılık
