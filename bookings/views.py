import razorpay

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import (
    login_required,
    user_passes_test,
)
from django.db import IntegrityError
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .models import Booking
from turfs.models import Turf


# Razorpay Client
razorpay_client = razorpay.Client(
    auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET
    )
)


# ==================================================
# CREATE MULTIPLE BOOKINGS
# ==================================================

@login_required
def create_booking(request):

    if request.method != "POST":
        return redirect("home")

    turf_id = request.POST.get("turf_id")

    booking_date = request.POST.get(
        "booking_date"
    )

    # Get multiple selected slots
    start_times = request.POST.getlist(
        "start_times"
    )

    # Backward compatibility for single-slot booking
    if not start_times:

        single_start_time = request.POST.get(
            "start_time"
        )

        if single_start_time:
            start_times = [single_start_time]

    if (
        not turf_id
        or not booking_date
        or not start_times
    ):

        messages.error(
            request,
            "Please select at least one valid time slot."
        )

        return redirect("home")

    turf = get_object_or_404(
        Turf,
        id=turf_id,
        is_active=True
    )

    created_booking_ids = []

    for start_time in start_times:

        try:

            start_time_obj = datetime.strptime(
                start_time,
                "%H:%M"
            ).time()

            start_datetime = datetime.combine(
                datetime.today().date(),
                start_time_obj
            )

            end_datetime = (
                start_datetime
                + timedelta(hours=1)
            )

            end_time_obj = end_datetime.time()

        except ValueError:

            messages.warning(
                request,
                f"Invalid time slot: {start_time}"
            )

            continue

        # Check whether the slot is already booked
        active_booking_exists = Booking.objects.filter(
            turf=turf,
            booking_date=booking_date,
            start_time=start_time_obj
        ).exclude(
            status="cancelled"
        ).exists()

        if active_booking_exists:

            messages.warning(
                request,
                f"Slot {start_time} is already booked."
            )

            continue

        # Check whether a previously cancelled booking exists
        cancelled_booking = Booking.objects.filter(
            turf=turf,
            booking_date=booking_date,
            start_time=start_time_obj,
            status="cancelled"
        ).first()

        if cancelled_booking:

            cancelled_booking.user = request.user

            cancelled_booking.end_time = end_time_obj

            cancelled_booking.status = "pending"

            cancelled_booking.payment_status = "pending"

            cancelled_booking.payment_method = ""

            cancelled_booking.save()

            created_booking_ids.append(
                cancelled_booking.id
            )

            continue

        try:

            booking = Booking.objects.create(
                user=request.user,
                turf=turf,
                booking_date=booking_date,
                start_time=start_time_obj,
                end_time=end_time_obj,
                status="pending",
                payment_status="pending"
            )

            created_booking_ids.append(
                booking.id
            )

        except IntegrityError:

            messages.warning(
                request,
                f"Slot {start_time} was just booked by another user."
            )

            continue

    # If no slots were created
    if not created_booking_ids:

        messages.error(
            request,
            "None of the selected slots are available."
        )

        return redirect(
            f"/turf/{turf.id}/?date={booking_date}"
        )

    # Save all booking IDs in session
    request.session[
        "selected_booking_ids"
    ] = created_booking_ids

    messages.success(
        request,
        f"{len(created_booking_ids)} slot(s) selected successfully."
    )

    # Go to payment page
    return redirect(
        "payment",
        booking_id=created_booking_ids[0]
    )


# ==================================================
# MY BOOKINGS
# ==================================================

@login_required
def my_bookings(request):

    bookings = Booking.objects.filter(
        user=request.user
    ).order_by(
        "-booking_date",
        "-start_time"
    )

    return render(
        request,
        "bookings/my_bookings.html",
        {
            "bookings": bookings
        }
    )


# ==================================================
# CANCEL BOOKING
# ==================================================

@login_required
def cancel_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    if request.method == "POST":

        booking.delete()

        messages.success(
            request,
            "Your booking has been cancelled successfully."
        )

    return redirect(
        "my_bookings"
    )


# ==================================================
# PAYMENT PAGE
# ==================================================

