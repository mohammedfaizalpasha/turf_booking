from django.contrib import admin
from .models import Turf


@admin.register(Turf)
class TurfAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'location',
        'price_per_hour',
        'opening_time',
        'closing_time',
        'is_active',
    )

    list_filter = ('is_active',)
    search_fields = ('name', 'location')