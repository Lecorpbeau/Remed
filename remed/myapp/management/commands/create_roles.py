from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = 'Create user roles and assign permissions'

    def handle(self, *args, **options):
        roles_permissions = {
            'Utilisateur': [],
            'Proprietor': ['add_user'],
            'Admin': ['add_user', 'change_user', 'delete_user', 'view_user']
        }

        for role, permissions in roles_permissions.items():
            group, created = Group.objects.get_or_create(name=role)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Role "{role}" created successfully'))
            else:
                self.stdout.write(self.style.WARNING(f'Role "{role}" already exists'))

            for perm in permissions:
                permission_qs = Permission.objects.filter(codename=perm)
                for permission in permission_qs:
                    group.permissions.add(permission)
                    self.stdout.write(self.style.SUCCESS(f'Permission "{perm}" added to role "{role}"'))

        self.stdout.write(self.style.SUCCESS('Roles and permissions initialized successfully'))
