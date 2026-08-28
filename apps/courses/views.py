from django.views.generic import DetailView, ListView

from .models import Course


class CourseListView(ListView):
    template_name = "courses/list.html"
    context_object_name = "courses"
    paginate_by = 12

    def get_queryset(self):
        return Course.objects.filter(is_active=True).select_related("category")


class CourseDetailView(DetailView):
    template_name = "courses/detail.html"
    context_object_name = "course"

    def get_queryset(self):
        return (
            Course.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("images")
        )
