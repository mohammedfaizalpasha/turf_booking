from django.conf import settings
from django.db import models

from turfs.models import Turf


class Booking(models.Model):

    STATUS_CHOICES = [
        ("pending", "Waiting for Admin Approval"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("online", "Online Payment"),
        ("offline", "Offline Payment"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    turf = models.ForeignKey(
        Turf,
        on_delete=models.CASCADE
    )

    booking_date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="offline"
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "turf",
                    "booking_date",
                    "start_time"
                ],
                name="unique_turf_booking_slot"
            )
        ]

    def __str__(self):
        return (
            f"{self.turf.name} | "
            f"{self.booking_date} | "
            f"{self.start_time}"
        )