# accounts/urls.py
from django.urls import path
from . import views
#from django.contrib.auth.views import LogoutView

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/delete-request/', views.delete_account_request, name='delete_account_request'),
    path('delete/<uuid:token>/', views.delete_account_confirm, name='delete_account_confirm'),
    path('verify/<uuid:token>/', views.verify_email, name='verify_email'),

    # Восстановление пароля
    path('recover/', views.password_recover, name='recover'),
    path('reset/<uuid:token>/', views.password_reset, name='password_reset'),
]
