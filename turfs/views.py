from datetime import datetime, timedelta

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Turf
from bookings.models import Booking


@login_required(login_url="login")
def home(request):

    turfs = Turf.objects.filter(is_active=True)

    return render(
        request,
        "turfs/home.html",
        {
            "turfs": turfs
        }
    )


@login_required(login_url="login")
def turf_detail(request, turf_id):

    turf = get_object_or_404(
        Turf,
        id=turf_id,
        is_active=True
    )

    selected_date = request.GET.get("date")

    slots = []

    current_time = datetime.combine(
        datetime.today().date(),
        turf.opening_time
    )

    closing_time = datetime.combine(
        datetime.today().date(),
        turf.closing_time
    )

    booked_times = []

    if selected_date:

        booked_times = list(
            Booking.objects.filter(
                turf=turf,
                booking_date=selected_date,
                status="confirmed"
            ).values_list(
                "start_time",
                flat=True
            )
        )

    while current_time + timedelta(hours=1) <= closing_time:

        end_time = current_time + timedelta(hours=1)

        is_booked = current_time.time() in booked_times

        slots.append({
            "start": current_time.time(),
            "end": end_time.time(),
            "is_booked": is_booked,
        })

        current_time = end_time

    return render(
        request,
        "turfs/turf_detail.html",
        {
            "turf": turf,
            "slots": slots,
            "selected_date": selected_date,
        }
    )