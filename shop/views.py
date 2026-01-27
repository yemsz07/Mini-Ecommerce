from django.shortcuts import render
from .models import Product
from . import staff_views

# Create references to the functions
staff_list = staff_views.staff_list
staff_crud = staff_views.staff_crud
get_new_row = staff_views.get_new_row
inventory = staff_views.inventory
bulk_delete = staff_views.bulk_delete

# Create your views here.
def home_page(request):
    products = Product.objects.all()
    return render(request, 'shop/home_page.html', {'products': products})

def base(request):
    return render(request, 'shop/base.html')

def about_page(request):
    return render(request, 'shop/about.html')

def register_page(request):
    return render(request, 'shop/register_page.html')


def staff_page(request):
    return staff_list(request)

