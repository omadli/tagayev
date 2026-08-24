# -*- coding: utf-8 -*-
"""
Build GNU-format .po + .mo catalogs for ru and en WITHOUT GNU gettext.

Strategy (gettext binaries are missing on this machine):
  1. Programmatically extract translatable msgids from templates and Python
     source so the *exact bytes* of each Uzbek key are preserved (the source
     mixes U+02BB, U+02BC and ASCII apostrophes -- gettext lookup is byte-exact).
  2. Translate by NORMALIZED key (all apostrophe variants -> ASCII ') so the
     "Oʻqituvchilar" / "O'qituvchilar" duplicates map to one translation.
  3. Emit valid .po (with correct Plural-Forms headers) and compile .mo via polib.

Run with the venv python from the project root:
    set PYTHONIOENCODING=utf-8
    venv\\Scripts\\python.exe locale\\_build_catalogs.py
"""
import os
import re

import polib
import unfold

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNFOLD_TPL = os.path.join(os.path.dirname(unfold.__file__), "templates")

# ---------------------------------------------------------------------------
# Apostrophe normalization (for translation-map lookup only; msgid keeps bytes)
# ---------------------------------------------------------------------------
APOS = {
    "ʻ": "'",  # ʻ MODIFIER LETTER TURNED COMMA (templates)
    "ʼ": "'",  # ʼ MODIFIER LETTER APOSTROPHE (news/teachers)
    "‘": "'",  # ‘
    "’": "'",  # ’
    "′": "'",  # ′
    "`": "'",
}


def norm(s):
    for k, v in APOS.items():
        s = s.replace(k, v)
    return s


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------
def walk(root, exts):
    for dirpath, dirnames, filenames in os.walk(root):
        if "venv" in dirpath or "staticfiles" in dirpath or "__pycache__" in dirpath:
            continue
        for fn in filenames:
            if os.path.splitext(fn)[1] in exts:
                yield os.path.join(dirpath, fn)


# {% translate "..." %} / {% trans "..." %} / {% translate '...' %}
TPL_RE = re.compile(r"{%\s*(?:translate|trans)\s+(\"[^\"]*\"|'[^']*')\s*%}")
# {% blocktranslate count var=... %}TEXT{% plural %}TEXT{% endblocktranslate %}
BLOCK_RE = re.compile(
    r"{%\s*blocktranslate\b[^%]*%}(.*?){%\s*plural\s*%}(.*?){%\s*endblocktranslate\s*%}",
    re.DOTALL,
)
# _("...") / _('...') / gettext_lazy("...") / gettext("...")
PY_RE = re.compile(r"(?:gettext_lazy|gettext|pgettext|_)\s*\(\s*(\"[^\"]*\"|'[^']*')")


def unquote(tok):
    return tok[1:-1]


def blocktext_to_msgid(t):
    # Django converts {{ var }} -> %(var)s for blocktranslate msgids.
    t = t.strip()
    t = re.sub(r"{{\s*(\w+)\s*}}", r"%(\1)s", t)
    return t


def unfold_msgids():
    """Exact {% trans %} msgids across Unfold's templates (Unfold ships no
    catalog, so we supply ru translations for its UI strings)."""
    ids = set()
    for dirpath, _dirs, files in os.walk(UNFOLD_TPL):
        for fn in files:
            if fn.endswith(".html"):
                with open(os.path.join(dirpath, fn), encoding="utf-8") as fh:
                    for m in TPL_RE.finditer(fh.read()):
                        ids.add(unquote(m.group(1)))
    return ids


singular = set()       # exact msgid bytes
plural_pairs = set()   # (msgid, msgid_plural) bytes

# Templates
for path in walk(os.path.join(BASE, "templates"), {".html"}):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    for m in TPL_RE.finditer(src):
        singular.add(unquote(m.group(1)))
    # Also catch _("...") used inside template tags, e.g. Unfold components:
    #   {% component "..." with title=_('Sayt kontenti') %}
    for m in PY_RE.finditer(src):
        singular.add(unquote(m.group(1)))
    for m in BLOCK_RE.finditer(src):
        sing = blocktext_to_msgid(m.group(1))
        plur = blocktext_to_msgid(m.group(2))
        plural_pairs.add((sing, plur))

# Python source: apps + config/settings.py (UNFOLD nav + Meta verbose_names)
py_files = list(walk(os.path.join(BASE, "apps"), {".py"}))
py_files.append(os.path.join(BASE, "config", "settings.py"))
for path in py_files:
    if path.endswith("_build_catalogs.py"):
        continue
    with open(path, encoding="utf-8") as f:
        src = f.read()
    for m in PY_RE.finditer(src):
        singular.add(unquote(m.group(1)))

# Drop any plural singular forms accidentally also caught as plain singulars
for sing, _plur in plural_pairs:
    singular.discard(sing)

