import json
from lib2to3.fixes.fix_input import context
from django.db.models import Sum, Value, IntegerField
from django.db.models.functions import Coalesce

from django.views.decorators.vary import vary_on_headers
from loguru import logger
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import OuterRef, Subquery, F, Q, Sum, Count
from django.utils.dateparse import parse_date, parse_time
from datetime import datetime, timedelta
from .models import BookingRestriction, RouteCapacity
from django.shortcuts import render, get_object_or_404
from apps.bookings.models import Booking
from django.core import serializers
from django.db import transaction

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from apps.gtfs.models import Stop, Route
from .models import BookingRestriction
from django.views.decorators.http import require_http_methods

from apps.gtfs.models import *
from ..users.models import Profile


# Create your views here.
@login_required(login_url='/users/signin/')
@vary_on_headers("HX-Request")
def index(request):
    logger.info(f"REQ : {request}")
    if request.htmx:
        logger.info(f"HTMX : {request.body}")
        id = request.POST.get('id')

        booking = Booking.objects.get(id=id)
        if booking.status == 'canceled':
            booking.delete()
        else:
            booking.status = 'canceled'
            booking.save()
        template_name = "bookings/bookings-list.html"
    else:
        template_name = 'bookings/all-bookings.html'
    if request.user.is_superuser:
        bookings = Booking.objects.filter().all()
    else:
        bookings = Booking.objects.filter(user=request.user).all()
    logger.info("Bookings: " + str(len(list(bookings))))
    context = {
        'segment': 'bookings',
        # 'parent': 'apps',
        'bookings': bookings
    }
    return render(request, template_name, context)


@login_required(login_url='/users/signin/')
def success_booking(request):
    context = {
        'segment': 'bookings',
    }
    return render(request, 'bookings/success-booking.html', context)


from django.http import JsonResponse
from apps.gtfs.models import Stop, Route, Trip


@login_required(login_url='/users/signin/')
def search_stations(request):
    route_id = request.GET.get("route_id", None)
    station_name = request.GET.get("station_name", "").strip()

    stops = Stop.objects.all()

    if route_id:
        # Filter stops associated with the selected route
        trips = Trip.objects.filter(route_id=route_id)
        stops = stops.filter(stoptime__trip__in=trips).distinct()

    if station_name:
        # Filter stops by name (case-insensitive partial match)
        stops = stops.filter(name__icontains=station_name)

    # Return a list of unique stop names
    stop_names = stops.values_list("name", flat=True).distinct()
    return JsonResponse({"stations": list(stop_names)})


@login_required(login_url='/users/signin/')
def search_routes(request):
    departure_stop_name = request.GET.get("departure_stop_name", "").strip()
    arrival_stop_name = request.GET.get("arrival_stop_name", "").strip()
    route_name = request.GET.get("route_name", "").strip()

    routes = Route.objects.all()

    if departure_stop_name or arrival_stop_name:
        # Filter routes with trips that include the specified departure and arrival stops
        trips = Trip.objects.all()

        if departure_stop_name:
            trips = trips.filter(stoptime__stop__name__icontains=departure_stop_name)

        if arrival_stop_name:
            trips = trips.filter(stoptime__stop__name__icontains=arrival_stop_name)

        routes = routes.filter(trip__in=trips).distinct()

    if route_name:
        # Filter routes by name (case-insensitive partial match)
        routes = routes.filter(short_name__icontains=route_name)

    # Return a list of routes with name and ID
    route_list = [{"id": route.pk, "name": route.short_name} for route in routes.distinct()]
    return JsonResponse({"routes": route_list})


@login_required(login_url='/users/signin/')
def all_booking_restrictions(request):
    restrictions = BookingRestriction.objects.all()
    context = {
        'segment': 'restrictions',
        'restrictions': restrictions
    }
    return render(request, 'restrictions/all-restrictions.html', context)


@login_required(login_url='/users/signin/')
def delete_route_capacity(request, capacity_id):
    """
    Delete a RouteCapacity instance.
    """
    if request.method == 'DELETE':
        try:
            capacity = get_object_or_404(RouteCapacity, id=capacity_id)
            capacity.delete()

            capacities = RouteCapacity.objects.all()
            context = {
                'segment': 'route-capacities',
                'capacities': capacities
            }
            return render(request, 'route-capacities/capacities-list.html', context)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


@login_required(login_url='/users/signin/')
def capacity_routes(request):
    capacities = RouteCapacity.objects.all()
    context = {
        'segment': 'route-capacities',
        'capacities': capacities
    }
    return render(request, 'route-capacities/all-capacities.html', context)


