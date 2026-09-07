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

    return (
        user.is_authenticated
        and user.is_superuser
    )


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


@user_passes_test(
    is_super_admin,
    login_url="admin_login"
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

    if request.method != "POST":

        return redirect(
            "superadmin_turfs"
        )

    name = request.POST.get(
        "name"
    ).strip()

    location = request.POST.get(
        "location"
    ).strip()

    map_url = request.POST.get(
        "map_url"
    ).strip()

    description = request.POST.get(
        "description"
    ).strip()

    price_per_hour = request.POST.get(
        "price_per_hour"
    )

    if not name or not location or not price_per_hour:

        messages.error(
            request,
            "Please fill all required fields."
        )

        return redirect(
            "superadmin_turfs"
        )

    Turf.objects.create(
        name=name,
        location=location,
        map_url=map_url,
        description=description,
        price_per_hour=price_per_hour,
        is_active=True
    )

    messages.success(
        request,
        "Turf added successfully."
    )

    return redirect(
        "superadmin_turfs"
    )


@user_passes_test(
    is_super_admin,
    login_url="admin_login"
)
def edit_turf(request, turf_id):

    turf = get_object_or_404(
        Turf,
        id=turf_id
    )

    if request.method != "POST":

        return redirect(
            "superadmin_turfs"
        )

    name = request.POST.get(
        "name"
    ).strip()

    location = request.POST.get(
        "location"
    ).strip()

    map_url = request.POST.get(
        "map_url"
    ).strip()

    description = request.POST.get(
        "description"
    ).strip()

    price_per_hour = request.POST.get(
        "price_per_hour"
    )

    if not name or not location or not price_per_hour:

        messages.error(
            request,
            "Please fill all required fields."
        )

        return redirect(
            "superadmin_turfs"
        )

    turf.name = name
    turf.location = location
    turf.map_url = map_url
    turf.description = description
    turf.price_per_hour = price_per_hour

    turf.save()

    messages.success(
        request,
        f"{turf.name} updated successfully."
    )

    return redirect(
        "superadmin_turfs"
    )


@user_passes_test(
    is_super_admin,
    login_url="admin_login"
)
def toggle_turf(request, turf_id):

    if request.method != "POST":

        return redirect(
            "superadmin_turfs"
        )

    turf = get_object_or_404(
        Turf,
        id=turf_id
    )

    turf.is_active = not turf.is_active

    turf.save()

    if turf.is_active:

        messages.success(
            request,
            f"{turf.name} has been activated."
        )

    else:

        messages.success(
            request,
            f"{turf.name} has been deactivated."
        )

    return redirect(
        "superadmin_turfs"
    )


@user_passes_test(
    is_super_admin,
    login_url="admin_login"
)
def delete_turf(request, turf_id):

    if request.method != "POST":

        return redirect(
            "superadmin_turfs"
        )

    turf = get_object_or_404(
        Turf,
        id=turf_id
    )

    turf_name = turf.name

    turf.delete()

    messages.success(
        request,
        f"{turf_name} deleted successfully."
    )

    return redirect(
        "superadmin_turfs"
    )


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

        current_time = datetime.combine(
            datetime.today().date(),
            datetime.min.time()
        )

        for hour in range(24):

            start_time = current_time.time()

            end_datetime = (
                current_time
                + timedelta(hours=1)
            )

            end_time = end_datetime.time()

            is_booked = (
                start_time in booked_times
            )

            slots.append(
                {
                    "start": start_time,
                    "end": end_time,
                    "is_booked": is_booked,
                }
            )

            current_time = end_datetime

    return render(
        request,
        "turfs/turf_detail.html",
        {
            "turf": turf,
            "slots": slots,
            "selected_date": selected_date,
        }
    )