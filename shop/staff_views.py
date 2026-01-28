from itertools import product
import logging
from django.shortcuts import render
from django.http import HttpResponse
from .models import Product, Category
from .staff_forms import Staff_view_Product


# Set up logging
logger = logging.getLogger(__name__)

# 1. Ipakita ang buong staff page
def staff_list(request):
    products = Product.objects.all().order_by('-id') # Naka-sort para nasa taas ang bago
    return render(request, 'staff/staff_page.html', {"products": products})

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
    if request.method == 'POST':
        form = Staff_view_Product(request.POST, request.FILES)
        if form.is_valid():
            # Get the category ID from the form data
            category_id = request.POST.get('category')
            try:
                category = Category.objects.get(id=category_id)
            except (Category.DoesNotExist, ValueError):
                return HttpResponse("Invalid category selected", status=400)
            
            # Save the product with the category
            product = form.save(commit=False)
            product.category = category
            product.save()
            
            # Update the image if provided
            if 'image' in request.FILES:
                product.image = request.FILES['image']
                product.save()
                
            return render(
                request,
                'staff/partials/product_row.html',
                {'product': product}
            )
        return HttpResponse(form.errors.as_json(), status=400)
    
    return HttpResponse("Method not allowed", status=405)



def bulk_delete(request):
    if request.method == "POST":
        product_ids = request.POST.getlist('product_ids')
        Product.objects.filter(id__in=product_ids).delete()
        
        # Ibalik ang updated na listahan ng products
        products = Product.objects.all().order_by('-id')
        return render(request, 'staff/partials/product_table_rows.html', {'products': products})