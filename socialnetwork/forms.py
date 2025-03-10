from django import forms
from django.contrib.auth.models import User
from .models import Profile, Post

#
# LoginForm
#
class LoginForm(forms.Form):
    username = forms.CharField(max_length=20, label='Username')
    password = forms.CharField(max_length=200, label='Password', widget=forms.PasswordInput())

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=20, label='Username')
    def clean_username(self):
        uname = self.cleaned_data.get('username')

        if User.objects.filter(username=uname).exists():
            raise forms.ValidationError('This username is already taken. Please choose another.')
        return uname
    password = forms.CharField(max_length=200, label='Password', widget=forms.PasswordInput())
    confirm_password = forms.CharField(max_length=200, label='Confirm', widget=forms.PasswordInput())
    email = forms.EmailField(max_length=50, label='E-mail')
    first_name = forms.CharField(max_length=20, label='First Name')
    last_name = forms.CharField(max_length=20, label='Last Name')

    # Optionally add a clean method to check password match
    def clean(self):
        cleaned_data = super().clean()
        pwd1 = cleaned_data.get('password')
        pwd2 = cleaned_data.get('confirm_password')
        if pwd1 and pwd2 and pwd1 != pwd2:
            self.add_error('confirm_password', 'Passwords did not match.')
        return cleaned_data

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'picture']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 3, 
                'cols': 60, 
                'id': 'id_bio_input_text'
            }),
            'picture': forms.ClearableFileInput(attrs={
                'id': 'id_profile_picture'
            }),
        }



class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={'id': 'id_post_input_text', 'name': 'posttext'}),
        }