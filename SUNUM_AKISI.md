# Sunum Akışı — SkillMatch AI

Perşembe sunumu için baştan sona prova edilmiş akış. Aşağıdaki 13 adımın
tamamı temiz veritabanıyla, gerçek tarayıcıda denendi; her adımın altında
**ne tıklanacak** ve **ne anlatılacak** yazıyor.

Hikâye tek bir işe alımı takip ediyor:

> Rixos Sungate'in barında şef ihtiyacı doğuyor → otel İK talep açıyor → merkez
> onaylıyor ve pozisyon açılıyor → Instagram kampanyası ve QR üretiliyor →
> aday QR'dan başvuruyor → mülakat → bant üstü teklif → iki kademeli onay →
> aday kabul ediyor → işe giriş kontrol listesi → rapora yansıması.

---

## 0. Sunumdan önce (15 dakika)

### 0.1 Sunucuyu başlat

`backend` klasöründen:

```
..\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Çalışma dizini **mutlaka `backend/`** olmalı (repo kökü değil).
Tarayıcıda: `http://localhost:8000`

### 0.2 Demo verisini sıfırla

Provalardan kalan kayıtları temizleyip başlangıç durumunu kurar:

```
..\venv\Scripts\python.exe scripts\seed_demo.py --reset
```

Bu komut şunları **hazır** bırakır: 6 pozisyon, ücret bantları (Bar Şefi
dahil), kadro bütçesi, 65 aday ve başvuru, 38 mevcut çalışan, 50 tamamlanmış
mülakat, işe alınanların onboarding listeleri.

Sahnede **canlı oluşturacakların** bilerek eklenmez: kadro talebi, kampanya/QR,
QR'dan gelen başvuru, mülakat, teklif.

> Prova yaptıysan sunumdan hemen önce bu komutu **tekrar çalıştır**.

### 0.3 QR'ı telefondan okutacaksan (opsiyonel ama etkili)

QR'ın içine `FRONTEND_URL` yazılır, varsayılanı `http://localhost:8000` —
**telefon bu adrese ulaşamaz.** Telefondan okutacaksan:

1. Bilgisayarın yerel IP'sini öğren (`ipconfig` → IPv4, ör. `192.168.1.25`).
2. `backend\.env` içine ekle: `FRONTEND_URL=http://192.168.1.25:8000`
3. Sunucuyu dışa açık başlat: `... -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`
4. Telefon ve bilgisayar **aynı ağda** olmalı (misafir Wi-Fi'ı genellikle
   cihazları birbirinden yalıtır — önce dene).

Riski sevmiyorsan telefonu hiç kullanma: QR'a tıklayıp büyüt, sonra
**"Linki kopyala"** ile linki alıp *gizli/ayrı bir pencerede* aç. Akış birebir aynı.

### 0.4 Girişler

| Rol | E-posta | Şifre | Sunumda kim |
|---|---|---|---|
| SYSTEM_ADMIN | `demo@skillmatch.ai` | `demo123` | **Merkez / Genel Müdürlük** |
| HOTEL_HR | `otelik@ornek.com` | `Otel1234!` | **Rixos Sungate otel İK** |
| RECRUITER | `test.kullanici@ornek.com` | `Test1234!` | (yedek, akışta kullanılmıyor) |

Rol değiştirmek için sağ üstten/sol alttan çıkış yapıp yeniden gir.
**İki ayrı tarayıcı penceresi** (biri normal, biri gizli) açıp ikisinde iki
farklı rolle giriş yapmak sunumu çok akıcı kılıyor — çıkış/giriş beklemezsin.

### 0.5 AI özellikleri hakkında

`GEMINI_API_KEY` boş olduğu sürece **CV analizi, aday-pozisyon eşleştirme,
mülakat sorusu üretimi, AI teklif mektubu ve chatbot çalışmaz.** Aday
havuzunda "En Uygun Pozisyon (AI)" sütunu bu yüzden "Uygun pozisyon yok" der.

- AI'ı göstermek istiyorsan kendi anahtarını `backend\.env` içine koy ve
  sunucuyu yeniden başlat.
- **`backend\.env.example` içindeki anahtarı kullanma** — depoda açıkta duruyor,
  muhtemelen sızmış. İptal ettirmeni öneririm.
