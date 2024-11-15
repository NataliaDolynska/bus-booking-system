from django.urls import path

from . import views
from .views import search_commute_suggestions, suggest_arrival_stops, suggest_departure_stops, suggest_bus_lines

urlpatterns = [
    path("", views.index, name="bookings"),
    path("booking-restrictions/", views.all_booking_restrictions, name="booking-restrictions"),
    path("booking-restriction/", views.create_or_update_booking_restriction, name="create_booking_restriction"),
    path("booking-restriction/<int:pk>/", views.create_or_update_booking_restriction, name="update_booking_restriction"),
    path("booking-restriction/<int:pk>/", views.create_or_update_booking_restriction, name="delete_booking_restriction"),
    path("new-booking", views.new_booking, name="new-bookings"),
    path("success-booking", views.success_booking, name="success-booking"),
    path("search_stations", views.search_stations, name="search_stations"),
    path("search_routes", views.search_routes, name="search_routes"),
    path('routes-capacities/', views.capacity_routes, name='routes_capacities'),
    path('serach-capacity-routes/', views.search_capacity_routes, name='search_capacity_routes'),
    path('create-route-capacity/', views.create_update_route_capacity, name='create_update_route_capacity'),
    path('route-capacity/<int:capacity_id>/delete/', views.delete_route_capacity, name='delete_route_capacity'),
    path('api/search-suggestions/', views.search_commute_suggestions, name='search_commute_suggestions'),
    path('api/suggest-arrival-stops/', views.suggest_arrival_stops, name='suggest_arrival_stops'),
    path('api/suggest-departure-stops/', views.suggest_departure_stops, name='suggest_departure_stops'),
    path('api/suggest-lines/', suggest_bus_lines, name='suggest_bus_lines'),

]
