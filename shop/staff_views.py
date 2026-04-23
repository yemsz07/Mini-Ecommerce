from itertools import product
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .models import Product, Category
from .staff_forms import Staff_view_Product
from .services import CartService
import logging

# Set up logging
logger = logging.getLogger(__name__)

# 1. Ipakita ang buong staff page
def staff_list(request):
    products = Product.objects.all()
    # DRY: Use service for cart count
    cart_count = CartService.get_cart_count(request)
    return render(request, 'staff/staff_page.html', {"products": products, "cart_count": cart_count})

# 2. Ibigay lang ang blankong input form row
def get_new_row(request):
    # I-include ang categories sa context
    categories = Category.objects.all()
    return render(request, 'staff/partials/new_row_form.html', {'categories': categories})

# 3. Ipakita ang inventory page
def inventory(request):
    inventory_items = Product.objects.all().order_by('-created_at')
    return render(request, 'staff/inventory.html', {'inventory_items': inventory_items})

# 4. Ang aktwal na magse-save sa database
# In staff_views.py, change the function name from staff_create to staff_crud
def staff_crud(request):
    """
    Handle CRUD operations for products via HTMX.
    Creates new products from form submission.
    """
    if request.method != 'POST':
        logger.warning(f"Invalid method {request.method} for staff_crud")
        return HttpResponse("Method not allowed", status=405)
    
    form = Staff_view_Product(request.POST, request.FILES)
    
    # Validation should be outside transaction
    if not form.is_valid():
        logger.warning(f"Form validation failed: {form.errors}")
        return HttpResponse(f"Form errors: {form.errors}", status=400)
    
    try:
        with transaction.atomic():
            product = form.save()
            logger.info(f"Product created successfully: {product.name} (ID: {product.id})")
            
            return render(
                request,
                'staff/partials/product_row.html',
                {'product': product}
            )
    except Exception as e:
        logger.error(f"Error saving product: {e}")
        return HttpResponse(f"Error saving product: {e}", status=500)



def bulk_delete(request):
    if request.method == "POST":
        product_ids = request.POST.getlist('product_ids')
        Product.objects.filter(id__in=product_ids).delete()
        
        # Ibalik ang updated na listahan ng products
        products = Product.objects.all().order_by('-id')
        return render(request, 'staff/partials/product_table_rows.html', {'products': products})