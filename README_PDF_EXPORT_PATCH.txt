Ertan AI v3.11 - PDF Rapor Çıktısı

Bu patch günlük / dönem kârlılık raporuna PDF indirme butonu ekler.

Yeni özellik:
- Günlük rapor veya aylık/dönem raporu çalışınca üstte "PDF raporu indir" butonu görünür.
- PDF içinde şu bölümler olur:
  1. Genel özet
  2. Ana kategori kârlılık özeti
  3. Alt kategori kârlılık özeti
  4. Zarar eden ürünler
  5. Maliyeti olmayan ürünler
  6. Şüpheli maliyetler
  7. En çok kâr bırakan ürünler

Kurulum:
1. Zip içeriğini C:\ertan-ai içine çıkar.
2. Dosyaların üzerine yazdır.
3. Gerekirse şu komutu çalıştır:

   pip install reportlab

   veya:

   pip install -r requirements.txt

4. Streamlit'i yeniden başlat:

   cd C:\ertan-ai
   .\.venv\Scripts\activate
   streamlit run app.py

Test:
- 2026 haziran ayı net karlılık
- 08.07.2026 net kârlılık

Not:
PDF raporu, muhasebe anlamında kesin net kâr değildir.
Rapor, stok kartı bazlı tahmini brüt kârlılık ve maliyet sağlık kontrolü çıktısıdır.
