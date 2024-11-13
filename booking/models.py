from email.policy import default
from random import randint

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, Group, Permission

from gtfs.models import Trip, Stop, Route

from django.db import models


# User model
class User(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('admin', 'Admin')
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=15, blank=True, null=True)

    # Avoid clashes by specifying unique related_name values
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",
        blank=True,
        help_text="The groups this user belongs to."
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",
        blank=True,
        help_text="Specific permissions for this user."
    )


# Booking model
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='bookings')
    date = models.DateField()
    starting_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='starting_bookings')
    destination_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='destination_bookings')
    departure_time = models.TimeField()
    num_passengers = models.PositiveIntegerField()
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('pending', 'Pending'),
        ('canceled', 'Canceled')
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)


# BookingRestriction model
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone


class BookingRestriction(models.Model):
    station = models.ForeignKey(Stop, null=True, blank=True, on_delete=models.CASCADE)
    route_id = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    weekdays = ArrayField(
        models.IntegerField(choices=[
            (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'),
            (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
        ]),
        null=True,
        blank=True,
        help_text='Select weekdays if applicable'
    )
    calendar_pattern = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Restriction on {self.station or self.route_id} from {self.start_date} to {self.end_date}"


class RouteCapacity(models.Model):
    route = models.OneToOneField(Route, on_delete=models.CASCADE, related_name='capacity')
    max_seats = models.PositiveIntegerField(default=30)

    def __str__(self):
        return f"{self.route.short_name} Capacity"


class GTFSData(models.Model):
    name = models.CharField(max_length=100, help_text="Name of the GTFS dataset")
    file = models.FileField(upload_to="gtfs_static_data/", help_text="Upload GTFS zip file")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (Uploaded on {self.uploaded_at})"


class GTFSRealtimeConfig(models.Model):
    name = models.CharField(max_length=100, help_text="Description of the GTFS-realtime feed")
    url = models.URLField(help_text="URL for the GTFS-realtime feed")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, help_text="Enable or disable this GTFS-realtime feed")

    def __str__(self):
        return f"{self.name} (Active: {self.is_active})"


class TaskProgress(models.Model):
    task_id = models.CharField(max_length=50, unique=True)  # To match Django Q's task_id format
    file_hash = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, unique=False, default='pending')
    progress = models.FloatField(default=0)
    message = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Progress for Task {self.task_id}: {self.progress}%"
