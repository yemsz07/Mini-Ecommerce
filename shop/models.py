from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
import uuid
from django.utils.text import slugify
from django.conf import settings



# CATEGORY MODEL
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)


    def __str__(self):
        return self.name


    def save(self, *args, **kwargs):
        if not self.slug: # Kung walang nilagay na slug
            self.slug = slugify(self.name) # Siya na ang gagawa base sa name
        super().save(*args, **kwargs)


class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name + " + " + self.sku

# INVENTORY MODEL
class Inventory(models.Model):
    # Field usage for Inventory
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventories')
    quantity = models.PositiveIntegerField(default=0)
    location = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=50, unique=True)  # para sa tracking
    last_updated = models.DateTimeField(auto_now=True)
    
    # auto generate sku
    #if no sku create 8 letter random code
    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self.product.sku
        super().save(*args, **kwargs)

    # design for Inventory
    def __str__(self):
        return f"{self.product.name} + {self.sku}"



# Built-in User Model 
class Customer(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username 


# ORDER MODEL
class Order(models.Model):

    # Choices for Order Status
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )

    # Field usage for Order
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    complete = models.BooleanField(default=False)

    # Design for Order Status
    def __str__(self):
        customer_name = self.customer.username if self.customer else "Anonymous"
        return f"Order {self.id} by {customer_name} - {self.status}"
    
    # Design for Order Total Price
    def get_total_order_price(self):
        return sum(item.get_total_price() for item in self.items.all())


# ORDER ITEM MODEL
class OrderItem(models.Model):
    # Field usage for OrderItem
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    # Design for OrderItem
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    # Design for OrderItem Total Price
    def get_total_price(self):
        if self.product:
            return self.quantity * self.product.price
        return 0
