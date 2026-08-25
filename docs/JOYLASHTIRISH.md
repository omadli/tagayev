# Serverga Joylashtirish (Deploy) — Tagayev Methods

> Bu qoʻllanma loyihani Ubuntu serverida (masalan, AWS EC2) ishlab chiqarish
> (production) muhitida ishga tushirishning toʻliq qadamlarini tavsiflaydi:
> **gunicorn + nginx + systemd + Certbot (HTTPS)** + xavfsizlik mustahkamlash va
> **DDoS/rate-limit himoyasi**.

Tayyor konfiguratsiya fayllari `deploy/` papkasida turadi.

---

## Mundarija

1. [Arxitektura](#arxitektura)
2. [Server talablari](#server-talablari)
3. [Foydalanuvchi va kataloglar](#foydalanuvchi-va-kataloglar)
4. [Kodni olish va paketlar](#kodni-olish-va-paketlar)
5. [.env (production)](#env-production)
6. [Baza, statik, tarjima, superuser](#baza-statik-tarjima-superuser)
7. [Xavfsizlik tekshiruvi](#xavfsizlik-tekshiruvi)
8. [gunicorn (systemd)](#gunicorn-systemd)
9. [nginx](#nginx)
10. [HTTPS (Certbot)](#https-certbot)
11. [Geo-IP jadval (systemd timer)](#geo-ip-jadval)
12. [DDoS va rate-limit himoyasi](#ddos-va-rate-limit-himoyasi)
13. [Yangilash (redeploy)](#yangilash-redeploy)
14. [Zaxira nusxa (backup)](#zaxira-nusxa)
15. [Muammolarni hal qilish](#muammolarni-hal-qilish)

---

## Arxitektura

```
Internet ──HTTPS──▶ nginx ──unix socket──▶ gunicorn ──▶ Django (config.wsgi)
                     │                                     │
                     ├─ /static/  → staticfiles/ (nginx)   └─ SQLite (WAL)
                     └─ /media/   → media/      (nginx)
```

- **nginx** — TLS (Certbot), statik/media fayllar, gzip, rate-limit, xavfsizlik headerlari.
- **gunicorn** — Django WSGI ilovasini ishga tushiradi (systemd boshqaradi).
- **whitenoise** faqat *static* fayllarni beradi; *media* (yuklangan rasm/video) ni **nginx** beradi.
- **SQLite (WAL)** — kichik/oʻrta trafik uchun yetarli; Redis talab qilinmaydi.

---

## Server talablari

| Komponent | Versiya / izoh |
|-----------|----------------|
| OS | Ubuntu 22.04 yoki 24.04 LTS |
| Python | 3.11+ (`python3 --version`) |
| nginx | `sudo apt install nginx` |
| Certbot | `sudo apt install certbot python3-certbot-nginx` |
| fail2ban | `sudo apt install fail2ban` (IP bloklash) |
| Domen | `tagayev.uz` A-yozuvi server IP ga yoʻnaltirilgan |

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx certbot python3-certbot-nginx fail2ban git
```

---

## Foydalanuvchi va kataloglar

Ilova **alohida servis foydalanuvchisi talab qilmaydi** — barcha ish oddiy
`ubuntu` login foydalanuvchisida, to'g'ridan-to'g'ri `/home/ubuntu/tagayev`
papkasida ketadi (alohida `app/` papka ham yoʻq).

```bash
mkdir -p /home/ubuntu/tagayev
# nginx (www-data) statik/media fayllarni oʻqishi uchun home papkaga "traverse"
# (x) ruxsati kerak — aks holda /static/ va /media/ 403 beradi:
chmod o+x /home/ubuntu
```

> `deploy/` ichidagi fayllar `/home/ubuntu/tagayev` yoʻlini va `ubuntu`
> foydalanuvchisini nazarda tutadi. Servis `www-data` guruhida ishlaydi, shuning
> uchun nginx gunicorn socketini (`/run/tagayev/gunicorn.sock`) oʻqiy oladi.

---

## Kodni olish va paketlar

```bash
cd /home/ubuntu/tagayev
git clone https://github.com/omadli/tagayev.git .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## .env (production)

```bash
cp .env.example .env
nano .env
```

Production uchun **majburiy** qiymatlar:

```env
DEBUG=False

# Kuchli kalit yarating:
#   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=<yangi-kuchli-kalit>

# Aniq domenlar — '*' EMAS
ALLOWED_HOSTS=tagayev.uz,www.tagayev.uz
CSRF_TRUSTED_ORIGINS=https://tagayev.uz,https://www.tagayev.uz

TELEGRAM_BOT_TOKEN=<bot-token>
TELEGRAM_ADMIN_CHAT_ID=<chat-id>
```

> **Diqqat:** `DEBUG=False` boʻlganda `settings.py` xavfsizlik bloki yoqiladi.
> Agar `SECRET_KEY` hali ham dev qiymati boʻlsa yoki `ALLOWED_HOSTS=*` boʻlsa,
> Django **ishga tushishdan bosh tortadi** (xato bilan) — bu ataylab shunday,
> xavfli sozlama bilan deploy boʻlib qolmaslik uchun.

> **HSTS haqida:** birinchi HTTPS deployda `.env` ga `SECURE_HSTS_SECONDS=3600`
> qoʻying. TLS barqaror ishlayotganiga ishonch hosil qilgach, qiymatni
> `31536000` (1 yil) ga koʻtaring. HSTS brauzerda keshlanadi — uni orqaga
> qaytarish qiyin.

---

## Baza, statik, tarjima, superuser

```bash
# venv aktiv, /home/ubuntu/tagayev da
python manage.py migrate
python manage.py createcachetable          # rate-limit uchun umumiy cache jadvali
python manage.py tailwind build            # → assets/css/tailwind.css (collectstatic'dan OLDIN!)
python manage.py collectstatic --noinput   # → staticfiles/  (tailwind.css yig'iladi; source.css o'tkazib yuboriladi)
python manage.py createsuperuser

# i18n (.mo) — bu serverda GNU gettext (msgfmt) yo'q, shuning uchun polib bilan:
python manage.py compilemo                 # locale/**/*.po → .mo (polib, requirements.txt'da)

# CEFR sertifikatlari — rasmlar media/ ga render qilinadi (git'da yo'q) va
# URL'lar `cefr_urls.txt` faylidan o'qiladi (bu fayl gitignored — real o'quvchi
# ma'lumotlari repo'da bo'lmaydi). Faylni serverga qo'lda ko'chiring, so'ng:
python manage.py import_cefr            # cefr_urls.txt dan o'qiydi
# yoki:  python manage.py import_cefr --file /path/urls.txt
```

Kataloglarga yozish huquqini taʼminlang:

```bash
sudo chown -R ubuntu:www-data /home/ubuntu/tagayev
sudo chmod -R g+rwX /home/ubuntu/tagayev/media
```

---

## Xavfsizlik tekshiruvi

Django joylashtirishdan oldin sozlamalarni tekshiradi:

```bash
DEBUG=False SECRET_KEY=$(grep SECRET_KEY .env | cut -d= -f2) \
ALLOWED_HOSTS=tagayev.uz python manage.py check --deploy
```

Natija **"System check identified no issues"** boʻlishi kerak. Loyiha bu
tekshiruvni avtomatlashtirilgan testda ham ushlab turadi
(`apps/common/test_deploy.py`).

---

## gunicorn (systemd)

```bash
sudo cp /home/ubuntu/tagayev/deploy/tagayev.service /etc/systemd/system/tagayev.service
# Unit sintaksisini tekshiring:
systemd-analyze verify /etc/systemd/system/tagayev.service
sudo systemctl daemon-reload
sudo systemctl enable --now tagayev
sudo systemctl status tagayev        # active (running) boʻlishi kerak
journalctl -u tagayev -f             # loglar
```

gunicorn unix-socketni `/run/tagayev/gunicorn.sock` da yaratadi
(`deploy/gunicorn.conf.py`). Worker sonini `.env` da `GUNICORN_WORKERS` bilan
sozlash mumkin (SQLite uchun 2–3 yetarli).

> **gunicorn 25+ "Control server error":** yangi gunicorn versiyalari boshqaruv
> socketini `~/.gunicorn` ga yozadi, lekin servis `ProtectHome=read-only` bilan
> ishlaydi — shuning uchun `deploy/gunicorn.conf.py` da
> `control_socket_disable = True` qoʻyilgan (biz `gunicornc` ishlatmaymiz).

### Avtomatik deploy uchun `sudo` (CI/CD)

GitHub Actions (`.github/workflows/deploy.yml`) `ubuntu` sifatida SSH orqali
ulanib, oxirida `sudo systemctl restart tagayev` bajaradi. Bu CI da **parolsiz**
ishlashi uchun tor doiradagi NOPASSWD qoidasini qoʻshing:

```bash
echo 'ubuntu ALL=(root) NOPASSWD: /usr/bin/systemctl restart tagayev, /usr/bin/systemctl reload tagayev' \
  | sudo tee /etc/sudoers.d/tagayev-deploy
sudo chmod 440 /etc/sudoers.d/tagayev-deploy
sudo visudo -cf /etc/sudoers.d/tagayev-deploy    # sintaksisni tekshiring
```

---

## nginx

```bash
# Rate-limit zonalari (http kontekstida — conf.d ga):
sudo cp /home/ubuntu/tagayev/deploy/nginx-ratelimit.conf /etc/nginx/conf.d/tagayev-ratelimit.conf
# Sayt konfiguratsiyasi:
sudo cp /home/ubuntu/tagayev/deploy/tagayev.uz.conf /etc/nginx/sites-available/tagayev.uz.conf
sudo ln -s /etc/nginx/sites-available/tagayev.uz.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

---

## HTTPS (Certbot)

```bash
sudo certbot --nginx -d tagayev.uz -d www.tagayev.uz
```

Certbot `tagayev.uz.conf` ni avtomatik tahrirlaydi: 443-portli TLS bloki va
HTTP→HTTPS yoʻnaltirishni qoʻshadi. Sertifikat avtomatik yangilanadi
(`systemctl status certbot.timer`).

HTTPS ishlagach, kerak boʻlsa `tagayev.uz.conf` dagi **CSP** (Content-Security-Policy)
blokini izohdan chiqaring va brauzer konsolida har bir sahifani tekshiring
(barcha tashqi resurslar — shriftlar, xaritalar, video — ishlashini).

---

## Geo-IP jadval

Dashboarddagi "Davlatlar boʻyicha tashriflar" paneli `resolve_geoip` buyruq
ishlamaguncha boʻsh boʻladi. Uni 30 daqiqada bir avtomatik ishlatamiz:

```bash
sudo cp /home/ubuntu/tagayev/deploy/tagayev-resolve-geoip.service /etc/systemd/system/
sudo cp /home/ubuntu/tagayev/deploy/tagayev-resolve-geoip.timer   /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tagayev-resolve-geoip.timer
sudo systemctl list-timers tagayev-resolve-geoip.timer
```

---

## DDoS va rate-limit himoyasi

Himoya **uch qatlamda** qurilgan:

### 1-qatlam — Ilova darajasi (allaqachon yoqilgan)
- **Honeypot** maydoni — botlar ariza formasini toʻldirsa, jimgina rad etiladi.
- **IP rate-limit** — bitta IP dan soatiga 5 tadan ortiq ariza qabul qilinmaydi
  (`apps/leads/views.py`). Hisoblagich **umumiy cache** (DatabaseCache) da
  saqlanadi, shuning uchun barcha gunicorn worker'lar boʻylab toʻgʻri ishlaydi.

### 2-qatlam — nginx (chekka/edge)
`deploy/nginx-ratelimit.conf` quyidagi cheklovlarni qoʻyadi (limit oshsa **429**):

| Zona | Cheklov | Qayerda |
|------|---------|---------|
| `tg_general` | 20 soʻrov/sek (burst 40) | barcha sahifalar |
| `tg_form` | 10 soʻrov/daq (burst 5) | `POST /ariza/` |
| `tg_login` | 20 soʻrov/daq (burst 10) | `/admin/login/` |
| `tg_conn` | 20 parallel ulanish/IP | barchasi (slow-loris) |

### 3-qatlam — fail2ban (firewall darajasida IP bloklash)
nginx loglarini kuzatib, cheklovni qayta-qayta buzgan IP larni **iptables**
darajasida bloklaydi — keyingi trafik nginx gacha ham yetib bormaydi.

```bash
sudo cp /home/ubuntu/tagayev/deploy/fail2ban/filter.d/tagayev-nginx-429.conf /etc/fail2ban/filter.d/
sudo cp /home/ubuntu/tagayev/deploy/fail2ban/jail.d/tagayev.conf /etc/fail2ban/jail.d/
# O'z IP manzilingizni jail.d/tagayev.conf ichidagi `ignoreip` ga qo'shing!
# Filtr regex'ini haqiqiy logga moslab tekshiring (0 ta match boʻlsa, format farq qiladi):
sudo fail2ban-regex /var/log/nginx/access.log /etc/fail2ban/filter.d/tagayev-nginx-429.conf
sudo systemctl enable --now fail2ban
sudo fail2ban-client status                      # jail roʻyxati
sudo fail2ban-client status tagayev-nginx-429 # bloklangan IP lar
sudo fail2ban-client set <jail> unbanip 1.2.3.4  # qoʻlda blokdan chiqarish
```

### Hajmli (volumetric) DDoS haqida muhim eslatma
Yuqoridagi himoyalar **ilova darajasidagi** suiisteʼmol (spam, brute-force,
sekin floodlar) ga qarshi samarali. Ammo **katta hajmli L3/L4 DDoS** (kanalni
toʻldiradigan) ni bitta server yoki nginx **toʻxtata olmaydi** — buning uchun
saytni quyidagilar orqasiga qoʻyish kerak:

- **Cloudflare** (bepul reja ham DDoS himoyasi + WAF beradi) — eng oson yechim,
- yoki **AWS Shield / CloudFront / WAF** (AWS da hosting boʻlsa),
- yoki provayder/CDN darajasidagi himoya.

> Tavsiya: domenni **Cloudflare** orqali ulang (proxy yoqilgan) — bu volumetric
> DDoS, bot himoyasi va keshlashni bir vaqtda beradi.

> **Cloudflare ishlatsangiz:** endi nginx oldida yana bitta proksi turadi, shuning
> uchun `.env` ga `TRUSTED_PROXY_COUNT=2` qoʻshing. Bu ariza rate-limiti
> `X-Forwarded-For` dan **haqiqiy** mijoz IP sini toʻgʻri olishini taʼminlaydi
> (aks holda barcha tashriflar Cloudflare IP si sifatida koʻrinib, rate-limit
> notoʻgʻri ishlaydi). Standart qiymat `1` (faqat nginx).

---

## Yangilash (redeploy)

```bash
cd /home/ubuntu/tagayev && source venv/bin/activate
git pull --ff-only
pip install -r requirements.txt
python manage.py migrate
python manage.py tailwind build            # collectstatic'dan OLDIN — aks holda CSS yig'ilmaydi
python manage.py collectstatic --noinput
python manage.py compilemo                 # .po → .mo (polib; serverda msgfmt yo'q)
sudo systemctl restart tagayev
```

---

## Zaxira nusxa

SQLite bazasi va yuklangan media — eng muhim maʼlumotlar:

```bash
# Baza (WAL rejimida xavfsiz nusxa olish uchun .backup ishlating):
sqlite3 /home/ubuntu/tagayev/db.sqlite3 ".backup '/home/ubuntu/backups/db-$(date +%F).sqlite3'"
# Media fayllar:
tar czf /home/ubuntu/backups/media-$(date +%F).tar.gz -C /home/ubuntu/tagayev media
```

> Bu buyruqlarni `cron` yoki systemd timer orqali kunlik avtomatlashtiring, va
> nusxalarni boshqa joyga (S3 va h.k.) koʻchiring.

---

## Muammolarni hal qilish

### 502 Bad Gateway
gunicorn ishlamayapti yoki socketga ruxsat yoʻq.
```bash
sudo systemctl status tagayev
journalctl -u tagayev -n 50
ls -l /run/tagayev/gunicorn.sock     # www-data oʻqiy olishi kerak
```

### Statik fayllar (CSS) yuklanmayapti
`collectstatic` bajarilmagan yoki nginx `alias` yoʻli notoʻgʻri.
```bash
python manage.py collectstatic --noinput
ls /home/ubuntu/tagayev/staticfiles/css/tailwind.css
```

### Yuklangan rasm/video koʻrinmayapti (404)
nginx `/media/` `alias` yoʻlini va kataloq ruxsatlarini tekshiring.

### `DisallowedHost` xatosi
`.env` dagi `ALLOWED_HOSTS` ga domeningiz kiritilmagan.

### Ariza yuborilganda 429
Rate-limit ishlayapti — bu normal. Test uchun cache jadvalini tozalang:
`python manage.py shell -c "from django.core.cache import cache; cache.clear()"`

### `manage.py check --deploy` xato beryapti
Xato matnini oʻqing — odatda `SECRET_KEY` zaif yoki `ALLOWED_HOSTS=*`.

---

## Bogʻliq qoʻllanmalar

- [`ORNATISH.md`](ORNATISH.md) — mahalliy (dev) oʻrnatish
- [`ADMIN.md`](ADMIN.md) — admin panelda kontent boshqaruvi
