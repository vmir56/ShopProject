# accounts/urls.py
from django.urls import path
from . import views

from django.contrib.auth.views import LogoutView
# from .views import login_view, logout_view, register_view тогда без views.login_view


app_name = 'accounts'


urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('verify/<uuid:token>/', views.verify_email, name='verify_email'),  # ← добавить
]
