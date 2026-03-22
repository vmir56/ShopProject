# core/views.py
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_dashboard(request):
    """Дашборд для администратора"""
    return render(request, 'core/admin_dashboard.html')

def start(request):
    return render(request,'start.html')
