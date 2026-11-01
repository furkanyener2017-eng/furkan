AKILLI ÇAY BARDAĞI — ÇALIŞAN YEREL REKONSTRÜKSİYON V3
======================================================

Bu klasör, eski Lipton "Akıllı Çay Bardağı" Flash istemcisini bugün tekrar
çalıştırabilmek için hazırlanmış yerel sunucu rekonstrüksiyonudur.

HIZLI BAŞLATMA
--------------
1) Windows'ta Python 3 kurulu olmalı.
2) BASLAT.bat dosyasını çalıştır.
3) Konsolda şu adresi gör:
      http://127.0.0.1:8000/
4) Adobe Flash Player Projector / uyumlu Flash oynatıcıda şu URL'yi aç:
      http://127.0.0.1:8000/Main.swf
5) Sunucu penceresini oyun açıkken kapatma.

TEST
----
Tarayıcıda:
    http://127.0.0.1:8000/__test

"SERVER V3 OK" görünmesi gerekir.

NE ORİJİNAL?
------------
Aşağıdaki ana medya dosyaları, kullanıcı tarafından sağlanan orijinal paketteki
dosyalarla SHA-256 düzeyinde birebir aynıdır:
- Main.swf
- Library.swf
- intro.flv
- 030.flv, 036.flv, 055.flv, 064.flv, 123.flv
- bekleme_1.flv ... bekleme_4.flv
- ürün, Lipton World ve tracking_data içerikleri

NE DEĞİŞTİRİLDİ?
----------------
- data.xml içindeki eski AI sunucusu:
      http://212.58.7.51/Default.aspx
  yerine:
      http://127.0.0.1:8000/Default.aspx
  kullanılır.
- server.py tamamen rekonstrüksiyon/emülasyon kodudur.
- crossdomain.xml yerel kullanım için eklenmiştir.

V3 NEDEN 6. SORUDAN SONRA DA ÇALIŞIYOR?
----------------------------------------
Elimizde yalnız 5 gerçek soru videosu var. V3, 200.flv ... 299.flv şeklinde
sanal URL'ler üretir ve bunları eldeki beş gerçek FLV'ye eşler. Flash her yeni
URL'yi farklı video olarak gördüğü için eski VideoViewer nesnesine dönüp
Error #1009 vermeden soru döngüsü devam eder.

ÖNEMLİ SINIRLAMA
----------------
Bu, kayıp orijinal Lipton AI veritabanının kendisi değildir.
Gerçek karar ağacı, yüzlerce olası soru/tahmin videosu ve sonuç ekranlarının
bazıları elimizde değildir. Bu sürümün amacı orijinal istemciyi ve mevcut
medyayı çalışır halde korumaktır.

Bu paket içinde 00_BILGI klasöründe ayrıntılı kurtarma notları ve SHA-256
doğrulama listeleri bulunmaktadır.
