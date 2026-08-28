from django.urls import path

from .views import CourseDetailView, CourseListView

app_name = "courses"

urlpatterns = [
    path("kurslar/", CourseListView.as_view(), name="list"),
    path("kurslar/<slug:slug>/", CourseDetailView.as_view(), name="detail"),
]
