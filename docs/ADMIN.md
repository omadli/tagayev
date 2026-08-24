# Admin Paneli — Kontent Boshqaruv Qoʻllanmasi

> Bu qoʻllanma Tagayev Methods admin paneli orqali sayt kontentini boshqarishni tavsiflab beradi.
> Texnik bilim talab qilinmaydi — barcha amallar forma orqali bajariladi.

**Admin paneli manzili:** `http://saytmanzili/admin/`

---

## Mundarija

1. [Admin paneliga kirish](#admin-paneliga-kirish)
2. [Umumiy tamoyillar](#umumiy-tamoyillar)
3. [Sayt sozlamalari](#sayt-sozlamalari)
4. [Bosh sahifa bloklari](#bosh-sahifa-bloklari)
5. [Kurslar](#kurslar)
6. [Oʻqituvchilar](#oʻqituvchilar)
7. [Yangiliklar va eʼlonlar](#yangiliklar-va-eʼlonlar)
8. [Galereya](#galereya)
9. [Sertifikatlar](#sertifikatlar)
10. [Ota-ona fikrlari](#ota-ona-fikrlari)
11. [Arizalar (Leads)](#arizalar-leads)
12. [Tashriflar analitikasi](#tashriflar-analitikasi)
13. [SEO — qidiruv tizimlariga ulash](#seo--qidiruv-tizimlariga-ulash)
14. [Uch til bilan ishlash](#uch-til-bilan-ishlash)
15. [CKEditor — boy matn muharriri](#ckeditor--boy-matn-muharriri)
16. [Tartiblashtirish va yashirish](#tartiblashtirish-va-yashirish)

---

## Admin paneliga kirish

1. Brauzerda `http://127.0.0.1:8001/admin/` manzilini oching
2. Login va parolni kiriting (oʻrnatish vaqtida `createsuperuser` bilan yaratilgan)
3. Chap tomonli menyu orqali boʻlimlarga oʻting

Yuqori oʻng burchakdagi **"Saytni koʻrish"** tugmasi asosiy saytga oʻtishga imkon beradi.

---

## Umumiy tamoyillar

### Saqlash tugmalari

Har bir forma pastki qismida uchta tugma bor:

| Tugma | Tavsif |
|-------|--------|
| **Saqlash va davom etish** | Saqlaydi, shu sahifada qoladi |
| **Saqlash va yangi qoʻshish** | Saqlaydi, boʻsh forma ochadi |
| **Saqlash** | Saqlaydi va roʻyxatga qaytadi |

### Tarix (History)

Har bir obʼekt sahifasida **"Tarix"** tugmasi bor — kimdir oʻzgartirgan barcha amallarni koʻrish mumkin.

### "Saytda koʻrsatilsin" maydoni

Koʻp modellar "**Saytda koʻrsatilsin**" katagiga ega. Belgini olib tashlash uchun mazmunan saytdan yashiriladi, lekin bazadan oʻchirilmaydi.

### Tartib raqami

"**Tartib raqami**" maydoni kichikroq son = yuqoroqda koʻrinadi. Masalan, 0 → birinchi, 10 → oxirgi.

---

## Sayt sozlamalari

**Admin menyusi → Sozlamalar → Sayt sozlamalari**

Bu yagona forma — barcha global sayt maʼlumotlari shu yerda saqlanadi.

### Brending

| Maydon | Tavsif |
|--------|--------|
| **Sayt nomi** | Sarlavhada va admin panelda koʻrinadigan nom |
| **Shior** | Qisqa tavsif (header yoki hero da ishlatilishi mumkin) |
| **Logo** | Sayt logotipi — JPG/PNG/WebP/GIF, maks 5 MB |
| **Favicon** | Brauzer yorliqcha ikonkasi |
| **Domen** | `tagayev.uz` (protokolsiz) — sitemap va canonical uchun |

### Kontaktlar

| Maydon | Tavsif |
|--------|--------|
| **Asosiy telefon** | +998 XX XXX XX XX formatida |
| **Qoʻshimcha telefon** | Ikkinchi raqam (ixtiyoriy) |
| **Email** | Bogʻlanish email manzili |
| **Manzil** | Toʻliq pochta manzili |
| **Ish vaqti** | Masalan: Dush–Shan, 09:00–18:00 |

### Joylashuv — Xaritadan tanlash

Bu boʻlimda interaktiv **Leaflet xarita** (OpenStreetMap asosida) koʻrinadi. API kalit talab qilinmaydi.

**Joylashuvni belgilash usullari:**

1. **Qidiruv orqali:** "Manzilni qidiring" maydoniga qishloq/shahar nomini kiriting → "Qidirish" tugmasini bosing → natijalar koʻrsatiladi
2. **Xaritani bosish orqali:** Xarita ustiga bosing — belgi (pin) shu joyga qoʻyiladi
3. **Belgini sudrab:** Belgini xaritada istalgan joyga suring

Joylashuv tanlanganida **Kenglik (lat)** va **Uzunlik (lng)** maydonlari avtomatik toʻladi. Bu koordinatalardan Google Xarita va Yandex Xarita havolalari avtomatik quriladi.

> **Eslatma:** "Xarita — qoʻlda override" boʻlimi odatda boʻsh qoldiriladi — faqat maxsus embed kodi kerak boʻlsa toʻldiring.

### Ijtimoiy tarmoqlar

Instagram, Telegram kanal, Telegram guruh, YouTube, Facebook va TikTok havolalarini kiriting. Boʻsh qoldirilgan tarmoqlar saytda koʻrsatilmaydi.

### SEO sozlamalari

| Maydon | Tavsif |
|--------|--------|
| **SEO sarlavha** | Brauzer yorliqcha va qidiruv natijalarida koʻrinadigan nom (maks 60 belgi tavsiya etiladi) |
| **SEO tavsif** | Qidiruv natijalarida tavsif (maks 160 belgi tavsiya etiladi) |
| **OG rasm** | Ijtimoiy tarmoqlarda ulashilganda koʻrinadigan rasm (1200×630 px tavsiya etiladi) |
| **Google verification** | Google Search Console dan olingan `content` qiymati |
| **Yandex verification** | Yandex Webmaster dan olingan tasdiqlash kodi |
| **Bing verification** | Bing Webmaster dan olingan tasdiqlash kodi |

### Analitika ID lari

| Maydon | Format | Tavsif |
|--------|--------|--------|
| **Google Analytics 4 ID** | `G-XXXXXXXXXX` | GA4 oʻlchov identifikatori |
| **Yandex Metrica ID** | Raqam | Yandex Metrica schetchik raqami |

### Telegram bildirishnomalari

Yangi arizalar Telegram bot orqali bir nechta adminga yuborilishi mumkin. Hammasi **admin paneldan** sozlanadi:

1. **Bot tokeni** — *Sozlamalar → Sayt sozlamalari → Telegram* boʻlimida "**Telegram bot tokeni**" maydoniga `@BotFather` bergan tokenni kiriting.
2. **Qabul qiluvchi adminlar** — *Sozlamalar → Telegram qabul qiluvchilar* boʻlimida har bir admin uchun yangi yozuv qoʻshing:
   - **Nomi** — kimligini eslatuvchi ixtiyoriy nom (masalan: *Direktor*).
   - **Chat ID** — adminning raqamli chat ID si (masalan: `123456789`). Buni bilish uchun: admin botga `/start` yozadi, soʻng [@userinfobot](https://t.me/userinfobot) ga oʻz raqamini koʻradi.
   - **Faol** — vaqtincha oʻchirib qoʻyish uchun belgini olib tashlang (yozuvni oʻchirmasdan).
   - Nechta admin kerak boʻlsa, shuncha yozuv qoʻshish mumkin — ariza har biriga yuboriladi.
3. **Yoqish/oʻchirish** — "**Telegram bildirishnomalari yoniq**" katagi butun tizimni bir marta yoqib/oʻchiradi.

> **Eslatma:** Bot tokeni yoki qabul qiluvchilar admin panelda boʻsh boʻlsa, server `.env` dagi `TELEGRAM_BOT_TOKEN` / `TELEGRAM_ADMIN_CHAT_ID` qiymatlaridan zaxira sifatida foydalanadi. Odatda esa hammasini admin paneldan kiritish yetarli.

---

## Bosh sahifa bloklari

### Biz haqimizda boʻlimi

**Admin menyusi → Bosh sahifa bloklari → Biz haqimizda**

| Maydon | Tavsif |
|--------|--------|
| **Sarlavha** | Asosiy sarlavha (masalan: "Bilim — ishonch — kelajak") |
| **Kichik sarlavha** | Yuqori qism belgisi (masalan: "Biz haqimizda") |
| **Matn** | CKEditor bilan boy matn, formatlashtirish imkoni bor |
| **Rasm** | Tasvir rasmi |

Faqat birinchi faol yozuv saytda koʻrsatiladi.

---

### Statistika raqamlari

**Admin menyusi → Bosh sahifa bloklari → Statistika**

Bosh sahifada animatsiyali hisoblagich raqamlari:

| Maydon | Tavsif |
|--------|--------|
| **Raqam** | Butun son (masalan: 300) |
| **Belgi** | Qoʻshimcha belgi — `+`, `%`, `k` va h.k. |
| **Izoh** | Raqam tagidagi matn (masalan: "Oʻquvchilar") |
| **Qizil rang bilan** | Belgilansa, urgʻu rangida koʻrsatiladi |
| **Tartib raqami** | Koʻrinish tartibi |

---

### "Nega biz" kartalari

**Admin menyusi → Bosh sahifa bloklari → Nega biz**

| Maydon | Tavsif |
|--------|--------|
| **Sarlavha** | Karta sarlavhasi |
| **Tavsif** | Qisqa izoh |
| **Ikonka** | Ikonka kodi — mavjud variantlardan tanlang |
| **Qizil ikonka** | Belgisiz — standart, belgilansa — urgʻu rangi |

---

## Kurslar

**Admin menyusi → Sayt mazmuni → Kurslar**

### Kurs turkumlarini boshqarish

Kurslardan oldin turkumlarni (toifalarni) yarating:

**Kurs turkumlari → Qoʻshish**

| Maydon | Tavsif |
|--------|--------|
| **Nomi** | Turkum nomi (masalan: "Til", "Aniq fan") |
| **Slug** | URL uchun nom — avtomatik toʻldiriladi |

### Yangi kurs qoʻshish

**Kurslar → Qoʻshish**

| Maydon | Tavsif |
|--------|--------|
| **Nomi** | Kurs nomi |
| **Slug** | URL manzil (avtomatik yoki qoʻlda) |
| **Turkum** | Yuqorida yaratilgan toifadan tanlang |
| **Qisqa tavsif** | Kurslar roʻyxatida koʻrinadigan qisqa matn (maks 255 belgi) |
| **Toʻliq tavsif** | CKEditor bilan boy matn — kurs detail sahifasida |
| **Davomiyligi** | Erkin matn (masalan: "6 oy", "Doimiy qabul") |
| **Guruh hajmi** | Masalan: "15 kishi", "6–10" |
| **Narx** | Raqam (ixtiyoriy) |
| **Narx izohi** | Masalan: "soʻm/oy" |
| **Narx koʻrsatilsin** | Belgilanmasa narx saytda yashirinadi |
| **Ikonka** | Vizual belgi kodi |
| **Rasm** | Kurs rasmi — JPG/PNG/WebP, maks 5 MB |
| **Top kurs** | Belgilansa, kursda maxsus urgʻu koʻrsatiladi |
| **SEO sarlavha** | Ushbu kurs sahifasi uchun maxsus sarlavha (boʻsh qolsa umumiy ishlatiladi) |
| **SEO tavsif** | Ushbu kurs uchun meta tavsif |

**Til tablari (uz / ru / en):** Har bir matn maydon uchta versiyada kiritiladi (qarang: [Uch til bilan ishlash](#uch-til-bilan-ishlash)).

---

## Oʻqituvchilar

**Admin menyusi → Sayt mazmuni → Oʻqituvchilar**

| Maydon | Tavsif |
|--------|--------|
| **F.I.Sh.** | Toʻliq ismi |
| **Slug** | URL uchun (avtomatik) |
| **Rasm** | Oʻqituvchi surati — JPG/PNG/WebP, maks 5 MB |
| **Lavozim / yoʻnalish** | Qisqa tavsif (masalan: "Ingliz tili · C1 daraja") |
| **Bio / tavsif** | CKEditor bilan toʻliq biografiya |
| **Fanlar** | Oʻqitiladigan fanlar roʻyxati |
| **Tajriba (yil)** | Ish tajribasi yillarda |
| **Instagram** | Instagram profil havolasi |
| **Telegram** | Shaxsiy Telegram havolasi |
| **YouTube** | YouTube kanal havolasi |
| **SEO sarlavha / tavsif** | Profil sahifasi uchun meta maʼlumotlar |

---

## Yangiliklar va Eʼlonlar

**Admin menyusi → Sayt mazmuni → Yangiliklar**

| Maydon | Tavsif |
|--------|--------|
| **Sarlavha** | Yangilik/eʼlon sarlavhasi |
| **Slug** | URL (avtomatik) |
| **Qisqa matn** | Roʻyxatda koʻrinadigan annotatsiya (maks 300 belgi) |
| **Toʻliq matn** | CKEditor bilan boy mazmun — maqola tana qismi |
| **Muqova rasmi** | Asosiy rasm — JPG/PNG/WebP, maks 5 MB |
| **Belgi (tag)** | Qisqa yorliq (masalan: "Eʼlon", "Yangilik", "Aksiya", "Tadbir") |
| **Qizil belgi** | Belgilansa, tag urgʻu rangida koʻrsatiladi |
| **Chop etilgan sana** | Avtomatik toʻldiriladi, qoʻlda oʻzgartirish mumkin |
| **Chop etilgan** | Belgisi olib tashlansa, maqola saytda koʻrinmaydi |
| **Tanlangan** | Belgilansa, sahifada alohida koʻrsatilishi mumkin |
| **SEO sarlavha** | Ushbu maqola sahifasi uchun maxsus meta sarlavha (boʻsh qolsa umumiy ishlatiladi) |
| **SEO tavsif** | Ushbu maqola uchun meta tavsif (boʻsh qolsa SiteConfig tavsifi ishlatiladi) |

---

## Galereya

**Admin menyusi → Sayt mazmuni → Galereya**

Galereya ikki qatlamdan iborat: **Albom** → **Rasmlar**.

### Albom yaratish

**Galereya albomlari → Qoʻshish**

| Maydon | Tavsif |
|--------|--------|
| **Albom nomi** | Masalan: "Oʻquv jarayoni", "Tadbir — 2025" |
| **Slug** | URL (avtomatik) |
| **Tavsif** | Qisqa izoh |
| **Muqova rasmi** | Albomni ifodalovchi rasm |

### Albomga rasm qoʻshish

Albomni ochib **"Rasmlar"** boʻlimida rasmlarni qoʻshing:

| Maydon | Tavsif |
|--------|--------|
| **Rasm** | JPG/PNG/WebP/GIF, maks 5 MB |
| **Izoh** | Rasm tagida koʻrinadigan matn |
| **ALT matn (SEO)** | Qidiruv tizimi va maxsus imkoniyatlar uchun tavsif |
| **Tartib raqami** | Koʻrsatish tartibi |

---

## Sertifikatlar

**Admin menyusi → Sayt mazmuni → Sertifikatlar**

Oʻquvchilar muvaffaqiyatlari va sertifikatlarini namoyish etish uchun.

| Maydon | Tavsif |
|--------|--------|
| **Sarlavha** | Sertifikat nomi (masalan: "Aziza R. — IELTS Band 7.0") |
| **Oʻquvchi ismi** | Sertifikat egasining ismi |
| **Izoh** | Qisqa tavsif (masalan: "IELTS Band 7.0", "Kimyo olimpiadasi gʻolibi") |
| **Belgi** | Qisqa yorliq (masalan: "IELTS", "SAT", "Gʻolib") |
| **Qizil belgi** | Belgilansa, urgʻu rangida koʻrsatiladi |
| **Rasm** | Sertifikat tasvirining surati — JPG/PNG/WebP/GIF, maks 5 MB |
| **PDF fayl** | Sertifikat PDF nusxasi — maks 10 MB |
| **Tashqi havola** | Masalan: Telegram kanal havolasi |

> **Diqqat:** Rasm, PDF yoki tashqi havoladan kamida bittasi kiritilishi **majburiy**.

---

## Ota-ona Fikrlari

**Admin menyusi → Sayt mazmuni → Fikrlar**

| Maydon | Tavsif |
|--------|--------|
| **Muallif** | Ismi (masalan: "Dildora opa") |
| **Roli** | Masalan: "Ona", "Ota · 8-sinf oʻquvchisining otasi" |
| **Fikr matni** | Asosiy sharh matni |
| **Rasm** | Muallif surati (ixtiyoriy) |
| **Baho (1–5)** | Reyting yulduzchalari |
| **Tanlangan** | Belgilansa, alohida ajratib koʻrsatilishi mumkin |

---

## Arizalar (Leads)

> **Holat: toʻliq ishlamoqda (Phase 3 tugallangan)**

**Admin menyusi → Murojaatlar → Arizalar**

Saytdagi `/ariza/` endpointiga yuborilgan barcha arizalar shu yerda saqlanadi.

### Ariza roʻyxati

Roʻyxatda quyidagi ustunlar koʻrinadi:

| Ustun | Tavsif |
|-------|--------|
| **Ism familiya** | Ariza yuborganning toʻliq ismi |
| **Telefon** | +998XXXXXXXXX formatida normallanadi |
| **Kurs** | Tanlangan kurs (ixtiyoriy) |
| **Holat** | `Yangi / Bogʻlanildi / Oʻquvchi boʻldi / Rad etildi` — roʻyxatda tahrirlanadi |
| **Telegram** | Bildirishnoma yuborilganmi — `Ha / Yoʻq` |
| **Vaqt** | Ariza kelib tushgan sana va soat |

### Sidebar badge

Chap menyu — **Murojaatlar → Arizalar** — yonida yangi (`Yangi` holatdagi) arizalar soni dinamik badge sifatida koʻrsatiladi. Barcha arizalar koʻrib chiqilgach, badge yoʻqoladi.

### Holat almashtirish

Arizani ochmasdan, roʻyxatdagi "Holat" ustunida to'gʻridan-toʻgʻri yangi holat tanlash mumkin. Masalan:

```
Yangi → Bogʻlanildi   (telefon qilinganda)
Bogʻlanildi → Oʻquvchi boʻldi   (yozilganda)
Bogʻlanildi → Rad etildi   (manfiy javob)
```

### Ariza manbasi

`Manba` maydoni (`source`) ariza qayerdan kelganini koʻrsatadi — UTM parametr yoki HTTP Referrer dan avtomatik toʻldiriladi. Bu reklama samaradorligini baholashda yordam beradi.

### Spam himoyasi

Sayt ikki usul bilan spam arizalardan himoyalangan:

| Usul | Tavsif |
|------|--------|
| **Honeypot** | Yashirin `website` maydoni — bot toʻldirsa, so jim rad etiladi (bazaga saqlanmaydi) |
| **IP rate-limit** | Bir IP dan 1 soat ichida 5 tadan ortiq ariza qabul qilinmaydi (HTTP 429) |

---

## Tashriflar analitikasi

> **Holat: qoʻshilmoqda (Phase 4)**

Admin panelidagi analitika boʻlimi saytga tashriflar statistikasini koʻrsatadi — hech qanday tashqi tracker (Google Analytics va h.k.) talab qilinmaydi, barchasi server tomonida yozib boriladi.

### Nima saqlanadi

Har bir sahifa koʻrishda quyidagi maʼlumotlar `VisitLog` jadvaliga yoziladi:

| Maydon | Tavsif |
|--------|--------|
| `ip_address` | Tashrif etuvchining IP manzili |
| `device_type` | `desktop`, `mobile`, `tablet` |
| `browser` | Brauzer nomi (Chrome, Firefox, Safari va h.k.) |
| `os` | Operatsion tizim (Windows, Android, iOS va h.k.) |
| `language` | Soʻralgan til: `uz`, `ru`, `en` |
| `path` | Koʻrilgan sahifa manzili |

Botlar, admin soʻrovlari va statik fayllar hisobga **olinmaydi**.

### Dashboard

Admin panelda analitika sahifasi quyidagilarni koʻrsatadi:

- Jami tashriflar (kunlik / haftalik / oylik)
- Qurilma turi boʻyicha taqsimot
- Eng koʻp koʻrilgan 10 ta sahifa
- Brauzer va OS statistikasi
- Til boʻyicha taqsimot

### Eski yozuvlarni tozalash

```bash
# 90 kundan eski yozuvlarni oʻchiradi (standart)
python manage.py prune_visitlogs

# 30 kundan eski yozuvlarni oʻchiradi
python manage.py prune_visitlogs --days 30
```

---

## SEO — qidiruv tizimlariga ulash

Bu boʻlim saytni qidiruv tizimlari uchun toʻgʻri sozlash boʻyicha amaliy koʻrsatma beradi.

---

### SiteConfig — global SEO maydonlari

**Admin menyusi → Sozlamalar → Sayt sozlamalari → SEO sozlamalari** boʻlimida global (barcha sahifalarga tegishli) maʼlumotlar saqlanadi.

> Bu maydonlar allaqachon "Sayt sozlamalari" boʻlimida jadval koʻrinishida keltirilgan. Quyida har birini qanday toʻldirish kerakligi tushuntiriladi.

#### SEO sarlavha va tavsif

| Maydon | Toʻldirish tartibi |
|--------|-------------------|
| **SEO sarlavha** (`seo_title`) | Sayt uchun umumiy sarlavha — bosh sahifada va boshqa sahifalarda alohida sarlavha kiritilmagan boʻlsa ishlatiladi. Maks 60 belgi. Misol: `Tagayev Methods — zamonaviy oʻquv markazi` |
| **SEO tavsif** (`seo_description`) | Qidiruv natijalarida tavsif matni. Maks 160 belgi. Misol: `Ingliz tili, matematika va boshqa fanlar boʻyicha kurslar.` |
| **OG rasm** (`og_image`) | Saytni ijtimoiy tarmoqlarda ulashganda koʻrinadigan umumiy rasm. Tavsiya etilgan oʻlcham: **1200 × 630 px**, JPG/PNG. |

**Meta sarlavha va tavsif fallback zanjiri:**

```
Sahifaga xos meta_title / meta_description
    → Kurs / Oʻqituvchi / Yangilik obyekti meta_title / meta_description
        → SiteConfig.seo_title / SiteConfig.seo_description
            → Standart qiymat
```

Yaʼni, SiteConfigni toʻliq kiritib qoʻysangiz, hech bir sahifa boʻsh meta bilan qolmaydi.

---

#### Webmaster tasdiqlash kodlari

Qidiruv tizimlari saytning egaligini tasdiqlash uchun maxsus `<meta>` teg ishlatadi. Kodni oʻsha platformadan koʻchirib **Sayt sozlamalari → SEO sozlamalari** ga kiriting.

##### Google Search Console

1. [Google Search Console](https://search.google.com/search-console/) ga kiring → **Mulk qoʻshish** → domenni kiriting.
2. Tasdiqlash usuli sifatida **"HTML tegi"** ni tanlang.
3. Koʻrsatilgan `content="..."` qiymatini (masalan, `abc123xyz`) koʻchiring.
4. Admin panelda **"Google verification"** maydoniga faqat `content` qiymatini (tirnoqsiz) kiriting.
5. Google Consoleda **"Tasdiqlash"** tugmasini bosing.

##### Yandex Webmaster

1. [Yandex Webmaster](https://webmaster.yandex.ru/) ga kiring → **"Sayt qoʻshish"** → domenni kiriting.
2. Tasdiqlash usuli sifatida **"Meta-teg"** ni tanlang.
3. `content="..."` qiymatini koʻchiring.
4. Admin panelda **"Yandex verification"** maydoniga kiriting.
5. Yandex Webmasterde **"Tekshirish"** tugmasini bosing.

##### Bing Webmaster

1. [Bing Webmaster Tools](https://www.bing.com/webmasters/) ga kiring → **"Sayt qoʻshish"** → domenni kiriting.
2. Tasdiqlash usuli sifatida **"HTML Meta-teg"** ni tanlang.
3. `content="..."` qiymatini koʻchiring.
4. Admin panelda **"Bing verification"** maydoniga kiriting.
5. Bing da **"Verify"** tugmasini bosing.

---

#### Analitika ID lari

Tashqi tracker skriptlari faqat ID kiritilganda sahifaga qoʻshiladi — boʻsh qolsa hech qanday skript yuklanmaydi.

| Maydon | Format | Qayerdan olinadi |
|--------|--------|-----------------|
| **GA4 oʻlchov ID** (`ga4_measurement_id`) | `G-XXXXXXXXXX` | [Google Analytics](https://analytics.google.com/) → Admin → Maʼlumotlar oqimi → Oʻlchov ID |
| **Yandex Metrica ID** (`yandex_metrica_id`) | Raqam (masalan: `98765432`) | [Yandex Metrica](https://metrica.yandex.ru/) → Schetchik sozlamalari → Schetchik raqami |

---

### Kurs, Oʻqituvchi va Yangilik — obyekt SEO maydonlari

Har bir kurs, oʻqituvchi va yangilik sahifasi uchun alohida meta maʼlumot kiritish mumkin. Bu SiteConfig umumiy maʼlumotlaridan ustunlik qiladi.

| Maydon | Qayerda | Tavsif |
|--------|---------|--------|
| **SEO sarlavha** (`meta_title`) | Kurs / Oʻqituvchi / Yangilik formasi | Sahifa `<title>` va OG sarlavhasi uchun. Maks 60 belgi |
| **SEO tavsif** (`meta_description`) | Kurs / Oʻqituvchi / Yangilik formasi | Qidiruv natijasi annotatsiyasi. Maks 160 belgi |

Boʻsh qoldirilsa, fallback zanjiri ishga tushadi (yuqorida keltirilgan).

---

### sitemap.xml — qidiruv tizimlarga yuborish

Sitemap avtomatik generatsiya qilinadi. Uni qidiruv tizimlarda roʻyxatga olish bir marta bajariladi:

**Sitemap manzili:** `https://DOMEN/sitemap.xml`

(Domen — SiteConfig → Brending → **Domen** maydonidan olinadi.)

#### Google Search Console orqali yuborish

1. Saytni yuqoridagi koʻrsatma bilan tasdiqlang.
2. Chap menyu → **"Indeksatsiya" → "Sitemaplar"** ga oʻting.
3. **"Yangi sitemap qoʻshish"** maydoniga `sitemap.xml` kiriting → **"Yuborish"**.
4. Holat: `Muvaffaqiyatli` boʻlganda sitemap qabul qilingan.

#### Yandex Webmaster orqali yuborish

1. Saytni tasdiqlang.
2. Chap menyu → **"Indeksatsiya" → "Sitemap fayllari"** ga oʻting.
3. **"Fayl qoʻshish"** → toʻliq URL ni kiriting (masalan, `https://tagayev.uz/sitemap.xml`) → **"Qoʻshish"**.

#### Bing Webmaster orqali yuborish

1. Saytni tasdiqlang.
2. Chap menyu → **"Sitemaps"** ga oʻting.
3. Sitemap URL ni kiriting → **"Submit"**.

> **Eslatma:** Sitemap tarkibi yangilanganida (yangi kurs yoki yangilik qoʻshilganda) qidiruv tizimlari uni avtomatik qayta tekshiradi. Qoʻlda qayta yuborish shart emas.

---

## Uch Til bilan Ishlash

Sayt uch tilda ishlaydi: **oʻzbek (uz)**, **rus (ru)** va **ingliz (en)**.

### Kontent maydonlari

Matn kiritish maydonlari admin formada uch guruhga ajratilgan:

```
[ uz tab ]  [ ru tab ]  [ en tab ]
```

Har bir tabda oʻsha til uchun matn kiritiladi. Masalan, kurs nomini uch tilda kiritish:

- **uz tab:** "Ingliz tili"
- **ru tab:** "Английский язык"
- **en tab:** "English Language"

Agar biror til uchun maydon boʻsh qolsa, standart til (oʻzbekcha) matn koʻrsatiladi.

### URL prefikslari

| URL | Til |
|-----|-----|
| `/uz/` | Oʻzbekcha |
| `/ru/` | Ruscha |
| `/en/` | Inglizcha |

### Til almashtirgich

Saytdagi til almashtirgich `POST /i18n/set_language/` endpointiga asoslangan. Bu URL URL prefikslari (`i18n_patterns`) dan tashqarida joylashgan, shuning uchun har qanday sahifadan til almashtirish ishlaydi.

### Interfeys tarjimasi haqida

Sahifa **kontenti** tanlangan tilda koʻrsatiladi (admindan kiritilgan). **Interfeys matnlari** (navigatsiya, tugmalar va h.k.) `locale/ru` va `locale/en` dagi `.po/.mo` fayllari orqali tarjima qilinadi — bu jarayon hozir yakunlanmoqda.

Tarjima fayllarini kompilatsiya qilish uchun qarang: [`ORNATISH.md`](ORNATISH.md#tarjima-fayllarini-kompilatsiya-qilish).

---

## CKEditor — Boy Matn Muharriri

CKEditor 5 quyidagi kontentlar uchun ishlatiladi:
- Kurs toʻliq tavsifi
- Oʻqituvchi bio
- Yangilik tana qismi
- "Biz haqimizda" matni

### Imkoniyatlar

| Funksiya | Tavsif |
|----------|--------|
| **Sarlavhalar** | H1, H2, H3 darajali sarlavhalar |
| **Qalin / kursiv / tagiga chizilgan** | Urgʻu berish |
| **Havola** | Tashqi va ichki havolalar |
| **Roʻyxat** | Nuqtali va raqamli roʻyxatlar |
| **Iqtibos** | Block quote |
| **Rasm yuklash** | Bevosita muharrirga rasm yuklash |
| **Bekor qilish / qaytarish** | Ctrl+Z / Ctrl+Y |

### Rasm yuklash chegaralari (CKEditor orqali)

- Faqat `staff` (xodim) maqomidagi foydalanuvchilar rasm yuklay oladi
- Ruxsat etilgan formatlar: **JPG, JPEG, PNG, WebP, GIF**
- Maksimal hajm: **5 MB**

---

## Tartiblashtirish va Yashirish

### Tartib raqami

Har bir kontent modelida "**Tartib raqami**" maydoni bor:

- **0** — eng yuqorida koʻrsatiladi
- **10, 20, 30...** — pastroqda koʻrsatiladi
- Bir xil raqam boʻlsa, yaratilgan vaqtga koʻra tartiblanadi

Masalan, kurslarni tartiblashtirish uchun "Ingliz tili"ga `0`, "Matematika"ga `1`, "Kimyo"ga `2` kiriting.

### Yashirish (oʻchirmasdan)

"**Saytda koʻrsatilsin**" belgisini olib tashlang — element bazadan oʻchirilmaydi, faqat saytda koʻrinmaydi. Keyinchalik qayta yoqish mumkin.

### Roʻyxatda tezkor amallar

Admin roʻyxat sahifasida elementni tanlagan holda:
- **Yashirish** — tanlangan elementlarni bir anda yashirish
- **Koʻrsatish** — tanlangan elementlarni bir anda yoqish
- **Oʻchirish** — doimiy oʻchirish (ehtiyot boʻling!)

---

## Tez-tez beriladigan savollar

**Kontent oʻzgarishlar saytda darhol koʻrinmaydimi?**
Ha, saqlashdan soʻng darhol yangilanadi. Kesh muammosi boʻlsa brauzerda Ctrl+F5 bosing.

**Logoni qanday almashtiriladi?**
Sayt sozlamalari → Brending → Logo → fayl yuklang → Saqlang.

**Yangi foydalanuvchi (admin) qanday yaratiladi?**
Admin paneli → Sozlamalar → Foydalanuvchilar → Qoʻshish. "Xodim maqomi" va "Superuser maqomi" kataglarini belgilang.

**Kontent oʻchib ketgan, qaytarish mumkinmi?**
Har bir elementning "Tarix" sahifasida oldingi versiyalarni koʻrish mumkin, lekin avtomatik tiklash funksiyasi hozircha yoʻq. Muhim oʻzgarishlardan oldin bazani zahiralang.

**Telegram bildirishnomalar kelmayapti?**
Quyidagilarni tekshiring: (1) **Sayt sozlamalari → Telegram** da bot tokeni kiritilganmi va "**Telegram bildirishnomalari yoniq**" katagi belgilanganmi; (2) **Telegram qabul qiluvchilar** da kamida bitta **Faol** yozuv borligi va uning **Chat ID** si toʻgʻriligi; (3) har bir admin avval botga `/start` yozgan boʻlishi shart — aks holda Telegram botga oʻsha foydalanuvchiga yozishga ruxsat bermaydi. Xato hollarda server loglarini koʻring.
