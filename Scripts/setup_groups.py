from django.contrib.auth.models import Group, Permission

def run():
    admin_group, created = Group.objects.get_or_create(name='Admin')
    proprietor_group, created = Group.objects.get_or_create(name='Proprietor')
    guest_group, created = Group.objects.get_or_create(name='Guest')

    # Ajouter des permissions aux groupes...
    # admin_group.permissions.add(...)
    # proprietor_group.permissions.add(...)
