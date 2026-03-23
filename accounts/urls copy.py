
from django.urls import path
from django.contrib.auth.views import LogoutView
# from .views import login_view, logout_view, register_view тогда без views.login_view
from . import views

app_name = 'accounts'

urlpatterns=[
  path('login/', views.login_view, name='login'),
  path('register/', views.register_view, name='register'),
# path('logout/', LogoutView.as_view(), name='logout'),
  path('logout/', views.logout_view, name='logout'),
  path('profile/', views.profile_view, name='profile'), 
]
