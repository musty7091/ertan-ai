Ertan AI v3.6 - Günlük Rapor Sekmeleri Doğrudan Görünsün

Sorun:
Günlük rapor sekmeleri kart/expander yapısında görünmeyebiliyordu.

Düzeltme:
- Günlük rapor artık kart içine gömülmüyor.
- app.py günlük raporu doğrudan render_daily_profit ile çiziyor.
- Sekmeler doğrudan ekranda görünür.
- Ana kategori özeti sekmesi korunur.

Güncellenen dosyalar:
- app.py
- reports/daily_profit.py
- reports/cards.py
- core/comments.py

Kurulum:
1. Zip içeriğini C:\ertan-ai içine çıkar.
2. Dosyaların üzerine yazdır.
3. Streamlit'i kapatıp yeniden başlat.
4. Uygulama açılınca önce 'Sohbeti temizle'ye bas.
5. Tekrar günlük rapor sor.

Test:
08.07.2026 net kârlılık
