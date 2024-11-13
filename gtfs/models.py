from django.contrib.gis.db import models


class Agency(models.Model):
    name = models.TextField()
    url = models.URLField()
    timezone = models.CharField(max_length=255)
    agency_id = models.CharField(max_length=255, null=True, blank=True)
    lang = models.CharField(max_length=2, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    fare_url = models.URLField(null=True, blank=True)


class Zone(models.Model):
    """Define the fare zone"""
    zone_id = models.CharField(max_length=255, unique=True)


class Stop(models.Model):
    STOP = 0
    STATION = 1
    LOCATION_TYPE_CHOICES = [
        (STOP, 'Stop'),
        (STATION, 'Station')
    ]

    stop_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, db_index=True)
    url = models.URLField(null=True, blank=True)
    desc = models.TextField(null=True, blank=True)
    geopoint = models.PointField(null=True, blank=True,  spatial_index=True)
    code = models.CharField(max_length=255, null=True, blank=True)
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True)
    location_type = models.IntegerField(choices=LOCATION_TYPE_CHOICES, null=True, blank=True)
    parent_station = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)


class RouteType(models.Model):
    """Referential data"""
    name = models.CharField(max_length=50)
    description = models.TextField()
    value = models.IntegerField(unique=True)


class Route(models.Model):
    route_id = models.CharField(max_length=255, unique=True)
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, null=True, blank=True)
    short_name = models.CharField(max_length=255)
    long_name = models.TextField(null=True, blank=True)  # Allow null and blank values
    desc = models.TextField(null=True, blank=True)
    route_type = models.ForeignKey(RouteType, on_delete=models.SET_NULL, null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    color = models.CharField(max_length=6, default="FFFFFF")
    text_color = models.CharField(max_length=6, default="000000")





class Direction(models.Model):
    """Referential data"""
    name = models.CharField(max_length=20)
    value = models.IntegerField(unique=True)


class Block(models.Model):
    block_id = models.CharField(max_length=255, unique=True)


class Shape(models.Model):
    shape_id = models.CharField(max_length=255)
    geopoint = models.PointField()
    pt_sequence = models.IntegerField()
    dist_traveled = models.FloatField(null=True, blank=True)


class Trip(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    service_id = models.CharField(max_length=255, unique=False)
    trip_id = models.CharField(max_length=255, unique=True)
    headsign = models.TextField(null=True, blank=True)
    direction = models.ForeignKey(Direction, null=True, blank=True, on_delete=models.SET_NULL)
    block = models.ForeignKey(Block, null=True, blank=True, on_delete=models.SET_NULL)
    shape_id = models.CharField(max_length=255, null=True, blank=True)


class PickupType(models.Model):
    """Referential data"""
    name = models.CharField(max_length=255)
    value = models.IntegerField()


class DropOffType(models.Model):
    """Referential data"""
    name = models.CharField(max_length=255)
    value = models.IntegerField()


class StopTime(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    arrival_time = models.TimeField(db_index=True)  # Indexed for time-based search
    departure_time = models.TimeField(db_index=True)  # Indexed for time-based search
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE)
    stop_sequence = models.IntegerField(db_index=True)  # Indexed for sequence filtering
    headsign = models.TextField(null=True, blank=True)
    pickup_type = models.ForeignKey(PickupType, null=True, blank=True, on_delete=models.SET_NULL)
    drop_off_type = models.ForeignKey(DropOffType, on_delete=models.SET_NULL, null=True, blank=True)
    shape_dist_traveled = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["stop"]),
        ]


class Calendar(models.Model):
    YES = 1
    NO = 0
    DAY_CHOICES = [
        (YES, 'Yes'),
        (NO, 'No')
    ]

    service_id = models.CharField(max_length=255, unique=False)
    monday = models.IntegerField(choices=DAY_CHOICES)
    tuesday = models.IntegerField(choices=DAY_CHOICES)
    wednesday = models.IntegerField(choices=DAY_CHOICES)
    thursday = models.IntegerField(choices=DAY_CHOICES)
    friday = models.IntegerField(choices=DAY_CHOICES)
    saturday = models.IntegerField(choices=DAY_CHOICES)
    sunday = models.IntegerField(choices=DAY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()


class ExceptionType(models.Model):
    """Referential data"""
    name = models.CharField(max_length=255)
    value = models.IntegerField()


class CalendarDate(models.Model):
    service_id = models.CharField(max_length=255, unique=False)
    date = models.DateField()
    exception_type = models.ForeignKey(ExceptionType, on_delete=models.SET_NULL, null=True, blank=True)


class Fare(models.Model):
    fare_id = models.CharField(max_length=255, unique=True)


class PaymentMethod(models.Model):
    name = models.CharField(max_length=50)
    value = models.IntegerField()


class FareAttribute(models.Model):
    fare = models.ForeignKey(Fare, on_delete=models.CASCADE)
    price = models.FloatField()
    currency = models.CharField(max_length=3)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    transfers = models.IntegerField(null=True, blank=True)
    transfer_duration = models.IntegerField(null=True, blank=True)  # duration in seconds


class FareRule(models.Model):
    fare = models.ForeignKey(Fare, on_delete=models.CASCADE)
    route = models.ForeignKey(Route, null=True, blank=True, on_delete=models.SET_NULL)
    origin = models.ForeignKey(Zone, null=True, blank=True, related_name="origin", on_delete=models.SET_NULL)
    destination = models.ForeignKey(Zone, null=True, blank=True, related_name="destination", on_delete=models.SET_NULL)
    contains = models.ForeignKey(Zone, null=True, blank=True, related_name="contains", on_delete=models.SET_NULL)


class Frequency(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    headway_secs = models.IntegerField()
    exact_times = models.IntegerField(null=True, blank=True)


class Transfer(models.Model):
    from_stop = models.ForeignKey(Stop, related_name="from_stop", on_delete=models.CASCADE)
    to_stop = models.ForeignKey(Stop, related_name="to_stop", on_delete=models.CASCADE)
    transfer_type = models.IntegerField()
    min_transfer_time = models.IntegerField(null=True, blank=True)

