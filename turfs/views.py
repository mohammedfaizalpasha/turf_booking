from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .models import Turf
from bookings.models import Booking


def is_super_admin(user):

    return user.is_authenticated and user.is_superuser


def home(request):

    turfs = Turf.objects.filter(
        is_active=True
    )

    return render(
        request,
        "turfs/home.html",
        {
            "turfs": turfs
        }
    )


def superadmin_turfs(request):

    turfs = Turf.objects.all().order_by(
        "-created_at"
    )

    return render(
        request,
        "turfs/superadmin_turfs.html",
        {
            "turfs": turfs
        }
    )


@user_passes_test(
    is_super_admin,
    login_url="admin_login"
)
def add_turf(request):

    if request.method == "POST":

        name = request.POST.get("name")
        location = request.POST.get("location")
        description = request.POST.get("description")
        price_per_hour = request.POST.get(
            "price_per_hour"
        )
        opening_time = request.POST.get(
            "opening_time"
        )
        closing_time = request.POST.get(
            "closing_time"
        )

        if not all([
            name,
            location,
            price_per_hour,
            opening_time,
            closing_time
        ]):

            messages.error(
                request,
                "Please fill all required fields."
            )

            return redirect("superadmin_turfs")

        Turf.objects.create(
            name=name,
            location=location,
            description=description,
            price_per_hour=price_per_hour,
            opening_time=opening_time,
            closing_time=closing_time,
            is_active=True
        )

        messages.success(
            request,
            "Turf added successfully."
        )

        return redirect("superadmin_turfs")

    return redirect("superadmin_turfs")


@user_passes_test(
    is_super_admin,
    login_url="admin_login"
)
def edit_turf(request, turf_id):

    turf = get_object_or_404(
        Turf,
        id=turf_id
    )

    if request.method == "POST":

        turf.name = request.POST.get(
            "name"
        )

        turf.location = request.POST.get(
            "location"
        )

        turf.description = request.POST.get(
            "description"
        )

        turf.price_per_hour = request.POST.get(
            "price_per_hour"
        )

        turf.opening_time = request.POST.get(
            "opening_time"
        )

        turf.closing_time = request.POST.get(
            "closing_time"
        )

        turf.save()

        messages.success(
            request,
            "Turf updated successfully."
        )

    return redirect("superadmin_turfs")


@user_passes_test(
    is_super_admin,
    login_url="admin_login"
)
def toggle_turf(request, turf_id):

    turf = get_object_or_404(
        Turf,
        id=turf_id
    )

    turf.is_active = not turf.is_active

    turf.save()

    messages.success(
        request,
        "Turf status updated successfully."
    )

    return redirect("superadmin_turfs")


@user_passes_test(
    is_super_admin,
    login_url="admin_login"
)
def delete_turf(request, turf_id):

    turf = get_object_or_404(
        Turf,
        id=turf_id
    )

    if request.method == "POST":

        turf.delete()

        messages.success(
            request,
            "Turf deleted successfully."
        )

    return redirect("superadmin_turfs")


def turf_detail(request, turf_id):

    turf = get_object_or_404(
        Turf,
        id=turf_id,
        is_active=True
    )

    selected_date = request.GET.get(
        "date"
    )

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
                booking_date=selected_date
            ).exclude(
                status="cancelled"
            ).values_list(
                "start_time",
                flat=True
            )
        )

    while current_time + timedelta(
        hours=1
    ) <= closing_time:

        end_time = current_time + timedelta(
            hours=1
        )

        is_booked = (
            current_time.time()
            in booked_times
        )

        slots.append(
            {
                "start": current_time.time(),
                "end": end_time.time(),
                "is_booked": is_booked,
            }
        )

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