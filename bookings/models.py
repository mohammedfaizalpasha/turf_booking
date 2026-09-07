from django.conf import settings
from django.db import models

from turfs.models import Turf


class Booking(models.Model):

    # ==========================================
    # BOOKING STATUS
    # ==========================================

    STATUS_CHOICES = [

        (
            "pending",
            "Waiting for Admin Approval"
        ),

        (
            "approved",
            "Approved - Payment Pending"
        ),

        (
            "confirmed",
            "Confirmed"
        ),

        (
            "cancelled",
            "Rejected / Cancelled"
        ),

    ]


    # ==========================================
    # PAYMENT METHOD
    # ==========================================

    PAYMENT_METHOD_CHOICES = [

        (
            "online",
            "Online Payment"
        ),

        (
            "offline",
            "Offline Payment"
        ),

    ]


    # ==========================================
    # PAYMENT STATUS
    # ==========================================

    PAYMENT_STATUS_CHOICES = [

        (
            "pending",
            "Payment Pending"
        ),

        (
            "paid",
            "Paid"
        ),

        (
            "unpaid",
            "Unpaid"
        ),

        (
            "failed",
            "Payment Failed"
        ),

    ]


    # ==========================================
    # USER
    # ==========================================

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )


    # ==========================================
    # TURF
    # ==========================================

    turf = models.ForeignKey(
        Turf,
        on_delete=models.CASCADE
    )


    # ==========================================
    # BOOKING DATE
    # ==========================================

    booking_date = models.DateField()


    # ==========================================
    # TIME SLOT
    # ==========================================

    start_time = models.TimeField()

    end_time = models.TimeField()


    # ==========================================
    # BOOKING STATUS
    #
    # FLOW:
    #
    # pending
    #     ↓
    # approved / cancelled
    #     ↓
    # payment completed
    #     ↓
    # confirmed
    # ==========================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )


    # ==========================================
    # PAYMENT METHOD
    #
    # online  -> Razorpay / UPI / Card etc.
    # offline -> Admin manually marks paid/unpaid
    # ==========================================

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="offline"
    )


    # ==========================================
    # PAYMENT STATUS
    #
    # Online:
    # Automatically updated after successful payment
    #
    # Offline:
    # Superadmin/Admin manually marks
    # Paid or Unpaid
    # ==========================================

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending"
    )


    # ==========================================
    # ONLINE PAYMENT DETAILS
    # ==========================================

    payment_platform = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    payment_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    razorpay_order_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )


    # ==========================================
    # CREATED DATE
    # ==========================================

    created_at = models.DateTimeField(
        auto_now_add=True
    )


    # ==========================================
    # UNIQUE TIME SLOT
    #
    # Same turf cannot be booked twice
    # for the same date and start time.
    # ==========================================

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

        ordering = [
            "-booking_date",
            "-start_time"
        ]


    # ==========================================
    # DISPLAY BOOKING
    # ==========================================

    def __str__(self):

        return (
            f"{self.user.username} | "
            f"{self.turf.name} | "
            f"{self.booking_date} | "
            f"{self.start_time}"
        )