from django.views.generic import TemplateView

from apps.certificates.models import Certificate
from apps.courses.models import Course
from apps.gallery.models import GalleryImage
from apps.news.models import NewsPost
from apps.teachers.models import Teacher
from apps.testimonials.models import Testimonial

from .models import AboutSection, HomeVideo, Partner, StatItem, WhyUsItem


class LandingView(TemplateView):
    template_name = "pages/landing.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["about"] = AboutSection.objects.filter(is_active=True).first()
        ctx["home_video"] = HomeVideo.get_solo()
        ctx["stats"] = StatItem.objects.filter(is_active=True)
        ctx["why_us"] = WhyUsItem.objects.filter(is_active=True)
        ctx["partners"] = Partner.objects.filter(is_active=True)
        # Karusel bo'lgani uchun kesish yo'q — barcha faol kurslar ko'rinadi.
        ctx["courses"] = Course.objects.filter(is_active=True).select_related("category")
        ctx["news"] = NewsPost.objects.filter(is_published=True)[:8]
        ctx["teachers"] = Teacher.objects.filter(is_active=True)[:12]
        ctx["certificates"] = Certificate.objects.filter(is_active=True)[:12]
        ctx["testimonials"] = Testimonial.objects.filter(is_active=True)[:12]
        ctx["gallery_images"] = (
            GalleryImage.objects.filter(is_active=True).select_related("album")[:12]
        )
        return ctx
