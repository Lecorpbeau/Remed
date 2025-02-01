from functools import wraps
from django.http import HttpResponseForbidden

def admin_only(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.groups.filter(name='Admin').exists():
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()
    return _wrapped_view

def group_required(*group_names):
    def in_groups(user):
        return user.is_authenticated and any(group.name in group_names for group in user.groups.all())

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if in_groups(request.user):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden('Vous n\'avez pas l\'autorisation d\'accéder à cette page.')
        return _wrapped_view
    return decorator
