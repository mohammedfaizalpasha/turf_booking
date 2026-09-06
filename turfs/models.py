from django.db import models


class Turf(models.Model):

    name = models.CharField(
        max_length=200
    )

    location = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True
    )

    price_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.name


class TurfSlot(models.Model):

    turf = models.ForeignKey(
        Turf,
        on_delete=models.CASCADE,
        related_name="slots"
    )

    date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "turf",
                    "date",
                    "start_time"
                ],
                name="unique_turf_slot"
            )

        ]

        ordering = [
            "date",
            "start_time"
        ]

    def __str__(self):

        return (
            f"{self.turf.name} | "
            f"{self.date} | "
            f"{self.start_time} - "
            f"{self.end_time}"
        )