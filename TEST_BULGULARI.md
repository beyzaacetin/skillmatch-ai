# SkillMatch AI — Test Bulguları ve Düzeltmeler

Chrome (Playwright + Chromium) ile yerel ortamda sistematik gezilerek çıkarıldı.
Sunucu `http://127.0.0.1:8000`, SQLite, giriş `demo@skillmatch.ai / demo123`.

**Dal:** `claude/pensive-johnson-wtyezh` · **Test durumu:** 26/26 pytest geçiyor
(16 mevcut + 10 yeni regresyon testi)

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

⚠️ **Hâlâ duran bir tane var, bilerek dokunmadım:** `routers/headcount.py` içinde
veritabanı tamamen boşsa 5 satırlık sahte tablo döndüren bir blok var
(Garson/Lifeguard/Resepsiyonist… "matching Screenshot 4" yorumuyla). Demo amaçlı
konmuş olabilir. **Kaldırmamı ister misin?**

---

## 5. 📋 Düzeltmediklerim — kararını bekliyor

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

---

## 7. Ortam notları

- `google-generativeai` deprecated uyarısı ve `sentence-transformers` eksikliği
  (keyword fallback) CLAUDE.md'de bilinen sorun olarak kayıtlı — dokunmadım.
- Bu konteynerde `unpkg.com` ve `api.qrserver.com` ağ politikasıyla engelli.
  Vue'yu npm'den alıp Playwright ile yerelden servis ederek test ettim; QR üretimi
  bu ortamda çalışmıyor, Railway'de çalışması beklenir.
- Yeniden test etmek için: `pytest tests/` (26 test, tarayıcı gerekmez).
