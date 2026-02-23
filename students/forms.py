from django import forms
from django.contrib.auth.models import User
from .models import StudentProfile


class RegistrationForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Password'}))

    # পেমেন্ট তথ্য
    mobile_number = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'bKash/Nagad Number'}))
    transaction_id = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'TrxID (Transaction ID)'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            # প্রোফাইল তৈরি করা হচ্ছে
            StudentProfile.objects.create(
                user=user,
                mobile_number=self.cleaned_data['mobile_number'],
                transaction_id=self.cleaned_data['transaction_id'],
                is_approved=False  # শুরুতে অ্যাপ্রুভ করা থাকবে না
            )
        return user

# একদম উপরে import এর জায়গায় এটি আছে কি না চেক করে নিন (না থাকলে দিন)

# ... আপনার RegistrationForm এর কোডগুলো যেমন আছে তেমনই থাকবে ...

# 👇 একদম নিচে এই দুটি নতুন ফর্ম যোগ করুন 👇


class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        label='আপনার নাম (First Name)', max_length=100)
    last_name = forms.CharField(
        label='বংশের নাম (Last Name)', max_length=100, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['profile_picture']
        labels = {'profile_picture': 'প্রোফাইল ছবি'}
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