@login_required(login_url='/users/signin/')
def search_capacity_routes(request):
    """
    Search for routes based on a query string.
    """
    route_name = request.GET.get('route_name', '').strip()
    if not route_name:
        return JsonResponse({'routes': []})  # Return empty if no query

    # Search for matching routes
    routes_ids = RouteCapacity.objects.values('route_id').distinct()
    routes = Route.objects.filter(short_name__icontains=route_name).exclude(route_id__in=routes_ids).values('id',
                                                                                                            'short_name')
    return JsonResponse({'routes': list(routes)})


@login_required(login_url='/users/signin/')
def create_update_route_capacity(request):
    """
    Create or update a RouteCapacity instance.
    """
    if request.method == 'POST':
        try:
            # Validate route ID
            route_name = request.POST.get('route-name')
            if not route_name:
                return JsonResponse({'success': False, 'error': 'Route ID is required.'}, status=400)

            route = Route.objects.get(short_name=route_name)
            if RouteCapacity.objects.filter(route_id=route.route_id).exists():
                return JsonResponse({'success': False, 'error': 'Capacity for this route already exists.'}, status=400)

            # Fetch or create RouteCapacity instance
            max_seats = request.POST.get('max_seats', 30)

            # Update or create RouteCapacity
            capacity, created = RouteCapacity.objects.update_or_create(
                route=route,
                defaults={'max_seats': max_seats}
            )

            return JsonResponse({
                'success': True,
                'message': 'RouteCapacity created.' if created else 'RouteCapacity updated.',
                'capacity_id': capacity.id,
            })
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    else:

        context = {
            'segment': 'route-capacities',
        }

        return render(request, "route-capacities/new-capacity.html", context)


@require_http_methods(["GET", "POST", 'DELETE'])
def create_or_update_booking_restriction(request, pk=None):
    """
    View for creating or updating a BookingRestriction.
    """
    if pk:
        restriction = get_object_or_404(BookingRestriction, pk=pk)
    else:
        restriction = BookingRestriction()

    if request.method == "POST":
        # Process the form data
        hide_result = request.POST.get("hide_result") == "true"
        station_name = request.POST.get("station-name", "").strip()
        route_name = request.POST.get("route-name", "").strip()
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        is_active = request.POST.get("is_active") == "true"

        # Find station
        station = None
        if station_name:
            station = Stop.objects.filter(name=station_name).first()
            if not station:
                return JsonResponse({"success": False, "error": "Station not found."}, status=400)

        # Find route
        route = None
        if route_name:
            route = Route.objects.filter(short_name=route_name).first()
            if not route:
                return JsonResponse({"success": False, "error": "Route not found."}, status=400)

        # Update or create the restriction
        restriction.hide_result = hide_result
        restriction.station = station
        restriction.route = route
        restriction.start_date = start_date
        restriction.end_date = end_date
        restriction.is_active = is_active
        restriction.save()

        return JsonResponse({"success": True, "redirect_url": "/bookings/booking-restrictions/"})

    elif request.method == "DELETE":
        # Delete the restriction
        restriction.delete()
        restrictions = BookingRestriction.objects.all()
        context = {
            'restrictions': restrictions
        }
        return render(request, 'restrictions/restrictions-list.html', context)

    # Render the template
    return render(request, "restrictions/new-restriction.html", {"form": restriction})


