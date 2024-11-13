import logging
from multiprocessing.pool import AsyncResult
from django.utils import timezone
from django.db.models import Q

from django.contrib.admin.views.decorators import staff_member_required
from loguru import logger
from django.db.models import Value, IntegerField
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from celery import shared_task, current_task
import os
import zipfile
from .gtfs_loader import GTFSLoader  # We'll refactor your command into a GTFSLoader class

from .forms import BookingRestrictionForm
from .models import Booking, TaskProgress
from django.contrib import messages
from django.contrib.auth import logout
from django.db.models.functions.datetime import ExtractHour, ExtractMinute
from django.db.models import F, Subquery, OuterRef, Sum, IntegerField, ExpressionWrapper, Max
from gtfs.models import StopTime, Route, Trip, Stop, CalendarDate, Calendar
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.utils.dateparse import parse_date, parse_time
from datetime import datetime, timedelta, time
from django.db.models import Q
from .models import Booking, BookingRestriction, RouteCapacity
from django.shortcuts import render
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django_q.tasks import async_task, result
from django_q.models import OrmQ, Task
import os
import tempfile
from django.http import JsonResponse
from django.db.models import Subquery, OuterRef
from django.http import JsonResponse
from django.db.models import Subquery, OuterRef, Q

from .tasks import import_gtfs_data
from .utils.db_utils import if_exists
from .utils.file_utils import compute_file_hash


def index(request):
    return render(request, "index.html", {})


def login_user(request):
    return render(request, "sign-in.html", {})


def booking_page(request):
    return render(request, "booking.html", {})


def choose_date(request):
    # Fetch available stops based on selected date
    return JsonResponse({"html": "Updated Stop Options HTML"})


def logout_user(request):
    return logout(request)


# @staff_member_required
def admin_upload_gtfs(request):
    if request.method == 'POST':
        gtfs_file = request.FILES.get('gtfs_file')
        if gtfs_file:
            # Save the uploaded file to a temporary location
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, gtfs_file.name)

            with open(temp_file_path, 'wb+') as destination:
                for chunk in gtfs_file.chunks():
                    destination.write(chunk)

            # Start the asynchronous task
            file_hash = compute_file_hash(temp_file_path)
            exits = if_exists(TaskProgress, file_hash=file_hash)
            if exits:
                logger.debug(f"Scheduling task already exists. ")
                task = Task.get_task(exits.task_id)
                if not task:
                    task_id = exits.task_id
                    return JsonResponse({'task_id': task_id, 'status': exits.status})
                else:
                    status = "success" if task.success else "failure"
                    return JsonResponse({'task_id': exits.task_id, 'status': status, 'message': 'Task finished'})
                #     exits.delete()
            logger.debug(f"Scheduling task with function: {import_gtfs_data}")
            from django_q.brokers import get_broker
            task_id = async_task(import_gtfs_data, file_path=temp_file_path, save=True)
            logger.info(f"Loading task with id is {task_id}")
            TaskProgress.objects.get_or_create(task_id=task_id, file_hash=file_hash)

            return JsonResponse({'task_id': task_id})
        else:
            return JsonResponse({'error': 'No file uploaded.'}, status=400)
    else:
        return render(request, 'admin_upload_gtfs.html')


# @staff_member_required
def task_status(request):
    task_id = request.GET.get("task_id")
    try:
        logger.info(f"Task status requested for task_id: {task_id}", )
        progress_record = if_exists(TaskProgress, task_id=task_id)
        if not progress_record:
            return JsonResponse({
                "error": "Task progress record not found.",
            }, status=500)
        progress = progress_record.progress
        message = progress_record.message
        status = progress_record.status
        return JsonResponse({
            "status": status,
            "progress": progress,
            "message": message,
        })
    except Task.DoesNotExist:
        return JsonResponse({
            "error": "Task not found.",
        }, status=500)


# @staff_member_required
def admin_booking_restrictions(request):
    # Fetch all booking restrictions
    restrictions = BookingRestriction.objects.all()

    context = {
        'restrictions': restrictions,
    }
    return render(request, 'admin_booking_restrictions.html', context)


