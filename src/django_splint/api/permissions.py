from django.conf import settings
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminUserOrReadOnlyAuthenticated(BasePermission):
    """Request is authenticated as a user admin, or is a read-only request."""

    def has_permission(self, request, view):
        """Verify if user and authenticated, then safe method or admin."""
        return bool(
            (request.user and request.user.is_authenticated) and (
                request.method in SAFE_METHODS or
                request.user.is_staff
            )
        )


class IsAdminUserAuthenticated(BasePermission):
    """Request is authenticated as a user admin, or is a read-only request."""

    def has_permission(self, request, view):
        """Verify if user and authenticated, then safe method or admin."""
        return bool(
            request.user and request.user.is_authenticated and
            request.user.is_staff
        )


class WorkflowExternalAuthenticated(BasePermission):
    def has_permission(self, request, view):
        """Allow external workflow authentication."""
        workflow_token = request.GET.get('workflow_token', None)
        return workflow_token == settings.WORKFLOW_TOKEN
