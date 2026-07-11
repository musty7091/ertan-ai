Ertan AI v3.8 - Günlük Rapor Kategori Filtresi ve Alt Kategori Açılır Menü

Bu patch iki şeyi net şekilde düzeltir:

1. Filtre artık ilk sekmede ve görünür:
   - Sekme adı: Kategori filtresi
   - Ana kategori seç
   - Alt kategori seç
   - Sıralama seç
   - Maliyeti olmayanları gizle
   - Sadece zarar edenler
   - Sadece şüpheli maliyetler
   - Ürün/barkod arama

2. Ana kategori / alt kategori açılır menüsü eklendi:
   - Sekme adı: Ana kategori / alt kategori
   - Ana kategoriyi seç
   - Alt kategoriler açılır/kapanır expander olarak görünür
   - Her alt kategoride satış, brüt kâr, kâr oranı ve ürün listesi görünür

Kurulum:
1. Zip içeriğini C:\ertan-ai içine çıkar.
2. app.py ve reports/daily_profit.py dosyalarının üzerine yazdır.
3. Streamlit'i tamamen kapatıp yeniden başlat.

Komut:
cd C:\ertan-ai
.\.venv\Scripts\activate
streamlit run app.py

Önemli:
Bu sürüm app version değişikliği yaptığı için eski sohbet geçmişini otomatik temizler.
Günlük raporu tekrar çalıştırman yeterli.

Test:
08.07.2026 net kârlılık
