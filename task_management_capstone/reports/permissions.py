from rest_framework.permissions import BasePermission


class IsManager(BasePermission):
    """
    Allow access only to manager users.
    """
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
        return request.user.groups.filter(name='Manager').exists()
