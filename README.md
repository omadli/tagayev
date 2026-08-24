# Tagayev Methods — Oʻquv Markazi Sayti

[![CI/CD](https://github.com/omadli/tagayev/actions/workflows/deploy.yml/badge.svg)](https://github.com/omadli/tagayev/actions/workflows/deploy.yml)
[![Tests](https://img.shields.io/badge/tests-286%20passing-brightgreen)](https://github.com/omadli/tagayev/actions/workflows/deploy.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4-38BDF8?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
![i18n](https://img.shields.io/badge/i18n-uz%20%7C%20ru%20%7C%20en-1E88E5)
![Node.js](https://img.shields.io/badge/Node.js-talab%20qilinmaydi-success)

> **Zamonaviy taʼlim markazi landing sayti.**
> Toʻliq admin-boshqaruv, 3 til (oʻzbek / rus / ingliz), avtomatik tarjima, analitika va bir tugmali deploy — **Node.js talab qilinmaydi**.

---

## Mundarija

1. [Loyiha haqida](#loyiha-haqida)
2. [Imkoniyatlar](#imkoniyatlar)
3. [Texnologiyalar](#texnologiyalar)
4. [Talablar](#talablar)
5. [Oʻrnatish](#ornatish)
6. [Muhit oʻzgaruvchilari](#muhit-ozgaruvchilari)
7. [Management buyruqlari](#management-buyruqlari)
8. [Loyiha tuzilishi](#loyiha-tuzilishi)
9. [Arizalar va Telegram](#arizalar-va-telegram)
10. [Auto-tarjima (mashina tarjimasi)](#auto-tarjima-mashina-tarjimasi)
11. [Sertifikatlar va CEFR import](#sertifikatlar-va-cefr-import)
12. [Tashriflar va Analitika](#tashriflar-va-analitika)
13. [SEO](#seo)
14. [i18n / Tarjima](#i18n--tarjima)
15. [Media xavfsizligi va CKEditor](#media-xavfsizligi-va-ckeditor)
16. [Tezlik, rasm optimizatsiyasi va accessibility](#tezlik-rasm-optimizatsiyasi-va-accessibility)
17. [CI/CD](#cicd)
18. [Deployment](#deployment)
19. [Hujjatlar](#hujjatlar)

---

## Loyiha haqida

**Tagayev Methods** — oʻquv markazi uchun yaratilgan reklama/landing veb-sayt. Sayt potentsial oʻquvchilar va ota-onalarga markaz haqida toʻliq maʼlumot beradi va ariza topshirish imkonini yaratadi.

Asosiy xususiyatlar:

- **Reklama maqsadida** — kurslar, oʻqituvchilar, muvaffaqiyatlar, sertifikatlar va ota-onalar fikrlari orqali markazni taqdim etadi.
- **3 til** — oʻzbek (standart), rus va ingliz tillari qoʻllab-quvvatlanadi; har bir kontent admin paneldan alohida kiritiladi yoki bir tugma bilan avtomatik tarjima qilinadi.
- **Toʻliq CMS-boshqaruv** — Django Unfold admin paneli orqali texnik bilimisiz barcha kontent, sozlamalar va arizalar boshqariladi.
- **Production-ga tayyor** — GitHub Actions CI/CD (test + avtomatik deploy), gunicorn + nginx + systemd + Certbot konfiguratsiyasi va uch qatlamli DDoS/rate-limit himoyasi tayyor holatda keladi.

> **Holat:** barcha asosiy bosqichlar tugallangan — **286 ta avtomatlashtirilgan test** yashil (`python manage.py test`).

---

## Imkoniyatlar

| # | Imkoniyat | Holat | Tavsif |
|---|-----------|-------|--------|
| 1 | **Kurslar** | ✓ Tayyor | Toifalar bilan kurslar roʻyxati, har bir kurs uchun batafsil sahifa; narx, guruh hajmi, CKEditor tavsif |
| 2 | **Oʻqituvchilar** | ✓ Tayyor | Profil sahifasi, tajriba yillari, fanlar, ijtimoiy tarmoq havolalari |
| 3 | **Galereya** | ✓ Tayyor | Albomlar tizimi, har bir albomda cheksiz rasm; ALT matn (SEO) |
| 4 | **Yangiliklar va eʼlonlar** | ✓ Tayyor | Maqolalar, badge/tag, muqova rasm, chop etish sanasi, SEO meta |
| 5 | **Sertifikatlar (CEFR)** | ✓ Tayyor | Oʻquvchi yutuqlari — rasm, PDF yoki tashqi havola; CEFR sertifikatlarini PDFdan ommaviy import qilish |
| 6 | **Ota-ona fikrlari** | ✓ Tayyor | Sharh matn, rasm, reyting (1–5), tanlangan belgi |
| 7 | **Statistika bloklari** | ✓ Tayyor | Admin paneldan boshqariladigan raqamlar (oʻquvchilar soni, yoʻnalishlar va h.k.) |
| 8 | **"Nega biz" bloklari** | ✓ Tayyor | Ikonkali afzallik kartalari, admin orqali tartiblanadi |
| 9 | **Ariza formasi + Telegram** | ✓ Tayyor | `/ariza/` → DB → admin "Murojaatlar → Arizalar" + sidebar badge; Telegram bot bildirishnoma; honeypot + IP rate-limit spam himoyasi |
| 10 | **Auto-tarjima (uz → ru/en)** | ✓ Tayyor | Admindan bir tugma bilan boʻsh ru/en maydonlarini avtomatik toʻldirish; HTML (CKEditor) teglari saqlanadi; inson tekshirib saqlaydi |
| 11 | **Tashriflar hisobi (Analitika)** | ✓ Tayyor | VisitLog middleware, KPI dashboard, Geo-IP (davlat boʻyicha), `prune_visitlogs` va `resolve_geoip` buyruqlari |
| 12 | **SEO** | ✓ Tayyor | `sitemap.xml` (3 til, hreflang); `robots.txt`; canonical + hreflang (uz/ru/en + x-default); meta fallback zanjiri; Open Graph + Twitter Card; JSON-LD; GA4 + Yandex Metrica; webmaster tasdiqlash teglari |
| 13 | **Xaritadan joylashuv tanlash** | ✓ Tayyor | Admin panelda interaktiv Leaflet xarita — belgi bosish yoki manzil qidirish orqali koordinatalar avtomatik toʻladi; Google va Yandex xaritalar shu koordinatalardan quriladi |
| 14 | **Kunduzgi/tungi rejim** | ✓ Tayyor | LocalStorage + `prefers-color-scheme` orqali flash-siz mavzu almashish |
| 15 | **CKEditor 5 rich-text** | ✓ Tayyor | Admin kontent maydonlarida formatlash, rasm yuklash (faqat `staff`) |
| 16 | **Media xavfsizligi** | ✓ Tayyor | Rasm: jpg/jpeg/png/webp/gif, maks 5 MB; PDF: 10 MB; serverda validatsiya |
| 17 | **Tezlik va optimizatsiya** | ✓ Tayyor | WebP responsive rasmlar (`easy_thumbnails`, `<picture>`), `loading="lazy"`, `width`/`height` (CLS), shrift preconnect + `font-display: swap`, JS defer, Core Web Vitals maqsadlari |
| 18 | **Accessibility (a11y)** | ✓ Tayyor | Skip-to-content havolasi + `id="main"`, `:focus-visible`, `prefers-reduced-motion` |
| 19 | **Admin URL yashirish** | ✓ Tayyor | `ADMIN_URL` orqali login sahifasini oddiy `/admin/` yoʻlidan chetlatish; ushbu URL analitikada ham hisobga olinmaydi |
| 20 | **DDoS / rate-limit himoyasi** | ✓ Tayyor | Uch qatlam: ilova (honeypot + IP rate-limit), nginx (`limit_req`/`limit_conn`), fail2ban (IP bloklash); tayyor configlar `deploy/` da |
| 21 | **CI/CD** | ✓ Tayyor | GitHub Actions — har push/PR da test; `main` ga push da testlar oʻtsa SSH orqali avtomatik deploy |

---

## Texnologiyalar

| Kutubxona | Versiya | Maqsad |
|-----------|---------|--------|
| `Django` | `>=5.2, <5.3` | Asosiy freymvork |
| `django-environ` | `>=0.11` | `.env` faylidan muhit oʻzgaruvchilari |
| `django-unfold` | `>=0.40` | Zamonaviy Django admin paneli |
| `django-import-export` | `>=4.0` | Admindan CSV/Excel import-export |
| `django-modeltranslation` | `>=0.19` | Model maydonlarini 3 tilda saqlash |
| `polib` | `>=1.2` | `.po` → `.mo` (GNU gettext talab qilinmaydi) |
| `deep-translator` | `>=1.11` | Auto-tarjima backend (bepul Google, API kalit shart emas) |
| `beautifulsoup4` | `>=4.12` | HTML (CKEditor) ni teg-xavfsiz tarjima qilish |
| `django-ckeditor-5` | `>=0.2.18` | Rich-text muharrir (admin) |
| `django-solo` | `>=2.4` | Yagona qator modellar (SiteConfig) |
| `Pillow` | `>=10.4` | Rasm qayta ishlash |
| `easy-thumbnails` | `>=2.10` | Responsive WebP miniatyuralar |
| `pypdfium2` | `>=4.30` | CEFR PDFni rasmga render qilish (Apache/BSD — AGPL emas) |
| `pypdf` | `>=4.3` | CEFR PDFdan matn (ism) ajratib olish |
| `requests` | `>=2.32` | Telegram API, Geo-IP va tashqi soʻrovlar |
| `user-agents` | `>=2.2.0` | Foydalanuvchi agentini tahlil qilish (Analitika) |
| `django-tailwind-cli` | `>=2.20` | Tailwind CSS v4 (Node.js talab qilinmaydi) |
| `whitenoise` | `>=6.7` | Statik fayllarni samarali xizmat qilish |
| `gunicorn` | `>=23.0` | Production WSGI server |
| `tzdata` | — | Windows uchun vaqt zonalari |

**Baza:** SQLite (WAL rejimi — parallel yozuvlarga bardoshli; kichik/oʻrta trafik uchun yetarli, Redis talab qilinmaydi).

---

## Talablar

- **Python 3.11+** (CI quvuri **3.14** da test qiladi)
- **Git**
- **Node.js talab qilinmaydi** — Tailwind CSS v4 standalone CLI avtomatik yuklab olinadi

---

## Oʻrnatish

> Quyidagi qadamlar **lokal / development** muhiti uchun. Production serverga joylashtirish uchun [`docs/JOYLASHTIRISH.md`](docs/JOYLASHTIRISH.md) ga qarang.

### 1. Repozitoriyani klonlash

```bash
git clone https://github.com/omadli/tagayev.git
cd tagayev
```

### 2. Virtual muhit yaratish va aktivlashtirish

```powershell
# Windows (PowerShell)
python -m venv venv
venv\Scripts\activate
```

```bash
# Linux / macOS
python -m venv venv
source venv/bin/activate
```

### 3. Kerakli paketlarni oʻrnatish

```bash
pip install -r requirements.txt
```

### 4. Muhit faylini sozlash

```bash
copy .env.example .env      # Windows
# yoki
cp .env.example .env        # Linux / macOS
```

Keyin `.env` faylini oching va qiymatlarni toʻldiring (quyidagi [jadvalga](#muhit-ozgaruvchilari) qarang).

### 5. Migratsiyalar va cache jadvali

```bash
python manage.py migrate
python manage.py createcachetable   # ariza rate-limiti uchun umumiy cache jadvali
```

### 6. Superuser yaratish

```bash
python manage.py createsuperuser
```

### 7. Tailwind CSS qurilishi

```bash
python manage.py tailwind build
```

> Birinchi ishga tushirishda Tailwind CLI binari avtomatik yuklab olinadi (~5 MB).

### 8. Development serverini ishga tushirish

```bash
python manage.py runserver 127.0.0.1:8001
```

Sayt: [http://127.0.0.1:8001](http://127.0.0.1:8001)
Admin: [http://127.0.0.1:8001/admin/](http://127.0.0.1:8001/admin/)

### 9. Kontentni toʻldirish

Baza boʻsh holda keladi. Kurslar, oʻqituvchilar, yangiliklar, galereya,
sertifikatlar va sayt matnlari **faqat admin panel** orqali kiritiladi
(`/admin/`). Demo/seed buyrugʻi yoʻq.

---

## Muhit oʻzgaruvchilari

`.env` faylida quyidagi oʻzgaruvchilar ishlatiladi (toʻliq roʻyxat va izohlar `.env.example` da):

| Oʻzgaruvchi | Majburiy | Standart | Tavsif |
|-------------|----------|----------|--------|
| `DEBUG` | Yoʻq | `True` | Development uchun `True`, production uchun `False` |
| `SECRET_KEY` | **Ha** | — | Django maxfiy kaliti; `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` bilan generatsiya qiling |
| `ALLOWED_HOSTS` | **Ha** | `*` | Vergul bilan ajratilgan domenlar, masalan: `tagayev.uz,www.tagayev.uz` |
| `CSRF_TRUSTED_ORIGINS` | Production | — | HTTPS manzillar, masalan: `https://tagayev.uz` |
| `ADMIN_URL` | Yoʻq | `admin` | Admin panel URL prefiksi — productionda topish qiyin qiymat qoʻying (masalan, `boshqaruv-7x3k`) |
| `TRUSTED_PROXY_COUNT` | Yoʻq | `1` | Oldindagi proksi soni: nginx=`1`, Cloudflare bilan `2` (rate-limit haqiqiy mijoz IP sini oladi) |
| `TELEGRAM_BOT_TOKEN` | Yoʻq | — | **Zaxira** Telegram bot tokeni (asosiysi admin paneldan kiritiladi). Panel boʻsh boʻlsa ishlatiladi |
| `TELEGRAM_ADMIN_CHAT_ID` | Yoʻq | — | **Zaxira** chat/guruh ID si (asosiysi *Telegram qabul qiluvchilar* boʻlimidan boshqariladi) |
| `SECURE_SSL_REDIRECT` | Yoʻq | `True` (`DEBUG=False`) | Barcha HTTPni HTTPS ga yoʻnaltirish |
| `SECURE_HSTS_SECONDS` | Yoʻq | `31536000` | HSTS muddati; birinchi HTTPS deployda `3600` qoʻying, barqarorlashgach 1 yilga koʻtaring |
| `DJANGO_LOG_LEVEL` | Yoʻq | `INFO` | Log darajasi (DEBUG/INFO/WARNING/ERROR) |
| `GUNICORN_WORKERS` | Yoʻq | `3` | gunicorn worker soni (SQLite uchun 2–3 yetarli) |

> **Telegram:** Bot tokeni va qabul qiluvchi adminlar endi **admin paneldan** boshqariladi (*Sayt sozlamalari → Telegram* va *Telegram qabul qiluvchilar*). Yuqoridagi `.env` qiymatlari faqat panel boʻsh boʻlsa zaxira sifatida ishlatiladi.

> **Xavfsizlik bloki:** `DEBUG=False` boʻlganda `settings.py` agar `SECRET_KEY` hali ham dev qiymatida boʻlsa yoki `ALLOWED_HOSTS=*` boʻlsa, ataylab **ishga tushishdan bosh tortadi** — xavfli sozlama bilan deploy boʻlib qolmaslik uchun.

**Namuna `.env` (production):**

```env
DEBUG=False
SECRET_KEY=your-very-secret-key-here
ALLOWED_HOSTS=tagayev.uz,www.tagayev.uz
CSRF_TRUSTED_ORIGINS=https://tagayev.uz,https://www.tagayev.uz
ADMIN_URL=boshqaruv-7x3k
TELEGRAM_BOT_TOKEN=1234567890:AAFxxxxxxxxxxxxxx
TELEGRAM_ADMIN_CHAT_ID=-1001234567890
```

---

## Management buyruqlari

| Buyruq | Tavsif |
|--------|--------|
| `python manage.py tailwind build` | Tailwind CSS faylini yaratadi (production uchun) |
| `python manage.py tailwind watch` | CSS oʻzgarishlarini kuzatadi (development uchun) |
| `python manage.py tailwind runserver` | `watch` + `runserver` birgalikda ishga tushiradi |
| `python manage.py migrate` | Migratsiyalarni qoʻllaydi |
| `python manage.py createcachetable` | Rate-limit uchun umumiy cache jadvalini yaratadi |
| `python manage.py createsuperuser` | Admin foydalanuvchi yaratadi |
| `python manage.py collectstatic` | Statik fayllarni `staticfiles/` ga yigʻadi (production) |
| `python manage.py makemessages -l ru -l en` | `ru` va `en` uchun `.po` fayllarini yaratadi/yangilaydi |
| `python manage.py compilemo` | `.po` → `.mo` fayllarini `polib` bilan kompilatsiya qiladi (GNU `gettext` talab qilinmaydi) |
| `python manage.py prune_visitlogs` | Eski tashrif yozuvlarini oʻchiradi — `--days N` parametri bilan |
| `python manage.py resolve_geoip` | VisitLog IP larini davlatga aylantiradi (dashboarddagi "Davlatlar" paneli uchun) |
| `python manage.py import_cefr` | CEFR sertifikatlarini PDF/URL roʻyxatidan import qiladi (`--file` parametri) |

> **`.mo` kompilatsiyasi:** GNU `msgfmt` (gettext) Windows va serverda mavjud emas, shuning uchun standart `compilemessages` ishlamaydi. Buning oʻrniga `manage.py compilemo` ishlating — u `polib` (requirements.txt'da) yordamida barcha `locale/**/*.po` fayllarini `.mo` ga aylantiradi.

---

## Loyiha tuzilishi

```
tagayev/
├── config/                  # Django konfiguratsiyasi
│   ├── settings.py          #   Asosiy sozlamalar (i18n, DB, Tailwind, Unfold, xavfsizlik, TELEGRAM)
│   ├── urls.py              #   URL marshrutlar (i18n_patterns + /ariza/ + /i18n/ + ADMIN_URL)
│   └── wsgi.py              #   WSGI entry point
│
├── apps/                    # Django ilovalar
│   ├── common/              #   Abstract modellar, validators, context_processors, auto-tarjima
│   ├── siteconfig/          #   Sayt sozlamalari (singleton): logo, kontakt, xarita, SEO, analitika
│   ├── pages/               #   Bosh sahifa bloklari: "Biz haqimizda", statistika, "Nega biz"
│   ├── courses/             #   Kurslar va toifalar, kurs detail sahifasi
│   ├── teachers/            #   Oʻqituvchilar profili va detail sahifasi
│   ├── gallery/             #   Galereya albomlari va rasmlari
│   ├── testimonials/        #   Ota-ona fikrlari
│   ├── news/                #   Yangiliklar va eʼlonlar
│   ├── certificates/        #   Sertifikatlar (rasm/PDF/tashqi havola) + CEFR import
│   ├── leads/               #   Ariza formasi, Lead modeli, Telegram signal, sidebar badge
│   └── analytics/           #   VisitLog, middleware, Geo-IP, dashboard, prune/resolve buyruqlari
│
├── templates/               # Django shablonlar
│   ├── base.html            #   Asosiy shablon (dark mode, toast, modal)
│   └── partials/            #   Header, footer, modal, mobile bar
│
├── deploy/                  # Production konfiguratsiya fayllari
│   ├── tagayev.service   #   gunicorn systemd unit
│   ├── gunicorn.conf.py     #   gunicorn sozlamalari (unix socket, workers)
│   ├── tagayev.uz.conf   #   nginx sayt konfiguratsiyasi
│   ├── nginx-ratelimit.conf #   nginx rate-limit / connection zonalari
│   ├── resolve-geoip.*      #   Geo-IP systemd service + timer (30 daq.)
│   └── fail2ban/            #   fail2ban filter + jail (429 spam IP bloklash)
│
├── static/                  # Statik fayllar (JS, rasm, ikonkalar)
├── assets/css/              # Tailwind manba CSS (source.css → tailwind.css)
├── locale/                  # .po/.mo tarjima fayllari (ru, en)
├── docs/                    # Qoʻllanmalar (ORNATISH, ADMIN, JOYLASHTIRISH)
├── media/                   # Yuklangan media fayllar (gitignore)
├── staticfiles/             # collectstatic chiqishi (gitignore)
├── .github/workflows/       # CI/CD (deploy.yml)
├── .env.example             # Muhit namuna fayli
├── requirements.txt         # Python bogʻliqliklar
└── manage.py
```

---

## Arizalar va Telegram

> **Holat: tayyor**

### Ish tartibi

```
Saytdagi ariza formasi  →  POST /ariza/
        │
        ├─ Honeypot tekshiruvi   (bot bo'lsa — 200 OK, lekin saqlanmaydi)
        ├─ IP rate-limit         (1 soatda max 5 ariza — 429 qaytariladi)
        ├─ Forma validatsiyasi   (ismi, +998XXXXXXXXX formati)
        │
        ├─ Lead bazaga saqlanadi
        │       (full_name, phone, course, message, source, status=new)
        │
        └─ post_save signal → transaction.on_commit → daemon thread
                └─ Telegram API: sendMessage (HTML parse_mode)
```

### Admin panel

- **Murojaatlar → Arizalar** — yangi arizalar roʻyxati
- **Sidebar badge** — yangi (holati `new`) arizalar soni dinamik koʻrsatiladi
- Holat ustuni roʻyxatda to'gʻridan-to'gʻri tahririlanadi: `Yangi → Bogʻlanildi → Oʻquvchi boʻldi → Rad etildi`
- `source` maydoni UTM parametr yoki HTTP Referrer dan avtomatik toʻldiriladi

### Telegram bildirishnoma sozlash

Hammasi **admin paneldan** sozlanadi (`.env` shart emas):

1. **Sayt sozlamalari → Telegram** — "**Telegram bot tokeni**" maydoniga `@BotFather` tokenini kiriting va "**Telegram bildirishnomalari yoniq**" katagini belgilang.
2. **Telegram qabul qiluvchilar** — arizalarni qabul qiladigan har bir admin uchun yozuv qoʻshing (**Nomi** + **Chat ID**). Bir nechta admin qoʻshish mumkin — ariza har bir **Faol** qabul qiluvchiga yuboriladi. Chat ID ni bilish uchun admin botga `/start` yozadi, soʻng [@userinfobot](https://t.me/userinfobot) orqali koʻradi.

> **Zaxira:** Panel boʻsh boʻlsa, server `.env` dagi `TELEGRAM_BOT_TOKEN` / `TELEGRAM_ADMIN_CHAT_ID` qiymatlaridan foydalanadi (eski deploylar bilan moslik uchun).

Agar na panelda, na `.env` da token/chat ID koʻrsatilgan boʻlsa, bildirishnoma yuborilmaydi — ariza baribir bazaga saqlanadi.

### Spam himoyasi

| Usul | Tavsif |
|------|--------|
| **Honeypot** | Yashirin `website` maydoni — real foydalanuvchilar toʻldirmaydi, botlar toʻldiradi; so jim rad etiladi |
| **IP rate-limit** | Bir IP manzilidan 1 soat ichida 5 tadan ortiq ariza qabul qilinmaydi (umumiy DatabaseCache asosida — barcha worker'lar boʻylab toʻgʻri ishlaydi) |
| **Telefon validatsiyasi** | Faqat `+998XXXXXXXXX` formatidagi raqamlar qabul qilinadi |

> Ilova darajasidagi bu himoya nginx (`limit_req`) va fail2ban bilan birga **uch qatlamli** DDoS himoyasini tashkil qiladi — qarang: [`docs/JOYLASHTIRISH.md → DDoS va rate-limit himoyasi`](docs/JOYLASHTIRISH.md#ddos-va-rate-limit-himoyasi).

---

## Auto-tarjima (mashina tarjimasi)

> **Holat: tayyor**

Kontentni uchta tilda qoʻlda yozish oʻrniga, oʻzbekcha (standart) maydonni toʻldirib, **admindan bir tugma bilan** boʻsh rus va ingliz maydonlarini avtomatik toʻldirish mumkin.

| Xususiyat | Tavsif |
|-----------|--------|
| **Manba** | Har doim oʻzbekcha (`MODELTRANSLATION_DEFAULT_LANGUAGE`) → ru/en ga tarjima qilinadi |
| **Backend** | `deep-translator` (bepul Google) — API kalit shart emas; bitta funksiyani almashtirib LLM/pulli APIga oʻtish mumkin |
| **HTML xavfsizligi** | CKEditor maydonlari `beautifulsoup4` orqali **node-ma-node** tarjima qilinadi — teglar va atributlar buzilmaydi |
| **Tezlik** | Tanlangan koʻp qatorlar uchun soʻrovlar thread-pool da parallel ketadi va bir xil matnlar (badge, "soʻm/oy" va h.k.) faqat bir marta tarjima qilinadi |
| **Inson nazorati** | Tarjima faqat admin amali bilan ishlaydi, render vaqtida emas; admin **tekshirib saqlaydi** (boʻsh maydonlar ustiga yozadi, mavjudini buzmaydi) |
| **Generiklik** | `modeltranslation` ga roʻyxatdan oʻtgan **har bir** model avtomatik qamrab olinadi — yangi modellar qoʻshilsa, alohida kod talab qilinmaydi |

> Agar tarjima yarim qolsa (ba'zi maydon boʻsh), admin tahrirlash sahifasida toʻldirilmagan maydonlar haqida ogohlantirish koʻrsatiladi.

---

## Sertifikatlar va CEFR import

> **Holat: tayyor**

Oʻquvchi yutuqlari (sertifikatlar) admin paneldan rasm, PDF yoki tashqi havola koʻrinishida qoʻshiladi. CEFR (ingliz tili darajasi) sertifikatlarini esa **ommaviy import** qilish mumkin.

- **PDF → rasm:** har bir CEFR PDF `pypdfium2` (Apache/BSD litsenziya — AGPL `PyMuPDF` emas) bilan rasmga render qilinadi va `media/` ga saqlanadi.
- **Ism ajratish:** `pypdf` PDF matnidan oʻquvchi ismini ajratib oladi.
- **Manba roʻyxati:** URL/fayllar `cefr_urls.txt` dan oʻqiladi (`--file` bilan boshqa yoʻl berish mumkin).

```bash
python manage.py import_cefr                       # cefr_urls.txt dan o'qiydi
python manage.py import_cefr --file /path/urls.txt # boshqa fayldan
```

> **Maxfiylik:** `cefr_urls.txt` va render qilingan rasmlar **gitignore** qilingan — real oʻquvchi maʼlumotlari (ism/rasm) repozitoriyada saqlanmaydi. Faylni serverga qoʻlda koʻchiring va import buyrugʻini oʻsha yerda ishlating.

---

## Tashriflar va Analitika

> **Holat: tayyor**

`apps/analytics` ilovasi tashrif hisobini **middleware** darajasida olib boradi — hech qanday JavaScript tracker talab qilinmaydi.

### VisitLog modeli

Har bir saytga kirishda quyidagi maʼlumotlar saqlanadi:

| Maydon | Tavsif |
|--------|--------|
| `ip_address` | Tashrif etuvchining IP manzili (X-Forwarded-For oxiridan, anti-spoof) |
| `country` | IP dan aniqlangan davlat (`resolve_geoip` buyruq ishlagach toʻladi) |
| `device_type` | Qurilma turi: desktop / mobile / tablet |
| `browser` | Brauzer nomi (user-agents kutubxonasi orqali) |
| `os` | Operatsion tizim |
| `language` | Soʻralgan til (URL prefiksi asosida: uz/ru/en) |
| `path` | Koʻrilgan sahifa manzili |
| `created_at` | Tashrif vaqti (Asia/Tashkent) |

### Middleware filtrlash

Middleware quyidagi soʻrovlarni **hisobga olmaydi**:

- **`DEBUG=True` (development) rejimidagi barcha soʻrovlar** — lokal ishlab chiqish trafigi analitikani ifloslantirmaydi
- **Localhost / ichki IP lar** (`127.0.0.1`, `::1`, private/loopback) — bular haqiqiy tashrif emas va geolokatsiya qilib boʻlmaydi
- Botlar va krawlerlar (User-Agent asosida)
- Admin paneli soʻrovlari (sozlanadigan `ADMIN_URL` prefiksi)
- Statik va media fayllar (`/static/`, `/media/`, `/ckeditor5/`, `/i18n/`, `/favicon`)
- Tizimga kirgan **staff** foydalanuvchilar va GET'dan boshqa metodlar / xato (≥400) javoblar

### Admin dashboard

Admin panelda analitika sahifasi quyidagi KPI va grafiklarni koʻrsatadi:

- Jami tashriflar (kunlik/haftalik/oylik)
- Qurilma turi boʻyicha taqsimot (desktop / mobile / tablet)
- Eng koʻp koʻrilgan sahifalar
- Brauzer va OS statistikasi
- Til va davlat boʻyicha taqsimot

### Buyruqlar

```bash
# Eski yozuvlarni o'chirish (standart: 90 kundan eski)
python manage.py prune_visitlogs
python manage.py prune_visitlogs --days 30

# IP -> davlat (dashboarddagi "Davlatlar" paneli uchun)
python manage.py resolve_geoip
```

> Productionda `resolve_geoip` 30 daqiqada bir systemd timer orqali avtomatik ishlaydi (`deploy/resolve-geoip.timer`); `prune_visitlogs` ni esa haftalik crontab/timer bilan rejalashtiring.

---

## SEO

Sayt qidiruv tizimi optimizatsiyasining barcha asosiy jihatlarini qoʻllab-quvvatlaydi. Barcha SEO sozlamalari admin panelda boshqariladi — kod oʻzgartirish talab qilinmaydi.

### sitemap.xml

`/sitemap.xml` manzilida avtomatik yaratiladigan xarita uchta til versiyasini (`/uz/`, `/ru/`, `/en/`) qamrab oladi. Har bir URL uchun `hreflang` muqobil havolalari va `x-default` (oʻzbekcha) kiritilgan.

Qamrab olingan sahifalar:

| Sahifa | Yangilish chastotasi |
|--------|----------------------|
| Bosh sahifa | Haftalik |
| Har bir kurs detail sahifasi | Haftalik |
| Har bir oʻqituvchi profil sahifasi | Oylik |
| Har bir yangilik/eʼlon sahifasi | Haftalik |
| Galereya sahifasi | Oylik |

### robots.txt

`/robots.txt` manzilida statik fayl xizmat qiladi. Admin paneli va media papkalariga crawl taqiqlanadi; saytmap manzili avtomatik koʻrsatiladi:

```
User-agent: *
Disallow: /admin/
Disallow: /media/
Sitemap: https://tagayev.uz/sitemap.xml
```

### Sahifa `<head>` — meta va canonical

Har bir sahifada quyidagi teglar generatsiya qilinadi:

**Meta sarlavha va tavsif — fallback zanjiri:**

```
Sahifaga xos meta_title / meta_description
    → Obyekt meta maydonlari (kurs, oʻqituvchi, yangilik meta_title/meta_description)
        → SiteConfig.seo_title / SiteConfig.seo_description
            → Standart qiymat
```

**Canonical va hreflang:**

```html
<link rel="canonical" href="https://tagayev.uz/uz/kurslar/ingliz-tili/" />
<link rel="alternate" hreflang="uz"      href="https://tagayev.uz/uz/kurslar/ingliz-tili/" />
<link rel="alternate" hreflang="ru"      href="https://tagayev.uz/ru/kurslar/ingliz-tili/" />
<link rel="alternate" hreflang="en"      href="https://tagayev.uz/en/kurslar/ingliz-tili/" />
<link rel="alternate" hreflang="x-default" href="https://tagayev.uz/uz/kurslar/ingliz-tili/" />
```

### Open Graph va Twitter Card

Ijtimoiy tarmoqlarda ulashilganda koʻrinadigan meta-teglar:

| Teg | Manba |
|-----|-------|
| `og:title` | Sahifa meta_title → SiteConfig.seo_title |
| `og:description` | Sahifa meta_description → SiteConfig.seo_description |
| `og:image` | Obyekt rasmi → SiteConfig.og_image |
| `og:url` | Joriy sahifaning canonical URL si |
| `twitter:card` | `summary_large_image` |
| `twitter:title`, `twitter:description`, `twitter:image` | og: teglar bilan bir xil manba |

OG rasm tavsiya etilgan oʻlchami: **1200 × 630 px**.

### JSON-LD tuzilgan maʼlumotlar

Qidiruv tizimlariga kontent turini tushuntirish uchun `<script type="application/ld+json">` bloklari generatsiya qilinadi:

| Tur | Sahifa |
|-----|--------|
| `EducationalOrganization` + `LocalBusiness` | Barcha sahifalarda (global, bosh sahifada kengaytirilgan) |
| `Course` | Kurs detail sahifasi |
| `NewsArticle` | Yangilik/eʼlon detail sahifasi |
| `BreadcrumbList` | Ichki sahifalarda navigatsiya zanjiri |

`LocalBusiness` da manzil, telefon, koordinatalar (SiteConfig.latitude/longitude) va ish vaqti kiritiladi.

### Google Analytics 4 va Yandex Metrica

Tashqi tracker skriptlari faqat admin panelida ID kiritilganda sahifaga qoʻshiladi:

| Xizmat | Sozlama joyi | Shart |
|--------|-------------|-------|
| **Google Analytics 4** | Sayt sozlamalari → `GA4 oʻlchov ID` | `G-XXXXXXXXXX` formatida kiritilganda yoqiladi |
| **Yandex Metrica** | Sayt sozlamalari → `Yandex Metrica ID` | Raqamli ID kiritilganda yoqiladi |

ID boʻsh qolsa, tegishli skript sahifaga umuman qoʻshilmaydi — ortiqcha HTTP soʻrov ketmaydi.

### Webmaster tasdiqlash

Qidiruv tizimlari saytni tasdiqlash uchun `<meta name="..." content="...">` tegi ishlatadi. Kodlar admin panelda **Sayt sozlamalari → SEO sozlamalari** boʻlimiga kiritiladi:

| Xizmat | Meta-teg nomi |
|--------|--------------|
| Google Search Console | `google-site-verification` |
| Yandex Webmaster | `yandex-verification` |
| Bing Webmaster | `msvalidate.01` |

Batafsil toʻldirish koʻrsatmasi va sitemap yuborish qadamlari uchun qarang: [`docs/ADMIN.md → SEO — qidiruv tizimlariga ulash`](docs/ADMIN.md#seo--qidiruv-tizimlariga-ulash).

---

## i18n / Tarjima

Sayt **ikki qatlamli** koʻptillilikdan foydalanadi.

### 1. Kontent tarjimasi (django-modeltranslation)

Barcha kontent modellari (kurslar, oʻqituvchilar, yangiliklar va h.k.) uchun har bir matn maydoni uchta versiyada saqlanadi:

```
MODELTRANSLATION_LANGUAGES = ("uz", "ru", "en")
MODELTRANSLATION_DEFAULT_LANGUAGE = "uz"
MODELTRANSLATION_FALLBACK_LANGUAGES = ("uz", "ru", "en")
```

Admin panelda har bir til uchun alohida tab koʻrinadi (`[uz]`, `[ru]`, `[en]`). Biror til uchun maydon boʻsh qolsa, standart — oʻzbekcha — koʻrsatiladi. Boʻsh ru/en maydonlarini [auto-tarjima](#auto-tarjima-mashina-tarjimasi) bilan bir tugmada toʻldirish mumkin.

URL prefikslari (`i18n_patterns` orqali): `/uz/`, `/ru/`, `/en/`

### 2. Interfeys tarjimasi (gettext / polib)

Admin panel va shablon matnlari `gettext_lazy` bilan belgilangan. Tarjima fayllari quyidagi tuzilmada saqlanadi:

```
locale/
├── ru/
│   └── LC_MESSAGES/
│       ├── django.po    # Ruscha tarjima manba fayli
│       └── django.mo    # Kompilatsiya qilingan fayl
└── en/
    └── LC_MESSAGES/
        ├── django.po
        └── django.mo
```

`.po` fayllari yaratish yoki yangilash:

```bash
python manage.py makemessages -l ru -l en
```

Tarjimalar kiritilgandan soʻng kompilatsiya:

```bash
python manage.py compilemo   # .po → .mo (polib; GNU gettext talab qilinmaydi)
```

> **Eslatma:** standart `compilemessages` GNU `msgfmt` (gettext) dasturini talab qiladi —
> u Windowsda ham, serverda ham mavjud emas. `compilemo` esa `polib` (requirements.txt'da)
> yordamida barcha `locale/**/*.po` fayllarini `.mo` ga aylantiradi.

### 3. Til almashtirgich

Saytdagi til almashtirgich Django standart `set_language` koʻrinishiga asoslangan:

```
POST /i18n/set_language/
```

Bu URL `i18n_patterns` dan **tashqarida** joylashgan (`config/urls.py` da `path("i18n/", include("django.conf.urls.i18n"))`) — til almashtirish har qanday sahifadan ishlaydi.

---

## Media xavfsizligi va CKEditor

### Ruxsat etilgan fayl turlari va chegaralar

| Tur | Formatlar | Maks hajm |
|-----|-----------|-----------|
| **Rasm** (modellar) | jpg, jpeg, png, webp, gif | **5 MB** |
| **PDF** (sertifikatlar) | pdf | **10 MB** |
| **CKEditor yuklash** | jpg, jpeg, png, webp, gif | **5 MB** |

Chegaralar `apps/common/validators.py` da `MaxFileSizeValidator` va `FileExtensionValidator` orqali serverda tekshiriladi — faqat client-side emas.

### CKEditor 5

CKEditor 5 quyidagi kontent maydonlarida ishlatiladi:

- Kurs toʻliq tavsifi
- Oʻqituvchi bio
- Yangilik tana qismi
- "Biz haqimizda" matni

**Rasm yuklash huquqi:** Faqat `is_staff=True` boʻlgan foydalanuvchilar CKEditor orqali rasm yuklay oladi (`CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"`).

---

## Tezlik, rasm optimizatsiyasi va accessibility

Ushbu boʻlim saytning yuklanish tezligini, rasm samaradorligini va barcha foydalanuvchilar uchun qulayligini taʼminlovchi optimizatsiyalarni qamrab oladi.

### Responsive WebP rasmlar (easy_thumbnails)

`easy_thumbnails` yordamida yuklangan har bir rasm uchun optimallashtrilgan versiyalar avtomatik yaratiladi.

Shablonlarda `<picture>` elementi qoʻllaniladi — brauzer WebP formatini qoʻllab-quvvatlasa WebP, qoʻllab-quvvatlamasa asl rasm yuklaydi:

```html
<picture>
  <source srcset="rasm.webp" type="image/webp">
  <img src="rasm.jpg" alt="..." width="800" height="450"
       loading="lazy" class="...">
</picture>
```

**Asosiy jihatlar:**

| Xususiyat | Tavsif |
|-----------|--------|
| `loading="lazy"` | Ekranda koʻrinmagan rasmlar keyinchalik yuklanadi — sahifaning dastlabki yuklanishi tezlashadi |
| `width` + `height` atributlari | Brauzer rasm joyi uchun joy ajratadi — layout sakrashining (CLS) oldini oladi |
| WebP format | JPEG/PNG ga nisbatan oʻrtacha 25–35% kichikroq hajm, sifat yoʻqotilmaydi |
| Responsive oʻlchamlar | Turli ekran kengliklariga mos miniatyuralar yaratiladi |

> **easy_thumbnails va media papkasi:** `easy_thumbnails` yaratilgan miniatyuralarni `media/` papkasidagi `cache/` quyi-papkasida saqlaydi. Production serverida `media/` papkasi **yozish huquqi bilan** va **doimiy (persistent)** boʻlishi shart — aks holda har deployment da miniatyuralar qayta hisoblanadi.

### Shrift optimizatsiyasi

Tashqi shrift provayderlariga (masalan, Google Fonts) ulanish vaqtini qisqartirish uchun `<head>` da preconnect havolasi qoʻshilgan:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
```

Shuningdek, `font-display: swap` CSS xossasi qoʻllaniladi — shrift yuklanayotgan vaqtda tizim shrifti koʻrsatiladi, sahifa bo'shliq qolmaydi (FOUT qabul qilinadi, FOIT emas).

### JavaScript defer

Interaktivlik talab qilmaydigan skriptlar `defer` atributi bilan yuklangan — brauzer HTML ni to'liq tahlil qilgandan soʻng skriptlarni bajaradi, bu LCP va INP koʻrsatkichlarini yaxshilaydi.

### Accessibility (a11y)

**Skip-to-content havolasi** — klaviatura va ekran oʻquvchi foydalanuvchilari uchun sahifa boshida "Asosiy mazmunga oʻtish" havolasi; odatda yashirin, fokus olganda koʻrinadi:

```html
<a href="#main" class="skip-link">Asosiy mazmunga oʻtish</a>
...
<main id="main">...</main>
```

**`:focus-visible` uslublari** — faqat klaviatura navigatsiyasida fokus ramkasi koʻrsatiladi:

```css
:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: 2px;
}
```

**`prefers-reduced-motion`** — harakatga sezgir foydalanuvchilar uchun animatsiyalar minimal darajaga tushiriladi:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Core Web Vitals maqsadlari

| Koʻrsatkich | Toʻliq nomi | Maqsad |
|-------------|------------|--------|
| **LCP** | Largest Contentful Paint (eng katta element yuklanishi) | ≤ 2.5 s |
| **CLS** | Cumulative Layout Shift (to'plangan layout sakrashi) | ≤ 0.1 |
| **INP** | Interaction to Next Paint (interaktivlikka javob) | ≤ 200 ms |

> **Eslatma:** INP 2024 yildan boshlab FID (First Input Delay) oʻrnini egalladi va hozirda Google tomonidan asosiy koʻrsatkich sifatida hisoblanadi.

### Lighthouse auditi (qoʻlda)

Lighthouse CI ga kiritilmagan — uni qoʻlda tekshirish tavsiya etiladi (Chrome DevTools → **Lighthouse** tabi, yoki tashqi [pagespeed.web.dev](https://pagespeed.web.dev/)).

> **Development vs Production:** Lighthouse natijalarini `DEBUG=False` holatida va `collectstatic` qilingan production-ga yaqin muhitda oʻlchang — `DEBUG=True` rejimida WhiteNoise kompressiyasi va kesh sarlavhalari toʻliq ishlamaydi.

---

## CI/CD

Loyiha **GitHub Actions** orqali avtomatlashtirilgan: `.github/workflows/deploy.yml`.

```
push / pull_request (main)
        │
        ▼
   ┌─────────┐   testlar oʻtsa va main ga push boʻlsa   ┌──────────┐
   │  test   │ ───────────────────────────────────────▶ │  deploy  │
   └─────────┘                                           └──────────┘
   • python check         • ubuntu sifatida SSH (parol) bilan ulanadi
   • makemigrations --check  (script → redeploy qadamlari ishga tushadi)
   • test (286 ta test)
```

**`test` ishi** (har push va har PR da):

| Qadam | Buyruq |
|-------|--------|
| Python | 3.14 (`actions/setup-python@v6`) + pip kesh |
| Django tekshiruvi | `python manage.py check` |
| Migratsiya butunligi | `python manage.py makemigrations --check --dry-run` |
| Test to'plami | `python manage.py test --verbosity 2` |

CI da `.env` yoʻq (gitignore) — sozlamalar dev standartlariga qaytadi va xavfsizlik bloki oʻchiq qolishi uchun `DEBUG=True` majburlanadi.

**`deploy` ishi** faqat `main` ga **push** boʻlganda va **testlar oʻtgach** ishlaydi:

- `appleboy/ssh-action` orqali `ubuntu` sifatida **parol bilan** SSH ulanadi.
- `script` bloki `/home/ubuntu/tagayev` da redeploy qadamlarini bajaradi: `git pull` → `pip install` → `migrate` → `tailwind build` → `collectstatic` → `compilemo` → `sudo systemctl restart tagayev`.
- Oxirgi qadam (`systemctl restart`) CI da parolsiz ishlashi uchun serverda tor NOPASSWD sudoers qoidasi kerak (`docs/JOYLASHTIRISH.md`).
- `concurrency` bilan ikki deploy bir vaqtda ketmasligi kafolatlanadi.

> Kerakli GitHub Secrets: `DEPLOY_HOST`, `DEPLOY_USER` (=`ubuntu`),
> `DEPLOY_KEY` — serverga kirish uchun **alohida** ed25519 kaliti (login paroli
> emas: parol har bir workflow ishga tushishiga butun serverni beradi). Ochiq
> yarmi `ubuntu` ning `~/.ssh/authorized_keys` faylida, izohi
> `github-actions-deploy@tagayev` — CI ni bekor qilish uchun shu qatorni
> o'chirish kifoya.
>
> Bundan tashqari `DEPLOY_ENABLED` **variable**'i `true` bo'lishi shart. Ushbu
> gate fork qilingan repo tasodifan boshqa saytning serveriga deploy qilib
> yubormasligi uchun; testlar undan qat'i nazar har push'da ishlaydi.

---

## Deployment

Toʻliq production joylashtirish qoʻllanmasi — **gunicorn + nginx + systemd + Certbot (HTTPS)** va uch qatlamli DDoS/rate-limit himoyasi: **[`docs/JOYLASHTIRISH.md`](docs/JOYLASHTIRISH.md)**. Tayyor konfiguratsiya fayllari `deploy/` papkasida.

Qisqacha (server allaqachon sozlangan boʻlsa, redeploy):

```bash
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py tailwind build            # collectstatic'dan OLDIN — aks holda CSS yig'ilmaydi
python manage.py collectstatic --noinput
python manage.py compilemo                 # .po → .mo (polib; serverda msgfmt yo'q)
sudo systemctl restart tagayev
```

> **Xavfsizlik tekshiruvi:** deploydan oldin `python manage.py check --deploy` "no issues" berishi kerak — bu tekshiruv `apps/common/test_deploy.py` testida ham ushlab turiladi.

> **easy_thumbnails (media keshi):** miniatyuralar `media/cache/` da saqlanadi va talab boʻyicha qayta yaratiladi. `media/` papkasi serverda **doimiy va yozish huquqi bilan** mavjud boʻlishi shart.

---

## Hujjatlar

| Fayl | Mazmun |
|------|--------|
| [`docs/ORNATISH.md`](docs/ORNATISH.md) | Batafsil lokal (dev) oʻrnatish qoʻllanmasi |
| [`docs/ADMIN.md`](docs/ADMIN.md) | Admin panelda kontent boshqaruvi |
| [`docs/JOYLASHTIRISH.md`](docs/JOYLASHTIRISH.md) | Production serverga joylashtirish (deploy) |