# ---------------------------------------------------------------------------
# Translation maps, keyed by NORMALIZED Uzbek source.
# ---------------------------------------------------------------------------
RU = {
    # --- Accessibility (a11y) ---
    "Asosiy kontentga oʻtish": "Перейти к основному содержимому",
    "Menyu": "Меню",
    "Tilni tanlash": "Выбрать язык",
    "Oldingi": "Назад",
    "Keyingi": "Далее",
    # --- Navigation / header / footer ---
    "Biz haqimizda": "О нас",
    "Kurslar": "Курсы",
    "Yangiliklar": "Новости",
    "Oʻqituvchilar": "Преподаватели",
    "Natijalar": "Результаты",
    "Bogʻlanish": "Контакты",
    "Ariza qoldirish": "Оставить заявку",
    "Rejimni almashtirish": "Сменить тему",
    "Sahifalar": "Страницы",
    "Telegram kanal": "Telegram-канал",
    "Telegram guruh": "Telegram-группа",
    "Barcha huquqlar himoyalangan.": "Все права защищены.",
    "Bosh sahifa": "Главная",
    # --- Hero ---
    "Zamonaviy taʻlim markazi · Toshkent": "Современный образовательный центр · Ташкент",
    "Farzandingiz kelajagi": "Будущее вашего ребёнка",
    "dan boshlanadi": " начинается с",
    "Bepul darsga yoziling": "Записаться на бесплатный урок",
    "Kurslarni koʻrish": "Посмотреть курсы",
    "oʻrtacha": "в среднем",
    "Bu oy": "В этом месяце",
    "yangi oʻquvchi": "новых учеников",
    # --- About ---
    "Biz bilan bogʻlaning": "Свяжитесь с нами",
    "Jamoamiz bilan tanishing": "Познакомьтесь с нашей командой",
    # --- Courses ---
    "Yoʻnalishlar": "Направления",
    "Bizning kurslarimiz": "Наши курсы",
    "Narx — murojaat orqali": "Цена — по запросу",
    "Batafsil": "Подробнее",
    "Davomiyligi": "Длительность",
    "Guruh": "Группа",
    # --- News ---
    "Yangiliklar va eʻlonlar": "Новости и объявления",
    "Markaz yangiliklari": "Новости центра",
    "Barchasi": "Все",
    "Boshqa yangiliklar": "Другие новости",
    "Hozircha yangilik yo'q.": "Пока нет новостей.",
    # --- Gallery ---
    "Galereya": "Галерея",
    "Oʻquv jarayonimizdan lavhalar": "Моменты учебного процесса",
    "Hozircha rasm yo'q.": "Пока нет изображений.",
    # --- Results / certificates / testimonials ---
    "Oʻquvchilarimiz yutuqlari": "Достижения наших учеников",
    "Barcha sertifikatlar": "Все сертификаты",
    "Ota-onalar fikri": "Отзывы родителей",
    "Sertifikatlar": "Сертификаты",
    "Oʻquvchilarimiz sertifikatlari": "Сертификаты наших учеников",
    "Hozircha sertifikat yo'q.": "Пока нет сертификатов.",
    # --- Teachers ---
    "Jamoa": "Команда",
    "Tajribali oʻqituvchilar": "Опытные преподаватели",
    "Darsga yoziling": "Записаться на урок",
    "%(years)s yil tajriba": "%(years)s лет опыта",
    # --- Contact section ---
    "Bepul sinov darsiga yoziling": "Запишитесь на бесплатный пробный урок",
    "Arizangizni qoldiring — mutaxassisimiz qaytib qoʻngʻiroq qiladi va sizga mos kursni tanlashda yordam beradi.":
        "Оставьте заявку — наш специалист перезвонит и поможет подобрать подходящий курс.",
    "Ism familiya": "Имя и фамилия",
    "Ismingiz": "Ваше имя",
    "Telefon raqam": "Номер телефона",
    "Qaysi kurs?": "Какой курс?",
    "Kursni tanlang (ixtiyoriy)": "Выберите курс (необязательно)",
    "Qoʻshimcha izoh": "Дополнительный комментарий",
    "Savolingiz yoki qoʻshimcha maʼlumot…": "Ваш вопрос или дополнительная информация…",
    "Arizani yuborish": "Отправить заявку",
    "Joylashuv admin paneldan belgilanadi": "Местоположение задаётся в админ-панели",
    "Manzil": "Адрес",
    "Telefon": "Телефон",
    "Ijtimoiy tarmoqlar": "Социальные сети",
    "Kanal": "Канал",
    "Guruh": "Группа",
    # --- Modal / mobile bar ---
    "Maʻlumotlaringizni qoldiring, tez orada bogʻlanamiz.":
        "Оставьте свои данные, мы скоро свяжемся с вами.",
    "Yuborish": "Отправить",
    "Yopish": "Закрыть",
    "Qoʻshimcha izoh (ixtiyoriy)": "Дополнительный комментарий (необязательно)",
    "Qoʻngʻiroq": "Позвонить",
    # --- base.html toast ---
    "Arizangiz qabul qilindi!": "Ваша заявка принята!",
    # --- leads (views/forms) ---
    "Juda koʻp soʻrov. Birozdan soʻng urinib koʻring.":
        "Слишком много запросов. Повторите попытку чуть позже.",
    "Telefon raqamni +998XXXXXXXXX koʻrinishida kiriting.":
        "Введите номер телефона в формате +998XXXXXXXXX.",
    # ---------------------------------------------------------------
    # Admin / models — verbose names, field labels, fieldsets
    # ---------------------------------------------------------------
    # common
    "Yaratilgan": "Создано",
    "Yangilangan": "Обновлено",
    "Tartib raqami": "Порядковый номер",
    "Kichik raqam yuqorida ko'rinadi.": "Меньший номер отображается выше.",
    "Saytda ko'rsatilsin": "Показывать на сайте",
    "Fayl hajmi %(mb)s MB dan oshmasligi kerak.": "Размер файла не должен превышать %(mb)s МБ.",
    # icon choices
    "Bitiruv shapkasi": "Выпускная шапочка",
    "Foydalanuvchi": "Пользователь",
    "Metodika": "Методика",
    "Qalqon (kafolat)": "Щит (гарантия)",
    "Kitob / til": "Книга / язык",
    "Hisob / matematika": "Счёт / математика",
    "Kod / IT": "Код / IT",
    "Grafik": "График",
    "Soat": "Часы",
    "Yulduz": "Звезда",
    "Til (globus)": "Язык (глобус)",
    # courses
    "Nomi": "Название",
    "Slug": "Слаг",
    "Kurs turkumi": "Категория курса",
    "Kurs turkumlari": "Категории курсов",
    "Turkum": "Категория",
    "Qisqa tavsif": "Краткое описание",
    "To'liq tavsif": "Полное описание",
    "Guruh hajmi": "Размер группы",
    "Narx": "Цена",
    "Narx izohi": "Примечание к цене",
    "Narx ko'rsatilsin": "Показывать цену",
    "Ikonka": "Иконка",
    "Rasm": "Изображение",
    "Top kurs (qizil belgi)": "Топ-курс (красная метка)",
    "SEO sarlavha": "SEO-заголовок",
    "SEO tavsif": "SEO-описание",
    "OG rasm": "OG-изображение",
    "Kurs": "Курс",
    # certificates
    "Sarlavha": "Заголовок",
    "O'quvchi ismi": "Имя ученика",
    "Izoh": "Комментарий",
    "Belgi": "Метка",
    "Qizil belgi": "Красная метка",
    "PDF fayl": "PDF-файл",
    "Tashqi havola": "Внешняя ссылка",
    "Sertifikat": "Сертификат",
    "Rasm, PDF yoki tashqi havoladan kamida bittasini kiriting.":
        "Укажите хотя бы одно: изображение, PDF или внешнюю ссылку.",
    # certificates — CEFR import (admin)
    "CEFR / havola (QR skaner)": "CEFR / ссылка (QR-сканер)",
    "CEFR sertifikati havolasini kiriting yoki QR kodni skanerlang — saqlaganda PDF rasmga aylantiriladi va oʻquvchi ismi aniqlanadi.":
        "Введите ссылку на сертификат CEFR или отсканируйте QR-код — при сохранении PDF преобразуется в изображение и определяется имя ученика.",
    "Havoladan import qilindi (rasm + ism aniqlandi). Tekshirib saqlang.":
        "Импортировано по ссылке (изображение + имя определены). Проверьте и сохраните.",
    "Avto-import boʻlmadi: %(e)s": "Автоимпорт не удался: %(e)s",
    "Havoladan qayta import qilish (PDF→rasm + ism)":
        "Повторно импортировать по ссылке (PDF→изображение + имя)",
    "Import yakunlandi — muvaffaqiyatli: %(ok)d, xato: %(f)d.":
        "Импорт завершён — успешно: %(ok)d, ошибок: %(f)d.",
    # gallery
    "Albom nomi": "Название альбома",
    "Tavsif": "Описание",
    "Muqova rasmi": "Обложка",
    "Galereya albomi": "Альбом галереи",
    "Galereya albomlari": "Альбомы галереи",
    "Albom": "Альбом",
    "Galereya rasmi": "Изображение галереи",
    "Galereya rasmlari": "Изображения галереи",
    "ALT matn (SEO)": "ALT-текст (SEO)",
    # testimonials
    "Muallif": "Автор",
    "Roli": "Роль",
    "Fikr matni": "Текст отзыва",
    "Baho (1–5)": "Оценка (1–5)",
    "Tanlangan": "Избранное",
    "Fikr": "Отзыв",
    "Fikrlar (ota-onalar)": "Отзывы (родители)",
    "Fikrlar": "Отзывы",
    # news
    "Qisqa matn": "Краткий текст",
    "To'liq matn": "Полный текст",
    "Belgi (tag)": "Метка (тег)",
    "Chop etilgan sana": "Дата публикации",
    "Chop etilgan": "Опубликовано",
    "Yangilik / eʼlon": "Новость / объявление",
    # pages
    "Kichik sarlavha": "Подзаголовок",
    "Matn": "Текст",
    "Biz haqimizda bo'limi": "Раздел «О нас»",
    "Raqam": "Число",
    "Statistika raqami": "Статистический показатель",
    "Statistika raqamlari": "Статистические показатели",
    "Nega biz — karta": "Почему мы — карточка",
    "Nega biz — kartalar": "Почему мы — карточки",
    "Qizil rang bilan": "Красным цветом",
    "Qizil ikonka": "Красная иконка",
    "Statistika": "Статистика",
    "Nega biz": "Почему мы",
    # leads
    "Yangi": "Новая",
    "Bogʻlanildi": "Связались",
    "Oʻquvchi boʻldi": "Стал учеником",
    "Rad etildi": "Отклонена",
    "Manba": "Источник",
    "UTM yoki referrer (avtomatik toʻldiriladi).": "UTM или реферер (заполняется автоматически).",
    "Holat": "Статус",
    "Telegramga yuborildi": "Отправлено в Telegram",
    "Ariza": "Заявка",
    "Arizalar": "Заявки",
    # siteconfig
    "Sayt nomi": "Название сайта",
    "Shior": "Слоган",
    "Logo": "Логотип",
    "Bo'sh qoldirilsa, standart logo ishlatiladi.":
        "Если оставить пустым, используется логотип по умолчанию.",
    "Favicon": "Favicon",
    "Domen": "Домен",
    "Masalan: tagayev.uz (protokolsiz). Sitemap/canonical uchun.":
        "Например: tagayev.uz (без протокола). Для sitemap/canonical.",
    "Asosiy telefon": "Основной телефон",
    "Qo'shimcha telefon": "Дополнительный телефон",
    "Email": "Эл. почта",
    "Ish vaqti": "Часы работы",
    "Kenglik (lat)": "Широта (lat)",
    "Uzunlik (lng)": "Долгота (lng)",
    "Google Maps embed": "Встраивание Google Maps",
    "Yandex Maps embed": "Встраивание Yandex Maps",
    "Instagram": "Instagram",
    "YouTube": "YouTube",
    "Facebook": "Facebook",
    "TikTok": "TikTok",
    "OG rasm (ulashish)": "OG-изображение (для шеринга)",
    "Google verification": "Подтверждение Google",
    "Yandex verification": "Подтверждение Yandex",
    "Bing verification": "Подтверждение Bing",
    "Google Analytics 4 ID": "ID Google Analytics 4",
    "Yandex Metrica ID": "ID Yandex Metrica",
    "Telegram bildirishnomalari yoniq": "Уведомления Telegram включены",
    "Sayt sozlamalari": "Настройки сайта",
    # siteconfig admin fieldsets
    "Brending": "Брендинг",
    "Kontaktlar": "Контакты",
    "Joylashuv (xaritadan tanlang)": "Местоположение (выберите на карте)",
    "Xaritani bosib yoki qidirib joylashuvni tanlang. ":
        "Выберите местоположение, кликнув по карте или через поиск. ",
    "Xarita — qo‘lda override (ixtiyoriy)": "Карта — ручное переопределение (необязательно)",
    "Faqat maxsus embed kerak bo‘lsa to‘ldiring. Bo‘sh qoldirilsa, ":
        "Заполняйте только при необходимости особого embed. Если оставить пустым, ",
    "Ijtimoiy tarmoqlar": "Социальные сети",
    "SEO": "SEO",
    "Analitika": "Аналитика",
    "Telegram": "Telegram",
    # siteconfig widget
    "Manzilni qidiring (masalan: Chilonzor, Toshkent)…":
        "Найдите адрес (например: Чиланзар, Ташкент)…",
    "Qidirish": "Поиск",
    "Xaritani bosing yoki belgini suring — koordinatalar avtomatik to‘ladi.":
        "Кликните по карте или перетащите метку — координаты заполнятся автоматически.",
    # teachers
    "F.I.Sh.": "Ф.И.О.",
    "Lavozim / yo'nalish": "Должность / направление",
    "Bio / tavsif": "Биография / описание",
    "Fanlar": "Предметы",
    "Tajriba (yil)": "Опыт (лет)",
    "O'qituvchi": "Преподаватель",
    "O'qituvchilar": "Преподаватели",
    # UNFOLD nav (settings.py)
    "Boshqaruv paneli": "Панель управления",
    "Boshqaruv": "Управление",
    "Saytni koʻrish": "Посмотреть сайт",
    "Sayt mazmuni": "Содержимое сайта",
    "Bosh sahifa bloklari": "Блоки главной страницы",
    "Murojaatlar": "Обращения",
    "Sozlamalar": "Настройки",
    "Foydalanuvchilar": "Пользователи",
    # analytics model
    "Planshet": "Планшет",
    "Kompyuter": "Компьютер",
    "Bot": "Бот",
    "Boshqa": "Прочее",
    "Metod": "Метод",
    "Yoʻnaltiruvchi": "Источник перехода",
    "IP manzil": "IP-адрес",
    "Brauzer maʼlumoti": "Данные браузера",
    "Qurilma turi": "Тип устройства",
    "Brauzer": "Браузер",
    "Operatsion tizim": "Операционная система",
    "Til": "Язык",
    "Vaqti": "Время",
    "Tashrif": "Визит",
    "Tashriflar": "Визиты",
    # analytics dashboard
    "Bugungi tashriflar": "Визиты сегодня",
    "Tashriflar (30 kun)": "Визиты (30 дней)",
    "Jami tashriflar": "Всего визитов",
    "Yangi arizalar": "Новые заявки",
    "Arizalar (30 kun)": "Заявки (30 дней)",
    "Kurslar / oʻqituvchilar": "Курсы / преподаватели",
    "Qurilmalar": "Устройства",
    "Sahifa": "Страница",
}

