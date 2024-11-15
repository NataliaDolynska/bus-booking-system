from csv import DictReader

from celery.app.task import Task
from loguru import logger
from django.core.management.base import CommandError
from django.contrib.gis.geos import fromstr
from datetime import time, date

import os

from apps.gtfs.models import *


class GTFSLoader:
    def __init__(self, task_id, progress_fn=None):
        self.task_id = task_id
        self.progress_fn = progress_fn
        self.total_steps = 100
        self.current_step = 0

    def update_progress(self, message):
        if self.progress_fn and self.task_id:
            self.progress_fn(task_id=self.task_id,
                             message=message,
                             total_steps=self.total_steps,
                             current_step=self.current_step)

    def load_data(self, root_dir):
        self.total_steps = 11
        self.update_progress('Starting GTFS data import...')
        self.current_step += 1
        self._populate_pickup_types()
        self.current_step += 1
        self._populate_dropoff_types()
        self.current_step += 1
        self._populate_exception_types()
        self.current_step += 1

        self._load_agency(root_dir)
        self.current_step += 1
        self._load_stops(root_dir)
        self.current_step += 1
        self._load_routes(root_dir)
        self.current_step += 1
        self._load_trips(root_dir)
        self.current_step += 1
        self._load_stop_times(root_dir)
        self.current_step += 1
        self._load_calendar(root_dir)
        self.current_step += 1
        self._load_calendar_dates(root_dir)
        self.current_step += 1
        self.update_progress('GTFS data import completed.')

    def _populate_pickup_types(self):
        # Ensure the PickupType table has required entries
        PickupType.objects.get_or_create(name="Regularly scheduled pickup", value=0)
        PickupType.objects.get_or_create(name="No pickup available", value=1)
        PickupType.objects.get_or_create(name="Must phone agency to arrange pickup", value=2)
        PickupType.objects.get_or_create(name="Must coordinate with driver to arrange pickup", value=3)
        self.update_progress('PickupType entries populated.')

    def _populate_dropoff_types(self):
        # Ensure the DropOffType table has required entries
        DropOffType.objects.get_or_create(name="Regularly scheduled drop off", value=0)
        DropOffType.objects.get_or_create(name="No drop off available", value=1)
        DropOffType.objects.get_or_create(name="Must phone agency to arrange drop off", value=2)
        DropOffType.objects.get_or_create(name="Must coordinate with driver to arrange drop off", value=3)
        self.update_progress('DropOffType entries populated.')

    def _populate_exception_types(self):
        # Ensure the DropOffType table has required entries
        ExceptionType.objects.get_or_create(name="Service has been added for the specified date.", value=1)
        ExceptionType.objects.get_or_create(name=" Service has been removed for the specified date.", value=2)
        self.update_progress('ExceptionType entries populated.')

    def _load_calendar_dates(self, root_dir):
        fields = []

        def create_cmd(line):
            temp = check_field(line, 'date')
            date_obj = date(int(temp[0:4]), int(temp[4:6]), int(temp[6:8]))
            return CalendarDate.objects.get_or_create(
                service_id=check_field(line, 'service_id'),
                date=date_obj,
                exception_type=ExceptionType.objects.get(value=check_field(line, 'exception_type'))
            )

        self._load(root_dir, "calendar_dates.txt", create_cmd, fields, optional=True)

    def _load_calendar(self, root_dir):
        fields = []

        def create_cmd(line):
            temp = check_field(line, 'start_date')
            start_date = date(int(temp[0:4]), int(temp[4:6]), int(temp[6:8]))
            temp = check_field(line, 'end_date')
            end_date = date(int(temp[0:4]), int(temp[4:6]), int(temp[6:8]))
            return Calendar.objects.get_or_create(
                service_id=check_field(line, 'service_id'),
                monday=int(check_field(line, 'monday')),
                tuesday=int(check_field(line, 'tuesday')),
                wednesday=int(check_field(line, 'wednesday')),
                thursday=int(check_field(line, 'thursday')),
                friday=int(check_field(line, 'friday')),
                saturday=int(check_field(line, 'saturday')),
                sunday=int(check_field(line, 'sunday')),
                start_date=start_date,
                end_date=end_date
            )

        self._load(root_dir, "calendar.txt", create_cmd, fields, optional=False)

    def _load_stop_times(self, root_dir):
        fields = []

        def create_cmd(line):
            arrival_time = self._parse_time(check_field(line, 'arrival_time'))
            departure_time = self._parse_time(check_field(line, 'departure_time'))

            # Check if Stop exists
            try:
                stop = Stop.objects.get(stop_id=check_field(line, 'stop_id'))
            except Stop.DoesNotExist:
                self.update_progress(
                    f"Warning: Stop with stop_id {check_field(line, 'stop_id')} does not exist. Skipping entry.")
                return None, False

            # Check if Trip exists
            try:
                trip = Trip.objects.get(trip_id=check_field(line, 'trip_id'))
            except Trip.DoesNotExist:
                self.update_progress(
                    f"Warning: Trip with trip_id {check_field(line, 'trip_id')} does not exist. Skipping entry.")
                return None, False

            # Only create StopTime if both Stop and Trip exist
            stop_time, created = StopTime.objects.get_or_create(
                trip=trip,
                stop=stop,
                arrival_time=arrival_time,
                departure_time=departure_time,
                stop_sequence=check_field(line, 'stop_sequence')
            )

            # Optionally set pickup and dropoff types if they exist
            if check_field(line, 'pickup_type', optional=True):
                stop_time.pickup_type = PickupType.objects.get(value=check_field(line, 'pickup_type'))
            if check_field(line, 'drop_off_type', optional=True):
                stop_time.drop_off_type = DropOffType.objects.get(value=check_field(line, 'drop_off_type'))

            # Save and return the created object
            stop_time.save()
            return stop_time, created

        self._load(root_dir, "stop_times.txt", create_cmd, fields, optional=True)

    def _load_stops(self, root_dir):
        fields = [('desc', 'stop_desc'), ('code', 'stop_code'), ('url', 'stop_url'), ('location_type', 'location_type')]

        def create_cmd(line):
            stop, created = Stop.objects.get_or_create(
                stop_id=check_field(line, 'stop_id'),
                name=check_field(line, 'stop_name'),
                geopoint=fromstr(
                    "POINT(%s %s)" % (float(check_field(line, 'stop_lat')), float(check_field(line, 'stop_lon'))))
            )
            if check_field(line, 'zone_id', optional=True):
                zone, _ = Zone.objects.get_or_create(zone_id=check_field(line, 'zone_id'))
                stop.zone = zone
            if check_field(line, 'parent_station', optional=True):
                try:
                    stop.parent_station = Stop.objects.get(stop_id=check_field(line, 'parent_station'))
                except Stop.DoesNotExist:
                    pass
            stop.save()
            return stop, created

        self._load(root_dir, "stops.txt", create_cmd, fields, optional=False)

    def _load_routes(self, root_dir):
        fields = [('desc', 'route_desc'), ('url', 'route_url'), ('color', 'route_color'),
                  ('text_color', 'route_text_color')]

        def create_cmd(line):
            route_type_value = check_field(line, 'route_type', optional=True)
            route_type = None
            if route_type_value:
                # Automatically add "Bus" RouteType if value is 700 and missing
                if route_type_value == '700':
                    route_type, _ = RouteType.objects.get_or_create(name="Bus", value=700)
                else:
                    try:
                        route_type = RouteType.objects.get(value=route_type_value)
                    except RouteType.DoesNotExist:
                        self.update_progress(f"RouteType with value {route_type_value} does not exist. Skipping route.")
                        return None, False

            route, created = Route.objects.get_or_create(
                route_id=check_field(line, 'route_id'),
                short_name=check_field(line, 'route_short_name'),
                long_name=check_field(line, 'route_long_name', optional=True),
                route_type=route_type
            )
            if check_field(line, 'agency_id', optional=True):
                try:
                    route.agency = Agency.objects.get(agency_id=check_field(line, 'agency_id'))
                except Agency.DoesNotExist:
                    self.update_progress("No agency with id %s " % check_field(line, 'agency_id'))
            route.save()
            return route, created

        self._load(root_dir, "routes.txt", create_cmd, fields, optional=False)

    def _load_agency(self, root_dir):
        fields = [('agency_id', 'agency_id'), ('lang', 'agency_lang'), ('phone', 'agency_phone'),
                  ('fare_url', 'agency_fare_url')]

        def create_cmd(line):
            agency, created = Agency.objects.get_or_create(
                name=check_field(line, 'agency_name'),
                url=check_field(line, 'agency_url'),
                timezone=check_field(line, 'agency_timezone')
            )
            return agency, created

        self._load(root_dir, "agency.txt", create_cmd, fields, optional=False)

    def _load_trips(self, root_dir):
        fields = [('headsign', 'trip_headsign'), ('shape_id', 'shape_id')]

        def create_cmd(line):
            trip, created = Trip.objects.get_or_create(
                route=Route.objects.get(route_id=check_field(line, 'route_id')),
                service_id=check_field(line, 'service_id'),
                trip_id=check_field(line, 'trip_id')
            )
            if check_field(line, 'direction_id', optional=True):
                trip.direction = Direction.objects.get(value=check_field(line, 'direction_id'))
            if check_field(line, 'block_id', optional=True):
                trip.block = Block.objects.get_or_create(block_id=check_field(line, 'block_id'))[0]
            trip.save()
            return trip, created

        self._load(root_dir, "trips.txt", create_cmd, fields, optional=False)

    def _load(self, root_dir, filename, get_or_create_cmd, fields, optional=False):
        count = 0
        file_path = os.path.join(root_dir, filename)

        try:
            with open(file_path, 'r') as file:
                reader = DictReader(file)
                for line in reader:
                    obj, created = get_or_create_cmd(line)
                    for key, value in fields:
                        if not getattr(obj, key) and check_field(line, value, optional=True):
                            setattr(obj, key, check_field(line, value))
                    obj.save()
                    count += 1
                    if count % 10000 == 0:
                        self.update_progress(
                            "\tProcessing %s lines from %s, still in progress...\n" % (count, filename))
            self.update_progress("%s entries loaded from %s\n" % (count, filename))
        except FileNotFoundError:
            if not optional:
                self.update_progress(f"Required file {filename} not found in directory.")
                raise CommandError(f"Required file {filename} not found in directory.")
            else:
                self.update_progress(f"Warning: Optional file {filename} not found or loaded improperly.\n")

        except Exception as e:
            self.update_progress(f"Failed to load {filename} data at line {count}. Error: {e}")
            raise CommandError(f"Failed to load {filename} data at line {count}. Error: {e}")

    def _parse_time(self, time_str):
        hour, minute, sec = map(int, time_str.split(":"))
        return time(hour % 24, minute % 60, sec % 60)


def check_field(reader, field, optional=False):
    if field in reader and reader[field]:
        return reader[field]
    elif not optional:
        raise CommandError(f"Field {field} is empty or missing in file.")
    return None
