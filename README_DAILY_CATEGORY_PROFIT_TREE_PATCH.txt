Ertan AI v3.9 - Ana Kategori Kârlılık Dağılımı ve Alt Kategori Drilldown

Bu patch yanlış anlaşılmayı düzeltir.

İstenen yapı:
- Günlük raporda önce ana kategorilerin kârlılığı görünür.
- Her ana kategori açılır/kapanır expander olur.
- Örneğin ALKOLLU ICECK açıldığında sadece bu ana kategorinin alt kategori kârlılık dağılımı görünür.
- Alt kategoriler de kendi içinde açılır/kapanır.
- Her alt kategoride ürün listesi, satış, maliyet, brüt kâr ve kâr oranı görünür.

Güncellenen dosya:
- reports/daily_profit.py

Kurulum:
1. Zip içeriğini C:\ertan-ai içine çıkar.
2. reports/daily_profit.py dosyasının üzerine yazdır.
3. Streamlit'i tamamen kapatıp yeniden başlat.
4. Günlük raporu tekrar çalıştır.

Test:
08.07.2026 net kârlılık

Kullanım:
1. İlk sekme: Ana kategori kârlılık dağılımı
2. ALKOLLU ICECK satırını/başlığını aç
3. İçeride alt kategorilerin satış, brüt kâr ve kâr oranını gör
4. Alt kategori başlığını açarak ürünlere in