EN = {
    "Asosiy kontentga oʻtish": "Skip to main content",
    "Menyu": "Menu",
    "Tilni tanlash": "Choose language",
    "Oldingi": "Previous",
    "Keyingi": "Next",
    "Biz haqimizda": "About us",
    "Kurslar": "Courses",
    "Yangiliklar": "News",
    "Oʻqituvchilar": "Teachers",
    "Natijalar": "Results",
    "Bogʻlanish": "Contact",
    "Ariza qoldirish": "Apply now",
    "Rejimni almashtirish": "Toggle theme",
    "Sahifalar": "Pages",
    "Telegram kanal": "Telegram channel",
    "Telegram guruh": "Telegram group",
    "Barcha huquqlar himoyalangan.": "All rights reserved.",
    "Bosh sahifa": "Home",
    "Zamonaviy taʻlim markazi · Toshkent": "Modern education center · Tashkent",
    "Farzandingiz kelajagi": "Your child's future",
    "dan boshlanadi": " starts with",
    "Bepul darsga yoziling": "Book a free lesson",
    "Kurslarni koʻrish": "View courses",
    "oʻrtacha": "average",
    "Bu oy": "This month",
    "yangi oʻquvchi": "new students",
    "Biz bilan bogʻlaning": "Get in touch",
    "Jamoamiz bilan tanishing": "Meet our team",
    "Yoʻnalishlar": "Programs",
    "Bizning kurslarimiz": "Our courses",
    "Narx — murojaat orqali": "Price — on request",
    "Batafsil": "Learn more",
    "Davomiyligi": "Duration",
    "Guruh": "Group",
    "Yangiliklar va eʻlonlar": "News and announcements",
    "Markaz yangiliklari": "Center news",
    "Barchasi": "View all",
    "Boshqa yangiliklar": "Other news",
    "Hozircha yangilik yo'q.": "No news yet.",
    "Galereya": "Gallery",
    "Oʻquv jarayonimizdan lavhalar": "Moments from our learning process",
    "Hozircha rasm yo'q.": "No images yet.",
    "Oʻquvchilarimiz yutuqlari": "Our students' achievements",
    "Barcha sertifikatlar": "All certificates",
    "Ota-onalar fikri": "Parents' reviews",
    "Sertifikatlar": "Certificates",
    "Oʻquvchilarimiz sertifikatlari": "Our students' certificates",
    "Hozircha sertifikat yo'q.": "No certificates yet.",
    "Jamoa": "Team",
    "Tajribali oʻqituvchilar": "Experienced teachers",
    "Darsga yoziling": "Book a lesson",
    "%(years)s yil tajriba": "%(years)s years of experience",
    "Bepul sinov darsiga yoziling": "Sign up for a free trial lesson",
    "Arizangizni qoldiring — mutaxassisimiz qaytib qoʻngʻiroq qiladi va sizga mos kursni tanlashda yordam beradi.":
        "Leave your request — our specialist will call you back and help you choose the right course.",
    "Ism familiya": "Full name",
    "Ismingiz": "Your name",
    "Telefon raqam": "Phone number",
    "Qaysi kurs?": "Which course?",
    "Kursni tanlang (ixtiyoriy)": "Choose a course (optional)",
    "Qoʻshimcha izoh": "Additional note",
    "Savolingiz yoki qoʻshimcha maʼlumot…": "Your question or additional details…",
    "Arizani yuborish": "Submit request",
    "Joylashuv admin paneldan belgilanadi": "Location is set in the admin panel",
    "Manzil": "Address",
    "Telefon": "Phone",
    "Ijtimoiy tarmoqlar": "Social networks",
    "Kanal": "Channel",
    "Maʻlumotlaringizni qoldiring, tez orada bogʻlanamiz.":
        "Leave your details and we'll get in touch soon.",
    "Yuborish": "Send",
    "Yopish": "Close",
    "Qoʻshimcha izoh (ixtiyoriy)": "Additional note (optional)",
    "Qoʻngʻiroq": "Call",
    "Arizangiz qabul qilindi!": "Your request has been received!",
    "Juda koʻp soʻrov. Birozdan soʻng urinib koʻring.":
        "Too many requests. Please try again shortly.",
    "Telefon raqamni +998XXXXXXXXX koʻrinishida kiriting.":
        "Enter the phone number in the format +998XXXXXXXXX.",
    # admin / models
    "Yaratilgan": "Created",
    "Yangilangan": "Updated",
    "Tartib raqami": "Order number",
    "Kichik raqam yuqorida ko'rinadi.": "A smaller number is shown higher.",
    "Saytda ko'rsatilsin": "Show on site",
    "Fayl hajmi %(mb)s MB dan oshmasligi kerak.": "File size must not exceed %(mb)s MB.",
    "Bitiruv shapkasi": "Graduation cap",
    "Foydalanuvchi": "User",
    "Metodika": "Methodology",
    "Qalqon (kafolat)": "Shield (guarantee)",
    "Kitob / til": "Book / language",
    "Hisob / matematika": "Calculation / math",
    "Kod / IT": "Code / IT",
    "Grafik": "Chart",
    "Soat": "Clock",
    "Yulduz": "Star",
    "Til (globus)": "Language (globe)",
    "Nomi": "Name",
    "Slug": "Slug",
    "Kurs turkumi": "Course category",
    "Kurs turkumlari": "Course categories",
    "Turkum": "Category",
    "Qisqa tavsif": "Short description",
    "To'liq tavsif": "Full description",
    "Guruh hajmi": "Group size",
    "Narx": "Price",
    "Narx izohi": "Price note",
    "Narx ko'rsatilsin": "Show price",
    "Ikonka": "Icon",
    "Rasm": "Image",
    "Top kurs (qizil belgi)": "Top course (red badge)",
    "SEO sarlavha": "SEO title",
    "SEO tavsif": "SEO description",
    "OG rasm": "OG image",
    "Kurs": "Course",
    "Sarlavha": "Title",
    "O'quvchi ismi": "Student name",
    "Izoh": "Note",
    "Belgi": "Badge",
    "Qizil belgi": "Red badge",
    "PDF fayl": "PDF file",
    "Tashqi havola": "External link",
    "Sertifikat": "Certificate",
    "Rasm, PDF yoki tashqi havoladan kamida bittasini kiriting.":
        "Provide at least one of: image, PDF, or external link.",
    # certificates — CEFR import (admin)
    "CEFR / havola (QR skaner)": "CEFR / link (QR scanner)",
    "CEFR sertifikati havolasini kiriting yoki QR kodni skanerlang — saqlaganda PDF rasmga aylantiriladi va oʻquvchi ismi aniqlanadi.":
        "Enter the CEFR certificate link or scan the QR code — on save the PDF is converted to an image and the student's name is detected.",
    "Havoladan import qilindi (rasm + ism aniqlandi). Tekshirib saqlang.":
        "Imported from the link (image + name detected). Review and save.",
    "Avto-import boʻlmadi: %(e)s": "Auto-import failed: %(e)s",
    "Havoladan qayta import qilish (PDF→rasm + ism)":
        "Re-import from the link (PDF→image + name)",
    "Import yakunlandi — muvaffaqiyatli: %(ok)d, xato: %(f)d.":
        "Import finished — successful: %(ok)d, failed: %(f)d.",
    "Albom nomi": "Album name",
    "Tavsif": "Description",
    "Muqova rasmi": "Cover image",
    "Galereya albomi": "Gallery album",
    "Galereya albomlari": "Gallery albums",
    "Albom": "Album",
    "Galereya rasmi": "Gallery image",
    "Galereya rasmlari": "Gallery images",
    "ALT matn (SEO)": "ALT text (SEO)",
    "Muallif": "Author",
    "Roli": "Role",
    "Fikr matni": "Review text",
    "Baho (1–5)": "Rating (1–5)",
    "Tanlangan": "Featured",
    "Fikr": "Review",
    "Fikrlar (ota-onalar)": "Reviews (parents)",
    "Fikrlar": "Reviews",
    "Qisqa matn": "Short text",
    "To'liq matn": "Full text",
    "Belgi (tag)": "Badge (tag)",
    "Chop etilgan sana": "Published date",
    "Chop etilgan": "Published",
    "Yangilik / eʼlon": "News / announcement",
    "Kichik sarlavha": "Subtitle",
    "Matn": "Text",
    "Biz haqimizda bo'limi": "\"About us\" section",
    "Raqam": "Number",
    "Statistika raqami": "Statistic item",
    "Statistika raqamlari": "Statistic items",
    "Nega biz — karta": "Why us — card",
    "Nega biz — kartalar": "Why us — cards",
    "Qizil rang bilan": "In red color",
    "Qizil ikonka": "Red icon",
    "Statistika": "Statistics",
    "Nega biz": "Why us",
    "Yangi": "New",
    "Bogʻlanildi": "Contacted",
    "Oʻquvchi boʻldi": "Enrolled",
    "Rad etildi": "Rejected",
    "Manba": "Source",
    "UTM yoki referrer (avtomatik toʻldiriladi).": "UTM or referrer (filled automatically).",
    "Holat": "Status",
    "Telegramga yuborildi": "Sent to Telegram",
    "Ariza": "Request",
    "Arizalar": "Requests",
    "Sayt nomi": "Site name",
    "Shior": "Tagline",
    "Logo": "Logo",
    "Bo'sh qoldirilsa, standart logo ishlatiladi.":
        "If left empty, the default logo is used.",
    "Favicon": "Favicon",
    "Domen": "Domain",
    "Masalan: tagayev.uz (protokolsiz). Sitemap/canonical uchun.":
        "E.g. tagayev.uz (without protocol). For sitemap/canonical.",
    "Asosiy telefon": "Primary phone",
    "Qo'shimcha telefon": "Secondary phone",
    "Email": "Email",
    "Ish vaqti": "Working hours",
    "Kenglik (lat)": "Latitude (lat)",
    "Uzunlik (lng)": "Longitude (lng)",
    "Google Maps embed": "Google Maps embed",
    "Yandex Maps embed": "Yandex Maps embed",
    "Instagram": "Instagram",
    "YouTube": "YouTube",
    "Facebook": "Facebook",
    "TikTok": "TikTok",
    "OG rasm (ulashish)": "OG image (sharing)",
    "Google verification": "Google verification",
    "Yandex verification": "Yandex verification",
    "Bing verification": "Bing verification",
    "Google Analytics 4 ID": "Google Analytics 4 ID",
    "Yandex Metrica ID": "Yandex Metrica ID",
    "Telegram bildirishnomalari yoniq": "Telegram notifications enabled",
    "Sayt sozlamalari": "Site settings",
    "Brending": "Branding",
    "Kontaktlar": "Contacts",
    "Joylashuv (xaritadan tanlang)": "Location (pick on the map)",
    "Xaritani bosib yoki qidirib joylashuvni tanlang. ":
        "Pick the location by clicking the map or searching. ",
    "Xarita — qo‘lda override (ixtiyoriy)": "Map — manual override (optional)",
    "Faqat maxsus embed kerak bo‘lsa to‘ldiring. Bo‘sh qoldirilsa, ":
        "Fill in only if a custom embed is needed. If left empty, ",
    "SEO": "SEO",
    "Analitika": "Analytics",
    "Telegram": "Telegram",
    "Manzilni qidiring (masalan: Chilonzor, Toshkent)…":
        "Search for an address (e.g. Chilanzar, Tashkent)…",
    "Qidirish": "Search",
    "Xaritani bosing yoki belgini suring — koordinatalar avtomatik to‘ladi.":
        "Click the map or drag the marker — coordinates fill in automatically.",
    "F.I.Sh.": "Full name",
    "Lavozim / yo'nalish": "Position / field",
    "Bio / tavsif": "Bio / description",
    "Fanlar": "Subjects",
    "Tajriba (yil)": "Experience (years)",
    "O'qituvchi": "Teacher",
    "O'qituvchilar": "Teachers",
    "Boshqaruv paneli": "Control panel",
    "Boshqaruv": "Management",
    "Saytni koʻrish": "View site",
    "Sayt mazmuni": "Site content",
    "Bosh sahifa bloklari": "Home page blocks",
    "Murojaatlar": "Inquiries",
    "Sozlamalar": "Settings",
    "Foydalanuvchilar": "Users",
    # analytics model
    "Planshet": "Tablet",
    "Kompyuter": "Desktop",
    "Bot": "Bot",
    "Boshqa": "Other",
    "Metod": "Method",
    "Yoʻnaltiruvchi": "Referrer",
    "IP manzil": "IP address",
    "Brauzer maʼlumoti": "User agent",
    "Qurilma turi": "Device type",
    "Brauzer": "Browser",
    "Operatsion tizim": "Operating system",
    "Til": "Language",
    "Vaqti": "Time",
    "Tashrif": "Visit",
    "Tashriflar": "Visits",
    # analytics dashboard
    "Bugungi tashriflar": "Visits today",
    "Tashriflar (30 kun)": "Visits (30 days)",
    "Jami tashriflar": "Total visits",
    "Yangi arizalar": "New requests",
    "Arizalar (30 kun)": "Requests (30 days)",
    "Kurslar / oʻqituvchilar": "Courses / teachers",
    "Qurilmalar": "Devices",
    "Sahifa": "Page",
}