@login_required(login_url='/users/signin/')
def new_booking(request):
    # profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'GET':
        context = {
            'segment': 'bookings',
        }
        return render(request, 'bookings/new-booking.html', context)

    elif request.method == 'POST':
        data = json.loads(request.body)
        trip_id = data.get('trip_id')
        route_id = data.get('route_id')
        date = parse_date(data.get('date'))
        num_passengers = int(data.get('num_passengers'))
        departure_stop_name = data.get('departure_stop_name')
        arrival_stop_name = data.get('arrival_stop_name')

        # Basic validation
        if not all([trip_id, route_id, date, num_passengers, departure_stop_name, arrival_stop_name]):
            return JsonResponse({'success': False, 'error': 'All fields are required.'}, status=400)

        try:
            trip = Trip.objects.get(id=trip_id, route__route_id=route_id)
        except Trip.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid trip or route.'}, status=404)

            # Check if the specified stops are part of the trip route
        try:
            # Retrieve all stops with the specified name
            departure_stops = Stop.objects.filter(name=departure_stop_name)
            arrival_stops = Stop.objects.filter(name=arrival_stop_name)

            # Ensure at least one stop was found for each
            if not departure_stops.exists() or not arrival_stops.exists():
                return JsonResponse({'success': False, 'error': 'Departure or arrival stop not found.'}, status=404)

            # If there are multiple stops with the same name, further filtering may be required
            # For simplicity, let’s assume we just pick the first matching stop in each list

            # Retrieve the corresponding stop times for the trip
            logger.info(f"DEPS: {departure_stop_name}, ARRS: {arrival_stop_name}")
            departure_stoptime = StopTime.objects.get(trip=trip, stop__in=departure_stops)
            logger.info(f"DEP {departure_stoptime}")

            arrival_stoptime = StopTime.objects.get(trip=trip, stop__in=arrival_stops)
            logger.info(f"ARR {arrival_stoptime}")

            # Ensure the correct stop sequence
            if departure_stoptime.stop_sequence >= arrival_stoptime.stop_sequence:
                return JsonResponse({'success': False, 'error': 'Invalid stop sequence.'}, status=400)

        except (Stop.DoesNotExist, StopTime.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Departure or arrival stop is not valid for this trip.'},
                                status=404)
        except Stop.MultipleObjectsReturned:
            return JsonResponse(
                {'success': False, 'error': 'Multiple stops found with the same name. Please refine your selection.'},
                status=400)

        # Check existing bookings for overlapping segments
        total_booked = Booking.objects.filter(
            trip=trip,
            date=date,
            from_stop=departure_stoptime.stop,
            to_stop=arrival_stoptime.stop,
        ).aggregate(total=Sum('num_passengers'))['total'] or 0

        max_capacity = 30
        try:
            max_seats = RouteCapacity.objects.get(route=trip.route).max_seats
            if max_seats:
                max_capacity = max_seats
        except RouteCapacity.DoesNotExist as e:
            logger.info(f"RouteCapacity.DoesNotExist for trip: {trip.trip_id}")

        try:
            restriction = BookingRestriction.objects.get(route=trip.route, station=departure_stoptime.stop,
                                                         is_active=True).hide_result
            if restriction:
                if restriction.start_date <= date <= restriction.end_date:
                    return JsonResponse(
                        {'success': False, 'error': 'Departure stop is currently restricted.'}, status=400)

        except BookingRestriction.DoesNotExist as e:
            logger.info(f"BookingRestriction.DoesNotExist for trip: {trip.trip_id}")

        # Ensure enough seats are available
        if total_booked + num_passengers > max_capacity:
            return JsonResponse({'success': False, 'error': 'Not enough seats available.'}, status=400)

        # Save the booking in a transaction for atomicity
        with transaction.atomic():
            Booking.objects.create(
                trip=trip,
                user=request.user,
                date=date,
                num_passengers=num_passengers,
                departure_time=departure_stoptime.departure_time,
                from_stop=departure_stoptime.stop,
                to_stop=arrival_stoptime.stop,
            )

        # Return success response with optional redirect URL if necessary
        return JsonResponse({'success': True}, status=200)


from django.db.models import Q, Count, Subquery, F
from django.http import JsonResponse
from django.db.models.functions import Coalesce
from django.utils import timezone


