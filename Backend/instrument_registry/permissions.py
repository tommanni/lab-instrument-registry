from rest_framework import permissions

# Used to ensure that logged in users can only edit/delete their own profiles.
class IsSameUserOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.id == request.user.id