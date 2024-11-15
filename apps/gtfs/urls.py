from django.urls import path
from . import views
from .views import task_status, admin_upload_gtfs

urlpatterns = [
    path('', views.index, name='gtfs'),
    path('gtfs/upload/', admin_upload_gtfs, name='upload-gtfs'),
    path('gtfs/upload/status/', task_status, name='upload-gtfs-status'),

]
