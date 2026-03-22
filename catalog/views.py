
from django.shortcuts import render
from .models import Product

def catalog(request):
    return render(request,'catalog/list.html',{'products':Product.objects.all()})
