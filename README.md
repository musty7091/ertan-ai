# Ertan Market Veri Asistanı v2

Modüler Streamlit rapor asistanı.

## Kurulum

```powershell
cd C:\ertan-ai
copy app.py app_backup.py
```

Zip içeriğini `C:\ertan-ai` klasörüne çıkar. Mevcut `.env` dosyanı silme.

```powershell
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Örnek sorular

- `5099873090183 analiz et`
- `Jack Daniels 1LT analiz et`
- `080432400395 son yıllar alış satış`
- `Chivas 12 son yıllar`
- `Whiskey kategorisinde en kârlı ürünler`
- `Rakı kategorisinde en çok satanlar`

## Yetenekler

- 2026 Ürün 360
- 2019–2026 yıllık alış/satış trendi
- 2026 kategori kârlılık raporu
- KDV dahil / KDV hariç ayrımı
- Bedelsiz / %100 iskonto etkisi
- Ürün arama ve seçim
