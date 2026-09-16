# SkillMatch AI — Test Bulguları ve Düzeltmeler

Chrome (Playwright + Chromium) ile yerel ortamda sistematik gezilerek çıkarıldı.
Sunucu `http://127.0.0.1:8000`, SQLite, giriş `demo@skillmatch.ai / demo123`.

**Dal:** `claude/pensive-johnson-wtyezh` · **Test durumu:** 38/38 pytest geçiyor
(16 mevcut + 22 yeni regresyon testi) · **33 commit**

| Durum | Anlamı |
|---|---|
| ✅ | Düzeltildi ve doğrulandı |
| 📋 | Senin kararın gerekiyor — dokunmadım |
| ⚠️ | Bilinen sınırlama / ortam kaynaklı |

---

## 0. İki yazarın yaklaşımı — hangisi öncelikli?

`git shortlog -sne` sonucu:

| Yazar | Commit | Kapsam |
|---|---:|---|
| **susry19** (sulesiray19@gmail.com) | **48** | Faz 0–7'nin tamamı: organizasyon/Excel import, StaffingNeed, RBAC & scope politikaları, pipeline, dashboard yeniden tasarımı, analytics, chatbot, onboarding, blacklist, custom reports |
| beyzaacetin (sen) | 2 | Karpathy rehberi + `EXAMPLES.md` + `README.md`; mobil responsive redesign |

Talimatın gereği **susry19'un yaklaşımını esas aldım.** Yaptığım her şey onun
mevcut desenine uyuyor:

