from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Record

class RecordForm(forms.ModelForm):
    class Meta:
        model = Record
        fields = ['title', 'artist', "genre", 'price', 'stock', 'image']  


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Requerido. Introduce una dirección de correo válida.")

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data['email'] 
        if commit:
            user.save() 
        return user
