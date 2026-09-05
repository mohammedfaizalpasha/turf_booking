from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create_booking, name="create_booking"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
    path(
        "cancel/<int:booking_id>/",
        views.cancel_booking,
        name="cancel_booking"
    ),

path(
    "payment/<int:booking_id>/",
    views.payment,
    name="payment"
),

path(
    "payment/<int:booking_id>/process/",
    views.process_payment,
    name="process_payment"
),

path(
    "admin-dashboard/",
    views.admin_dashboard,
    name="admin_dashboard"
),

path(
    "mark-payment-paid/<int:booking_id>/",
    views.mark_payment_paid,
    name="mark_payment_paid"
),

path(
    "online-payment/<int:booking_id>/",
    views.online_payment,
    name="online_payment"
),

path(
    "verify-payment/<int:booking_id>/",
    views.verify_payment,
    name="verify_payment"
),

path(
    "admin-login/",
    views.admin_login,
    name="admin_login"
),
]