- Anahtar koymayacaksan sunumda AI sütunlarında oyalanma; hikâye AI olmadan da
  baştan sona yürüyor.

---

## Akış

### ADIM 1 — Otel İK kadro talebi açıyor
**Giriş:** `otelik@ornek.com`
**Yol:** Sol menü → **Kadro İhtiyacı** → **Manuel Ekle**

Doldur:

| Alan | Değer |
|---|---|
| Otel | Rixos Sungate (SUN) |
| Departman | Yiyecek ve İçecek |
| Pozisyon | Bar Şefi |
| FTE | 1 |
| **En geç ne zaman ihtiyaç var?** | 15.11.2026 |
| Öncelik | Normal |
| Notlar | Kış sezonu bar ekibi için şef ihtiyacı. Mevcut kadro yetersiz. |

**Kaydet** → satır tabloda **"Bekliyor"** olarak görünür.

> **Anlat:** "İhtiyacı sahadaki otel giriyor, merkez değil. Tarih alanı önemli:
> sezon açılışına yetişmesi gereken kadroyu buradan takip ediyoruz."

**Dikkat çek:** Satırın sonunda otel İK'ya **"Merkez onayı bekleniyor"** yazıyor —
onay butonu yok. Otel kendi talebini onaylayamaz.

---

### ADIM 2 — Merkez talebi onaylıyor, pozisyon açılıyor
**Giriş:** `demo@skillmatch.ai` (Merkez)
**Yol:** Sol menü → **Kadro İhtiyacı**

Aynı satır, bu sefer **Onayla / Reddet** butonlarıyla. **Onayla**'ya bas →
durum **"Onaylandı"** olur.

**Yol:** Sol menü → **Pozisyonlar** → listede **Bar Şefi (x1)** belirir.

> **Anlat:** "Onay sadece bir kutucuk değil — onayla birlikte pozisyon açılıyor,
> kadro bütçesinden düşüyor ve işe alım süreci başlıyor. Yetki ayrımı da burada:
> pozisyon açmak bütçe harcamak demek, o yüzden karar merkezde."

---

### ADIM 3 — Kampanya ve QR üretimi
**Yol:** Sol menü → **Kampanyalar & QR** → **+ Yeni Kampanya**

| Alan | Değer |
|---|---|
| Kampanya adı | Kış Sezonu Bar Ekibi |
| Otel | Rixos Sungate (SUN) |
| Pozisyon | Bar Şefi |
| Kaynak | Instagram |
| utm_source | `instagram` |
| utm_medium | `qr` |
| utm_campaign | `kis-bar-ekibi` |

> ⚠️ **Üç UTM kutusunu mutlaka doldur.** Kaynak listesinden Instagram seçmek
> bunları kendiliğinden doldurmuyor; boş bırakırsan kampanya satırında UTM "—"
> görünür ve ADIM 13'teki kaynak raporuna düşmez.

**Oluştur** → satırda QR görseli belirir.

> **Anlat:** "Pozisyon başına link ve QR üretiyoruz. QR afişe, Instagram
> hikâyesine, otel girişindeki panoya gidiyor. Her kanal ayrı etiketle, böylece
> sonunda hangi kanalın gerçekten işe alım getirdiğini sayıyla görebiliyoruz."

QR'a tıkla → tam boyutta açılır (sahnede göstermek için).

---

### ADIM 4 — Aday QR'dan başvuruyor
Telefonla QR'ı okut, ya da **"Linki kopyala"** → gizli pencerede aç.

Açılan sayfa adayın gördüğü ilan sayfası. Doldur:

| Alan | Değer |
|---|---|
| Ad Soyad | Sinem Kaplan |
| E-posta | sinem.kaplan@ornek.com |
| Telefon | 0533 214 55 88 |
| Ön yazı | 8 yıl bar yöneticiliği deneyimim var, kokteyl menüsü kurdum. |
| Özgeçmiş | herhangi bir PDF |

**Başvuruyu Tamamla** → "Başvurunuz başarıyla alındı" bildirimi çıkar
(birkaç saniye görünür).

> **Anlat:** "Aday hesap açmıyor, form doldurmuyor, İK'yla yazışmıyor. QR'ı
> okutuyor, CV'sini yüklüyor, bitti. Arka planda hangi kampanyadan geldiği de
> kaydediliyor — bunu birazdan raporda göreceğiz."

