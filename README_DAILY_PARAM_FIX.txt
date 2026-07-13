Ertan AI v3.15.1 - Gunluk Rapor Parametre Duzeltmesi

Hata:
The SQL contains 3 parameter markers, but 2 parameters were supplied

Sebep:
Gunluk rapor Python tarafindan 2 parametre gonderiyor:
1) rapor tarihi
2) haric tutulacak sorunlu belge IND

v3.15 daily_profit.sql icinde yanlislikla 3 adet ? parametresi kalmisti:
- Baslangic
- BitisHaric
- HaricIND

Duzeltme:
Gunluk SQL tekrar 2 parametreye alindi.
Baslangic = rapor tarihi
BitisHaric = rapor tarihi + 1 gun

Degisen dosyalar:
- sql/daily_profit.sql
- sql/period_profit.sql ayni mantikla pakette duruyor; aylik/donem raporu icin 3 parametre kullanmaya devam eder.

Kurulum:
Zip icerigini C:\ertan-ai icine cikar ve dosyalarin uzerine yazdir.
Sonra Streamlit'i CTRL+C ile kapatip yeniden baslat.

Test:
2026-07-11 net karlilik
