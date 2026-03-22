# core/urls.py
from django.urls import path
from . import views

app_name = 'core'


urlpatterns = [
    path('', views.start, name='start'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]

