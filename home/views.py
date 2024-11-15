from apps.bookings.models import Booking
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import *


@login_required(login_url='/users/signin/')
def index(request):
    if request.user.is_superuser:
        bookings  = Booking.objects.all()
        context = {
            'segment': 'dashboard',
            "bookings" : bookings
        }

        return render(request, "dashboard/index.html", context)
    else:
        context = {
            'segment': 'bookings',
        }
        return render(request, "bookings/all-bookings.html", context)

# @login_required(login_url='/users/signin/')
# def starter(request):
#
#   context = {}
#   return render(request, "pages/starter.html", context)
