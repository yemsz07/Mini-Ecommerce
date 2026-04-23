from .models import Customer
from django.contrib.auth.forms import UserCreationForm
from django import forms

class registration_form(UserCreationForm):
    # Dahil ang email ay default sa AbstractUser, 
    # kailangan lang natin itong i-set as required kung gusto mo
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)

    class Meta:
        model = Customer
        # Dito mo ilalagay lahat ng fields na lalabas sa form mo
        fields = ['username', 'email', 'phone']

class login_form(UserCreationForm):
    class Meta:
        model = Customer
        fields = ['username', 'email', 'password']