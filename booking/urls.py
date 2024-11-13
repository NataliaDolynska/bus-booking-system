from django.urls import path

from .views import index, login_user, logout_user, search_commute_suggestions, \
    suggest_arrival_stops, suggest_departure_stops, suggest_lines, booking_page, user_bookings, cancel_booking, \
    admin_bookings, admin_cancel_booking, admin_booking_restrictions, add_booking_restriction, \
    delete_booking_restriction, admin_upload_gtfs, task_status

urlpatterns = [
    path('', index, name='index'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('user/bookings/', user_bookings, name='user_bookings'),
    path('user/new-booking/', booking_page, name='booking'),
    path('user/cancel-booking/<int:booking_id>/', cancel_booking, name='cancel_booking'),
    path('manager/bookings/', admin_bookings, name='admin_bookings'),
    path('manager/cancel-booking/<int:booking_id>/', admin_cancel_booking, name='admin_cancel_booking'),
    path('manager/booking-restrictions/', admin_booking_restrictions, name='admin_booking_restrictions'),
    path('manager/add-booking-restriction/', add_booking_restriction, name='add_booking_restriction'),
    path('manager/delete-booking-restriction/<int:restriction_id>/', delete_booking_restriction, name='delete_booking_restriction'),
    # API endpoints
    path('api/search-suggestions/', search_commute_suggestions, name='search_commute_suggestions'),
    path('api/suggest-arrival-stops/', suggest_arrival_stops, name='suggest_arrival_stops'),
    path('api/suggest-departure-stops/', suggest_departure_stops, name='suggest_departure_stops'),
    path('api/suggest-lines/', suggest_lines, name='suggest_lines'),

    path('api/task/status/', task_status, name='scheduled_task_status'),
    path('manager/task/upload-gtfs/', admin_upload_gtfs, name='manager_upload_gtfs'),


]
