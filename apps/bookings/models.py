from django.contrib.postgres.fields.array import ArrayField
from django.contrib.auth.models import AbstractUser, Group, Permission, User

from apps.gtfs.models import Route, Stop, Trip
from django.utils import timezone
from django.db import models


class Booking(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='bookings')
    date = models.DateField()
    from_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='starting_bookings')
    to_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='destination_bookings')
    departure_time = models.TimeField()
    num_passengers = models.PositiveIntegerField()
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('pending', 'Pending'),
        ('canceled', 'Canceled')
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)


class BookingRestriction(models.Model):
    hide_result = models.BooleanField(blank=False, null=False, default=False)
    station = models.ForeignKey(Stop, null=True, blank=True, on_delete=models.CASCADE)
    route = models.ForeignKey(Route, null=True, blank=True, on_delete=models.CASCADE)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Restriction on {self.station or self.route} from {self.start_date} to {self.end_date}"


class RouteCapacity(models.Model):
    route = models.OneToOneField(Route, on_delete=models.CASCADE, related_name='capacity')
    max_seats = models.PositiveIntegerField(default=30)

    def __str__(self):
        return f"{self.route.short_name} Capacity"