# @staff_member_required
def add_booking_restriction(request):
    if request.method == 'POST':
        form = BookingRestrictionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Booking restriction added successfully.')
            return redirect('admin_booking_restrictions')
    else:
        form = BookingRestrictionForm()

    context = {
        'form': form,
    }
    return render(request, 'add_booking_restriction.html', context)


# @staff_member_required
def delete_booking_restriction(request, restriction_id):
    restriction = get_object_or_404(BookingRestriction, id=restriction_id)
    restriction.delete()
    messages.success(request, 'Booking restriction deleted.')
    return redirect('admin_booking_restrictions')


@staff_member_required
def admin_bookings(request):
    # Fetch all bookings
    bookings = Booking.objects.all().order_by('-date')

    context = {
        'bookings': bookings,
    }
    return render(request, 'admin_bookings.html', context)


# @staff_member_required
def admin_cancel_booking(request, booking_id):
    # Get the booking object
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.status == 'active':
        booking.status = 'canceled'
        booking.save()
        messages.success(request, f'Booking {booking.id} has been canceled.')
    else:
        messages.error(request, 'This booking cannot be canceled.')

    return redirect('admin_bookings')


# @login_required
def user_bookings(request):
    # Fetch active and canceled bookings for the logged-in user
    # active_bookings = Booking.objects.filter(user=request.user, status='active')
    active_bookings = Booking.objects.filter(status='active')
    # canceled_bookings = Booking.objects.filter(user=request.user, status='canceled')
    canceled_bookings = Booking.objects.filter(status='canceled')

    context = {
        'active_bookings': active_bookings,
        'canceled_bookings': canceled_bookings,
    }
    return render(request, 'user_bookings.html', context)


# @login_required
def cancel_booking(request, booking_id):
    # Get the booking object
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if booking.status == 'active':
        booking.status = 'canceled'
        booking.save()
        messages.success(request, 'Your booking has been canceled.')
    else:
        messages.error(request, 'This booking cannot be canceled.')

    return redirect('user_bookings')

from django.http import JsonResponse
from django.db.models import OuterRef, Subquery, F, Q





def suggest_departure_stops(request):
    arrival_stop_name = request.GET.get("arrival_stop_name", None)
    line_id = request.GET.get("line_id", None)  # Bus line ID for faster queries
    departure_name = request.GET.get("departure_stop_name", None)

    # Start with all stop names (duplicates allowed due to same names)
    stops = Stop.objects.all()

    # Filter by bus line if provided
    if line_id:
        trips_with_line = Trip.objects.filter(route__route_id=line_id)
        stops = stops.filter(stoptime__trip__in=trips_with_line).distinct()

    # Filter by arrival stop if provided
    if arrival_stop_name:
        # Get trips that stop at the arrival stop
        trips_with_arrival = Trip.objects.filter(
            stoptime__stop__name=arrival_stop_name
        )
        # If line is also selected, intersect trips
        if line_id:
            trips_with_arrival = trips_with_arrival.filter(route__route_id=line_id)
        # Get departure stops from these trips
        stops = stops.filter(
            stoptime__trip__in=trips_with_arrival
        ).distinct()

    # Filter by partial departure name for autocomplete functionality
    if departure_name:
        stops = stops.filter(name__icontains=departure_name)

    # Only return unique stop names
    stop_names = stops.values_list("name", flat=True).distinct()

    return JsonResponse({"suggested_departure_stops": list(stop_names)})

