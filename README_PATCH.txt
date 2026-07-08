Ertan AI v2.2 - Yıllık Rapor Düzeltmesi

Bu patch iki problemi düzeltir:

1. Yıllık raporda brüt kâr artık "Satış KDV Hariç - aynı yılın toplam alış tutarı" olarak hesaplanmaz.
   Bu yöntem stok artışı olan ürünlerde yanıltıcı negatif kâr gösteriyordu.

2. Yeni mantık:
   Ortalama Alış Maliyeti = Alış KDV Hariç / Alış Miktarı
   Tahmini Satılan Mal Maliyeti = Satış Miktarı x Ortalama Alış Maliyeti
   Tahmini Brüt Kâr = Satış KDV Hariç - Tahmini Satılan Mal Maliyeti

3. Grafiklerde Decimal/pyodbc kaynaklı bozuk eksen görünümü düzeltildi.
   Sayısal kolonlar çizimden önce float'a çevriliyor.

Kurulum:
- Bu zip içeriğini C:\ertan-ai içine çıkar.
- Mevcut dosyaların üzerine yazdır.
- Streamlit'i yeniden başlat.

Dosyalar:
- reports/product_yearly.py
- sql/product_yearly_sales_purchase.sql
