Ertan AI v2.5 - Sohbet Arayuzu + Yorum Motoru + Bulanik Arama

BU SURUM UYGULAMAYI DONUSTURUR: duvar gibi metrik ekrani yerine
sohbet gecmisli, net cevap kartli, akilli yorumlu bir asistan.
Tamamen ucretsiz: yapay zeka API'si yok, Ollama yok, internet sarti yok.

YENILIKLER

1. SOHBET ARAYUZU (app.py yeniden yazildi)
   - Soru-cevap gecmisi ekranda kalir, gercek sohbet hissi verir.
   - Her cevap "net cevap karti": 4-5 kilit sayi + kisa yorum.
   - Tum ayrinti (tablolar, grafikler) "Tum detaylar" altinda katlanir.
   - Birden fazla urun bulununca secim kutusu + "Analiz et" dugmesi.
   - Kenar cubugunda "Sohbeti temizle" dugmesi.
   - Sade tema (.streamlit/config.toml) - begenmezsen dosyayi sil.

2. KURAL TABANLI YORUM MOTORU (core/comments.py - YENI)
   Raporlardaki sayilardan otomatik tek cumlelik tespitler uretir:
   - Kar marji degerlendirmesi (cok dusuk / dusuk / guclu / zararda)
   - Stok kapsamasi: "mevcut satis hiziyla X yillik stok var"
   - Hareketsiz urun uyarisi (30+ gun satis yok)
   - Veri kalitesi: "alis KDV dahil = haric, satir KDV'si girilmemis olabilir"
   - Yillik trend: satis dususu/artisi, marj degisimi, en karli yil
   - Kategori: genel marj, tek urune bagimlilik, zararda satilan urunler
   Esikler core/comments.py basindaki sabitlerden ayarlanabilir.
   AI DEGILDIR: deterministik kurallardir, asla uydurmaz.

3. BULANIK ARAMA (reports/product_search.py + core/turkce.py - YENI)
   Normal arama bos donerse devreye girer:
   - "jack danials" -> JACK DANIELS, "singelton" -> SINGLETON,
     "sivas 12" -> CHIVAS 12, "ukiyo votka" -> UKIYO VODKA
   - Turkce karakter farklarini onemsemez (i/i, s/s, c/c...)
   - Urun listesi 10 dakikalik onbellekte tutulur, arama anliktir.

DEGISEN / YENI DOSYALAR
- app.py                       (YENIDEN YAZILDI)
- core/comments.py             (YENI)
- core/turkce.py               (YENI)
- reports/cards.py             (YENI)
- reports/product_search.py    (bulanik arama eklendi)
- reports/product_360.py       (sabit 2026 basligi rapor yilina baglandi)
- requirements.txt             (rapidfuzz eklendi)
- .streamlit/config.toml       (YENI - tema)

KURULUM
1. Zip icerigini C:\ertan-ai icine cikar, uzerine yazdir.
2. Komut satirinda:  pip install rapidfuzz
3. Streamlit'i yeniden baslat.

TEST LISTESI
[ ] "5000281065762 analiz et" -> kart: 5 sayi + yorumlar
    (dusuk marj + yuksek stok uyarisi gelmeli)
[ ] Karttaki "Tum detaylar"i ac -> eski ayrintili gorunum orada olmali
[ ] Ikinci bir soru sor -> ilk kart ekranda kalmali (sohbet gecmisi)
[ ] "jack danials" yaz -> JACK DANIELS urunleri secim kutusunda gelmeli
[ ] "sivas 12 son yillar" -> CHIVAS 12 yillik raporu
[ ] "Whiskey kategorisinde en karli urunler" -> kategori karti + yorumlar
[ ] Kenar cubugundan "Sohbeti temizle" -> ekran bosalmali

NOT: Eski app.py'yi yedeklemek istersen kurulumdan once
app_eski.py adiyla kopyala.
