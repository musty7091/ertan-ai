Ertan AI v3.4 - Günlük Rapor Sekmeleri Görünür Hale Getirildi

Sorun:
Günlük rapordaki sekmeler 'Tüm detaylar' açılır panelinin içinde kalıyordu.
Bu yüzden rapor kartında sekmeler görünmüyordu.

Düzeltme:
- Günlük raporda sekmeler artık direkt görünür.
- 'Maliyeti olmayanlar', 'Zarar eden ürünler', 'Şüpheli maliyetler' sekmeleri ilk ekranda görünür.
- Özet kart metrikleri tekrarlanmasın diye günlük detay render'ı kart içinden başlıksız/metriksiz çağrılır.

Güncellenen dosyalar:
- reports/cards.py
- reports/daily_profit.py
- core/comments.py

Kurulum:
1. Zip içeriğini C:\ertan-ai içine çıkar.
2. Dosyaların üzerine yazdır.
3. Streamlit'i yeniden başlat.
