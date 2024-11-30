from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from .models import Uploaded_img
#
# class UForm(forms.Form):
#     username = forms.CharField(label = 'username',max_length = 100)
#     password = forms.CharField(label = 'password',widget=forms.PasswordInput())
#     email = forms.EmailField(label = 'email')
#     address = forms.CharField(label='address',max_length = 100)



class RegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email","address")

class ImgForm(forms.ModelForm):
    class Meta:
        model = Uploaded_img
        fields = ('img',)