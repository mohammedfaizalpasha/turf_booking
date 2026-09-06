from django.contrib import admin

from .models import Turf, TurfSlot


@admin.register(Turf)
class TurfAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "location",
        "price_per_hour",
        "opening_time",
        "closing_time",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "location",
    )


@admin.register(TurfSlot)
class TurfSlotAdmin(admin.ModelAdmin):

    list_display = (
        "turf",
        "date",
        "start_time",
        "end_time",
        "is_active",
        "created_at",
    )

    list_filter = (
        "turf",
        "date",
        "is_active",
    )

    search_fields = (
        "turf__name",
    )

    ordering = (
        "date",
        "start_time",
    )