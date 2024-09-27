from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Record, Review

class RecordForm(forms.ModelForm):
    class Meta:
        model = Record
        fields = ['title', 'artist', "genre", 'price', 'stock', 'image']  

class CustomUserCreationForm(UserCreationForm):
    address = forms.CharField(max_length=255, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'address')

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

