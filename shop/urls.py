from django.urls import path
from . import views

urlpatterns = [
    # shop Paths
    path('', views.base, name='base'),
    path('about/', views.about_page, name='about_page'),
    path('register/', views.register_page, name='register_page'),
    path('slidebar/', views.slidebar_page, name='slidebar_page'),
    path('view-options/<int:product_id>/', views.view_options, name='view_options'),
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('process-purchase/<int:product_id>/', views.process_purchase, name='process_purchase'),
    path('cart/', views.cart_view, name='cart_view'),
    path('update-cart/<int:product_id>/', views.update_cart, name='update_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout_view'),
    path('process-checkout/', views.process_checkout, name='process_checkout'),
    path('receipt/', views.receipt_view, name='receipt_view'),
    
    # Staff/Inventory Paths
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/get-row/', views.get_new_row, name='get_new_row'),
    path('staff/crud/', views.staff_crud, name='staff_crud'), # IMPORTANTE: Idagdag ito para sa Save button
    path('inventory/', views.inventory, name='inventory'),
    path('staff/bulk-delete/', views.bulk_delete, name='bulk_delete'),
]