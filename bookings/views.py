from decimal import Decimal

import razorpay

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .models import Booking


# Razorpay Client
razorpay_client = razorpay.Client(
    auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET
    )
)


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
            "Offline booking submitted successfully. "
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
        booking_id=booking.id
    )


@login_required
def online_payment(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    # Amount in paise
    amount = int(
        Decimal(booking.turf.price_per_hour) * 100
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

        return redirect(
            "my_bookings"
        )

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

        return redirect(
            "my_bookings"
        )

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