---

### ADIM 5 — Aday sisteme düştü
**Merkez penceresine dön.**
**Yol:** Sol menü → **Adaylar** → arama kutusuna `Sinem`

Aday havuzunda görünür. (AI anahtarı yoksa "En Uygun Pozisyon (AI)" sütunu
"Uygun pozisyon yok" der — anahtar koyduysan burada eşleşme skoru çıkar.)

---

### ADIM 6 — Kanban: sürükle-bırak
**Yol:** **Adaylar** → üst sekmelerden **Aday Pipeline (Kanban)**

Sinem Kaplan **"Başvurdu"** kolonunda. Kartı **"Değerlendirme"** kolonuna
sürükle.

> **Anlat:** "Süreç tek ekranda. Kimin nerede olduğunu, hangi aşamada kaç aday
> beklediğini görüyoruz — aşama değiştirmek kartı sürüklemek kadar basit."

---

### ADIM 7 — Mülakat planla
Sinem'in kartına tıkla → **Mülakatlar** sekmesi → **+ Mülakat Planla**

| Alan | Değer |
|---|---|
| Tur | 1. Tur |
| Tür | Teknik |
| Tarih & Saat | 18.09.2026 10:30 |
| Süre | 45 |
| Görüşmeci | Şule Sıray |
| Yer | Sungate Bar - Toplantı Odası 2 |

**Planla** → mülakat listeye düşer. Modalı kapat (Esc) → aday Kanban'da
otomatik olarak **"Teknik Mülakat"** kolonuna geçmiş olur.

> **Anlat:** "Mülakat planlanınca aday kendiliğinden doğru aşamaya geçiyor;
> kimse ayrıca durum güncellemeyi hatırlamak zorunda değil."

---

### ADIM 8 — Bant üstü teklif → onay süreci tetikleniyor
Sinem'in kartı → **Teklif** sekmesi → **Teklif Oluştur**

Formun üstünde Bar Şefi ücret bandı yazıyor: **Min 38.000 / Hedef 43.000 /
Max 48.000 TRY**.

| Alan | Değer |
|---|---|
| Maaş | **52000** |
| Başlangıç Tarihi | 01.11.2026 |
| Resmi Unvan | Bar Şefi |
| Yan Haklar | Konaklama, yemek, ulaşım |

52.000 yazar yazmaz **kırmızı uyarı** açılır: *"Teklif edilen maaş politika
sınırları dışındadır! Onay süreci tetiklenecektir."*

| Alan | Değer |
|---|---|
| Sapma Nedeni | Piyasa Koşulları |
| Açıklama | Adayın 8 yıllık bar yöneticiliği deneyimi ve rakip teklif nedeniyle band üstü. |

**Oluştur** → teklif **"Taslak + Onay Bekliyor"** rozetiyle açılır ve
**gönder butonu çıkmaz**; yerinde "Onay tamamlanınca gönderilebilir" yazar.

> **Anlat:** "Bant içinde kalsaydı İK tek başına gönderebilirdi. Bandı aşınca
> sistem gönderime izin vermiyor — gerekçe zorunlu, onay zinciri otomatik açılıyor.
> Ücret politikasının kâğıt üstünde değil, sistemde uygulanması bu."

---

### ADIM 9 — Birinci onay: Otel İK
**Giriş:** `otelik@ornek.com`
**Yol:** **Adaylar** → **Teklif Onayları**

Satırda: aday, pozisyon, **52.000 TRY**, sapma nedeni ve gerekçe metni, sıradaki
onaylayan **HOTEL_HR**. **Onayla**'ya bas → liste boşalır, sıra merkeze geçer.

---

### ADIM 10 — İkinci onay: Merkez / Genel Müdürlük
**Giriş:** `demo@skillmatch.ai`
**Yol:** **Adaylar** → **Teklif Onayları**

Aynı teklif, bu sefer onaylayan rol **CENTRAL_HR**. **Onayla**'ya bas.

> **Anlat:** "İki kademe: önce oteli, sonra merkezi geçiyor. Kim, ne zaman,
> hangi gerekçeyle onayladı — hepsi kayıtlı. Yıl sonunda 'bu maaş neden böyle
> verilmiş' sorusunun cevabı sistemde duruyor."

