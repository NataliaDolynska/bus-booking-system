from .models import User, Booking, BookingRestriction, RouteCapacity, TaskProgress

from django.contrib import admin


# admin.py

from django.contrib import admin

admin.site.register(User)
admin.site.register(Booking)
admin.site.register(TaskProgress)

@admin.register(RouteCapacity)
class RouteCapacityAdmin(admin.ModelAdmin):
    list_display = ('route', 'max_seats')

@admin.register(BookingRestriction)
class BookingRestrictionAdmin(admin.ModelAdmin):
    list_display = ('station', 'route_id', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date', 'end_date')