def suggest_departure_stops(request):
    arrival_stop_name = request.GET.get("arrival_stop_name", None)
    line_id = request.GET.get("line_id", None)
    departure_name = request.GET.get("departure_stop_name", None)

    # Start with all stops
    stops = Stop.objects.all()

    # Filter by partial departure name for autocomplete functionality
    if departure_name and departure_name != 'undefined' and departure_name != 'null':
        stops = stops.filter(name__icontains=departure_name)

    if arrival_stop_name and arrival_stop_name != 'undefined' and arrival_stop_name != 'null':
        # Get all arrival stops that match the provided name
        arr_stops = stops.filter(name__icontains=arrival_stop_name)

        # Filter trips to include both the specified arrival stops and the stops found above
        trips = Trip.objects.filter(
            stoptime__stop__in=stops  # Filtered stops for departure
        ).filter(
            stoptime__stop__in=arr_stops  # Filtered stops for arrival
        )

        if line_id and line_id != 'undefined' and line_id != 'null':
            trips = trips.filter(route__route_id=line_id)

        # Filter trips to ensure each has both departure and arrival stops
        trips_with_both_stops = trips.annotate(
            dep_count=Count('stoptime', filter=Q(stoptime__stop__in=stops), distinct=True),
            arr_count=Count('stoptime', filter=Q(stoptime__stop__in=arr_stops), distinct=True)
        ).filter(
            dep_count__gt=0,
            arr_count__gt=0
        ).distinct()

        # Annotate trips with stop sequences for departure and arrival
        departure_sequence = StopTime.objects.filter(
            trip=OuterRef('pk'),
            stop__in=stops
        ).order_by('stop_sequence').values('stop_sequence')[:1]

        arrival_sequence = StopTime.objects.filter(
            trip=OuterRef('pk'),
            stop__in=arr_stops
        ).order_by('stop_sequence').values('stop_sequence')[:1]

        # Add sequence annotations and filter for correct ordering
        trips_with_sequences = trips_with_both_stops.annotate(
            departure_sequence=Subquery(departure_sequence),
            arrival_sequence=Subquery(arrival_sequence)
        ).filter(
            departure_sequence__lt=F('arrival_sequence')
        )

        # Filter stops to include only those associated with the valid trips
        stops = stops.filter(
            stoptime__trip__in=trips_with_sequences
        ).distinct()

    else:
        # If no arrival stop, filter only by line_id if provided
        if line_id:
            trips = Trip.objects.filter(route__route_id=line_id)
            stops = stops.filter(
                stoptime__trip__in=trips
            ).distinct()

    # Return only unique stop names
    stop_names = stops.values_list("name", flat=True).distinct()

    return JsonResponse({"suggested_departure_stops": list(stop_names)})


def suggest_arrival_stops(request):
    departure_stop_name = request.GET.get("departure_stop_name", None)
    line_id = request.GET.get("line_id", None)
    arrival_name = request.GET.get("arrival_stop_name", None)

    # Start with all stops
    stops = Stop.objects.all()

    # Filter by partial arrival name for autocomplete functionality
    if arrival_name and arrival_name != 'undefined' and arrival_name != 'null' and arrival_name != '':
        stops = stops.filter(name__icontains=arrival_name)

    if departure_stop_name and departure_stop_name != 'undefined' and departure_stop_name != 'null' and departure_stop_name != '':
        # Get trips that include both departure and arrival stops
        dep_stops = Stop.objects.filter(name__exact=departure_stop_name)

        trips = Trip.objects.filter(
            stoptime__stop__in=stops  # Ensure arrival stops are among these stops
        ).filter(
            stoptime__stop__in=dep_stops
        )
        logger.info(f"ARR Len {len(list(trips.all()))}")
        if line_id and line_id != 'undefined' and line_id != 'null':
            trips = trips.filter(route__route_id=line_id)

        # Filter trips that have at least one departure stop and one arrival stop
        trips_with_both_stops = trips.filter(
            Q(stoptime__stop__id__in=dep_stops) | Q(stoptime__stop__id__in=stops)
        ).annotate(
            dep_count=Count('stoptime', filter=Q(stoptime__stop__id__in=dep_stops), distinct=True),
            arr_count=Count('stoptime', filter=Q(stoptime__stop__id__in=stops), distinct=True)
        ).filter(
            dep_count__gt=0,
            arr_count__gt=0
        ).distinct()

        departure_sequence = StopTime.objects.filter(
            trip=OuterRef('pk'),
            stop__id__in=dep_stops
        ).order_by('stop_sequence').values('stop_sequence')[:1]

        arrival_sequence = StopTime.objects.filter(
            trip=OuterRef('pk'),
            stop__id__in=stops
        ).order_by('stop_sequence').values('stop_sequence')[:1]

        trips_with_sequences = trips_with_both_stops.annotate(
            departure_sequence=Subquery(departure_sequence),
            arrival_sequence=Subquery(arrival_sequence)
        )

        stops = stops.filter(
            stoptime__trip__in=trips_with_sequences
        ).distinct()
    else:
        if line_id:
            trips = Trip.objects.filter(route__route_id=line_id)
            stops = stops.filter(
                stoptime__trip__in=trips
            ).distinct()

    # Only return unique stop names
    stop_names = stops.values_list("name", flat=True).distinct()

    return JsonResponse({"suggested_arrival_stops": list(stop_names)})


