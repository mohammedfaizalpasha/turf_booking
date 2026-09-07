import uuid

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
from turfs.models import Turf


# ==========================================
# RAZORPAY CLIENT
# ==========================================

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

    start_times = request.POST.getlist("start_times")

    # Support single slot if needed
    if not start_times:

        single_start_time = request.POST.get("start_time")

        if single_start_time:

            start_times = [single_start_time]

    # Remove duplicate slot values
    start_times = list(
        dict.fromkeys(start_times)
    )

    if not turf_id or not booking_date or not start_times:

        messages.error(
            request,
            "Please select at least one available time slot."
        )

        return redirect(
            f"/turf/{turf_id}/?date={booking_date}"
        )

    turf = get_object_or_404(
        Turf,
        id=turf_id,
        is_active=True
    )

    # Create one group ID for all selected slots
    booking_group_id = uuid.uuid4()

    created_booking_ids = []

    unavailable_slots = []

    for start_time in start_times:

        try:

            start_time_obj = datetime.strptime(
                start_time.strip(),
                "%H:%M"
            ).time()

            start_datetime = datetime.combine(
                datetime.today().date(),
                start_time_obj
            )

            end_time_obj = (
                start_datetime + timedelta(hours=1)
            ).time()

        except ValueError:

            unavailable_slots.append(start_time)

            continue

        # Check whether this exact slot is already active
        existing_booking = Booking.objects.filter(
            turf=turf,
            booking_date=booking_date,
            start_time=start_time_obj
        ).exclude(
            status="cancelled"
        ).exists()

        if existing_booking:

            unavailable_slots.append(start_time)

            continue

        try:

            booking = Booking.objects.create(

                booking_group_id=booking_group_id,

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

            unavailable_slots.append(
                start_time
            )

            continue

    # Show information about unavailable slots
    if unavailable_slots:

        messages.warning(
            request,
            "Some selected slots were already booked: "
            + ", ".join(unavailable_slots)
        )

    # No booking was successfully created
    if not created_booking_ids:

        messages.error(
            request,
            "None of the selected slots are currently available. "
            "Please choose different slots."
        )

        return redirect(
            f"/turf/{turf.id}/?date={booking_date}"
        )

    # Save booking IDs in session
    request.session[
        "selected_booking_ids"
    ] = created_booking_ids

    request.session[
        "booking_group_id"
    ] = str(booking_group_id)

    messages.success(
        request,
        f"{len(created_booking_ids)} slot(s) added successfully. "
        "Please choose your payment method."
    )

    # IMPORTANT: Redirect to payment page
    return redirect(
        "payment",
        booking_id=created_booking_ids[0]
    )

# ==========================================
# MY BOOKINGS
# ==========================================

@login_required
def my_bookings(request):

    bookings = Booking.objects.filter(
        user=request.user
    ).exclude(
        status="cancelled"
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


# ==========================================
# CANCEL USER BOOKING
# ==========================================

@login_required
def cancel_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    if request.method == "POST":

        Booking.objects.filter(
            user=request.user,
            booking_group_id=booking.booking_group_id
        ).exclude(
            status="confirmed"
        ).update(
            status="cancelled"
        )

        messages.success(
            request,
            "Your booking has been cancelled successfully."
        )

    return redirect("my_bookings")


# ==========================================
# PAYMENT PAGE
# ==========================================

@login_required
def payment(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    bookings = Booking.objects.filter(
        booking_group_id=booking.booking_group_id,
        user=request.user
    ).exclude(
        status="cancelled"
    ).select_related(
        "turf"
    ).order_by(
        "start_time"
    )

    total_amount = sum(
        item.turf.price_per_hour
        for item in bookings
    )

    request.session[
        "selected_booking_ids"
    ] = list(
        bookings.values_list(
            "id",
            flat=True
        )
    )

    request.session[
        "booking_group_id"
    ] = str(
        booking.booking_group_id
    )

    return render(
        request,
        "bookings/payment.html",
        {
            "booking": booking,
            "bookings": bookings,
            "total_amount": total_amount,
            "total_slots": bookings.count(),
        }
    )


# ==========================================
# PROCESS PAYMENT METHOD
# ==========================================

@login_required
def process_payment(request, booking_id):

    if request.method != "POST":

        return redirect(
            "payment",
            booking_id=booking_id
        )

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    bookings = Booking.objects.filter(
        booking_group_id=booking.booking_group_id,
        user=request.user
    ).exclude(
        status="cancelled"
    )

    payment_method = request.POST.get(
        "payment_method"
    )


    # ONLINE PAYMENT
    if payment_method == "online":

        bookings.update(
            payment_method="online",
            payment_platform="razorpay",
            payment_status="pending",
            status="pending"
        )

        return redirect(
            "online_payment",
            booking_id=booking.id
        )


    # OFFLINE PAYMENT
    if payment_method == "offline":

        bookings.update(
            payment_method="offline",
            payment_platform="offline",
            payment_status="pending",
            status="pending"
        )

        messages.success(
            request,
            "Offline booking submitted successfully. "
            "Please wait for admin approval."
        )

        return redirect(
            "my_bookings"
        )


    messages.error(
        request,
        "Please select a payment method."
    )

    return redirect(
        "payment",
        booking_id=booking.id
    )


# ==========================================
# ONLINE PAYMENT PAGE
# ==========================================

@login_required
def online_payment(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    bookings = Booking.objects.filter(
        booking_group_id=booking.booking_group_id,
        user=request.user
    ).exclude(
        status="cancelled"
    ).select_related(
        "turf"
    ).order_by(
        "start_time"
    )

    total_amount = sum(
        item.turf.price_per_hour
        for item in bookings
    )

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

        bookings.update(
            razorpay_order_id=razorpay_order["id"]
        )

        return render(
            request,
            "bookings/online_payment.html",
            {
                "booking": booking,
                "bookings": bookings,
                "total_amount": total_amount,
                "total_slots": bookings.count(),
                "razorpay_order_id": razorpay_order["id"],
                "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                "amount": amount,
            }
        )

    except Exception as error:

        print(
            "RAZORPAY ERROR:",
            str(error)
        )

        messages.error(
            request,
            "Unable to start payment. Please try again."
        )

        return redirect(
            "payment",
            booking_id=booking.id
        )


# ==========================================
# VERIFY ONLINE PAYMENT
# ==========================================

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

    bookings = Booking.objects.filter(
        booking_group_id=booking.booking_group_id,
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
                "razorpay_signature": signature,
            }
        )

        bookings.update(
            payment_method="online",
            payment_platform="razorpay",
            payment_status="paid",
            payment_id=payment_id,
            razorpay_order_id=order_id,
            status="pending"
        )

        request.session.pop(
            "selected_booking_ids",
            None
        )

        request.session.pop(
            "booking_group_id",
            None
        )

        messages.success(
            request,
            "Payment successful! Please wait for admin approval."
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
            "Payment verification failed."
        )

        return redirect(
            "payment",
            booking_id=booking.id
        )


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@staff_member_required
def admin_dashboard(request):

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

    approved_bookings = bookings.filter(
        status="approved"
    ).count()

    confirmed_bookings = bookings.filter(
        status="confirmed"
    ).count()

    paid_payments = bookings.filter(
        payment_status="paid"
    ).count()

    unpaid_payments = bookings.filter(
        payment_status__in=[
            "pending",
            "unpaid"
        ]
    ).count()

    cancelled_bookings = bookings.filter(
        status="cancelled"
    ).count()

    recent_bookings = bookings[:10]

    return render(
        request,
        "bookings/admin_dashboard.html",
        {
            "bookings": recent_bookings,
            "total_bookings": total_bookings,
            "pending_bookings": pending_bookings,
            "approved_bookings": approved_bookings,
            "confirmed_bookings": confirmed_bookings,
            "paid_payments": paid_payments,
            "unpaid_payments": unpaid_payments,
            "cancelled_bookings": cancelled_bookings,
        }
    )


# ==========================================
# MANAGE BOOKINGS
# ==========================================

@staff_member_required
def manage_bookings(request):

    all_bookings = Booking.objects.select_related(
        "turf",
        "user"
    ).order_by(
        "-booking_date",
        "start_time"
    )

    grouped_bookings = []

    seen_groups = set()

    for booking in all_bookings:

        group_id = booking.booking_group_id

        if group_id in seen_groups:

            continue

        seen_groups.add(
            group_id
        )

        group_slots = all_bookings.filter(
            booking_group_id=group_id
        ).order_by(
            "start_time"
        )

        first_booking = group_slots.first()

        grouped_bookings.append(
            {
                "booking": first_booking,
                "slots": group_slots,
                "total_slots": group_slots.count(),
                "total_amount": sum(
                    slot.turf.price_per_hour
                    for slot in group_slots
                ),
            }
        )

    total_bookings = len(
        grouped_bookings
    )

    pending_bookings = sum(
        1
        for group in grouped_bookings
        if group["booking"].status == "pending"
    )

    approved_bookings = sum(
        1
        for group in grouped_bookings
        if group["booking"].status == "approved"
    )

    confirmed_bookings = sum(
        1
        for group in grouped_bookings
        if group["booking"].status == "confirmed"
    )

    return render(
        request,
        "bookings/manage_bookings.html",
        {
            "grouped_bookings": grouped_bookings,
            "total_bookings": total_bookings,
            "pending_bookings": pending_bookings,
            "approved_bookings": approved_bookings,
            "confirmed_bookings": confirmed_bookings,
        }
    )


# ==========================================
# BOOKING DETAILS
# ==========================================

@staff_member_required
def booking_details(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    bookings = Booking.objects.filter(
        booking_group_id=booking.booking_group_id
    ).select_related(
        "user",
        "turf"
    ).order_by(
        "start_time"
    )

    total_amount = sum(
        item.turf.price_per_hour
        for item in bookings
    )

    return render(
        request,
        "bookings/booking_details.html",
        {
            "booking": booking,
            "bookings": bookings,
            "total_slots": bookings.count(),
            "total_amount": total_amount,
        }
    )


# ==========================================
# APPROVE BOOKING
# ==========================================

@staff_member_required
def approve_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    if request.method == "POST":

        Booking.objects.filter(
            booking_group_id=booking.booking_group_id
        ).update(
            status="approved"
        )

        messages.success(
            request,
            "Booking approved successfully."
        )

    return redirect(
        "manage_bookings"
    )


# ==========================================
# REJECT BOOKING
# ==========================================

@staff_member_required
def admin_cancel_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    if request.method == "POST":

        Booking.objects.filter(
            booking_group_id=booking.booking_group_id
        ).update(
            status="cancelled"
        )

        messages.success(
            request,
            "Booking rejected successfully."
        )

    return redirect(
        "manage_bookings"
    )


# ==========================================
# MARK OFFLINE PAYMENT AS PAID
# ==========================================

@staff_member_required
def mark_payment_paid(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    if request.method != "POST":

        return redirect(
            "manage_bookings"
        )

    if booking.payment_method != "offline":

        messages.error(
            request,
            "Only offline payments can be marked manually."
        )

        return redirect(
            "manage_bookings"
        )

    if booking.status != "approved":

        messages.error(
            request,
            "Please approve the booking first."
        )

        return redirect(
            "manage_bookings"
        )

    Booking.objects.filter(
        booking_group_id=booking.booking_group_id
    ).update(
        payment_status="paid",
        payment_platform="offline"
    )

    messages.success(
        request,
        "Offline payment marked as paid successfully."
    )

    return redirect(
        "manage_bookings"
    )


# ==========================================
# MARK OFFLINE PAYMENT AS UNPAID
# ==========================================

@staff_member_required
def mark_payment_unpaid(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    if request.method != "POST":

        return redirect(
            "manage_bookings"
        )

    if booking.payment_method != "offline":

        messages.error(
            request,
            "Only offline payments can be marked manually."
        )

        return redirect(
            "manage_bookings"
        )

    if booking.status != "approved":

        messages.error(
            request,
            "Please approve the booking first."
        )

        return redirect(
            "manage_bookings"
        )

    Booking.objects.filter(
        booking_group_id=booking.booking_group_id
    ).update(
        payment_status="unpaid",
        payment_platform="offline"
    )

    messages.success(
        request,
        "Offline payment marked as unpaid."
    )

    return redirect(
        "manage_bookings"
    )


# ==========================================
# CONFIRM BOOKING
# ==========================================

@staff_member_required
def confirm_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    if request.method != "POST":

        return redirect(
            "manage_bookings"
        )

    bookings = Booking.objects.filter(
        booking_group_id=booking.booking_group_id
    )

    if booking.status != "approved":

        messages.error(
            request,
            "Please approve the booking first."
        )

        return redirect(
            "manage_bookings"
        )

    if (
        booking.payment_method == "offline"
        and booking.payment_status != "paid"
    ):

        messages.error(
            request,
            "Please mark the offline payment as paid first."
        )

        return redirect(
            "manage_bookings"
        )

    if (
        booking.payment_method == "online"
        and booking.payment_status != "paid"
    ):

        messages.error(
            request,
            "Online payment has not been completed successfully."
        )

        return redirect(
            "manage_bookings"
        )

    bookings.update(
        status="confirmed"
    )

    messages.success(
        request,
        "Booking confirmed successfully."
    )

    return redirect(
        "manage_bookings"
    )
    
# ==========================================
# DELETE BOOKING - ADMIN / STAFF ADMIN
# ==========================================

@staff_member_required
def delete_booking(request, booking_id):

    if request.method != "POST":

        return redirect("manage_bookings")

    booking = get_object_or_404(
        Booking,
        id=booking_id
    )

    booking_group_id = booking.booking_group_id

    Booking.objects.filter(
        booking_group_id=booking_group_id
    ).delete()

    messages.success(
        request,
        "Booking and all slots in this booking have been deleted successfully."
    )

    return redirect("manage_bookings")    


# ==========================================
# ADMIN LOGIN
# ==========================================

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


# ==========================================
# SUPER ADMIN CHECK
# ==========================================

def is_super_admin(user):

    return (
        user.is_authenticated
        and user.is_superuser
    )