from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet


class SplintViewSetMixin:
    """Mixin for creating generic methos for SplintViewsets."""

    def get_serializer_class(self):
        """Change serializer for list."""
        if hasattr(self, 'list_serializer_class') and self.action == 'list':
            return self.list_serializer_class
        if (hasattr(self, 'write_serializer_class') and
                self.action in [
                'create', 'update', 'partial_update', 'destroy']):
            return self.write_serializer_class
        if (hasattr(self, 'read_serializer_class') and
                self.action in ['list', 'retrieve']):
            return self.read_serializer_class
        return super().get_serializer_class()

    def paginate_queryset(self, *args, **kwargs):
        """Remove pagination if parameter no_page is passed."""
        if 'no_page' in self.request.query_params:
            return None
        return super().paginate_queryset(*args, **kwargs)


class SplintModelViewSet(SplintViewSetMixin, ModelViewSet):
    """Splint version of DRF ModelViewSet."""
    pass


class SplintViewSet(SplintViewSetMixin, GenericViewSet):
    """Splint version of DRF GenericViewSet."""
    pass


class CreateListMixin:
    """Allows bulk creation of a resource."""

    def get_serializer(self, *args, **kwargs):
        """List serialier adding many kwargs."""
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)


class DestroyListMixin:
    """Allows bulk delete of a resource."""

    @action(methods=['delete'], detail=False, url_path='bulk')
    def bulk_delete(self, request):
        """Perform bulk delete."""
        queryset = self.get_queryset()
        queryset.filter(id__in=request.data).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
