from django.urls import path
from . import views

urlpatterns = [
    # shop Paths
    path('', views.base, name='base'),
    path('home/', views.home_page, name='home_page'),
    path('about/', views.about_page, name='about_page'),
    path('register/', views.register_page, name='register_page'),
    
    # Staff/Inventory Paths
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/get-row/', views.get_new_row, name='get_new_row'),
    path('staff/crud/', views.staff_crud, name='staff_crud'), # IMPORTANTE: Idagdag ito para sa Save button
    path('inventory/', views.inventory, name='inventory'),
    path('staff/bulk-delete/', views.bulk_delete, name='bulk_delete'),
    
    
]