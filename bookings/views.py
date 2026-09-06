import razorpay

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from .models import Booking
from turfs.models import Turf, TurfSlot


razorpay_client = razorpay.Client(
    auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET
    )
)


@login_required
def create_booking(request):

    if request.method != "POST":
        return redirect("home")

    turf_id = request.POST.get("turf_id")
    booking_date = request.POST.get("booking_date")
    slot_id = request.POST.get("slot_id")

    if not turf_id or not booking_date or not slot_id:
        messages.error(
            request,
            "Please select a valid date and time slot."
        )
        return redirect("home")

    turf = get_object_or_404(
        Turf,
        id=turf_id,
        is_active=True
    )

    slot = get_object_or_404(
        TurfSlot,
        id=slot_id,
        turf=turf,
        is_active=True
    )

    already_booked = Booking.objects.filter(
        turf=turf,
        booking_date=booking_date,
        start_time=slot.start_time
    ).exclude(
        status="cancelled"
    ).exists()

    if already_booked:

        messages.error(
            request,
            "Sorry! This slot is already booked."
        )

        return redirect(
            "turf_detail",
            turf_id=turf.id
        )

    try:

        booking = Booking.objects.create(
            user=request.user,
            turf=turf,
            booking_date=booking_date,
            start_time=slot.start_time,
            end_time=slot.end_time,
            status="pending",
            payment_status="pending"
        )

        return redirect(
            "payment",
            booking_id=booking.id
        )

    except IntegrityError:

        messages.error(
            request,
            "This slot was just booked by another user."
        )

        return redirect(
            "turf_detail",
            turf_id=turf.id
        )


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
            "Your booking has been cancelled and removed successfully."
        )

    return redirect("my_bookings")


@login_required
def payment(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    return render(
        request,
        "bookings/payment.html",
        {
            "booking": booking
        }
    )


@login_required
def process_payment(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    if request.method != "POST":

        return redirect(
            "payment",
            booking_id=booking.id
        )

    payment_method = request.POST.get(
        "payment_method"
    )

    if payment_method == "online":

        booking.payment_method = "online"
        booking.save()

        return redirect(
            "online_payment",
            booking_id=booking.id
        )

    elif payment_method == "offline":

        booking.payment_method = "offline"
        booking.payment_status = "pending"
        booking.status = "pending"
        booking.save()

        messages.info(
            request,
            "Offline booking submitted successfully. Please wait for admin approval."
        )

        return redirect("my_bookings")

    messages.error(
        request,
        "Please select a valid payment method."
    )

    return redirect(
        "payment",
        booking_id=booking.id
    )


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

    return redirect("admin_dashboard")


@login_required
def online_payment(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    amount = int(
        booking.turf.price_per_hour * 100
    )

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
            "booking": booking,
            "razorpay_order_id": razorpay_order["id"],
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "amount": amount,
        }
    )


@login_required
def verify_payment(request, booking_id):

    if request.method != "POST":
        return redirect("my_bookings")

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
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

        booking.payment_method = "online"
        booking.payment_status = "paid"
        booking.status = "confirmed"
        booking.save()

        messages.success(
            request,
            "Payment successful! Your booking is confirmed."
        )

        return redirect("my_bookings")

    except razorpay.errors.SignatureVerificationError:

        booking.payment_status = "failed"
        booking.save()

        messages.error(
            request,
            "Payment verification failed. Please try again."
        )

        return redirect(
            "payment",
            booking_id=booking.id
        )


def admin_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None and user.is_staff:

            login(request, user)

            return redirect("admin_dashboard")

        messages.error(
            request,
            "Invalid admin username or password."
        )

    return render(
        request,
        "bookings/admin_login.html"
    )

@staff_member_required
def manage_bookings(request):

    bookings = Booking.objects.all().order_by(
        "-booking_date",
        "-start_time"
    )

    return render(
        request,
        "bookings/manage_bookings.html",
        {
            "bookings": bookings
        }
    )


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

    return redirect("manage_bookings")


@staff_member_required
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
            "Booking cancelled successfully."
        )

    return redirect("manage_bookings")    