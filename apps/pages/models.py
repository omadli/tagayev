from django.db import models
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field
from solo.models import SingletonModel

from apps.common.constants import ICON_CHOICES
from apps.common.models import OrderedActiveModel, VideoMixin
from apps.common.validators import image_validators


class AboutSection(OrderedActiveModel):
    """'Biz haqimizda' bo'limining matni (birinchi faol yozuv ko'rsatiladi)."""

    title = models.CharField(_("Sarlavha"), max_length=200)
    subtitle = models.CharField(_("Kichik sarlavha"), max_length=200, blank=True)
    body = CKEditor5Field(_("Matn"), config_name="default", blank=True)
    image = models.ImageField(_("Rasm"), upload_to="about/", blank=True, validators=image_validators)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Biz haqimizda bo'limi")
        verbose_name_plural = _("Biz haqimizda bo'limi")

    def __str__(self):
        return self.title


class StatItem(OrderedActiveModel):
    """Statistika raqamlari (hero bo'limida counter bilan)."""

    number = models.PositiveIntegerField(_("Raqam"), default=0)
    suffix = models.CharField(_("Belgi"), max_length=8, blank=True, help_text="+, %, k …")
    label = models.CharField(_("Izoh"), max_length=80)
    accent = models.BooleanField(_("Qizil rang bilan"), default=False)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Statistika raqami")
        verbose_name_plural = _("Statistika raqamlari")

    def __str__(self):
        return f"{self.number}{self.suffix} — {self.label}"


class WhyUsItem(OrderedActiveModel):
    """'Nega biz' kartalari."""

    title = models.CharField(_("Sarlavha"), max_length=120)
    description = models.TextField(_("Tavsif"), blank=True)
    icon = models.CharField(_("Ikonka"), max_length=20, choices=ICON_CHOICES, default="cap")
    accent = models.BooleanField(_("Qizil ikonka"), default=False)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Nega biz — karta")
        verbose_name_plural = _("Nega biz — kartalar")

    def __str__(self):
        return self.title


class HeroSection(SingletonModel):
    """Bosh sahifa 'hero' blokidagi tahrirlanadigan matnlar (yagona yozuv)."""

    badge_text = models.CharField(
        _("Yorliq matni"), max_length=160,
        default="Zamonaviy taʼlim markazi",
        help_text=_("Hero tepasidagi kichik yorliq (masalan, shahar)."),
    )
    title_prefix = models.CharField(
        _("Sarlavha — boshi"), max_length=120, default="Farzandingiz kelajagi",
        help_text=_("Sayt nomidan oldingi qism."),
    )
    title_suffix = models.CharField(
        _("Sarlavha — oxiri"), max_length=120, default="dan boshlanadi",
        help_text=_("Sayt nomidan keyingi qism."),
    )
    primary_cta = models.CharField(
        _("Asosiy tugma"), max_length=60, default="Bepul darsga yoziling",
    )
    secondary_cta = models.CharField(
        _("Ikkilamchi tugma"), max_length=60, default="Kurslarni koʻrish",
    )
    # Hero rasmi ustidagi suzuvchi yorliqlardagi raqamlar. Faqat qiymat
    # (raqam) tahrirlanadi; atrofidagi so'zlar ({% translate %}) tarjimada
    # qoladi, shuning uchun bu maydonlar tildan mustaqil — modeltranslationsiz.
    metric1_value = models.CharField(
        _("1-yorliq — qiymat"), max_length=40, default="IELTS 7.5",
        help_text=_("Chap yuqoridagi yorliq, masalan «IELTS 7.5» ('oʻrtacha' izohi bilan)."),
    )
    metric2_value = models.CharField(
        _("2-yorliq — qiymat"), max_length=20, default="100+",
        help_text=_("«Bu oy … yangi oʻquvchi» yorlig'idagi raqam, masalan «100+»."),
    )
    image = models.ImageField(
        _("Rasm"), upload_to="hero/", blank=True, validators=image_validators,
        help_text=_("Hero blokidagi katta rasm/poster."),
    )

    class Meta:
        verbose_name = _("Hero bo'limi")
        verbose_name_plural = _("Hero bo'limi")

    def __str__(self):
        return "Hero bo'limi"


class SiteCopy(SingletonModel):
    """Bo'lim sarlavhalari va forma matnlari — barchasi admin-tahrir (yagona yozuv)."""

    # --- Natijalar bo'limi ---
    results_eyebrow = models.CharField(
        _("Natijalar — yorliq"), max_length=80, default="Natijalar",
    )
    results_title = models.CharField(
        _("Natijalar — sarlavha"), max_length=160, default="Oʻquvchilarimiz natijalari",
    )
    results_link_label = models.CharField(
        _("Natijalar — havola matni"), max_length=80, default="Barcha natijalar",
    )
    testimonials_title = models.CharField(
        _("Fikrlar — sarlavha"), max_length=120, default="Ota-onalar fikri",
    )

    # --- Kontakt bo'limi ---
    contact_eyebrow = models.CharField(
        _("Kontakt — yorliq"), max_length=80, default="Bogʻlanish",
    )
    contact_title = models.CharField(
        _("Kontakt — sarlavha"), max_length=160, default="Bepul sinov darsiga yoziling",
    )
    contact_intro = models.TextField(
        _("Kontakt — matn"), blank=True,
        default="Arizangizni qoldiring — mutaxassisimiz qaytib qoʻngʻiroq qiladi "
                "va sizga mos kursni tanlashda yordam beradi.",
    )
    lead_submit_label = models.CharField(
        _("Kontakt — yuborish tugmasi"), max_length=60, default="Arizani yuborish",
    )

    # --- Ariza oynasi (modal) ---
    modal_title = models.CharField(
        _("Oyna — sarlavha"), max_length=120, default="Ariza qoldirish",
    )
    modal_subtitle = models.CharField(
        _("Oyna — matn"), max_length=200,
        default="Maʻlumotlaringizni qoldiring, tez orada bogʻlanamiz.",
    )
    modal_submit_label = models.CharField(
        _("Oyna — yuborish tugmasi"), max_length=60, default="Yuborish",
    )

    # --- Footer ---
    footer_note = models.CharField(
        _("Footer — pastki matn"), max_length=120, default="", blank=True,
    )

    class Meta:
        verbose_name = _("Sayt matnlari")
        verbose_name_plural = _("Sayt matnlari")

    def __str__(self):
        return "Sayt matnlari"


class HomeVideo(VideoMixin, SingletonModel):
    """Optional video showcase block on the home page (yagona yozuv)."""

    is_enabled = models.BooleanField(_("Yoqilgan"), default=False)
    title = models.CharField(_("Sarlavha"), max_length=160, blank=True)
    subtitle = models.CharField(_("Kichik matn"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Bosh sahifa videosi")
        verbose_name_plural = _("Bosh sahifa videosi")

    def __str__(self):
        return "Bosh sahifa videosi"


class Partner(OrderedActiveModel):
    """A partner organisation shown in the homepage marquee (text only)."""

    name = models.CharField(_("Nomi"), max_length=80)
    website_url = models.URLField(_("Veb-sayt (ixtiyoriy)"), blank=True)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Hamkor")
        verbose_name_plural = _("Hamkorlar")

    def __str__(self):
        return self.name
