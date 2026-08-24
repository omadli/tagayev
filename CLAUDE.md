# Tagayev Methods — loyiha konvensiyalari

## Django template kommentariyalari

**Hech qachon ko'p qatorli `{# … #}` kommentariyadan foydalanmang.**

Django `{# … #}` ni faqat **bitta qatorda** ochilib-yopilganda kommentariya deb
biladi. `{#` bilan `#}` orasida yangi qator (newline) bo'lsa, u kommentariya
sifatida tahlil qilinmaydi — ichidagi matn **render qilingan sahifada ko'rinib
qoladi** (page text sifatida "oqib chiqadi"). Bu bug bir necha marta yuz bergan
(commitlar `b152226`, va PR #2 landing/500 template'larida).

Bu **har qanday** ko'p qatorli `{# #}` ga tegishli — jumladan kodni izohlovchi
bloklar (masalan `{% cache %}` yoki `{% block %}` ustidagi izohlar) ham. Yozishdan
oldin har doim bir qatorda ochilib-yopilishiga ishonch hosil qiling.

**Qo'shimcha xavf:** parse qilinmagan `{# #}` ichidagi template teglar (masalan
`{% csrf_token %}`) haqiqatan **bajariladi** — nafaqat matn oqadi, balki
kutilmagan render/xatolik ham yuzaga keladi.

- ✅ Bir qatorli: `{# qisqa izoh, bitta qatorda #}`
- ❌ Ko'p qatorli `{# … #}` — sahifa matni sifatida oqib chiqadi
- Ko'p qatorli izoh kerak bo'lsa `{% comment %} … {% endcomment %}` ishlating
  (masalan `templates/admin/base_site.html` faylining boshidagi bloklar).

Tekshirish (commit oldidan):
`grep -rn '{#' templates apps --include=*.html | grep -v '#}'` — natija **bo'sh
bo'lishi kerak** (har bir `{#` o'z qatorida `#}` bilan yopilishi shart).

## Dev server

Django dev serverni **8000** emas, **8001**-portda ishga tushiring:
`python manage.py runserver 8001`.

## Kontent — baza boʻsh keladi

Bu loyihada **demo/seed maʼlumot yoʻq** (`seed_demo` buyrugʻi olib tashlangan).
Kurslar, oʻqituvchilar, sharhlar, yangiliklar, galereya, sertifikatlar, hamkorlar
va sayt matnlari **faqat admin panel** orqali kiritiladi. Kontent seed qiluvchi
migratsiya qoʻshmang — faqat `pages/0004` dagi UI matnlari (tugma yozuvlari,
boʻlim sarlavhalari) istisno, ular interfeys chrome'i.

## Brend ranglari

Asosiy — **binafsha** (`brand-violet-*`), aksent — **tilla** (`brand-gold-*`);
ikkalasi `assets/css/source.css` dagi `@theme` blokida. Tilla fonda **oq matn
ishlatmang** (kontrast yetmaydi) — tilla tugmalarda matn `text-brand-violet-900`.
Xato xabarlari tilla emas, Tailwind'ning `text-red-600` rangida qoladi.

Ranglar **admin paneldan** ham o'zgaradi (Sayt sozlamalari → Brend ranglari):
Tailwind v4 har bir utilitani `var(--color-brand-*)` ga kompilyatsiya qiladi,
shuning uchun `base.html` `<html>` ga `--brand-p` / `--brand-a` ni yozadi va
`source.css` dagi `:root[data-brand-p]` / `[data-brand-a]` bloklari barcha
soyalarni `color-mix()` bilan chiqaradi. **Rebuild kerak emas.**
Yangi brend rang qo'shsangiz — hexni to'g'ridan-to'g'ri yozmang, mavjud
`--brand-p` / `--brand-a` / `--p-*` / `--a-*` o'zgaruvchilaridan foydalaning,
aks holda u admin sozlamasiga bo'ysunmay qoladi.

Admin paneli ham shu palitraga ergashadi: `{% admin_brand_style %}` tegi
(`apps/common/templatetags/brand.py`) Unfold'ning `--color-primary-*` larini
`html:root` bilan qayta yozadi — `:root` emas, chunki Unfold o'zinikini
`<body>` boshida, ya'ni **keyinroq** chiqaradi.

`site_context` kontekst protsessori admin so'rovlarida bo'sh qaytadi, shuning
uchun admin shablonlarida `site_config` **yo'q** — singletonni teg orqali
oling.

Palitraga ergashmaydigan yagona joy — `templates/500.html`: u baza/ilova
ishlamay qolganda render bo'ladi, shuning uchun SiteConfig'ga murojaat
qilmasligi shart. Logotip va PWA ikonkalari ham rasm (admin yuklaydi).
