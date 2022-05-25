from rest_framework.filters import OrderingFilter
from django_filters import rest_framework as filters

DEFAULT_DATE_FILTERS = ['gte', 'lte', 'exact', 'gt', 'lt', 'range']


class CustomFieldOrdering(OrderingFilter):

    CUSTOM_QUERY_ORDERING = {}

    def filter_queryset(self, request, queryset, view):
        """Field ordering queryset."""
        ordering = self.get_ordering(request, queryset, view)
        if ordering:
            # === Custom fields adapt =========================================
            def remove_order(term):
                if term.startswith('-'):
                    term = term[1:]
                return term

            custom_fields = [
                remove_order(o)
                for o in ordering
                if remove_order(o) in list(self.CUSTOM_QUERY_ORDERING.keys())
            ]

            for c_field in custom_fields:
                queryset = self.CUSTOM_QUERY_ORDERING.get(c_field)(queryset)
            # =================================================================
            return queryset.order_by(*ordering)

        return queryset


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass
