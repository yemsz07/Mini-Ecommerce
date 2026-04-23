from django.shortcuts import render, redirect
from .models import Product
from . import staff_views
from django.contrib import messages
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem, Customer
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import logout as auth_logout, authenticate, login
from .forms import registration_form, login_form
from .backend import EmailBackend
import logging
import json
from django.contrib.auth.decorators import login_required
from .cart import Cart
from .services import CartService, PurchaseService

# Create references to the functions
staff_list = staff_views.staff_list
staff_crud = staff_views.staff_crud
get_new_row = staff_views.get_new_row
inventory = staff_views.inventory
bulk_delete = staff_views.bulk_delete

logger = logging.getLogger(__name__)

# Create your views here.

# itong line na ito ay para sa about_page
def about_page(request):
    return render(request, 'shop/about_page.html')

# itong line na ito ay para sa logout_user
def logout_user(request):
    auth_logout(request)
    return redirect('base')

# itong line na ito ay para sa slidebar_page
def slidebar_page(request):
    return render(request, 'shop/slidebar_page.html')

# itong line na ito ay para sa staff_page
def staff_page(request):
    return staff_list(request)

# itong line na ito ay para sa login_user
def login_user(request):
    # ito yung line na kung saan mag sesend ng POST request sa login_user
    if request.method == 'POST':
        # line kung saan itatype ni user ang username na naka save sa database
        username = request.POST.get('username')
        # ling kung saan itatype ni user ang password na naka save sa database
        password = request.POST.get('password')
        # ito yung line na kung saan i validate ni django kung merong naka save username,password at email sa database 
        user = authenticate(request, username=username, password=password, backend='shop.backend.EmailBackend')
        
        # ito yung logic na kung saan i validate ni django kung tama ba yung username , password at email na inilagay ni user
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            # pag tama ang username at password mapupunta sa base page
            return redirect('base')
        else:
            messages.error(request, "Invalid username or password.")
            # pag nag error balik sa login page
            return render(request, 'shop/login_user.html')
        # para pumunta sa login page
    return render(request, 'shop/login_user.html')

# itong line na ito ay para sa register_page
def register_page(request):
    # ito yung line na kung saan mag sesend ng POST request sa register_page
    if request.method == 'POST':
        # ito yung line na kung saan mag sesend si user based sa ginamit na field sa registration_form
        form = registration_form(request.POST)
        # ito yung line na kung saan i vavalidate ni django kung tama ba yung POST na binigay ni user
        if form.is_valid():
            # Dahil ang Customer ay AbstractUser na, lahat ng fields 
            # (username, email, phone, address) ay mase-save dito sa isang tawag lang.
            form.save() 
            
            messages.success(request, "Account created successfully")
            return redirect('login_user')
    else:
        # Kapag binuksan ang page (GET), gumawa ng blank form.
        form = registration_form()
    
    # Dito papasok ang 'form' variable              / ito ang gagamitin para matawag sa html
    return render(request, 'shop/register_page.html', {'form': form})



# itong line na ito ay para sa base_page
def base(request):
    # itong line na ito kinukua nito ang buong Data sa Product Model
    products = Product.objects.all()
    
    # itong line na ito ay kinuha nito ang function get_cart_count na galing sa CartService na ginagamit para sa cart_count 
    cart_count = CartService.get_cart_count(request)
    
    # itong line na ito ay render nito sa base.html / ito naman ang gagamitin para ma-i connect sa html
    return render(request, 'shop/base.html', {'products': products, 'cart_count': cart_count})

# itong line na ito ay para sa view_options
def view_options(request, product_id):
    # itong line na ito ay ang pagkuha ng specific Data sa Product Model
    product = get_object_or_404(Product, id=product_id)
    
    # itong line na ito ay kinuha nito ang function get_cart_count na galing sa CartService na ginagamit para sa cart_count 
    cart_count = CartService.get_cart_count(request)
    # ito yung line na ito ay render para sa view_options.html / ito naman ang gagamitin para ma-i connect sa html
    return render(request, 'shop/view_options.html', {
        'product': product, 
        'cart_count': cart_count
    })

# itong line na ito ay para sa add_to_cart
@login_required
def add_to_cart(request, product_id):
    # ito yung line na kung saan kinukuha yung specific product
    product = get_object_or_404(Product, id=product_id)
    # *kino-convert nito as interger ang lahat ng pumapasok sa POST*
    quantity = int(request.POST.get('quantity', 1))
    
    # ito yung line na kung saan ginagamit ang kapangyarihan ni CartService na add_to_cart function para makapag add ng product at quantity sa cart session
    CartService.add_to_cart(request, product, quantity)
    # ito yung message na binigay ni Django kapag pumasok na ang data 
    messages.success(request, f"{product.name} added to cart!")
    # ito yung line na ito ay redirect para sa view_options.html / ito naman ang gagamitin para ma-i connect sa html
    return redirect('view_options', product_id=product.id)

