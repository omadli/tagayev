# Oʻrnatish Qoʻllanmasi — Tagayev Methods

> Bu qoʻllanma loyihani mahalliy kompyuterda ishga tushirish uchun toʻliq qadamlarni tavsiflab beradi.

---

## Mundarija

1. [Talablar](#talablar)
2. [Repozitoriyani olish](#repozitoriyani-olish)
3. [Virtual muhit](#virtual-muhit)
4. [Paketlarni oʻrnatish](#paketlarni-ornatish)
5. [Muhit faylini sozlash (.env)](#muhit-faylini-sozlash)
6. [Migratsiyalar](#migratsiyalar)
7. [Superuser yaratish](#superuser-yaratish)
8. [Tailwind CSS qurilishi](#tailwind-css-qurilishi)
9. [Development serverini ishga tushirish](#development-serverini-ishga-tushirish)
10. [Demo maʼlumotlar (ixtiyoriy)](#demo-malumotlar)
11. [Tarjima fayllarini kompilatsiya qilish](#tarjima-fayllarini-kompilatsiya-qilish)
12. [Muammolarni hal qilish](#muammolarni-hal-qilish)

---

## Talablar

Oʻrnatishdan avval quyidagi dasturlar mavjudligini tekshiring:

| Dastur | Versiya | Eslatma |
|--------|---------|---------|
| Python | 3.13 (yoki 3.11+) | `python --version` |
| Git | istalgan | `git --version` |
| pip | 24+ (odatda Python bilan keladi) | `pip --version` |

**Node.js talab qilinmaydi.** Tailwind CSS v4 standalone CLI birinchi ishga tushirishda avtomatik yuklab olinadi.

---

## Repozitoriyani olish

```bash
git clone https://github.com/omadli/tagayev.git
cd tagayev
```

---

## Virtual muhit

Virtual muhit yaratish majburiy — bu loyiha paketlarini tizim Pythonidan ajratib turadi.

### Windows (PowerShell)

```powershell
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

Aktivlashtirilganidan keyin terminal satri `(venv)` bilan boshlanishi kerak.

---

## Paketlarni oʻrnatish

```bash
pip install -r requirements.txt
```

Bu buyruq barcha kerakli kutubxonalarni, jumladan Django 5.2, Unfold, modeltranslation, CKEditor 5, Tailwind CLI va gunicorn'ni oʻrnatadi.

---

## Muhit faylini sozlash

`.env.example` faylini `.env` nomi bilan nusxalang:

```powershell
# Windows
copy .env.example .env
```

```bash
# Linux / macOS
cp .env.example .env
```

Keyin `.env` faylini matn muharrirda oching va quyidagi oʻzgaruvchilarni toʻldiring:

```env
# True — dev uchun, False — production uchun
DEBUG=True

# Kuchli tasodifiy kalit (production uchun albatta oʻzgartiring):
#   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=change-me-to-a-real-secret-key

# Development uchun * qoldirish mumkin
ALLOWED_HOSTS=*

# Production uchun: https://tagayev.uz
CSRF_TRUSTED_ORIGINS=

# Telegram — yangi arizalarni real vaqtda qabul qilish uchun (ixtiyoriy)
# Ikkala qiymat boʻlmasa bildirishnoma yuborilmaydi
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_CHAT_ID=
```

### Muhit oʻzgaruvchilari jadvali

| Oʻzgaruvchi | Majburiy | Tavsif |
|-------------|----------|--------|
| `DEBUG` | Yoʻq | `True` — dev, `False` — production |
| `SECRET_KEY` | **Ha** | Django maxfiy kaliti |
| `ALLOWED_HOSTS` | **Ha** | Vergul bilan ajratilgan domenlar |
| `CSRF_TRUSTED_ORIGINS` | Production | HTTPS manzillar |
| `TELEGRAM_BOT_TOKEN` | Yoʻq | Bot tokeni — [@BotFather](https://t.me/BotFather) dan; boʻsh qolsa Telegram bildirishnomasi oʻchiriladi |
| `TELEGRAM_ADMIN_CHAT_ID` | Yoʻq | Arizalar yuboriladigan chat/guruh ID si (guruh uchun manfiy raqam) |

---

## Migratsiyalar

```bash
python manage.py migrate
```

Bu buyruq SQLite bazasini yaratadi (`db.sqlite3`) va barcha jadvallarni tuzadi. Baza WAL rejimida ishlaydi — bu parallel yozuvlarga bardoshliligini oshiradi.

---

## Superuser yaratish

```bash
python manage.py createsuperuser
```

Login, email va parol soʻraladi. Keyin admin panelga kirish uchun shu maʼlumotlardan foydalaning.

---

## Tailwind CSS qurilishi

```bash
python manage.py tailwind build
```

**Birinchi ishga tushirishda** Tailwind CLI binary (~5 MB) avtomatik yuklab olinadi — bu bir marta sodir boʻladi va internet talab qiladi.

### Development rejimida (avtomatik qayta qurilish)

```bash
python manage.py tailwind watch
```

Yoki server va watch'ni birgalikda ishga tushirish:

```bash
python manage.py tailwind runserver
```

---

## Development serverini ishga tushirish

```bash
python manage.py runserver 127.0.0.1:8001
```

> Server **8001**-portda ishga tushadi (8000 boshqa loyiha bilan toʻqnashuv oldini olish uchun).

Brauzerda oching:

| Manzil | Tavsif |
|--------|--------|
| [http://127.0.0.1:8001/](http://127.0.0.1:8001/) | Asosiy sayt (oʻzbekcha) |
| [http://127.0.0.1:8001/ru/](http://127.0.0.1:8001/ru/) | Ruscha versiya |
| [http://127.0.0.1:8001/en/](http://127.0.0.1:8001/en/) | Inglizcha versiya |
| [http://127.0.0.1:8001/admin/](http://127.0.0.1:8001/admin/) | Admin paneli |
| [http://127.0.0.1:8001/ariza/](http://127.0.0.1:8001/ariza/) | Ariza topshirish (POST endpoint) |

---

## Kontent

Baza boʻsh — barcha kontent (sayt sozlamalari, kurslar, oʻqituvchilar,
sharhlar, yangiliklar, galereya, sertifikatlar) admin panel orqali
kiritiladi: `/admin/`.

---

## Tarjima fayllarini kompilatsiya qilish

Sayt `django-modeltranslation` orqali kontent tarjimasini, `gettext` orqali esa interfeys tarjimasini qoʻllab-quvvatlaydi.

### .po fayllarini yaratish yoki yangilash

```bash
python manage.py makemessages -l ru -l en
```

Bu buyruq `locale/ru/LC_MESSAGES/django.po` va `locale/en/LC_MESSAGES/django.po` fayllarini yaratadi yoki yangilaydi.

### .po → .mo kompilatsiyasi

Standart `manage.py compilemessages` GNU `msgfmt` (gettext) ni talab qiladi — u Windowsda
ham, bu Ubuntu serverda ham mavjud emas. Shuning uchun loyiha `polib`-asosidagi
`compilemo` buyrugʻidan foydalanadi (`polib` `requirements.txt` ichida):

```bash
python manage.py compilemo
```

Bu barcha `locale/**/*.po` fayllarini `.mo` ga aylantiradi. Buyruq mavjud `.po`
fayllarni faqat kompilatsiya qiladi (qayta yaratmaydi), shuning uchun har bir
deployda xavfsiz ishga tushiriladi.

> `.po` fayllarini Uzbek manbadan **qayta yaratish** (yangi `_()` satrlari qoʻshilganda)
> uchun esa `locale/_build_catalogs.py` (Windows dev vositasi) ishlatiladi.

> **Eslatma:** `.mo` fayllari ikkilik formatda boʻlib, Git da hisobga olinmaydi (`.gitignore` da). Serverga joylashtirilganda kompilatsiya qayta bajarilishi kerak.

---

## Muammolarni hal qilish

### `ModuleNotFoundError: No module named 'django'`

Virtual muhit aktivlashtirilmagan. `venv\Scripts\activate` (Windows) yoki `source venv/bin/activate` (Linux) buyruqlarini bajaring.

### Tailwind CLI yuklanmaydi

Internet ulanishi mavjudligini tekshiring. Tailwind CLI bir marta yuklab olinadi va `~/.local/share/tailwind-cli/` (Linux) yoki `%LOCALAPPDATA%\tailwind-cli\` (Windows) papkasida saqlanadi.

### `db.sqlite3` fayli topilmaydi

`python manage.py migrate` buyruqi bajarilmagan. Avval migratsiyalarni ishga tushiring.

### Port 8001 band

```bash
python manage.py runserver 127.0.0.1:8002
```

Boshqa port raqamini belgilang.

### Windows da `'python' is not recognized`

Python PATH ga qoʻshilmagan boʻlishi mumkin. `py` yoki `python3` buyruqlarini sinab koʻring, yoki Pythonni qayta oʻrnating va "Add Python to PATH" katagini belgilang.

### Telegram bildirishnomalar kelmayapti

1. `.env` da `TELEGRAM_BOT_TOKEN` va `TELEGRAM_ADMIN_CHAT_ID` toʻldirilganligini tekshiring.
2. Admin panelda **Sayt sozlamalari → "Telegram bildirishnomalari yoniq"** katagini belgilang.
3. Server logida xato xabarlarni koʻring (`logger.warning` va `logger.exception` tomonidan yoziladi).
4. Bot token va chat ID toʻgʻriligini Telegram API orqali tekshiring:
   ```
   https://api.telegram.org/bot<TOKEN>/getMe
   ```

---

## Keyingi qadam

Oʻrnatish muvaffaqiyatli boʻlgandan soʻng kontent qoʻshishni boshlash uchun [`ADMIN.md`](ADMIN.md) qoʻllanmasini oʻqing.
