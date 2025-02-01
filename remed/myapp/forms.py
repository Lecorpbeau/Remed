from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from .models import Client, Service, Appointment, CustomUser, Specialist

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[(group.name, group.name) for group in Group.objects.all()]
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            role = self.cleaned_data['role']
            group = Group.objects.get(name=role)
            user.groups.add(group)
        return user

class SignUpForm(CustomUserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}))

    class Meta:
        model = CustomUser
        fields = ('username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'price']
    def __init__(self, *args, **kwargs): 
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs) 
    def save(self, commit=True): 
        instance = super().save(commit=False) 
        if self.user: 
            instance.created_by = self.user 
        if commit: 
            instance.save() 
        return instance

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']
    def __init__(self, *args, **kwargs): 
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs) 
        
    def save(self, commit=True): 
        instance = super().save(commit=False) 
        if self.user: 
            instance.created_by = self.user 
        if commit: 
            instance.save() 
        return instance

class AppointmentCreationForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['user', 'service', 'specialist', 'date']

class ChangeUserRoleForm(forms.ModelForm):
    role = forms.ChoiceField(choices=[(group.name, group.name) for group in Group.objects.all()])

    class Meta:
        model = CustomUser
        fields = ['role']

class ConvertToProprietorForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['is_proprietaire']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_proprietaire = True
        if commit:
            user.save()
        return user

class SpecialistForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=CustomUser.objects.filter(is_staff=True, is_proprietaire=True), required=True, label='Select User')

    class Meta:
        model = Specialist
        fields = ['user', 'description', 'speciality']
