from django.contrib import admin

from apps.bookings.models import Booking, BookingRestriction, RouteCapacity

admin.site.register(Booking)
admin.site.register(BookingRestriction)
admin.site.register(RouteCapacity)