def suggest_bus_lines(request):
    departure_stop_name = request.GET.get("departure_stop_name", None)
    arrival_stop_name = request.GET.get("arrival_stop_name", None)
    line_name = request.GET.get("line_name", None)

    # Start with all routes
    routes = Route.objects.all()

    # Filter trips based on selected stops
    trips = Trip.objects.all()

    if departure_stop_name:
        trips = trips.filter(
            stoptime__stop__name=departure_stop_name
        )
    if arrival_stop_name:
        trips = trips.filter(
            stoptime__stop__name=arrival_stop_name
        )

    if departure_stop_name or arrival_stop_name:
        # Filter routes based on trips
        routes = routes.filter(trip__in=trips).distinct()

    # Filter by partial line name for autocomplete functionality
    if line_name:
        routes = routes.filter(short_name__icontains=line_name)

    # Return list of unique route names and IDs
    route_info = routes.values("short_name", "route_id").distinct()

    # Prepare the response as a list of dictionaries
    suggested_lines = [
        {"name": route["short_name"], "id": route["route_id"]}
        for route in route_info
    ]

    return JsonResponse({"suggested_lines": suggested_lines})


def search_commute_suggestions(request):
    # Parse query parameters
    date_str = request.GET.get("date")
    num_passengers = request.GET.get("group_size")
    departure_stop_name = request.GET.get("departure_stop_name")
    arrival_stop_name = request.GET.get("arrival_stop_name")
    line_name = request.GET.get("line_name", None)
    line_id = request.GET.get("line_id", None)
    is_arrival = request.GET.get("is_arrival", "false").lower() == "true"
    time_str = request.GET.get("time", None)

    # Validate required fields
    if not date_str or not num_passengers or not departure_stop_name or not arrival_stop_name or not time_str:
        return JsonResponse({
            "error": "Date, number of passengers, departure stop, arrival stop, and time are required."
        }, status=400)

    # Parse date and time
    date = parse_date(date_str)
    required_time = parse_time(time_str)
    num_passengers = int(num_passengers)

    # Validate date is not in the past
    today = datetime.now().date()
    if date < today:
        return JsonResponse({"error": "Date cannot be in the past."}, status=400)

    # Step 1: Retrieve active service_ids
    day_of_week = date.strftime('%A').lower()
    active_services = Calendar.objects.filter(
        start_date__lte=date,
        end_date__gte=date,
        **{day_of_week: 1}
    ).values_list('service_id', flat=True)

    # Include added services and exclude removed services
    added_services = CalendarDate.objects.filter(
        date=date,
        exception_type__value=1  # Assuming exception_type is a ForeignKey
    ).values_list('service_id', flat=True)
    removed_services = CalendarDate.objects.filter(
        date=date,
        exception_type__value=2
    ).values_list('service_id', flat=True)

    active_services = active_services.union(added_services).difference(removed_services)

    # Step 2: Filter trips
    trips = Trip.objects.filter(service_id__in=active_services)

    # Ensure `line_id` is treated as a string
    if line_id:
        line_id = str(line_id)

    # Filter by line_id if provided
    if line_id and line_id != "null":
        trips = trips.filter(route__route_id=line_id)
    elif line_name and line_name != "null":
        trips = trips.filter(route__short_name__icontains=line_name)

    # Ensure correct stop sequence (departure before arrival)
    trips = trips.annotate(
        departure_sequence=Subquery(
            StopTime.objects.filter(
                trip=OuterRef('pk'),
                stop__name=departure_stop_name
            ).values('stop_sequence')[:1]
        ),
        arrival_sequence=Subquery(
            StopTime.objects.filter(
                trip=OuterRef('pk'),
                stop__name=arrival_stop_name
            ).values('stop_sequence')[:1]
        )
    ).filter(
        departure_sequence__lt=F('arrival_sequence')
    )

    # Step 3: Filter by time constraints
    if is_arrival:
        end_time = required_time
        start_time = (datetime.combine(date, required_time) - timedelta(hours=1)).time()
        trips = trips.annotate(
            arrival_time=Subquery(
                StopTime.objects.filter(
                    trip=OuterRef('pk'),
                    stop__name=arrival_stop_name
                ).values('arrival_time')[:1]
            )
        ).filter(
            arrival_time__gte=start_time,
            arrival_time__lte=end_time
        )
    else:
        start_time = required_time
        end_time = (datetime.combine(date, required_time) + timedelta(hours=1)).time()
        trips = trips.annotate(
            departure_time=Subquery(
                StopTime.objects.filter(
                    trip=OuterRef('pk'),
                    stop__name=departure_stop_name
                ).values('departure_time')[:1]
            )
        ).filter(
            departure_time__gte=start_time,
            departure_time__lte=end_time
        )

    # Step 4: Exclude trips with booking restrictions
    restrictions = BookingRestriction.objects.filter(hide_result=True, is_active=True)
    station_restrictions = restrictions.exclude(station__isnull=True)
    restriction_q = Q()

    if station_restrictions.exists():
        restriction_q |= Q(
            stoptime__stop__in=station_restrictions.values_list('station', flat=True)
        )

    if restriction_q:
        trips = trips.exclude(restriction_q)

    # Step 5: Annotate trips with max_seats
    trips = trips.annotate(
        max_seats=Coalesce(
            Subquery(
                RouteCapacity.objects.filter(route=OuterRef('route')).values('max_seats')[:1]
            ),
            Value(30, output_field=IntegerField())  # Default to 30 seats
        )
    )

    suggestions = []
    for trip in trips.select_related('route__agency').distinct():
        route = trip.route
        agency_name = route.agency.name if route.agency else "Unknown Agency"
        line_name = route.short_name

        # Get departure and arrival stoptimes and sequences
        try:
            departure_stoptime = StopTime.objects.get(trip=trip, stop__name=departure_stop_name)
            arrival_stoptime = StopTime.objects.get(trip=trip, stop__name=arrival_stop_name)
            departure_time = departure_stoptime.departure_time
            arrival_time = arrival_stoptime.arrival_time
            departure_sequence = departure_stoptime.stop_sequence
            arrival_sequence = arrival_stoptime.stop_sequence
        except StopTime.DoesNotExist:
            continue  # Skip if stoptimes are missing

        # Check for booking restrictions with hide_result=False
        logger.info(f"departure_stoptime.stop: {departure_stoptime.stop.id}")
        has_restriction = BookingRestriction.objects.filter(
            is_active=True,
            hide_result=False
        ).filter(
            Q(route=trip.route) | Q(station__in=[departure_stoptime.stop, arrival_stoptime.stop])
        ).exists()

        logger.info(f"has_restriction: {has_restriction}")
        if has_restriction:
            is_fully_booked = True
        # Get all bookings for this trip on this date
        bookings = Booking.objects.filter(trip=trip, date=date)

        # Calculate total booked seats overlapping with the requested segment
        total_booked = 0
        for booking in bookings:
            # Get booking's from_sequence and to_sequence
            try:
                booking_departure_stoptime = StopTime.objects.get(trip=trip, stop=booking.from_stop)
                booking_arrival_stoptime = StopTime.objects.get(trip=trip, stop=booking.to_stop)
                booking_from_sequence = booking_departure_stoptime.stop_sequence
                booking_to_sequence = booking_arrival_stoptime.stop_sequence
            except StopTime.DoesNotExist:
                continue  # Skip if stoptimes are missing

            # Ensure booking sequences are in order
            if booking_from_sequence >= booking_to_sequence:
                continue  # Invalid booking, skip

            # Check if booking's segment overlaps with the requested segment
            if (booking_from_sequence < arrival_sequence) and (booking_to_sequence > departure_sequence):
                total_booked += booking.num_passengers

        # Calculate available seats
        max_seats = trip.max_seats
        available_seats = max_seats - total_booked

        # Determine if the trip is fully booked for the requested segment
        if not is_fully_booked:
            is_fully_booked = available_seats < num_passengers

        # Optionally skip trips that cannot accommodate the group size

        # Calculate travel time
        departure_datetime = datetime.combine(date, departure_time)
        arrival_datetime = datetime.combine(date, arrival_time)
        if arrival_datetime < departure_datetime:
            arrival_datetime += timedelta(days=1)
        travel_time = arrival_datetime - departure_datetime
        hours, remainder = divmod(travel_time.total_seconds(), 3600)
        minutes = remainder // 60
        formatted_travel_time = f"{int(hours)} hours, {int(minutes)} minutes" if hours > 0 else f"{int(minutes)} minutes"

        # Prepare suggestion
        suggestion = {
            "agency_name": agency_name,
            "route_id": route.route_id,
            "trip_id": trip.id,
            "date": date.strftime("%Y-%m-%d"),
            "departure_time": departure_time.strftime("%H:%M"),
            "arrival_time": arrival_time.strftime("%H:%M"),
            "travel_time": formatted_travel_time,
            "line_name": line_name,
            "available_seats": available_seats if not has_restriction else 0,
            "is_fully_booked": is_fully_booked,
            "total_booked": total_booked,
            "max_seats": max_seats,
        }

        suggestions.append(suggestion)
        suggestions.sort(key=lambda suggestion: (suggestion["travel_time"], suggestion["departure_time"]))
    return JsonResponse({"suggestions": suggestions})
