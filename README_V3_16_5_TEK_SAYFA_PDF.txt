Ertan AI v3.16.5 - Tek Sayfa POS PDF Özeti

Bu paket PDF çıktısını sadeleştirir ve tek sayfalık lüks yönetim özeti haline getirir.

PDF içeriği:
- Ciro KDV dahil
- Ciro KDV hariç
- Satış maliyeti KDV hariç
- Brüt kâr
- Brüt kâr oranı
- Satışların ana kategori dağılımı
- Kategorilerin kendi içindeki kâr ortalamaları
- Ana kategori özet tablosu

Notlar:
- PDF sadece yazarkasa/POS raporu içindir.
- Ofis/toptan faturalar dahil değildir.
- Brüt kâr = KDV hariç satış - KDV hariç satış maliyeti.
- Bu rapor net kâr değildir; personel, kira, finansman, fire vb. giderler dahil değildir.

Kurulum:
1) Streamlit'i kapat.
2) Zip içeriğini C:\ertan-ai içine çıkar, dosyaların üzerine yazdır.
3) PowerShell:
   cd C:\ertan-ai
   Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
   streamlit run app.py
