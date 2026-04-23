from django import forms
from .models import Product, Category

class Staff_view_Product(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), empty_label="Select Category")
    
    class Meta:
        model = Product
        fields = ['name', 'price', 'stock', 'image', 'category']  # Added category here
    def clean_price(self):
        price = self.cleaned_data['price']
        if price <= 0:
            raise forms.ValidationError("Price must be greater than 0")
        return price
    def clean_stock(self):
        stock = self.cleaned_data['stock']
        if stock < 0:
            raise forms.ValidationError("Stock cannot be negative")
        return stock
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the sku field since it's auto-generated
        if 'sku' in self.fields:
            del self.fields['sku']
        
        # Update widget attributes
        self.fields['name'].widget.attrs.update({
            'class': 'form-control form-control-sm',
            'placeholder': 'Product Name'
        })
        self.fields['price'].widget.attrs.update({
            'class': 'form-control form-control-sm',
            'step': '0.01',
            'min': '0.01'
        })
        self.fields['stock'].widget.attrs.update({
            'class': 'form-control form-control-sm',
            'min': '0'
        })
        self.fields['image'].widget.attrs.update({
            'class': 'form-control form-control-sm',
            'accept': 'image/*'
        })
        self.fields['category'].widget.attrs.update({
            'class': 'form-select form-select-sm'
        })