def suggest_arrival_stops(request):
    departure_stop_name = request.GET.get("departure_stop_name", None)
    line_id = request.GET.get("line_id", None)
    arrival_name = request.GET.get("arrival_stop_name", None)

    # Start with all stops
    stops = Stop.objects.all()

    # Filter by bus line if provided
    if line_id:
        trips_with_line = Trip.objects.filter(route__route_id=line_id)
        stops = stops.filter(stoptime__trip__in=trips_with_line).distinct()

    # Filter by departure stop if provided
    if departure_stop_name:
        # Get trips that stop at the departure stop
        trips_with_departure = Trip.objects.filter(
            stoptime__stop__name=departure_stop_name
        )
        # If line is also selected, intersect trips
        if line_id:
            trips_with_departure = trips_with_departure.filter(route__route_id=line_id)
        # Get arrival stops from these trips
        stops = stops.filter(
            stoptime__trip__in=trips_with_departure
        ).distinct()

    # Filter by partial arrival name for autocomplete functionality
    if arrival_name:
        stops = stops.filter(name__icontains=arrival_name)

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
    from django.db.models import Sum, Value, IntegerField
    from django.db.models.functions import Coalesce

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

    # Filter by line_id if provided
    if line_id and line_id != "null":
        trips = trips.filter(route__route_id=line_id)
    elif line_name and line_name != "null":
        trips = trips.filter(route__short_name__icontains=line_name)

    # Filter trips that include both departure and arrival stops
    trips = trips.filter(
        stoptime__stop__name=departure_stop_name
    ).filter(
        stoptime__stop__name=arrival_stop_name
    ).distinct()

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
        # Arrival time constraint
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
        # Departure time constraint
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
    from django.db.models import Q

    # Fetch active booking restrictions with hide_result=True
    restrictions = BookingRestriction.objects.filter(hide_result=True, is_active=True)

    # Build Q objects for route and station restrictions
    route_restrictions = restrictions.exclude(route_id__isnull=True)
    station_restrictions = restrictions.exclude(station__isnull=True)

    # Q object to accumulate all restrictions
    restriction_q = Q()

    # Route-based restrictions
    if route_restrictions.exists():
        restriction_q |= Q(route__route_id__in=route_restrictions.values_list('route_id', flat=True))

    # Station-based restrictions
    if station_restrictions.exists():
        restriction_q |= Q(
            stoptime__stop__in=station_restrictions.values_list('station', flat=True)
        )

    # Exclude trips matching any restriction
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

    # Step 6: Process each trip to calculate available seats based on overlapping bookings
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
            # Overlaps if booking_from_sequence < arrival_sequence and booking_to_sequence > departure_sequence
            if (booking_from_sequence < arrival_sequence) and (booking_to_sequence > departure_sequence):
                total_booked += booking.num_passengers

        # Calculate available seats
        max_seats = trip.max_seats
        available_seats = max_seats - total_booked

        # Determine if the trip is fully booked for the requested segment
        is_fully_booked = available_seats < num_passengers

        # Optionally, hide trips that are fully booked or continue to display them
        # For now, we exclude trips that cannot accommodate the group size
        if is_fully_booked:
            continue  # Skip trips that cannot accommodate the group size

        # Calculate travel time
        departure_datetime = datetime.combine(date, departure_time)
        arrival_datetime = datetime.combine(date, arrival_time)
        if arrival_datetime < departure_datetime:
            arrival_datetime += timedelta(days=1)
        travel_time = arrival_datetime - departure_datetime
        hours, remainder = divmod(travel_time.total_seconds(), 3600)
        minutes = remainder // 60
        if hours > 0:
            formatted_travel_time = f"{int(hours)} hours, {int(minutes)} minutes"
        else:
            formatted_travel_time = f"{int(minutes)} minutes"

        # Prepare suggestion
        suggestion = {
            "agency_name": agency_name,
            "date": date.strftime("%Y-%m-%d"),
            "departure_time": departure_time.strftime("%H:%M"),
            "arrival_time": arrival_time.strftime("%H:%M"),
            "travel_time": formatted_travel_time,
            "line_name": line_name,
            "book_url": f"/book-trip/{trip.id}/",
            "available_seats": available_seats,
            "is_fully_booked": is_fully_booked,
            "total_booked": total_booked,
            "max_seats": max_seats,
        }

        suggestions.append(suggestion)

    return JsonResponse({"suggestions": suggestions})
