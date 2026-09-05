from django.contrib import admin
from django.urls import path, include
from turfs import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path(
        "turf/<int:turf_id>/",
        views.turf_detail,
        name="turf_detail"
    ),
    path("booking/", include("bookings.urls")),
    path("accounts/", include("accounts.urls")),
]