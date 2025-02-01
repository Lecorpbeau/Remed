from django.contrib import admin
from .models import Client, Service, User
from django.contrib.auth.admin import UserAdmin

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone_number', 'address', 'created_by')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price', 'created_by')

admin.site.register(User, UserAdmin)