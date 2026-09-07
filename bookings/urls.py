from django.urls import path

from . import views


urlpatterns = [

    # ==========================================
    # USER BOOKING
    # ==========================================

    path(
        "create/",
        views.create_booking,
        name="create_booking"
    ),

    path(
        "my-bookings/",
        views.my_bookings,
        name="my_bookings"
    ),

    path(
        "cancel/<int:booking_id>/",
        views.cancel_booking,
        name="cancel_booking"
    ),


    # ==========================================
    # PAYMENT
    # ==========================================

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
        "online-payment/<int:booking_id>/",
        views.online_payment,
        name="online_payment"
    ),

    path(
        "verify-payment/<int:booking_id>/",
        views.verify_payment,
        name="verify_payment"
    ),


    # ==========================================
    # ADMIN
    # ==========================================

    path(
        "admin-login/",
        views.admin_login,
        name="admin_login"
    ),

    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin_dashboard"
    ),

    path(
        "manage-bookings/",
        views.manage_bookings,
        name="manage_bookings"
    ),

    path(
        "booking-details/<int:booking_id>/",
        views.booking_details,
        name="booking_details"
    ),


    # ==========================================
    # BOOKING APPROVAL
    # ==========================================

    path(
        "approve-booking/<int:booking_id>/",
        views.approve_booking,
        name="approve_booking"
    ),

    path(
        "admin-cancel-booking/<int:booking_id>/",
        views.admin_cancel_booking,
        name="admin_cancel_booking"
    ),

    path(
        "confirm-booking/<int:booking_id>/",
        views.confirm_booking,
        name="confirm_booking"
    ),


    # ==========================================
    # OFFLINE PAYMENT
    # ==========================================

    path(
        "mark-payment-paid/<int:booking_id>/",
        views.mark_payment_paid,
        name="mark_payment_paid"
    ),

    path(
        "mark-payment-unpaid/<int:booking_id>/",
        views.mark_payment_unpaid,
        name="mark_payment_unpaid"
    ),

]