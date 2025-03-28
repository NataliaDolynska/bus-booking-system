# Generated by Django 5.1.3 on 2024-11-13 21:52

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Agency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('url', models.URLField()),
                ('timezone', models.CharField(max_length=255)),
                ('agency_id', models.CharField(blank=True, max_length=255, null=True)),
                ('lang', models.CharField(blank=True, max_length=2, null=True)),
                ('phone', models.CharField(blank=True, max_length=255, null=True)),
                ('fare_url', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Block',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('block_id', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Calendar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_id', models.CharField(max_length=255)),
                ('monday', models.IntegerField(choices=[(1, 'Yes'), (0, 'No')])),
                ('tuesday', models.IntegerField(choices=[(1, 'Yes'), (0, 'No')])),
                ('wednesday', models.IntegerField(choices=[(1, 'Yes'), (0, 'No')])),
                ('thursday', models.IntegerField(choices=[(1, 'Yes'), (0, 'No')])),
                ('friday', models.IntegerField(choices=[(1, 'Yes'), (0, 'No')])),
                ('saturday', models.IntegerField(choices=[(1, 'Yes'), (0, 'No')])),
                ('sunday', models.IntegerField(choices=[(1, 'Yes'), (0, 'No')])),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='Direction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('value', models.IntegerField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='DropOffType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('value', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ExceptionType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('value', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Fare',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fare_id', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('value', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='PickupType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('value', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='RouteType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField()),
                ('value', models.IntegerField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Shape',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shape_id', models.CharField(max_length=255)),
                ('geopoint', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('pt_sequence', models.IntegerField()),
                ('dist_traveled', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Zone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zone_id', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='CalendarDate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_id', models.CharField(max_length=255)),
                ('date', models.DateField()),
                ('exception_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gtfs.exceptiontype')),
            ],
        ),
        migrations.CreateModel(
            name='FareAttribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.FloatField()),
                ('currency', models.CharField(max_length=3)),
                ('transfers', models.IntegerField(blank=True, null=True)),
                ('transfer_duration', models.IntegerField(blank=True, null=True)),
                ('fare', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gtfs.fare')),
                ('payment_method', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gtfs.paymentmethod')),
            ],
        ),
        migrations.CreateModel(
            name='Route',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('route_id', models.CharField(max_length=255, unique=True)),
                ('short_name', models.CharField(max_length=255)),
                ('long_name', models.TextField(blank=True, null=True)),
                ('desc', models.TextField(blank=True, null=True)),
                ('url', models.URLField(blank=True, null=True)),
                ('color', models.CharField(default='FFFFFF', max_length=6)),
                ('text_color', models.CharField(default='000000', max_length=6)),
                ('agency', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='gtfs.agency')),
                ('route_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gtfs.routetype')),
            ],
        ),
        migrations.CreateModel(
            name='Stop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stop_id', models.CharField(max_length=255, unique=True)),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('url', models.URLField(blank=True, null=True)),
                ('desc', models.TextField(blank=True, null=True)),
                ('geopoint', django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326)),
                ('code', models.CharField(blank=True, max_length=255, null=True)),
                ('location_type', models.IntegerField(blank=True, choices=[(0, 'Stop'), (1, 'Station')], null=True)),
                ('parent_station', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gtfs.stop')),
                ('zone', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gtfs.zone')),
            ],
        ),
        migrations.CreateModel(
            name='Transfer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transfer_type', models.IntegerField()),
                ('min_transfer_time', models.IntegerField(blank=True, null=True)),
                ('from_stop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_stop', to='gtfs.stop')),
                ('to_stop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_stop', to='gtfs.stop')),
            ],
        ),
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_id', models.CharField(max_length=255)),
                ('trip_id', models.CharField(max_length=255, unique=True)),
                ('headsign', models.TextField(blank=True, null=True)),
                ('shape_id', models.CharField(blank=True, max_length=255, null=True)),
                ('block', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gtfs.block')),
                ('direction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gtfs.direction')),
                ('route', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gtfs.route')),
            ],
        ),
        migrations.CreateModel(
            name='Frequency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('headway_secs', models.IntegerField()),
                ('exact_times', models.IntegerField(blank=True, null=True)),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gtfs.trip')),
            ],
        ),
        migrations.CreateModel(
            name='FareRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fare', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gtfs.fare')),
                ('route', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gtfs.route')),
                ('contains', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contains', to='gtfs.zone')),
                ('destination', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='destination', to='gtfs.zone')),
                ('origin', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='origin', to='gtfs.zone')),
            ],
        ),
        migrations.CreateModel(
            name='StopTime',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arrival_time', models.TimeField(db_index=True)),
                ('departure_time', models.TimeField(db_index=True)),
                ('stop_sequence', models.IntegerField(db_index=True)),
                ('headsign', models.TextField(blank=True, null=True)),
                ('shape_dist_traveled', models.FloatField(blank=True, null=True)),
                ('drop_off_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gtfs.dropofftype')),
                ('pickup_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gtfs.pickuptype')),
                ('stop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gtfs.stop')),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gtfs.trip')),
            ],
            options={
                'indexes': [models.Index(fields=['stop'], name='gtfs_stopti_stop_id_64a4e3_idx')],
            },
        ),
    ]