# Merge auto-drafted + hand-corrected project translations (Phases B–F).
from _extra_translations import PROJECT_EN, PROJECT_RU, UNFOLD_RU  # noqa: E402

RU.update(PROJECT_RU)
EN.update(PROJECT_EN)

PLURAL_RU = {
    "%(years)s yil tajriba": {
        0: "%(years)s год опыта",
        1: "%(years)s года опыта",
        2: "%(years)s лет опыта",
    },
    "%(counter)s result": {
        0: "%(counter)s результат",
        1: "%(counter)s результата",
        2: "%(counter)s результатов",
    },
}
PLURAL_EN = {
    "%(years)s yil tajriba": {
        0: "%(years)s year of experience",
        1: "%(years)s years of experience",
    },
    "%(counter)s result": {
        0: "%(counter)s result",
        1: "%(counter)s results",
    },
}

PLURAL_FORMS = {
    "ru": "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
    "en": "nplurals=2; plural=(n != 1);",
}


def build(lang, tmap, pmap):
    # Normalize the translation-map keys so apostrophe variants in the source
    # (U+02BB / U+02BC / ASCII ') all resolve to the same entry.
    tmap = {norm(k): v for k, v in tmap.items()}
    pmap = {norm(k): v for k, v in pmap.items()}
    po = polib.POFile()
    po.metadata = {
        "Project-Id-Version": "tagayev 1.0",
        "Report-Msgid-Bugs-To": "",
        "POT-Creation-Date": "2026-06-06 00:00+0500",
        "PO-Revision-Date": "2026-06-06 00:00+0500",
        "Last-Translator": "i18n agent",
        "Language-Team": lang,
        "Language": lang,
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=UTF-8",
        "Content-Transfer-Encoding": "8bit",
        "Plural-Forms": PLURAL_FORMS[lang],
    }
    missing = []
    seen = set()
    for msgid in sorted(singular):
        if msgid in seen:
            continue
        seen.add(msgid)
        key = norm(msgid)
        val = tmap.get(key)
        if val is None:
            missing.append(msgid)
            val = ""  # leave untranslated; report it
        po.append(polib.POEntry(msgid=msgid, msgstr=val))
    for sing, plur in sorted(plural_pairs):
        key = norm(sing)
        forms = pmap.get(key)
        if forms is None:
            missing.append(sing + " (plural)")
            forms = {i: "" for i in range(3)}
        po.append(polib.POEntry(msgid=sing, msgid_plural=plur, msgstr_plural=forms))

    # Unfold UI strings — ru only (en keeps Unfold's own English msgids).
    if lang == "ru":
        uf = {norm(k): v for k, v in UNFOLD_RU.items()}
        existing = {e.msgid for e in po}
        for mid in sorted(unfold_msgids()):
            if mid in existing:
                continue
            val = uf.get(norm(mid))
            if val:
                po.append(polib.POEntry(msgid=mid, msgstr=val))
                existing.add(mid)

        # Curated Unfold strings from Python (_()) not templates — e.g.
        # "Select record" in unfold/admin.py — aren't found by unfold_msgids();
        # emit them by their exact msgid key.
        for key, val in UNFOLD_RU.items():
            if val and key not in existing:
                po.append(polib.POEntry(msgid=key, msgstr=val))
                existing.add(key)

    lc_dir = os.path.join(BASE, "locale", lang, "LC_MESSAGES")
    os.makedirs(lc_dir, exist_ok=True)
    po_path = os.path.join(lc_dir, "django.po")
    mo_path = os.path.join(lc_dir, "django.mo")
    po.save(po_path)
    po.save_as_mofile(mo_path)
    return po, missing, po_path, mo_path


if __name__ == "__main__":
    total_sing = len(set(singular))
    total_plur = len(plural_pairs)
    print("Extracted unique singular msgids: %d ; plural pairs: %d" % (total_sing, total_plur))
    for lang, tmap, pmap in (("ru", RU, PLURAL_RU), ("en", EN, PLURAL_EN)):
        po, missing, po_path, mo_path = build(lang, tmap, pmap)
        translated = sum(1 for e in po if (e.msgstr or any((e.msgstr_plural or {}).values())))
        print("\n[%s] entries=%d translated=%d missing=%d" % (lang, len(po), translated, len(missing)))
        print("  po=%s" % po_path)
        print("  mo=%s" % mo_path)
        if missing:
            print("  MISSING translations (%d):" % len(missing))
            for m in missing:
                print("    - %r" % m)
