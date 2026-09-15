# SkillMatch AI — Test Bulguları ve Düzeltmeler

> Chrome (Playwright + Chromium) ile yerel ortamda (`http://127.0.0.1:8000`,
> SQLite, demo@skillmatch.ai) sistematik gezilerek çıkarıldı.
> Durum sütunu: ✅ düzeltildi · 🔧 üzerinde çalışılıyor · 📋 senin kararın gerekiyor

---

## 0. Yazar notu — hangi yaklaşım öncelikli?

`git shortlog` sonucu:

| Yazar | Commit | Kapsam |
|---|---|---|
| **susry19** (sulesiray19@gmail.com) | **48** | Faz 0–7'nin tamamı: organizasyon/Excel import, StaffingNeed, RBAC/scope, pipeline, dashboard yeniden tasarımı, analytics, chatbot |
| beyzaacetin (sen) | 2 | Karpathy rehberi (`EXAMPLES.md`), mobil responsive redesign |

Talimatın gereği **susry19'un yaklaşımı önceliklidir**. Yaptığım tüm düzeltmeler
onun mevcut desenine uyuyor: şablon `index.html` içinde `<template v-if="page==='x'">`,
state/metod `app.js` `setup()` içinde ve `return` bloğunda export, ayrı `.vue` dosyası
veya build adımı yok, renkler `style.css` `:root` token'larından.

---

## 1. Kritik hatalar

### ✅ H-01 — Raporlar sayfası tüm uygulamayı çökertiyordu
**Belirti:** Sol menüden *Raporlar*'a tıklayınca ekran tamamen beyaz kalıyor, sidebar dahil
her şey kayboluyordu. Sayfa yenilenene kadar uygulama kullanılamıyordu.

**Kök neden:** `app.js` `setup()` dönüş bloğu state'i `salary_stats: salaryStats` adıyla
veriyordu, `index.html` ise 5 yerde `salaryStats` diye kullanıyordu. Şablonda `salaryStats`
`undefined` olduğu için `salaryStats.avg_offered` okunurken Vue render'ı patlıyor ve
Vue 3'te render hatası tüm uygulama ağacını düşürüyordu.

**Düzeltme:** `backend/static/app.js:3467` — `salary_stats: salaryStats,` → `salaryStats,`

**Doğrulama:** Raporlar sayfası artık 2528 karakterlik içerikle açılıyor, konsol hatası yok.

**Ek önlem:** Aynı sınıftan başka hata var mı diye `index.html` içindeki 1428 şablon
ifadesinin tamamını `setup()`'ın export ettiği 415 isimle karşılaştıran statik bir tarayıcı
yazdım. Başka gerçek uyumsuzluk çıkmadı (kalan 5 eşleşme arrow-fonksiyon parametresi).

### 🔧 H-02 — Üç menü öğesi bomboş sayfa açıyor
*Kampanyalar & QR*, *İşe Giriş* ve *Blacklist* menüye eklenmiş ama karşılık gelen
`<template v-if="page==='...'">` bloğu `index.html` içinde **hiç yok**. Tıklayınca içerik
alanı tamamen boş kalıyor (konsol hatası bile vermiyor, çünkü Vue eşleşen şablon bulamıyor).

`index.html` içindeki gerçek sayfa şablonları: `dashboard`, `headcount`, `talent`,
`staffing`, `jobs`, `interviews`, `analytics`, `tracking`, `settings`, `ai_search`,
`candidate_profile` — yani 11 menü öğesine karşılık 8 çalışan sayfa.

Backend tarafı hazır, sadece arayüz eksik:
- Kampanyalar: `GET/POST/DELETE /api/campaigns` (`routers/campaigns.py`)
- İşe Giriş: `GET /api/onboarding/{app_id}`, `POST .../generate`, `PATCH /task/{id}` (`routers/onboarding.py`)
- Blacklist: `POST /api/candidates/{id}/blacklist`, aday listesinde `is_blacklisted` alanı

### 🔧 H-03 — Dashboard'da ölü buton: "Teklifi görüntüle →"
`index.html:656` `@click="page='offers'"` yapıyor ama `offers` diye bir sayfa şablonu yok.
Buton hiçbir şey yapmıyor gibi görünüyor (aslında içerik alanını boşaltıyor).

---

## 2. Tutarsız görünen veriler

### 📋 V-01 — "Açık kadro" iki ekranda iki farklı sayı
- *Genel Bakış* KPI kartı: **Açık kadro 127**
- *Kadro İhtiyaçları*: **Onaylı kadro 154 / Aktif çalışan 130 / Net açık ihtiyaç 16**

İki ekran aynı kavramı farklı kaynaktan hesaplıyor. Hangisinin doğru tanım olduğunu
netleştirmen gerekiyor (`routers/analytics.py` dashboard-stats vs `routers/headcount.py`).

### 📋 V-02 — FTE açığı 0 görünüyor
*Genel Bakış* → "FTE Açığı Özeti: 0 (Toplam açık bütçe FTE)". Yerel veritabanında
`workforce_plan_lines` ve `workforce_budget_records` tabloları **boş** olduğu için
gerçek FTE hesabı 0 dönüyor; *Kadro İhtiyaçları* ekranındaki aylık grafik ise
`routers/headcount.py:587-593` içindeki **sentetik fallback** sayılarını gösteriyor
(`b_fte = 150.0 + 10.0 * ...`). Yani o grafikteki 9/10/11/12 değerleri gerçek veri değil.

Senin sorduğun **1.185,58** rakamı da bu tablolardan geliyor; yerel kopyada veri
olmadığı için hangi satırlardan oluştuğunu buradan doğrulayamıyorum — canlı ortam
(Railway/PostgreSQL) verisi veya `Organizasyon_Butce_FTE` Excel'i gerekiyor.

---

## 3. Senin sorduğun 3 madde — durum

1. **GM ekranlarını gezmek** → Gezildi. Ama listelediğin beş ekranın karşılığı şu an şöyle:
   *Genel Bakış* ✅ var · *Kadro Planlama* ✅ var (adı **Kadro İhtiyaçları**, üst etiketi
   "İŞ GÜCÜ PLANLAMA") · *Onaylar* ⚠️ ayrı ekran değil, **Kadro İhtiyacı Yönetimi**
   ekranındaki onayla/reddet akışı · *Raporlar* ✅ var (H-01 düzeltildikten sonra) ·
   *Takvim* ⚠️ ayrı ekran yok, sadece Genel Bakış'taki "Bugünkü programım" kartı ve
   Pipeline içindeki "Takvim & Görevler" alt sekmesi.
2. **Talep gönderme akışı** → "Talebi Gönder" butonu mevcut; akış test ediliyor.
   **"En geç ne zaman ihtiyaç var" alanı veritabanında yok** — `staffing_needs` tablosunda
   böyle bir kolon bulunmuyor (kolonlar: hotel_id, department_id, organization_node_id,
   position_title, position_code, needed_fte, priority, status, approved_by_id, approved_at,
   rejection_reason, source, notes, created_position_id, created_at, updated_at).
3. **FTE 1.185,58 kırılımı** → V-02'de açıkladığım sebeple canlı veri olmadan doğrulanamıyor.

---

## 4. Ortam notları

- Bu depoda `google-generativeai` deprecated uyarısı ve `sentence-transformers` eksikliği
  (keyword fallback) CLAUDE.md'de zaten bilinen sorun olarak kayıtlı, dokunmadım.
- `backend/.env.example` içindeki Gemini API key hâlâ commit'li. **İptal ettirmeni öneririm.**
