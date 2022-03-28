
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import FieldError

from import_export.admin import ExportActionMixin

from db.models import SplintModel


try:
    EXTRA_CSS = settings.EXTRA_CSS
except AttributeError:
    EXTRA_CSS = '/static/css/custom_admin.css'


class SplintBaseAdminMixin(object):
    exclude = ['_deleted', '_deleted_at']

    class Media:
        css = {
            'all': (EXTRA_CSS,)
        }

    def get_queryset(self, request):
        """Filter not deleted."""
        qs = super().get_queryset(request)

        return qs.filter(_deleted=False)

    def save_model(self, request, obj, form, change):
        """Inject action origin at the object."""
        # obj.user_id = request.user.id
        obj.origin = SplintModel.ADMIN_ORIGIN
        return super().save_model(request, obj, form, change)


class SplintInlineAdminMixin(object):
    extra = 1
    exclude = ['_deleted', '_deleted_at']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Remove deleted from queryset."""
        if 'queryset' not in kwargs:
            queryset = self.get_naive_queryset(db_field)
            if queryset is not None:
                try:
                    kwargs['queryset'] = queryset.filter(_deleted=False)
                except FieldError:
                    pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_naive_queryset(self, db_field):
        """Naive default manager."""
        return db_field.remote_field.model._default_manager


class SplintInlineAdmin(SplintInlineAdminMixin, admin.StackedInline):
    pass


class SplintModelAdminMixin(SplintBaseAdminMixin):

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Remove deleted from queryset."""
        if 'queryset' not in kwargs:
            queryset = self.get_naive_queryset(db_field)
            if queryset is not None:
                try:
                    kwargs['queryset'] = queryset.filter(_deleted=False)
                except FieldError:
                    pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Remove deleted from queryset."""
        if 'queryset' not in kwargs:
            queryset = self.get_naive_queryset(db_field)
            if queryset is not None:
                try:
                    kwargs['queryset'] = queryset.filter(_deleted=False)
                except FieldError:
                    pass

        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_naive_queryset(self, db_field):
        """Naive default manager."""
        return db_field.remote_field.model._default_manager

    def get_search_results(self, request, queryset, search_term):
        """Add support for ajax autocomplete search.

        Dont know why this does not work.... so I have to implement a
        workaround.
        """
        if request.is_ajax:
            search_term = request.GET.get('term')
            if search_term is None:
                search_term = request.GET.get('q', '')
        return super().get_search_results(request, queryset, search_term)


class SplintModelAdmin(ExportActionMixin, SplintModelAdminMixin, admin.ModelAdmin):
    ordering = ('-created_at',)


class SplintReadOnlyAdminMixin:

    def has_add_permission(self, request):
        """No add permission for answer at admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """No permission to change tracks on admin."""
        return False

    def has_delete_permission(self, request, obj=None):
        """No permission to delete tracks on admin."""
        return False


class SplintReadOnlyModelAdmin(SplintReadOnlyAdminMixin, SplintModelAdmin):
    """ModelAdmin class that prevents modifications through the admin."""
    pass


class SplintTabularInlineAdmin(SplintInlineAdminMixin, admin.TabularInline):
    pass
