from django.db import models


class Turf(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    price_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    opening_time = models.TimeField()
    closing_time = models.TimeField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name