from django.urls import path
from . import views

urlpatterns = [

    # Create booking
    path(
        "create-booking/",
        views.create_booking,
        name="create_booking"
    ),

    # My bookings
    path(
        "my-bookings/",
        views.my_bookings,
        name="my_bookings"
    ),

    # Cancel booking
    path(
        "cancel-booking/<int:booking_id>/",
        views.cancel_booking,
        name="cancel_booking"
    ),

    # Select payment method
    path(
        "payment/<int:booking_id>/",
        views.payment,
        name="payment"
    ),

    # Process selected payment method
    path(
        "process-payment/<int:booking_id>/",
        views.process_payment,
        name="process_payment"
    ),

    # Razorpay payment page
    path(
        "online-payment/<int:booking_id>/",
        views.online_payment,
        name="online_payment"
    ),

    # Verify Razorpay payment
    path(
        "verify-payment/<int:booking_id>/",
        views.verify_payment,
        name="verify_payment"
    ),

    # Admin login
    path(
        "admin-login/",
        views.admin_login,
        name="admin_login"
    ),

    # Admin dashboard
    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin_dashboard"
    ),

    # Approve payment
    path(
        "mark-payment-paid/<int:booking_id>/",
        views.mark_payment_paid,
        name="mark_payment_paid"
    ),
]