---

### ADIM 11 — Teklif gönderiliyor ve kabul ediliyor
**Yol:** **Adaylar** → **Aday Pipeline (Kanban)** → Sinem'in kartı → **Teklif**

Onay bittiği için rozet yeniden **"Taslak"** ve **Teklifi Gönder** butonu geri
gelmiş. Bas → **"Gönderildi"**.

Şimdi **"Aday Kabul Etti"** butonuna bas → onayla.

Rozet **"Kabul Edildi"** olur. Esc ile kapat → Sinem Kanban'da **"İşe Alındı"**
kolonunda.

---

### ADIM 12 — İşe giriş kontrol listesi
**Yol:** Sol menü → **İşe Giriş** → soldaki listeden **Sinem Kaplan**
→ **Kontrol listesi oluştur**

12 görev oluşur: evrak (kimlik, sözleşme, SGK, banka), IT kurulumu (e-posta,
ekipman, yetkiler), tanışma, oryantasyon ve iş güvenliği eğitimi, 30 günlük
hedef, 1. ay değerlendirme görüşmesi. Her birinde sorumlu (İK / IT / Yönetici /
Aday) ve kaçıncı gün olduğu yazıyor.

İlk birkaç görevi işaretle → üstteki ilerleme çubuğu dolar (**%25**).

> **Anlat:** "İşe alım imzayla bitmiyor. İlk gün neyin hazır olması gerektiği,
> kimin sorumlu olduğu burada takip ediliyor — 'SGK girişi unutulmuş' diye
> aranmıyoruz."

---

### ADIM 13 — Rapor: kampanya işe yaradı mı?
**Yol:** Sol menü → **Raporlar** → metrikleri seç → **Rapor Oluştur**

Göster:

- **İşe Alım Hunisi** — başvurudan işe alıma aşama aşama sayılar.
- **Başvuru Kaynakları** — listede **Instagram** kalemi var: az önce QR'dan
  gelen başvuru. Kampanyadan işe alıma kadar izlenebiliyor.
- **İşe Alım Süresi** — ortalama gün.
- **Teklif Kabul / Red Oranları** — az önce kaydettiğimiz kabul buraya düştü.

Üstte "Dışa Aktar (CSV)" var; otel/departman/tarih kırılımıyla rapor alınabiliyor.

> **Kapanış:** "Baştan sona tek sistem: ihtiyaç doğduğu andan işe girişe kadar.
> Talebi sahadan alıyor, onayı merkezde tutuyor, adaya QR'dan ulaşıyor, ücret
> politikasını kendiliğinden uyguluyor ve sonunda hangi kanalın gerçekten adam
> kazandırdığını sayıyla söylüyor."

---

## Yedek plan / bilinen pürüzler

| Durum | Ne yap |
|---|---|
| QR telefondan açılmıyor | `FRONTEND_URL` yerel IP'ye ayarlı mı, sunucu `--host 0.0.0.0` mı? Olmazsa "Linki kopyala" + gizli pencere. |
| Ekranda hiçbir şey yüklenmiyor | Sunucu `backend/` içinden mi başlatıldı? Repo kökünden başlatılınca import hataları veriyor. |
| Aday havuzunda AI sütunu boş | Normal, `GEMINI_API_KEY` yok. Bu sütunda oyalanma. |
| Prova kayıtları görünüyor | `scripts\seed_demo.py --reset` çalıştır. |
| Kampanyada UTM "—" | Üç UTM kutusu boş bırakılmış. Kampanyayı silip yeniden oluştur. |
| Sol menüde iki benzer madde | **"Kadro İhtiyaçları"** = FTE bütçe/açık analizi. **"Kadro İhtiyacı"** = otellerin talepleri (akışta kullandığımız). Karıştırma. |

## Hikâye kısa kalsın istersen

Zaman daralırsa **ADIM 6 (sürükle-bırak)** ve **ADIM 12 (işe giriş)** atlanabilir.
Sunumun omurgası: **1 → 2 → 3 → 4 → 8 → 9 → 10 → 11 → 13**
(talep → onay → QR → başvuru → bant üstü teklif → çift onay → kabul → rapor).