# itong line na ito ay para sa process_purchase
@login_required
def process_purchase(request, product_id):
    """DRY: Refactored to use service layer"""
    #ito yung logic na kung saan bina-validate ni Django na dapat POST lang ang papasok wala ng iba
    if request.method != 'POST':
        # ito yung line na kung saan hindi pinapayagan Django ang ibang method maliban sa POST
        return HttpResponse("Invalid Method", status=405)
    # ito yung line na kung saan kinoconvert nito as interger ang lahat ng pumapasok sa POST
    quantity = int(request.POST.get('quantity', 1))
    
    # itong line na ito ay multiple assignment ang pag proseso ng pagbili ibabalik ang 'result' kung success at 'errors' kung may problema.
    result, errors = PurchaseService.process_purchase(request, product_id, quantity)
    
    # Errors
    if errors:
        for error in errors:
            logger.error(f"Purchase failed: {error}")
            messages.error(request, error)
        return redirect('view_options', product_id=product_id)
    
    # Result
    logger.info(f"Purchase successful: {result}")
    messages.success(request, 
        f"Order successful! Order #{result['order'].id} - "
        f"{result['quantity']} x {result['product'].name} = ₱{result['total_price']:.2f}"
    )
    # go to base.html
    return redirect('base')
    
    #line for cart_view
@login_required
def cart_view(request):
    
    from .services import CartService
    
    # ito yung line na kung saan kinukuha nito yung buong total ng cart
    cart_data = CartService.get_cart_totals(request)
    cart_items = cart_data['cart_items']
    subtotal = cart_data['subtotal']       
    total = cart_data['total']        
    
    # Calculate total items count
    total_items = sum(item['quantity'] for item in cart_items)
    
    # Get cart count for badge
    cart_count = CartService.get_cart_count(request)

    # ito yung gagamitin para ma connect sa html
    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'total': total,
        'total_items': total_items,
        'cart_count': cart_count
    })

# ito yung gagamitin para ma connect sa html
@login_required
def update_cart(request, product_id):
    """Update cart item quantity via form submission"""
    from .services import CartService
    from decimal import Decimal
    
    
    if request.method != 'POST':
        return redirect('cart_view')
    
    try:
        action = request.POST.get('action')
        current_quantity = int(request.POST.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id)
        cart = Cart(request)
        
        # Calculate new quantity based on action
        if action == 'increase':
            new_quantity = current_quantity + 1
        elif action == 'decrease':
            new_quantity = current_quantity - 1
        else:
            new_quantity = current_quantity
        
        # Stock validation
        if new_quantity > product.stock:
            messages.error(request, f'Only {product.stock} items available in stock')
            return redirect('cart_view')
        
        if new_quantity < 1:
            messages.error(request, 'Quantity must be at least 1')
            return redirect('cart_view')
        
        # Update cart
        cart.add(product=product, quantity=new_quantity, override_quantity=True)
        messages.success(request, f'Updated {product.name} quantity to {new_quantity}')
        
    except (ValueError, TypeError):
        messages.error(request, 'Invalid quantity')
    except Exception as e:
        messages.error(request, 'An error occurred while updating cart')
    
    return redirect('cart_view')

@login_required
def checkout_view(request):
    """Display checkout page with cart items"""
    from .services import CartService
    
    # Get cart totals with proper VAT handling
    cart_data = CartService.get_cart_totals(request)
    cart_items = cart_data['cart_items']
    subtotal = cart_data['subtotal']
    total = cart_data['total']
    
    # Calculate total items count
    total_items = sum(item['quantity'] for item in cart_items)
    
    # Get cart count for badge
    cart_count = CartService.get_cart_count(request)
    
    if not cart_items:
        messages.warning(request, 'Your cart is empty. Please add items before checkout.')
        return redirect('cart_view')
    
    return render(request, 'shop/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'total': total,
        'total_items': total_items,
        'cart_count': cart_count
    })

@login_required
def process_checkout(request):
    """Process checkout and create order"""
    from .services import CartService
    
    if request.method != 'POST':
        return redirect('checkout_view')
    
    # Get cart data
    cart_data = CartService.get_cart_totals(request)
    cart_items = cart_data['cart_items']
    
    if not cart_items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart_view')
    
    try:
        # Create order
        with transaction.atomic():
            order = Order.objects.create(
                customer=request.user,
                status='Completed',
                complete=True
            )
            
            # Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity']
                )
            
            # Clear cart
            cart = Cart(request)
            cart.clear()
            
            # Store order in session for receipt
            request.session['last_order_id'] = order.id
            
            messages.success(request, 'Order completed successfully!')
            return redirect('receipt_view')
            
    except Exception as e:
        messages.error(request, f'Error processing order: {str(e)}')
        return redirect('checkout_view')

@login_required
def receipt_view(request):
    """Display order receipt"""
    order_id = request.session.get('last_order_id')
    
    if not order_id:
        return redirect('base')
    
    try:
        order = Order.objects.get(id=order_id, customer=request.user)
        order_items = OrderItem.objects.filter(order=order).select_related('product')
        
        # Clear session
        del request.session['last_order_id']
        
        return render(request, 'shop/receipt.html', {
            'order': order,
            'order_items': order_items,
            'cart_count': CartService.get_cart_count(request)
        })
        
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('base')

@login_required
def remove_from_cart(request, product_id):
    """Remove item from cart via form submission"""
    from .services import CartService
    
    if request.method != 'POST':
        return redirect('cart_view')
    
    try:
        product = get_object_or_404(Product, id=product_id)
        cart = Cart(request)
        
        product_id_str = str(product_id)
        if product_id_str in cart.cart:
            del cart.cart[product_id_str]
            cart.save()
            messages.success(request, f'{product.name} removed from cart')
        else:
            messages.error(request, 'Item not found in cart')
        
    except Exception as e:
        messages.error(request, 'An error occurred while removing item from cart')
    
    return redirect('cart_view')