@login_required
def payment(request, booking_id):

    selected_booking_ids = request.session.get(
        "selected_booking_ids",
        []
    )

    # Fallback for direct payment access
    if not selected_booking_ids:

        booking = get_object_or_404(
            Booking,
            id=booking_id,
            user=request.user
        )

        selected_booking_ids = [booking.id]

        request.session[
            "selected_booking_ids"
        ] = selected_booking_ids

    bookings = Booking.objects.filter(
        id__in=selected_booking_ids,
        user=request.user
    ).select_related(
        "turf"
    ).order_by(
        "booking_date",
        "start_time"
    )

    if not bookings.exists():

        messages.error(
            request,
            "No bookings found for payment."
        )

        return redirect(
            "my_bookings"
        )

    # Calculate total price
    total_amount = sum(
        booking.turf.price_per_hour
        for booking in bookings
    )

    return render(
        request,
        "bookings/payment.html",
        {
            "booking": bookings.first(),
            "bookings": bookings,
            "total_amount": total_amount,
            "total_slots": bookings.count(),
        }
    )


# ==================================================
# PROCESS PAYMENT METHOD
# ==================================================

@login_required
def process_payment(request, booking_id):

    if request.method != "POST":

        return redirect(
            "payment",
            booking_id=booking_id
        )

    selected_booking_ids = request.session.get(
        "selected_booking_ids",
        []
    )

    if not selected_booking_ids:

        messages.error(
            request,
            "Your selected slots were not found."
        )

        return redirect(
            "my_bookings"
        )

    bookings = Booking.objects.filter(
        id__in=selected_booking_ids,
        user=request.user
    )

    if not bookings.exists():

        messages.error(
            request,
            "No bookings found."
        )

        return redirect(
            "my_bookings"
        )

    payment_method = request.POST.get(
        "payment_method"
    )

    # ------------------------------------------
    # ONLINE PAYMENT
    # ------------------------------------------

    if payment_method == "online":

        bookings.update(
            payment_method="online"
        )

        return redirect(
            "online_payment",
            booking_id=booking_id
        )

    # ------------------------------------------
    # OFFLINE PAYMENT
    # ------------------------------------------

    elif payment_method == "offline":

        bookings.update(
            payment_method="offline",
            payment_status="pending",
            status="pending"
        )

        request.session.pop(
            "selected_booking_ids",
            None
        )

        messages.info(
            request,
            "Your bookings have been submitted. "
            "Please wait for admin approval."
        )

        return redirect(
            "my_bookings"
        )

    messages.error(
        request,
        "Please select a valid payment method."
    )

    return redirect(
        "payment",
        booking_id=booking_id
    )


# ==================================================
# ADMIN DASHBOARD
# ==================================================

@staff_member_required
def admin_dashboard(request):

    bookings = Booking.objects.all().order_by(
        "-booking_date",
        "-start_time"
    )

    total_bookings = bookings.count()

    pending_bookings = bookings.filter(
        status="pending"
    ).count()

    confirmed_bookings = bookings.filter(
        status="confirmed"
    ).count()

    paid_payments = bookings.filter(
        payment_status="paid"
    ).count()

    return render(
        request,
        "bookings/admin_dashboard.html",
        {
            "bookings": bookings,
            "total_bookings": total_bookings,
            "pending_bookings": pending_bookings,
            "confirmed_bookings": confirmed_bookings,
            "paid_payments": paid_payments,
        }
    )


# ==================================================
# ADMIN MARK PAYMENT AS PAID
# ==================================================