- Şablon → `backend/templates/index.html` içinde `<template v-if="page==='x'">`
- State/metod → `backend/static/app.js` `setup()` içinde, `return` bloğunda export
- Ayrı `.vue` dosyası yok, build adımı yok (CDN'den global Vue)
- Renkler `style.css` `:root` token'larından, rozetler `b-applied`/`b-hired`/… sınıflarından
- Migrasyon → Alembic değil, `main.py` içindeki idempotent `ALTER TABLE` listesine satır ekleme
- Yeni Pydantic şeması → `class Config: from_attributes = True` (dosyadaki mevcut stil)

### İki yazar arasında dikkatini çekmek istediğim iki nokta

1. **`README.md` artık projeyi anlatmıyor.** Senin `01720c3` commit'in `README.md`'yi
   ilk kez oluşturmuş ve içeriği *Karpathy CLAUDE.md rehberi* (`Multica`, `x.com/jiayuan_jy`
   linkleri dahil). Depoda SkillMatch AI'ı anlatan bir README hiç olmamış.
   Projeyi ilk gören kişi ne olduğunu anlayamaz. **Karar senin** — dokunmadım.
2. **`KULLANIM_KILAVUZU.md` ile `CLAUDE.md` çelişiyordu** (başlatma komutu ve
   dolayısıyla hangi veritabanı dosyasının açıldığı). Bunun yol açtığı gerçek
   hatayı ✅ D-14'te düzelttim.

---

## 1. Uygulamayı çökerten / kullanılamaz kılan hatalar

### ✅ D-01 — Raporlar sayfası tüm uygulamayı çökertiyordu
Sol menüden *Raporlar*'a tıklayınca ekran tamamen beyaz kalıyor, **sidebar dahil her şey
kayboluyordu**; sayfa yenilenene kadar uygulama kullanılamıyordu.

`app.js` `setup()` state'i `salary_stats: salaryStats` adıyla veriyordu, `index.html` ise
5 yerde `salaryStats` kullanıyordu. Şablonda `undefined` olan bir şeyden `.avg_offered`
okununca Vue render'ı patlıyor ve Vue 3'te render hatası **tüm uygulama ağacını düşürüyor**.

`app.js:3467` → `salaryStats,`

**Ek önlem:** Aynı sınıftan başka hata var mı diye `index.html` içindeki **1428 şablon
ifadesini**, `setup()`'ın export ettiği **415 isimle** karşılaştıran statik bir tarayıcı
yazdım. Başka gerçek uyumsuzluk çıkmadı. Bu kontrol artık testte
(`test_setup_exposes_every_name_the_template_binds`).

### ✅ D-02 — Üç menü öğesi bomboş sayfa açıyordu
*Kampanyalar & QR*, *İşe Giriş*, *Blacklist* menüde vardı ama `index.html` içinde karşılık
gelen `<template>` bloğu **hiç yoktu**. Tıklayınca içerik alanı boşalıyor, konsolda hata
bile çıkmıyordu. Backend'leri hazırdı, sadece arayüz eksikti.

Üçünü de yazdım:
- **Kampanyalar:** liste, oluştur (otel/pozisyon/kaynak + UTM üçlüsü), başvuru linkini kopyala, sil
- **İşe Giriş:** solda işe alınanlar, sağda o kişinin kontrol listesi + ilerleme çubuğu, görev işaretleme
- **Blacklist:** kara listedeki adaylar, sebepleri, listeden çıkarma

### ✅ D-03 — Pozisyonlar sayfası ilk pozisyon açılır açılmaz 500 veriyordu
`schemas.PositionBase.description` zorunlu `str` ilan edilmiş ama veritabanında
`nullable`. Kadro ihtiyacı onaylayınca doğan pozisyonun açıklaması olmadığı için
`GET /api/positions/` **tüm listeyi** 500'lüyordu. Sayfa "0 pozisyon" gösteriyordu.

### ✅ D-04 — Kadro ihtiyacı listesi veri girer girmez 500 veriyordu
`@router.get("/", response_model=list)` — Pydantic v2 çıplak `list` ile ORM nesnesini
serialize edemiyor. Tablo boşken 200 dönüyordu, **ilk kayıt girildiği anda 500**.
`schemas.StaffingNeedOut` eklendi.

---

## 2. Sessizce yanlış çalışan akışlar

### ✅ D-05 — Onay akışının tamamı arayüzden erişilemezdi
Tabloda **Onayla/Reddet** butonları `need.status === 'PENDING'` koşuluna bağlıydı;
model ise küçük harfle `pending` saklıyor. Yani **butonlar hiç görünmüyordu**.
Aynı sebeple durum filtresi de hiçbir zaman eşleşmiyordu.

Artık durum ve öncelik Türkçe okunuyor (*Bekliyor / Onaylandı / Reddedildi*,
*Acil / Yüksek / Normal / Düşük*) ve tasarım sistemindeki rozet sınıflarını kullanıyor.
Filtre büyük/küçük harf duyarsız.

### ✅ D-06 — Kadro ihtiyacı sayfası verisini hiç yüklemiyordu
Hiçbir watcher `page === 'staffing'` olduğunda `loadStaffingNeeds()` çağırmıyordu.
Sayfa, sen "Filtrele"ye basana kadar boş duruyordu.

### ✅ D-07 — Özet kartları hep 0 gösteriyordu
Arayüz `.pending` / `.approved` / `.rejected` okuyordu, API `*_count` döndürüyor.
Üstelik backend'de `rejected_count` **hiç yoktu**, yani "Reddedilen" kartı hiçbir
koşulda dolamazdı. Anahtarlar hizalandı, eksik sayaç eklendi.

### ✅ D-08 — Kaydetme isteği 405, liste isteği 404 veriyordu
Rotalar `/api/staffing-needs` ön ekiyle `"/"` olarak tanımlı, yani koleksiyon
`/api/staffing-needs/` adresinde. `app.js` slash'sız çağırıyordu ve SPA catch-all
rotası isteği yutuyordu. Boş formda ise `payload["hotel_id"]` **KeyError → 500**
veriyordu; artık Türkçe mesajlı 400 dönüyor ve seçim kutularında "Otel seçin…" var.

### ✅ D-09 — Departman filtresi ölü kontroldü
Açılır menü duruyordu ama `app.js` parametreyi hiç göndermiyor, backend de kabul
etmiyordu. İki tarafa da eklendi.

### ✅ D-10 — "İşe alım kararı" kaydetme/okuma 404 veriyordu
`app.js` `/api/applications/{id}/decision` çağırıyor; rotalar
`/api/positions/applications/{id}/decision` altında.

### ✅ D-11 — Kara listeye alma 405 veriyordu, çıkarma hiç mümkün değildi
Arayüz `PATCH` gönderiyordu, rota sadece `POST`. Ayrıca endpoint her çağrıda
`is_blacklisted = True` yapıyordu — arayüz ise toggle olarak yazılmış. Artık
`{"is_blacklisted": false}` ile listeden çıkarma çalışıyor ve serbest metin sebep
kabul ediliyor.

### ✅ D-12 — Pozisyonlar sayfasındaki departman etiketleri hiçbir şeyle eşleşmiyordu
Etiketler sabit kodlanmıştı: **Teknoloji, Ürün, Analitik, Finans, Pazarlama,
İnsan Kaynakları, Satış** — bir otel zincirinde hiçbir pozisyonla eşleşmez, yani
her etiket tabloyu boşaltıyordu. Artık yüklü pozisyonlardan türetiliyor.

### ✅ D-13 — Kampanya QR linkleri prototip bir alan adına gidiyordu
`https://skillmatch-os-prototype.susry.chatgpt.site/portal/apply/...` sabit kodluydu.
Basılıp asılan bir QR'ın yanlış adrese gitmesi demek. Artık `settings.FRONTEND_URL`.

Ayrıca QR dosyaları `os.getcwd()`'ye göre `backend/static/qrcodes` yoluna yazılıyordu;
uygulama `backend/` içinden çalıştığı için dosyalar `backend/backend/static/qrcodes`
altına, yani **`/static` ile servis edilen dizinin dışına** düşüyordu — üretilen QR
döndürdüğü adresten hiçbir zaman okunamıyordu. Hata durumunda da depoda bulunmayan
`placeholder.png` döndürülüyor, arayüzde kırık resim çıkıyordu.

### ✅ D-14 — Nereden başlattığına göre **farklı veritabanı** açılıyordu
`DATABASE_URL` varsayılanı göreli bir SQLite yolu (`sqlite:///./skillmatch.db`).
`KULLANIM_KILAVUZU.md`'deki komut (kökten `uvicorn backend.main:app`) ile
`CLAUDE.md`'deki komut (`backend/` içinden `uvicorn main:app`) **iki ayrı dosya**
açıyordu; birinde girdiğin veri diğerinde yok gibi görünüyordu. Varsayılan dosya
artık `backend/` dizinine sabitlendi. Railway'deki açık `DATABASE_URL` etkilenmiyor.

### ✅ D-15 — Dashboard'da ölü buton
"Teklifi görüntüle →" `page='offers'` yapıyordu; öyle bir sayfa yok. Artık
*Adaylar → Teklif Onayları* sekmesini açıyor.

### ✅ D-16 — "Şablon indir" ve "Kolonlar ⚙" hiçbir şey yapmıyordu
İkisinde de `@click` yoktu.
- **Şablon indir** artık içe aktarmanın doğruladığı kolonların *birebir* aynısını
  taşıyan gerçek bir `.xlsx` indiriyor, veritabanındaki gerçek bir otel koduyla örnek
  satır dolu. Uçtan uca doğrulandı: indir → geri yükle → 1 kayıt işlendi.
- **Kolonlar ⚙** mevcut `headcountLayout` localStorage kaydını genişleten bir kolon
  seçici açıyor; başlık ve hücreler birlikte gizleniyor, seçim yenilemeden sonra kalıyor.

### ✅ D-17 — Menü rozeti yanlış sayıyı gösteriyordu
*Kampanyalar & QR* yanındaki rozet `dashboardStatsData.pending_offers`'a bağlıydı,
yani **bekleyen teklif** sayısını kampanya sayısı gibi gösteriyordu.

### ✅ D-18 — Yenileyince sayfayı kaybediyordun
`reversePathMap` adrese `/headcount`, `/staffing` vb. yazıyordu ama `pathMap`'te
karşılıkları yoktu; F5'e basınca dashboard'a düşüyordun.

### ✅ D-19 — Walk-in QR başvuru akışının tamamı kırıktı
`/portal/walk-in/1` mevcut bir otel için **404** veriyordu. `app.js`
`/api/portal/walk-in/{id}` çağırıyor, rotalar ise
`/api/portal/public/walk-in/hotel/{id}` altında. Gönderim adresinde de aynı
uyumsuzluk vardı, üstelik branding yanıtı `hotel_id` döndürmediği için URL'de
`undefined` oluşuyordu.

Yani **kampanya QR kodlarının işaret ettiği başvuru yolu hiç çalışmıyordu.**
Uçtan uca doğrulandı: form otelin gerçek pozisyon listesini yüklüyor, gönderim
adayı ve `QR Walk-In` kaynaklı başvuruyu oluşturuyor.

Bu ikisi ilk API taramasında kaçmıştı çünkü `api()` yardımcısı yerine ham
`fetch()` kullanıyorlar. Artık 6 ham `fetch` yolunun tamamı da rota tablosuyla
karşılaştırıldı ve eşleşiyor.

### ✅ D-20 — Modallar Escape ile kapanmıyordu
Yaklaşık 20 modal var; hepsi backdrop tıklamasıyla kapanıyor (`@click.self`),
ama Escape'i dinleyen hiçbir şey yoktu. Backdrop'u bulamayan kullanıcı modalda
sıkışıyordu — otomatik test de tam bu yüzden aday modalında takıldı.

### ✅ D-21 — Kadro İhtiyacı sayfasında mobil menü butonu yoktu
Telefonda o sayfaya girince sidebar'a dönüş yolu kalmıyordu. Artık 14 sayfa
şablonunun tamamında hamburger butonu var.

### ✅ D-22 — Mobilde sayfa viewport'a sığmıyordu
Mobil responsive geçişi breakpoint'leri eklemiş, ama içerik hâlâ viewport'tan
geniş kaldığı için **tarayıcı sayfayı küçültüyordu**: 390px telefonda layout
viewport Genel Bakış'ta 562px, Kadro İhtiyaçları'nda 718px çıkıyordu. Sonuç:
480px ve 360px kuralları hiç devreye girmiyor, 12px taban font ~6,5px'e iniyordu.

Üç ayrı sebep vardı: (1) grid track'leri min-content'in altına inemiyordu,
(2) geniş tabloların yatay kaydırma kutusu yoktu, (3) satır içi `style`
(`repeat(5, 1fr)`, `min-width:260px`) media query ile ezilemiyordu.

Ölçüm sonucu: beş sayfanın hepsinde 390px ve 360px'te `scrollWidth == viewport`.

### ✅ D-23 — CV yüklemesi, yüklenen dosyayı okumak yerine aday uyduruyordu
`GEMINI_API_KEY` yokken `analyze_cv()` kendisine verilen CV metnini **tamamen yok
sayıp** sabit bir kişi döndürüyordu: *"Mock Candidate"*, `mock@example.com`,
AWS sertifikalı kıdemli Python geliştiricisi, *"Experienced developer with a
passion for AI."* özetiyle. Bu doğrudan `candidates` tablosuna yazılıyordu —
yani kat hizmetleri adayının CV'sini yükleyince sisteme bir yazılım mühendisi
giriyordu. Aynı sabit özet, başka yollardan oluşturulan kayıtlara da yazılmıştı.

Daha kötüsü: aynı fallback **Gemini çağrısı hata verdiğinde de** çalışıyordu,
yani geçici bir API hatası gerçek başvuranı sessizce örnek kişiyle değiştiriyordu.

Artık dosyada gerçekten yazan şeyi çıkarıyor (ad, e-posta, telefon) ve yalnızca
AI'ın doldurabileceği alanları boş bırakıyor; özet de CV'nin neden AI ile analiz
edilmediğini söylüyor. Gerçek PDF ile doğrulandı.

### ✅ D-24 — Gereksinimi tanımlanmamış pozisyonda herkes "%100 eşleşme" alıyordu
Kanban'da, becerisi hiç çıkarılmamış bir aday **%100 eşleşme** rozetiyle
görünüyordu. Sebep: `get_skill_overlap_ratio`, pozisyonda hiç "aranan beceri"
yazmıyorsa **1.0 (mükemmel örtüşme)** dönüyordu — yani *hiçbir şeyle* karşılaştırıp
tam puan veriyordu. Gemini anahtarı yokken kural tabanlı fallback bunu %30
ağırlıkla alıyor, sonra semantik bileşeni de aynı değerle tabanlıyordu
(`max(50, keyword_score)`), böylece skor iki kez 100'e çıkıyordu.

Gereksinimleri henüz doldurulmamış her pozisyonda (ki başlangıçta çoğu öyle)
tüm adaylar mükemmel uyumlu görünüyordu.

**Bilinmeyen, mükemmel demek değildir:** artık beceri bileşeni nötr (0,5) ve
semantik fallback anahtar kelime skorunu taban almıyor. %100 alan walk-in aday
şimdi **62** alıyor, beceri alt skoru 50 olarak raporlanıyor.

📋 **Bu bir puanlama politikası kararı** (çökme değil) — `net_open` yuvarlama
kararı gibi senin onayını bekliyor.

### ✅ D-25 — Teklif oluşturma her seferinde 500 veriyordu
Aday kartı → **Teklif** sekmesi → "Teklif Oluştur" → "Oluştur" dediğinde
`POST /api/offers/` **500** dönüyordu:

```
TypeError: 'approval_status' is an invalid keyword argument for Offer
```

`main.py` bu kolonu veritabanına ekliyor, `schemas.OfferOut` alanı zaten
tanımlıyor, `routers/offers.py` hem yazıyor hem "gönder" ve onay geçişlerinde
okuyor — ama `models.Offer` içinde **hiç tanımlanmamış**. Yani pipeline'ın
teklif adımı hiçbir zaman tamamlanamıyormuş.

Model kolonu eklendikten sonra tüm zincir çalışıyor (aşağıda).

### ✅ D-26 — Bir mülakat planlanır planlanmaz dashboard çöküyordu
`GET /api/analytics/dashboard-stats` → **500**:

```
AttributeError: 'Interview' object has no attribute 'candidate_id'
```

`models.Interview` yalnızca `application_id` taşıyor; aday ve pozisyon
başvurunun üzerinden geliniyor. Ama `analytics.py` `iv.candidate_id` /
`iv.position_id` okuyor, otel filtresinde de `Interview.position_id` ile
sorguluyordu. Bu kod **hiç çalışmamıştı**, çünkü veritabanında hiç mülakat yoktu
ve uydurma fallback widget'ı dolduruyordu — gerçek veri girer girmez patladı.

Ek olarak widget'ın başlığı "**Bugünkü** programım" ama sorgusunda **hiç tarih
filtresi yoktu**: üç hafta sonraki mülakat "bugün" diye listeleniyor, hemen
yanındaki sayaç ise 0 diyordu. Artık sayacın kullandığı aralığı kullanıyor.

### ✅ D-27 — Organizasyon/Bütçe Excel importer'ı hiç çalışmamış
Faz 1'in amiral gemisi olan tek-Excel importer'ı, kolon adlarını küçük harfe
çevirip alias tablosuyla eşleştiriyor, ama sonra **orijinal yazımına geri
çeviriyordu**. Satır okumaları küçük harfli DataFrame'de yapıldığı için her
`row.get()` ıskalıyordu:

- Tüm alanlar `"None"` **stringi** olarak geliyordu
- Tüm FTE'ler `0.0` oluyordu
- Satırlar birbirinin aynısı göründüğü için ilki hariç hepsi
  *"Aynı dönem, otel ve pozisyon için mükerrer kayıt"* diye işaretleniyordu

Importer'ın kendi belgelediği başlıklar (`Donem`, `OtelKodu`, `OtelAdi`…)
büyük-küçük karışık olduğu için **belgelendiği hâliyle hiç çalışmamış**;
yalnızca tamamı küçük harfli bir dosya geçebilirmiş.

Düzeltmeden sonra 3 satırlık dosya doğru okunuyor: SUN/Garson/12,5 ·
PRM/Resepsiyonist/8,25 · bilinmeyen `XXX` otel kodu da doğru şekilde
"eşleşmeyen otel" olarak raporlanıyor.

Ayrıca boş hücreler artık `"nan"` / `"None"` stringi olarak değil, boş olarak
okunuyor.

### ✅ D-28 — Kanban sürükle-bırak ✓, mülakat planlama ✓ (doğrulandı)
Kartı "İK Mülakatı"ndan "Teknik Mülakat"a sürükledim, durum `tech_interview`
oldu. Mülakat planlama modalı başvuru detayından çalışıyor; planlanan mülakat
Pipeline listesinde ve dashboard'da doğru göründü.

⚠️ Not: **"+ Mülakat Planla" butonu Pipeline sayfasında yok**, sadece aday
başvurusunun içinde. Pipeline sayfası boş listeyle açılıyor ve oradan mülakat
eklemenin yolu yok. Ayrı bir buton ister misin?

### ✅ D-29 — "Özel Rapor Oluşturucu" tamamen maketti
Raporlar sayfasındaki rapor oluşturucu, **çalışan bir backend'in üstüne konmuş
bir maketti**:

- Hiçbir açılır menü veya onay kutusu `v-model` taşımıyordu
- Her iki buton da `onclick="alert('Rapor oluşturuluyor...')"` — sadece uyarı gösteriyordu
- Altındaki sonuç tablosu **iki sabit satırdı**: *Rixos Premium Tekirova 145/98/32/12*,
  *Rixos Downtown Antalya 88/65/24/8* — çıktı gibi sunuluyordu

Oysa `routers/custom_reports.py` Faz 6'dan beri `/custom` ve `/custom/export`
uçlarını sunuyor. Artık filtreler bağlı, "Rapor Oluştur" gerçek metrikleri
getiriyor, "Dışa Aktar" gerçek CSV indiriyor.

### ✅ D-30 — Şablona gömülü, hiçbir veriye bağlı olmayan istatistikler
`index.html` içinde veriye bağlı olmayan ama gerçek gibi duran rakamlar:

| Yer | Gömülü değer | Şimdi |
|---|---|---|
| Raporlar · Ortalama İşe Alım Süresi | `18.5 Gün` | Gerçek endpoint'ten; veri yoksa `—` |
| Raporlar · "Mevcut verilere göre… 18.5 gündür" + "sektör ortalaması 24 güne kıyasla %23 daha hızlı" | tamamen uydurma performans iddiası | Veri yoksa açıkça "hesaplanamıyor" diyor |
| Raporlar · Teklif Kabul / Red | `%84.2` / `%15.8` | `/api/analytics/offer-acceptance`'tan |
| Pozisyonlar · her satırdaki ilerleme çubuğu | her satırda `65%` | İşe alınan / onaylı kadro |
| Pozisyon çalışma alanı · Gün Açık | `18 Gün` | `created_at`'ten hesaplanıyor |
| Pozisyonlar · Ortalama İlerleme, Pipeline Uyum Ort. | `82%` | 📋 `—` — **tanımını söyle, bağlayayım** |

### ✅ D-31 — Admin olmayan kullanıcılar için uygulama büyük ölçüde kullanılamazdı
Bu turun en etkili bulgusu. `loadSettings()` on bir ucu `Promise.all` ile
çekiyordu. Admin olmayan bir kullanıcı `/api/settings/audit-logs` için **403**
alıyor — `Promise.all` tek bir reddedişte **tüm partiyi** düşürdüğü için
`catch` bloğu her şeyi yutuyor ve `settingsData` **boş kalıyordu**.

Sonuç: admin olmayan her kullanıcı için
- Otel ve departman açılır menüleri **her yerde boştu**
- `getHotelName()` "Bilinmeyen Otel" diyordu
- Kadro ihtiyacı, kampanya oluşturmak veya otele göre filtrelemek mümkün değildi

Bir İK sisteminde kullanıcıların çoğu admin değildir.

**Doğrulama:** RECRUITER rolüyle giriş yapıldı. Otel filtresinde önce yalnızca
1 seçenek ("Tüm Oteller") vardı; düzeltmeden sonra 16 otelin tamamı +
departmanlar (33 seçenek) geliyor.

`Promise.allSettled`'a çevrildi; okunamayan uçlar boş dönüyor.

ℹ️ **RBAC'in kendisi doğru çalışıyor:** recruiter'ın menüsünde *Ayarlar* gizli,
erişebildiği tüm sayfalar hatasız açılıyor. (Konsolda hâlâ zararsız bir 403
görünüyor — sunucu doğru davranıyor, sadece gereksiz bir istek.)

### ✅ D-32 — Maaş politikası listesi NULL alanda 500 veriyordu
`SalaryPolicyOut` `version`, `is_active` ve `status` alanlarını **zorunlu**
istiyor; bu kolonlar veritabanında nullable ve varsayılanları yalnızca
Python tarafında (ORM insert'inde) uygulanıyor. ORM dışından gelen herhangi bir
satır NULL kalıyor ve **tüm listeyi** 500'lüyor — D-03'teki
`PositionBase.description` ile birebir aynı hata.

Bu projede özellikle önemli: kolonlar Alembic ile değil, `main.py` içindeki
idempotent `ALTER TABLE` listesiyle ekleniyor ve o yolla eklenen bir kolon
**mevcut tüm satırlarda NULL** olur.

### ✅ D-33 — Kara liste, telefonu yeniden yazarak atlatılabiliyordu 🔒
Kara listedeki bir aday, **kendi numarasını farklı biçimde yazarak** sisteme
geri girebiliyordu. Çalışan sunucuda birebir üretildi:

| Başvuru | Sonuç |
|---|---|
| `+90 555 987 65 43` (kayıtlı biçim) | **403 — "Aday kara listededir"** ✅ |
| `0555 987 65 43` + farklı e-posta | **200 — kabul edildi** ❌ |

Aynı açık, sıradan mükerrer tespitini de bozuyordu: tek kişi iki ayrı aday
kaydına bölünüyordu.

**Parçaların hepsi zaten vardı, sadece birbirine bağlanmamıştı:**
`normalize_phone()` `routers/candidates.py` içinde duruyor, `phone_normalized`
kolonu `main.py`'de migrasyonla ekleniyor, mükerrer-kontrol ucu onu sorguluyor —
ama **hiçbir yer onu yazmıyordu**, yani her satırda NULL'dı ve yalnızca birebir
aynı biçimdeki metin eşleşiyordu.

Düzeltme: her iki portal başvuru yolu ve CV yükleme artık normalize edilmiş
numarayı saklıyor ve kara liste/mükerrer kontrollerinde onu da kullanıyor;
mevcut kayıtlar startup'taki normalizasyon adımında geriye dönük dolduruluyor
(deponun migrasyon desenine uygun).

Düzeltmeden sonra: `0555 987 65 43` de `+905559876543` de, farklı e-postayla
bile, **403** alıyor.

---

## 2b. Sunum provası sırasında çıkanlar (D-34 … D-42)

Perşembe sunumu için akışı baştan sona **temiz veritabanıyla** prova ettim
(kadro talebi → GM onayı → pozisyon → kampanya/QR → QR'dan başvuru → Kanban →
mülakat → teklif → çift onay → kabul → işe giriş → rapor). Prova sırasında
çıkan ve düzelttiğim maddeler:

### ✅ D-34 — İşe giriş kontrol listesi sayfa yenilenince bozuluyordu
`GET /api/onboarding/{id}` `{completion_percentage, tasks}` döndürüyor ama hem
`loadOnboarding()` hem `selectOnboardingApp()` yanıtın **tamamını** görev
dizisine atıyordu. Listeyi oluşturduktan hemen sonra doğru görünüyordu (POST
yanıtı doğru okunuyor), sayfayı yenileyince listenin yerine iki çöp satır ve
üstünde "henüz görev yok" kutusu geliyordu; aday kartının Onboarding sekmesi de
`onboardingTasks.filter is not a function` ile patlıyordu. Artık `.tasks` okunuyor.

### ✅ D-35 — QR kodu dış servisten indiriliyordu
Hem kampanya hem ilan QR'ı `api.qrserver.com`'dan HTTP ile indiriliyordu — yani
QR, aday karşısında/sahnede oluşturulurken **üçüncü parti bir servise bağımlıydı**.
Bağlantı takılınca kayıt boş `qr_code_path` ile yazılıyor ve tabloda "—" görünüyordu;
seed'deki kampanya tam olarak bu durumdaydı. Artık `qrcode` paketiyle yerelde
çiziliyor (`requirements.txt`'e eklendi), ağ gerekmiyor. Tablodaki 40px küçük
görsel de artık tıklanınca tam boyutta açılıyor.

**Dikkat:** QR'ın içine `settings.FRONTEND_URL` yazılıyor, varsayılanı
`http://localhost:8000`. **Telefonla okutulacaksa** bu adres telefonun
erişebildiği bir adres olmalı (aşağıdaki sunum akışında anlatılıyor).

### ✅ D-36 — Pozisyon modalinde kırık görsel
İlan modali `/static/qrcodes/placeholder.png` gösteriyordu; depoda böyle bir
dosya yok, yani ilan kaydedilene kadar kırık resim ikonu duruyordu. Boş durum kutusu kondu.

### ✅ D-37 — Raporda "interview" yazıyordu
`/api/analytics/stats` üç mülakat aşamasını tek `interview` anahtarında
topluyor, `stageLabelMap`'te bu anahtar yoktu; huni grafiğinde Türkçe
aşamaların arasında İngilizce `interview` yazıyordu. "Mülakat" etiketi eklendi.

### ✅ D-38 — Butonlar ve açılır listeler farklı yazı tipindeydi
`font-family` `button`/`input`/`select`/`textarea`'ya miras geçmiyor, stil
dosyası da sadece `body`'ye veriyordu. Yani **uygulamadaki bütün butonlar ve
menüler** tarayıcının varsayılan yazı tipiyle, yanlarındaki metin Inter ile
çiziliyordu. Tek satırlık `font-family:inherit` sıfırlaması eklendi; on bir
sayfada taşma/kırpılma kontrolü yapıldı, hiçbiri bozulmadı.

Aynı yerde: sol menüdeki **"Kadro İhtiyacı"** maddesi tek `<a>` olarak yazılmış,
ikonu da satır-içi `margin-right` taşıdığı için komşularından ~25px sağda ve
farklı yazı tipiyle duruyordu. Diğerleri gibi `<button class="nav-item">` oldu.

### ✅ D-39 — Oteller kendi kadro taleplerini onaylayabiliyordu (yetki)
Kadro talebini onaylamak **pozisyon açıyor ve bütçe harcıyor**, yani merkezin
kararı. Ne uç nokta ne tablo rol kontrolü yapıyordu: talebi giren otel İK'sı
kendi satırında Onayla/Reddet görüyor ve basabiliyordu. Artık uç nokta
ADMIN/SYSTEM_ADMIN/CENTRAL_HR dışındakini **403** ile çeviriyor, tabloda
diğerlerine "Merkez onayı bekleniyor" yazıyor.

### ✅ D-40 — Onayla açılan pozisyon listede görünmüyordu
Pozisyonlar, adaylar ve genel bakış verisi yalnızca açılışta bir kez
çekiliyordu. GM kadro talebini onaylayınca pozisyon oluşuyor ama Pozisyonlar
sayfasında **tarayıcı yenilenene kadar** yoktu. (Kadro/talep/kampanya/işe giriş
sayfalarında aynı boşluğu daha önce kapatmıştım; kalan üçü de eklendi.)

### ✅ D-41 — Pozisyon tablosunda herkes "0 Aday"dı
Tablo `p.applications` okuyordu, `/api/positions/` böyle bir alan hiç
döndürmemiş. Yani üstte "65 Aktif Aday" yazarken tablodaki her satır "0 Aday"
ve boş ilerleme çubuğu gösteriyordu. Uç nokta artık `application_count` ve
`hired_count` sayılarını dönüyor (başvuru satırlarını değil — tablonun ihtiyacı
iki sayı).

### ✅ D-42 — "Ahmet" adlı adaya uydurma %91 uyum veriliyordu
`/with-best-position` içinde ilk seed isimlerine sabitlenmiş skorlar vardı:
adı "ahmet" geçen bir aday Garson ilanına başvurunca **91**, "elif"
Resepsiyonist'e **87**, "mehmet" lifeguard'a **83**. Üstelik bu değer
`match_scores` tablosuna **yazılıyordu**, yani uydurma skor istekten sonra da
kalıyordu. Diğer gösteri verileri gibi `settings.DEMO_DATA` arkasına alındı.

### ✅ D-43 — Onay bekleyen teklif "Taslak" görünüp gönder butonu sunuyordu
Bant dışı teklif `PENDING_APPROVAL` ile oluşuyor ve gönderme ucu onu reddediyor;
ama ekran sade "Taslak" rozeti ve **kesinlikle hata verecek** bir "Teklifi
Gönder" butonu gösteriyordu. Artık "Onay Bekliyor" / "Onay Reddedildi" rozeti
var, onay bitene kadar gönder butonu çıkmıyor.

### ✅ D-44 — Adayın teklife verdiği cevap hiçbir yerden kaydedilemiyordu
Teklif "Gönderildi"den ileri gidemiyordu: `accepted`/`rejected` durumları hem
rozette hem `/api/analytics/offer-acceptance` raporunda var, uç nokta da kabul
ediyor — ama **hiçbir ekran çağırmıyordu**. Yani "Teklif Kabul / Red Oranları"
raporu gerçek kullanımda hep boş kalıyordu. Gönderilmiş teklife "Aday Kabul
Etti" / "Aday Reddetti" butonları eklendi (kabul, başvuruyu `hired` yapıyor —
bunu uç nokta zaten yapıyordu).

### ✅ D-45 — Boş ilan açıklaması başlığı
Kadro talebinin onayıyla açılan pozisyonun açıklaması yok; adayın gördüğü ilan
sayfasında "POZİSYON TANIMI & KAPSAMI" başlığı boş paragrafın üstünde
duruyordu. Yanındaki "Aranan Yetenekler" bloğu gibi koşula bağlandı.

**Sunum öncesi bilmen gerekenler (düzeltme değil, karar):**

- **`GEMINI_API_KEY` boş.** CV analizi, aday-pozisyon eşleştirme, mülakat sorusu
  üretimi, teklif mektubu ve chatbot bu anahtar olmadan çalışmıyor. Aday
  havuzunda "En Uygun Pozisyon (AI)" sütunu bu yüzden "Uygun pozisyon yok"
  diyor — yanlış değil, sadece AI analizi yok. Sunumda AI tarafını göstermek
  istiyorsan **kendi anahtarını** `backend/.env` içine koy.
  (`backend/.env.example` içindeki anahtarı kullanma — commit'lenmiş, muhtemelen
  sızmış; iptal ettirmeni öneririm.)
- **Kampanya UTM alanları elle doldurulmalı.** Kaynak listesinden "Instagram"
  seçmek `utm_source`'u kendiliğinden doldurmuyor; üç kutuyu boş bırakırsan
  kampanya satırında UTM "—" görünür ve rapordaki kaynak kırılımına düşmez.
- **Teklif sapma açıklaması aslında zorunlu değil.** Etiket "Açıklama *" diyor
  ama Oluştur butonu yalnızca *sapma nedeni* seçilmemişse kapalı. Davranışı
  değiştirmedim; istersen açıklamayı da zorunlu yaparım.

---

## 2c. 🔴 En ciddi bulgu — API'nin büyük kısmı kimlik doğrulaması istemiyordu (D-46)

Sunum provasından sonra kalan test edilmemiş alanlara bakarken çıktı ve
şu ana kadarki en ciddi bulgu bu.

**212 uçtan 94'ü hiçbir kimlik doğrulaması istemiyordu.** Bunlar "unutulmuş bir
iki uç" değil; `offers`, `applications`, `interviews`, `onboarding` router'larının
**tamamı**, `positions` ve `analytics`'in büyük bölümü hiç `Depends(auth...)`
yazmamıştı. Çalışan sunucuya karşı, token'sız ve hesapsız denedim:

```
POST   /api/offers/                       → 999.000 TRY'lik teklif oluşturdu
GET    /api/analytics/salary-report       → maaş raporunu döndü
GET    /api/candidates/with-best-position → bütün adayları döndü
DELETE /api/candidates/{id}/hard-delete   → adayı kalıcı sildi
PATCH  /api/applications/{id}/status      → adayı istediği aşamaya taşıdı
```

**En kötüsü `POST /api/chat`.** Chatbot bağlamını *bütün adayların adı,
seviyesi, yetenekleri ve özetiyle* kuruyor; otel/departman filtreleri
`current_user`'a bağlı. Anonim çağıranın kullanıcısı olmadığı için filtreler
hiç uygulanmıyordu — yani **kimliksiz biri "bütün adayları listele" diyebiliyordu.**
Şu an sadece `GEMINI_API_KEY` boş olduğu için sessiz; **anahtar koyar koymaz
açılacaktı.** (Sunum için anahtar koymayı düşünüyorsan bu düzeltme olmadan koyma.)

**Düzeltme:** Giriş zorunluluğu tek tek uçlara değil **router seviyesine**
konuldu (`include_router(..., dependencies=staff_only)`). Böylece o router'a
yarın eklenecek uçta unutulması mümkün değil. Açık kalanlar bilerek açık:

| Açık kalan | Neden |
|---|---|
| `/api/auth/login` | Giriş ucu |
| `/api/portal/public/*`, `/api/portal/job/*` | Adayın gördüğü ilan ve başvuru formu |
| `/api/portal/me`, `/applications`, `/notifications`, `/offer/*/accept\|reject` | Aday kendi linkindeki token ile doğrulanıyor (token'sız **422**, sahte token **401** — doğrulandı) |
| `/`, `/health`, `/health/db`, `/{catchall}` | Uygulama kabuğu ve sağlık kontrolü |

Korumasız uç sayısı **103 → 18**'e indi, kalan 18'in hepsi yukarıdaki listede.

**Düzeltmeden sonra doğrulandı:** on bir sayfanın tamamı hatasız yükleniyor,
QR'dan gelen aday başvurusu token'sız hâlâ çalışıyor, giriş yapmış kullanıcıyla
17 ana uç 200 dönüyor, 51/51 test geçiyor.

> Not: `test_hotfixes.py` bu uçları kimliksiz çağırdığı için **açık sayesinde**
> geçiyordu; artık admin olarak çalışıyor.

### Bununla birlikte çıkan, düzeltmediğim ölü kod (silmedim, haberin olsun)

- **`routers/candidates_v3.py` ve `routers/positions_v3.py`** (222 satır)
  `main.py`'de hiç import edilmiyor, hiç `include_router` edilmiyor. Tamamen ölü.
- **`services/routing_service.py`** hiçbir yerden çağrılmıyor. İçindeki yorumlar
  da zaten "Just a mock logic" / "dummy suggestions for demonstration" diyor:
  yetenek bakmadan ilk 2 pozisyonu alıp `source_hotel_id=1` sabitiyle yönlendirme
  önerisi yazıyor. Gerçek yönlendirme `services/budget_service.py` içinde
  (`trigger_scoped_routing`) ve portal başvuru yollarına bağlı — o düzgün:
  önce aynı bölge, sonra aynı şehir, sonra merkez İK, mükerrer kontrolüyle.
- **`routers/auth.py` → `register()`** ilk satırda 403 fırlatıyor (kayıt kapalı),
  ama `raise`'in **altındaki erişilemez kod** kullanıcıyı `role=ADMIN` ile
  oluşturuyor. Bugün çalışmıyor; ama biri kaydı açmak için o `raise`'i silerse
  **herkese açık admin kaydı** olur. Silmedim, dikkatini çekiyorum.

---

## 2d. Yetki/kapsam turu (D-47, D-48) + temiz çıkanlar

Kimlik doğrulaması (D-46) kapandıktan sonra bir sonraki katmana baktım:
*giriş yapmış* ama başka otele yetkili olmayan biri ne görebiliyor?

### ✅ D-47 — Başka otelin ilanı ve teklifi kimlikle okunabiliyordu (IDOR)
Pozisyon **listesi** `hotel_access_ids`'e göre süzülüyor, ama **kimlikle tek
kayıt okuma** hiç süzülmüyordu. Sadece otel 1'e yetkili İK kullanıcısıyla
denedim — Rixos Almaty'ye ait bir ilan ve o ilana yapılmış **175.000 TRY'lik
teklif** açıldı. Kimlikler sıralı tamsayı, yani tahmin bile gerekmiyor.

```
GET /api/positions/9            → "GIZLI Almaty Müdürü" (başka otel)
GET /api/offers/application/66  → 175.000 TRY teklif
```

Düzeltme, kuralı yeniden yazmak yerine **listenin kullandığı filtrenin aynısını**
tekil okumaya uyguluyor (`position_in_scope`, `application_in_scope`). Yanıt
**404** — 403 deseydi kaydın var olduğunu doğrulamış olurduk. Kapsam kararı
veren iki uç `get_current_user_optional` okuyordu; `None` olabilen kullanıcıyla
yetki kontrolü yapılamayacağı için `get_current_user`'a çevrildi.

**Bilerek DEĞİŞTİRMEDİĞİM yer — adaylar.** Aday detay ucu oteller arası
okunabilir olacak şekilde *tasarlanmış*: `test_candidate_duplicate_detection_and_locking`
testi, başka otel adayı aktif kilitliyken komşu otelin kaydı **maskeli**
(`***@***`) aldığını, reddedilmediğini sabitliyor. Yani model "ortak aday
havuzu + sahiplik kilidi". Buraya kapsam koysaydım o tasarımı bozacaktım.

> **Senin kararını bekleyen çelişki:** aday **listesi** kapsamla süzülüyor
> (`apply_candidate_scope`), aday **detayı** ise oteller arası açık ve yalnızca
> kilitliyse maskeleniyor. İkisi aynı şeyi söylemiyor. Hangisi doğru — liste de
> mi açılmalı, detay da mı kapanmalı? Ana geliştiricinin tasarımı olduğu için
> dokunmadım.

### ✅ D-48 — Pozisyon ekranından eklenen aday "otelsiz" kaydediliyordu
Başvuru oluşturan **her** yol pozisyonun `hotel_id`'sini kopyalıyor
(applications.py, portal.py ×2, settings.py yönlendirme kabulü, seed) —
ama pozisyon çalışma alanındaki **"aday ekle"** butonunun çağırdığı
`POST /api/positions/{id}/candidates` kopyalamıyordu, `hotel_id` NULL kalıyordu.

`hotel_id` otel filtrelerinin eşleştiği kolon. Sonuç: bu başvurular
**ilanın sahibi otele görünmez** oluyordu — ve asıl canı yakan yer,
`/api/offers/approvals/pending` de aynı kolonla süzdüğü için **böyle bir adaya
yapılan teklif onay kuyruğuna hiç düşmüyor**, sessizce öylece kalıyordu.

Mevcut kayıtlar startup'ta pozisyonlarından onarılıyor (depodaki
`phone_normalized` geri-doldurma desenine uygun; gerçek sunucu açılışında
`[Startup] 1 application(s) given the hotel of their position.` ile doğrulandı).

### Test edip sorun bulamadıklarım (bu turda)

- **Audit log değişmezliği:** `ImmutableAuditLog` için depoda **hiç** güncelleme
  veya silme yolu yok — sadece ekleme ve iki okuma sorgusu var, okuma ucu da
  `can_access_settings` izniyle kapalı (otel İK'sı 403 alıyor). Uygulama
  seviyesinde iddia tutuyor. *Not:* değişmezlik yalnızca kodun yokluğuyla
  sağlanıyor; veritabanı tarafında tetikleyici/hash zinciri yok.
- **Sahiplik (ownership) kilidi:** gerçekten bağlı ve çalışıyor — kilit başvuru
  sırasında kuruluyor, mülakat planlama/tamamlama ve durum değişiminde sayaç
  sıfırlanıyor, süre dolunca serbest bırakılıyor. (Süre dolunca `rejected`
  yapılması konusu zaten kararını beklediğim maddelerde.)
- **Aday yönlendirme hiyerarşisi:** gerçek olan `budget_service.trigger_scoped_routing`
  düzgün: önce aynı bölge, sonra aynı şehir, sonra merkez İK; mükerrer kontrolü var.

---

## 2e. Başvuru tarafı kapsam turu (D-49 … D-51)

D-47'yi (pozisyon/teklif) kapattıktan sonra aynı soruyu başvurulara sordum.

### 🔴 D-49 — Bir otel, başka otelin adayını reddedebiliyordu
Sadece otel 1'e yetkili İK hesabıyla, Almaty'nin (otel 2) başvurusu üzerinde:

```
PATCH /api/applications/66/status  {"status":"rejected"}   → 200  ✔ reddedildi
```

Aynı durum `/stage`, `/notes` ve `DELETE` için de geçerliydi. Bu, "ortak aday
havuzu" tartışmasının dışında: başvuru **o otelin onay zincirini ve sahiplik
kilidini taşıyor**, yani bir otelin başka otelin sürecinin içinde işlem
yapmasıydı. Dördü de artık otel kapsamından geçiyor ve **404** dönüyor.

Kapsam kararı veren bu uçlar `get_current_user_optional` okuyordu;
`None` olabilen bir kullanıcıyla yetki kontrolü yapılamayacağı için
`get_current_user`'a çevrildi.

### 🔴 D-50 — Kanban panosu bütün otellerin adaylarını gösteriyordu
`/api/applications/pipeline` — yani **asıl çalışılan ekran** — hiç
süzülmüyordu; yanındaki aday ve pozisyon listeleri süzülürken pano herkesi
gösteriyordu.

Bunu düzeltmek zorunluydu: D-49'da sürükle-bırak hedefini kapsama aldım, panoyu
almasaydım ekranda **sürüklenince 404 veren kartlar** kalacaktı. Tarayıcıda
doğrulandı — merkez 66 kartın hepsini, otel İK kendi 65'ini görüyor.

### ✅ D-51 — Tek bir NULL satır mülakat listesini komple 500'lüyordu
`GET /api/interviews/application/{id}` sızdırmıyordu ama **çöküyordu**:
`round_number`, `interview_type`, `status` ve `duration_minutes` veritabanında
nullable (varsayılanları Python tarafında), `InterviewOut` ise dördünü de
zorunlu istiyordu. ORM'den geçmemiş tek bir satır (toplu içe aktarma, elle
SQL, eski kayıt) o başvurunun **bütün mülakat listesini 500 yapıyordu** —
aday kartının Mülakatlar sekmesi tamamen açılmıyordu.

Şema artık NULL'a tolerans gösteriyor ve ekranda "— Tur" yazmaması için
kolonun varsayılanına düşüyor (`Position.description` için daha önce yapılanın
aynısı).

> Bu, "şema veritabanından katı" sınıfının canlı bir örneği. Kalan alanlar için
> (bkz. *Düzeltmediklerim*) hâlâ söylemeni bekliyorum; bunu düzelttim çünkü
> elimde gerçek bir 500 vardı.

---

## 2f. Departman müdürü ve kadro filtresi (D-52 … D-56)

### ✅ D-52 — Kadro filtresinde departman seçmek hiçbir şey döndürmüyordu
Açılır listeden "Mutfak" seçince **0 satır**, arama kutusuna yazınca 1 satır
geliyordu — filtre duruyordu ama hiç eşleşmiyordu, o yüzden elle yazmak
gerekiyordu.

Açılır liste **Departman tablosundan** doldurulurken kadro satırları
**Excel'deki yazımı** saklıyor. İçe aktarma departmanları büyük/küçük harf
duyarsız aradığı için, tabloda "Mutfak" varken "MUTFAK" yazan bir dosya yeni
kayıt açmıyor ve ikisi kalıcı olarak birbirini tutmuyor. Filtre ise `=` ile
karşılaştırıyordu.

Düzeltme iki parçalı: (1) seçilen ad, verinin gerçekten kullandığı yazımlara
çözülüyor; (2) uç nokta artık `available_departments` dönüyor ve açılır liste
ondan besleniyor — yani boş dönecek bir seçenek sunulması mümkün değil.

> **Dikkat — SQL tarafında katlama işe yaramıyor:** önce `func.lower()` ile
> denedim, **"Ön Büro" ve "Yiyecek ve İçecek" boş dönmeye başladı**. SQLite'ın
> `lower()`'ı yalnızca ASCII katlıyor. Karşılaştırma Python'a alındı, noktalı/
> noktasız I de Türkçe kuralıyla eşleniyor (Python'un `casefold`'u "İ"yi
> birleşik noktalı bir "i"ye çevirdiği için "İçecek" ile "içecek" buluşmuyordu).

### 🔴 D-53 — Departman müdürü aday havuzunu HİÇ göremiyordu
Kapsamı sıkı değil, **sorgusu bozuktu**: `apply_candidate_scope` Candidate'i
doğrudan Position'a bağlamaya çalışıyordu, oysa iki tablo arasında yol yok —
aday departmana tıpkı otele olduğu gibi **başvuru üzerinden** bağlanıyor. Filtre
hiçbir şey eşleştirmediği için müdür kendi panosunda 9 kart görürken havuzu
bomboştu.

### 🔴 D-54 — Departman müdürü bütün departmanların kadrosunu görüyordu
`/api/headcount/summary` HOTEL kapsamlı kullanıcıda oteli sabitliyor ama
departman karşılığı yoktu: 6 departmanın hepsi dönüyordu ve sorguda başka bir
departmanı adıyla istemek de çalışıyordu. `/api/staffing-needs/` ise
`current_user`'ı alıp hiç kullanmıyordu.

| | Önce | Sonra |
|---|---|---|
| Aday havuzu | **0** | 9 |
| Kadro İhtiyaçları | **6 departman** | 1 (Mutfak) |
| Kadro talepleri | süzülmüyor | kendi departmanı |
| Pozisyonlar / Kanban | doğru | doğru |

> Not: departmanlar **düz bir liste** — üst/alt departman ilişkisi veri
> modelinde yok. Yani "bir üst departmanı görme" riski zaten yoktu.

### ✅ D-55 — Departman müdürü arayüzden atanamıyordu
`data_visibility_scope`, `hotel_access_ids` ve `department_access_ids`
backend'de baştan beri kullanılıyordu ama **hiçbir ekran göndermiyordu** ve
kullanıcı şemaları bu alanları düşürüyordu — departman müdürü ancak SQL ile
tanımlanabiliyordu.

Her iki kullanıcı formuna "Görünürlük Kapsamı" seçimi (tüm organizasyon /
seçili oteller / seçili departmanlar) ve buna bağlı çoklu seçim eklendi. Rol
listesine backend'in zaten tanıdığı CENTRAL_HR, HOTEL_HR ve
DEPARTMENT_MANAGER geldi. Kapsam değişince eski seçim geride kalmıyor; kapsam
seçilip hiçbir şey işaretlenmezse kaydetmiyor (o hesap hiçbir şey göremezdi,
bu da kısıtlı değil **bozuk** görünürdü).

### ✅ D-56 — Kalan kapsam sızıntıları (sistematik tarama)
Otel 1 İK'sıyla, otel 2'nin kayıtları üzerinde tek tek denedim:

```
POST   /api/offers/                          başka otelin başvurusuna teklif açtı
PATCH  /api/offers/{id}/status?status=accepted  kabul etti → adayı İŞE ALDI
GET    /api/offers/{id}/salary-check         ücret bandını okudu
POST   /api/offers/{id}/generate-letter      teklif mektubunu yazdı
GET    /api/onboarding/{app_id}              işe giriş listesini okudu
POST   /api/onboarding/{app_id}/generate     yeniden oluşturdu
PATCH  /api/onboarding/task/{id}             görev işaretledi
GET    /api/positions/{id}/workspace         pozisyon ekranının tamamı
GET    /api/positions/{id}/candidates|matches
GET    /api/applications/{id}/interviews     mülakat cevapları
PATCH  /api/interviews/{id}                  mülakatı değiştirdi
DELETE /api/interviews/{id}                  mülakatı SİLDİ
```

Hepsi kapatıldı; merkez aynı uçlarda 200 almaya devam ediyor, 11 sayfa temiz.

**Bilerek açık bırakılanlar — senin kararını bekliyor (madde 14):** aday uçları
(`GET /api/candidates/{id}`, `/profile`, `/applications`, `/activities` ve
`blacklist` / `rating` / `DELETE`) hâlâ oteller arası cevap veriyor. Okuma,
ortak havuz tasarımının kendisi (kilitliyken maskeleniyor). Ama **kara listeye
alma ve silme** ayrı bir soru: ortak bir adayı tek bir otel kara listeye
alabilmeli mi, silebilmeli mi? Karar senin.

---

## 3. 📋 Senin sorduğun 3 madde

### 1. GM ekranlarını tek tek gezmek
Gezildi, ekran görüntüleri alındı. Listelediğin beş ekranın karşılığı şu an şöyle:

| Senin dediğin | Uygulamadaki karşılığı |
|---|---|
| Genel Bakış | ✅ Var (`page='dashboard'`) |
| Kadro Planlama | ✅ Var — adı **Kadro İhtiyaçları**, üst etiketi "İŞ GÜCÜ PLANLAMA" |
| Onaylar | ⚠️ Ayrı ekran değil — **Kadro İhtiyacı Yönetimi** içindeki onayla/reddet akışı (D-05'e kadar erişilemiyordu) |
| Raporlar | ✅ Var (D-01'den sonra) |
| Takvim | ⚠️ Ayrı ekran yok — Genel Bakış'taki "Bugünkü programım" kartı ve Pipeline içindeki "Takvim & Görevler" alt sekmesi |

**Karar gerekiyor:** *Onaylar* ve *Takvim* ayrı birer GM ekranı mı olmalı, yoksa
mevcut yerlerinde mi kalsın? İkisi de bugünkü hâliyle GM'nin aradığı yerde değil.

### 2. Talep gönderme akışı — "en geç ne zaman ihtiyaç var" alanı
Akış **arayüzden uçtan uca denendi** ve çalışıyor: boş form → Türkçe uyarı; dolu form →
kayıt; tabloda satır; Onayla → pozisyon doğuyor; Reddet → sebep soruluyor; özet kartları
güncelleniyor.

**"En geç ne zaman ihtiyaç var" alanı sistemde hiç yoktu** — ne formda ne veritabanında.
`StaffingNeed.needed_by` (DATE) olarak ekledim; idempotent `ALTER TABLE` ile migrasyon,
formda tarih alanı, tabloda "En geç" kolonu.

📋 **Karar gerekiyor:** Bu alan *zorunlu* mu olmalı? Şu an opsiyonel. Ayrıca önceliği
(`urgent/high/normal/low`) bu tarihten otomatik türetmek isteyip istemediğini söyle.

### 3. 1.185,58 FTE'nin hangi satırlardan oluştuğu — **çözüldü** ✅
Canlı ortam erişimi gerekmedi; sayıyı yerelde birebir yeniden ürettim ve **aradaki farkın
sebebini buldum**.

120 satırlık, "Toplam FTE" sütunu tam olarak **1.185,58** eden bir bütçe dosyası
hazırlayıp içe aktardım:

| | Değer |
|---|---:|
| Excel'de `SUM(Toplam FTE)` | **1.185,58** |
| Ekranda "Onaylı kadro" (düzeltmeden önce) | **1.121** |
| **Kayıp** | **64,58 FTE (%5,4)** |

**Sebep:** `routers/headcount.py` her satırı toplamadan **önce** `int()` ile kırpıyordu
(`budget_fte = int(agg["budget_fte"])`). 4,58 → 4. 120 satırda satır başına ortalama
0,54 kayıp, toplamda 64,58. Kırpma her zaman aşağı yuvarladığı için hata **birikiyor ve
hep aynı yöne** sapıyor — yani ekran açık kadro ihtiyacını sistematik olarak **az**
gösteriyordu.

Düzeltildikten sonra ekran **1.185,58** gösteriyor, fark **0,00**.

📋 **Tek iş kararı senin:** `net_open` (net açık ihtiyaç) artık `int()` yerine `round()`
ile hesaplanıyor. Kırpma sistematik olarak eksik gösteriyordu, `round()` bu sapmayı
kaldırır ama "her kesir yukarı yuvarlansın" politikası istiyorsan `math.ceil` yapmak
tek satır. (4,58 FTE bütçe + 4 aktif çalışan → `round` ile 1 kişi açık, `ceil` ile de
1; ama 4,2 FTE + 4 aktif → `round` ile 0, `ceil` ile 1.)

---

## 4. 📋 Uydurma veriler — hepsi temizlendi ama haberin olsun

Arayüz, gerçek değer 0 veya eksik olduğunda **inandırıcı görünen sahte rakamlar**
gösteriyordu. Bir İK sisteminde bu, yanlış karara sebep olabilecek en tehlikeli şey:

| Yer | Sahte varsayılan |
|---|---|
| Kadro İhtiyaçları · Onaylı kadro | `|| 2846` |
| Kadro İhtiyaçları · Aktif çalışan | `|| 2719` |
| Kadro İhtiyaçları · Doluluk | `|| 95.5` |
| Kadro İhtiyaçları · Net açık | `|| 127` |
| Kadro İhtiyaçları · İlanı olmayan | `|| 18` |
| Kadro İhtiyaçları · Kesinleşen giriş | `|| 36` |
| Dashboard · bildirim rozeti | `|| 4` |
| Dashboard · aksiyon sayacı | `|| 5` |
| Pozisyon sihirbazı özeti | `|| 24` FTE, `|| 18`, `|| 6` |
| Mülakat soru sayacı | `|| 4` |
| Dashboard selamlama | `|| 'Şule'` — giriş yapan kim olursa olsun |

Yani **boş bir veritabanı, eksiksiz ve tamamen kurgusal bir iş gücü tablosu**
gösteriyordu. Hepsi 0'a (selamlama giriş yapan kullanıcıya) çevrildi.

### ✅ Ve asıl büyük olan: backend de uyduruyordu

Arayüzdeki sahte varsayılanları temizledikten sonra rakamlar hâlâ tutmuyordu.
Sebep: `routers/analytics.py` gerçek sorgu boş dönünce **gerçek kayıt gibi
okunan örnek satırlar** koyuyordu:

- Aday isimleri: *Ahmet Yılmaz*, *Elif Demir*, eşleşme yüzdeleriyle
- Mülakat saatleri: *10:30 İK Mülakatı*, *14:00 Teknik Mülakat*
- Denetim günlüğü kayıtları, **gerçek bir çalışanın adına** atfedilmiş (*Şule Sıray*)
- Maaş bandı referansları, departman bazlı işe alım maliyetleri
- `open_headcount = 127`, `active_candidates = 1248`, `today_interviews = 18`, `pending_offers = 7`

"İlgilenmeniz gerekenler" paneli daha da kötüydü: **beş sabit metin**, üçünün
arkasında hiçbir sorgu yok; sorgusu olan ikisi de `max(3, ...)` / `max(1, ...)`
ile taban uyguladığı için gerçek 0 veya 1 yine 3 ve 1 olarak görünüyordu.

Ayrıca `index.html`'deki **beş widget'ın her birinde** aynı örnek satırların bir
kopyası `v-else` dalında duruyordu — yani backend'i düzeltmek tek başına yetmedi.

**Ne yaptım:** Silmek yerine `DEMO_DATA` özellik bayrağının arkasına aldım,
varsayılan **kapalı**. Gerçek kurulum gerçek rakamları gösterir; demo isteyen
`DEMO_DATA=true` yapar. Aksiyon paneli artık veriden türetiliyor: sahiplik
süresi dolanlar ve bekleyen onaylar **gerçek sayılarını** gösteriyor, sıfırda
kayboluyor; aday bulunmayan pozisyonlar gerçek pozisyon listesinden adlandırılıyor.
Widget'ların `v-else` dalları dürüst boş durumlara çevrildi
("Bugün planlanmış görüşme yok.", "Şu an bekleyen bir işiniz yok." …).

⚠️ **Dikkat:** `tests/test_hotfixes.py::test_dashboard_stats` bu sahte veriye
karşı assert ediyormuş — bütçe satırı oluşturup hiç `Position` oluşturmuyordu,
yani `active_positions` sadece uydurma yüzünden doluydu. Testi gerçek pozisyon
oluşturacak şekilde düzelttim ki assert bir anlam ifade etsin.

---

## 5. 📋 Düzeltmediklerim — kararını bekliyor

### 📋 Uygulama hiç e-posta göndermiyor — e-posta servisi tamamen bağlanmamış
`backend/services/email_service.py` beş hazır işlemsel e-posta şablonu içeriyor:
mülakat daveti, teklif bildirimi, başvuru durum güncellemesi, aday portal erişim
linki, onboarding karşılama. Ama:

- Modül **hiçbir router veya servisten çağrılmıyor** (tüm depoda tek referans yok)
- Bağımlılığı `fastapi_mail` **kurulu değil ve `requirements.txt`'te de yok** —
  yani import edilmeye çalışılsa modül zaten yüklenemez
- `EmailLog` ve `EmailTemplate` modelleri ile `email_logs` / `email_templates`
  tabloları da kullanılmıyor

Pratikte: **aday hiçbir bildirim almıyor.** Mülakata çağrıldığında, teklif
aldığında, durumu değiştiğinde ya da işe girişi başladığında sistem ona hiçbir
şey yazmıyor.

ℹ️ Arayüz bu konuda dürüst: "Mail At" butonu sunucudan gönderdiğini iddia etmiyor,
*"Varsayılan e-posta istemciniz üzerinden…"* diyerek kullanıcının kendi mail
programına devrediyor. Yani bu bozuk bir söz değil, **yapılmamış bir iş**.

**Karar senin:** hangi olaylarda otomatik e-posta gitsin? Bağlamamı istersen
`fastapi_mail`'i requirements'a eklemem ve SMTP/SendGrid bilgilerini `.env`'e
girmen gerekiyor.

### 📋 "10 günlük değerlendirme sayacı" yapılmamış ama tamamlandı işaretli
`IMPLEMENTATION_STATUS.md` → Faz 4 → **`- [x] 10-day evaluation counter logic
(evaluation_deadline on Application)`** diyor. Gerçekte:

- `Application.evaluation_deadline` kolonu modelde var ve migrasyonla ekleniyor
- Ama **hiçbir yerde yazılmıyor, okunmuyor, gösterilmiyor** (tüm depoda tek
  atama yok, arayüzde de geçmiyor)

Yani sayaç yok, sadece boş bir kolon var. Nasıl çalışması gerektiğini (10 gün
neyden itibaren? süre dolunca ne olmalı?) bilmediğim için **uydurmadım**.

ℹ️ Aynı listede işaretli olan **sahiplik süresi mekanizması gerçekten çalışıyor** —
test ettim: süresi geçmiş kilitli bir başvuru, aday listesi çağrıldığında
otomatik olarak serbest bırakılıyor (`UNLOCKED`).

📋 Ancak serbest bırakırken başvurunun durumunu **`rejected`** yapıyor — yani
İK zamanında ilgilenmediği için aday otomatik elenmiş oluyor. Durum geçmişine
sebebi yazılıyor. "Havuza geri dön" mü olmalı, "elendi" mi? İş kuralı senin.

### `POST /api/positions/{id}/deep-analyze` diye bir rota yok
Pozisyon ekranındaki **"Derin AI Analizi"** butonu bu adrese istek atıyor; backend'de
böyle bir endpoint hiçbir yerde tanımlı değil, yani buton her zaman 404 alıyor.
Arayüz `{ results: [{ rank, ... }] }` bekliyor.

Bunu **uydurmadım**: ne tür bir analiz istediğini (hangi kriterler, hangi çıktı) bilmiyorum
ve Gemini anahtarı da tanımlı değil. Ne yapmasını istediğini yaz, yazayım.

### FTE 2,5 onaylanınca pozisyon `headcount = 2` oluyor
`staffing_needs.approve_staffing_need` içinde `headcount=int(need.needed_fte)`.
2,5 FTE → 2 kadro. Yukarıdaki FTE tartışmasının aynısı; iş kuralı senin.

### Şemada zorunlu ama veritabanında NULL olabilen 3 alan (gizli 500 riski)
`Position.title`, `UserOut.email`, `UserOut.full_name`, `LogOut.action/target_type/target_id`.
Şu an hiçbirinde NULL veri yok, yani patlamıyor. D-03'ün aynısı olduğu için işaret
ediyorum ama CLAUDE.md'deki "bozuk olmayanı düzeltme" kuralı gereği dokunmadım.

### Prod'da bilgi sızıntısı riski
`main.py` tüm startup'ı `try/except` ile sarıp hata hâlinde **traceback'i HTML olarak**
döndüren bir "Fallback Diagnostic Server" açıyor. CLAUDE.md'de zaten not düşülmüş;
Railway dışına çıkmadan önce gözden geçir.

### Olmayan bir pozisyon için başvuru formu yine de açılıyor
`/portal/job/9999` "Pozisyon bulunamadı" uyarısı veriyor ama form kabuğunu yine
de çiziyor ("Genel Başvuru"). Aday formu doldurabilir, gönderim sırasında hata
alır. Formu hiç göstermemek mi, yoksa "Genel Başvuru" olarak kabul etmek mi
istersin?

### `backend/.env.example` içindeki Gemini API anahtarı hâlâ commit'li
**İptal ettirmeni öneririm.**

---

## 6. Test edilip sorun çıkmayanlar

- **11/11 sayfa** hatasız açılıyor (konsol hatası yok, başarısız API çağrısı yok)
- **19 alt sekme** (Adaylar 4, Pipeline 4, Ayarlar 11) hepsi temiz
- Sayfalardaki **tüm yıkıcı olmayan butonlar** tıklandı — hata üretmedi
- `app.js` içindeki **133 API çağrısının tamamı** canlı rota tablosuyla karşılaştırıldı;
  uyuşmayan 3'ü (D-10, D-11 ve deep-analyze) yukarıda
- **1428 şablon ifadesi** `setup()` export'larıyla karşılaştırıldı; D-01 dışında temiz
- **Ayarlar'ın 11 alt sekmesi** tek tek açıldı — hata yok
- **Aday modalının 5 sekmesi** (Genel Bakış, CV, Değerlendirme, Başvurular,
  Zaman Çizelgesi) — hata yok
- **Public portal**: ilan sayfası ve walk-in formu (D-19'dan sonra) çalışıyor
- **Mobil**: 390px / 768px / 360px'te beş sayfa ölçüldü, yatay taşma yok
- **14 sayfa şablonunun tamamında** mobil hamburger butonu var
- **Chatbot ve AI sekmeleri** (Soru Üretimi, Mülakat Notu Analizi): anahtar
  yokken dürüstçe "Demo Modu: API Anahtarı bulunamadı" diyor, çökmüyor
- **Ayarlar'ın kalan 6 sekmesi** (Denetim Günlüğü, Uzatma Talepleri, Maaş
  Politikaları, Pipeline Şablonları, Sistem Parametreleri, İş Gücü Bütçesi):
  hepsi temiz, denetim günlüğü gerçek kayıt gösteriyor
- **Blacklist tam turu**: aday modalından kara listeye al (sebep sorularak) →
  Blacklist sayfasında göründü → listeden çıkar → temizlendi
- **Kanban sürükle-bırak**: kart taşındı, durum veritabanında değişti
- **RECRUITER rolüyle** tüm sayfalar gezildi

### Teklif onay zinciri — uçtan uca doğrulandı (kod değişmedi, testle sabitlendi)

İşin en kritik iş kuralı. HOTEL_HR rolünde ikinci bir kullanıcı açıp hem API'den
hem arayüzden çalıştırdım:

1. Bant **içi** teklif (35.000 / bant 30–40K) → doğrudan `APPROVED`
2. Bant **üstü** teklif (48.000) → `PENDING_APPROVAL` + sapma gerekçesi,
   iki sıralı onay isteği açılıyor (HOTEL_HR `PENDING`, CENTRAL_HR `WAITING`)
3. Onay beklerken göndermeyi denedim → **400**: *"Teklif henüz onaylanmadı. Gönderilemez."*
4. HOTEL_HR onayladı (arayüzdeki "Teklif Onayları" sekmesinden) → 2. adım `PENDING`'e geçti
5. Merkez onayladı → teklif `APPROVED`, artık gönderilebiliyor
6. Reddetme senaryosu: 1. adım reddedilince teklif `REJECTED`, bekleyen 2. adım
   da iptal ediliyor, gönderme → **400**: *"Teklif onay sürecinde reddedildi."*

ℹ️ Bir SYSTEM_ADMIN'in bekleyen onaylar listesinin boş görünmesi **hata değil** —
sıralı akış önce otel İK'sını bekliyor, merkez adımı henüz `WAITING`.

### Son turda ayrıca doğrulananlar (sorun çıkmadı)

- **Maaş politikası Excel import**: 2 satırlık dosya doğru okundu, otel eşleşti,
  lojman/servis/yemek boolean'ları ayrıştırıldı. ⚠️ Not: import **mevcut tüm
  politikaları siliyor** (`delete()` sonra ekliyor) — "değiştir" semantiği
  kasıtlıysa sorun yok, değilse söyle.
- **Pipeline şablonu düzenleme**: aşama adı değiştirildi, kaydedildi, sayfa
  yenilendikten sonra da kalıcıydı.
- **Teklif Onayları sekmesi (arayüz)**: HOTEL_HR rolüyle bekleyen onay listelendi,
  "Onayla" butonu çalıştı, ikinci adım aktifleşti.

- **"Eşleştir" akışı**: aday modalından pozisyon seçilince uyum skorları anında
  hesaplanıp listeleniyor, hata yok.
- **KVKK onayı**: onay kutusu işaretlenmeden başvuru gönderilemiyor
  (400 — *"KVKK rıza onay metnini kabul etmeniz zorunludur."*)
- **Sahiplik süresi dolması**: süresi geçmiş kilit otomatik serbest bırakılıyor

ℹ️ Buton taramasında görünen `404 /api/positions/applications/1/decision`
**hata değil** — "bu başvuru için henüz karar girilmemiş" demek ve arayüz bunu
doğru şekilde sessizce ele alıyor.
- **6 adımlı pozisyon sihirbazı**: boş gönderimde net Türkçe uyarı veriyor
  ("Otel ve Pozisyon Başlığı alanları zorunludur…"), gerçek veriyle tam tur
  atıldı ve pozisyon oluştu
- **CV yükleme**: gerçek PDF ile denendi, adayın kendi bilgileri kaydediliyor
- **Pipeline / mülakat listesi**: dürüst boş durum ("Henüz mülakat planlanmamış")
- **Aday Kanban**: kartlar, kolonlar ve kaynak etiketi ("QR Walk-In") doğru
- **Ayarlar → Organizasyon Yapısı**: gerçek organizasyon kaydını gösteriyor

### Uçtan uca doğrulanan tam işe alım zinciri

D-25 düzeltildikten sonra çekirdek ATS akışının tamamı gerçek veriyle çalıştırıldı:

1. **QR walk-in başvurusu** → aday + başvuru oluştu (`QR Walk-In` kaynağıyla)
2. **Kanban** → kart "Başvurdu" kolonunda, %62 eşleşme rozetiyle
3. **Teklif oluştur** → 42.000 TRY, maaş politikası kontrolü (`has_policy:false`, geçerli)
4. **Gönder** → `sent`, `sent_at` damgalandı
5. **Kabul** → `accepted`, başvuru otomatik `hired` oldu
6. **İşe Giriş** → aday listede çıktı, 12 maddelik kontrol listesi üretildi
   (Evrak / IT Setup / Tanışma / Eğitim, sorumlularıyla)
7. **Görev işaretle** → ilerleme %0 → %8

8. **Mülakat planla** → başvuru modalından planlandı, Pipeline listesinde
   ve dashboard'un "Bugünkü programım" kartında doğru göründü

Ayrıca: 6 adımlı pozisyon sihirbazı gerçek veriyle tamamlanıp pozisyon oluşturdu;
Ayarlar'dan yeni kullanıcı oluşturuldu; organizasyon/bütçe Excel'i içe aktarıldı.

---

## 7. Ortam notları

- `google-generativeai` deprecated uyarısı ve `sentence-transformers` eksikliği
  (keyword fallback) CLAUDE.md'de bilinen sorun olarak kayıtlı — dokunmadım.
- Bu konteynerde `unpkg.com` ve `api.qrserver.com` ağ politikasıyla engelli.
  Vue'yu npm'den alıp Playwright ile yerelden servis ederek test ettim; QR üretimi
  bu ortamda çalışmıyor, Railway'de çalışması beklenir.
- Yeniden test etmek için: `pytest tests/` (26 test, tarayıcı gerekmez).