@staff_member_required
def mark_payment_paid(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    if request.method == "POST":

        booking.payment_status = "paid"

        booking.status = "confirmed"

        booking.save()

        messages.success(
            request,
            "Booking approved and payment marked as paid."
        )

    return redirect(
        "admin_dashboard"
    )


# ==================================================
# ONLINE PAYMENT / RAZORPAY
# ==================================================

@login_required
def online_payment(request, booking_id):

    selected_booking_ids = request.session.get(
        "selected_booking_ids",
        []
    )

    if not selected_booking_ids:

        messages.error(
            request,
            "Your selected slots were not found."
        )

        return redirect(
            "my_bookings"
        )

    bookings = Booking.objects.filter(
        id__in=selected_booking_ids,
        user=request.user
    ).select_related(
        "turf"
    ).order_by(
        "booking_date",
        "start_time"
    )

    if not bookings.exists():

        messages.error(
            request,
            "No bookings found for payment."
        )

        return redirect(
            "my_bookings"
        )

    # Calculate total price
    total_amount = sum(
        booking.turf.price_per_hour
        for booking in bookings
    )

    # Razorpay requires amount in paise
    amount = int(
        total_amount * 100
    )

    try:

        razorpay_order = razorpay_client.order.create(
            {
                "amount": amount,
                "currency": "INR",
                "payment_capture": 1
            }
        )

        return render(
            request,
            "bookings/online_payment.html",
            {
                "booking": bookings.first(),
                "bookings": bookings,
                "total_amount": total_amount,
                "total_slots": bookings.count(),
                "razorpay_order_id": razorpay_order["id"],
                "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                "amount": amount,
            }
        )

    except Exception as e:

        print(
            "RAZORPAY ERROR:",
            str(e)
        )

        messages.error(
            request,
            "Unable to start payment. Please try again."
        )

        return redirect(
            "payment",
            booking_id=booking_id
        )


# ==================================================
# VERIFY RAZORPAY PAYMENT
# ==================================================

@login_required
def verify_payment(request, booking_id):

    if request.method != "POST":

        return redirect(
            "my_bookings"
        )

    selected_booking_ids = request.session.get(
        "selected_booking_ids",
        []
    )

    if not selected_booking_ids:

        messages.error(
            request,
            "Your selected bookings were not found."
        )

        return redirect(
            "my_bookings"
        )

    bookings = Booking.objects.filter(
        id__in=selected_booking_ids,
        user=request.user
    )

    if not bookings.exists():

        messages.error(
            request,
            "No bookings found."
        )

        return redirect(
            "my_bookings"
        )

    payment_id = request.POST.get(
        "razorpay_payment_id"
    )

    order_id = request.POST.get(
        "razorpay_order_id"
    )

    signature = request.POST.get(
        "razorpay_signature"
    )

    try:

        razorpay_client.utility.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            }
        )

        # Confirm ALL selected slots
        bookings.update(
            payment_method="online",
            payment_status="paid",
            status="confirmed"
        )

        # Remove booking IDs from session
        request.session.pop(
            "selected_booking_ids",
            None
        )

        messages.success(
            request,
            "Payment successful! All your selected slots are confirmed."
        )

        return redirect(
            "my_bookings"
        )

    except razorpay.errors.SignatureVerificationError:

        bookings.update(
            payment_status="failed"
        )

        messages.error(
            request,
            "Payment verification failed. Please try again."
        )

        return redirect(
            "payment",
            booking_id=booking_id
        )


# ==================================================
# ADMIN LOGIN
# ==================================================

def admin_login(request):

    if request.method == "POST":

        username = request.POST.get(
            "username"
        )

        password = request.POST.get(
            "password"
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None and user.is_staff:

            login(
                request,
                user
            )

            return redirect(
                "admin_dashboard"
            )

        messages.error(
            request,
            "Invalid admin username or password."
        )

    return render(
        request,
        "bookings/admin_login.html"
    )


# ==================================================
# MANAGE BOOKINGS
# ==================================================

@staff_member_required
def manage_bookings(request):

    bookings = Booking.objects.select_related(
        "turf",
        "user"
    ).all().order_by(
        "-booking_date",
        "-start_time"
    )

    total_bookings = bookings.count()

    pending_bookings = bookings.filter(
        status="pending"
    ).count()

    confirmed_bookings = bookings.filter(
        status="confirmed"
    ).count()

    return render(
        request,
        "bookings/manage_bookings.html",
        {
            "bookings": bookings,
            "total_bookings": total_bookings,
            "pending_bookings": pending_bookings,
            "confirmed_bookings": confirmed_bookings,
        }
    )


# ==================================================
# CONFIRM BOOKING
# ==================================================

@staff_member_required
def confirm_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    if request.method == "POST":

        booking.status = "confirmed"

        if booking.payment_status == "pending":

            booking.payment_status = "paid"

        booking.save()

        messages.success(
            request,
            "Booking confirmed successfully."
        )

    return redirect(
        "manage_bookings"
    )


# ==================================================
# SUPER ADMIN CHECK
# ==================================================

def is_super_admin(user):

    return (
        user.is_authenticated
        and user.is_superuser
    )


# ==================================================
# ADMIN CANCEL BOOKING
# ==================================================

@user_passes_test(
    is_super_admin,
    login_url="admin_login"
)
def admin_cancel_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    if request.method == "POST":

        booking.status = "cancelled"

        booking.save()

        messages.success(
            request,
            "Booking cancelled successfully. "
            "This slot is now available for other users."
        )

    return redirect(
        "manage_bookings"
    )