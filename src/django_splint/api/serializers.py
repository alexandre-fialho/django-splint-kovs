from django.core.exceptions import ValidationError
from rest_framework import serializers


class SplintSerializerMixin:
    """Serializer mixin to validate request data and change fields names."""

    skip = set(['csrfmiddlewaretoken'])

    def get_field_names(self, declared_fields, info):
        """Mixin for removing protect fields."""
        fields = super().get_field_names(declared_fields, info)
        if getattr(self.Meta, 'extra_fields', None):
            fields += self.Meta.extra_fields
        return list(filter(lambda f: not f.startswith('_'), fields))

    def validate(self, data):
        """Raise error in case any aditional data is passed in the request."""
        if hasattr(self, 'initial_data'):
            if isinstance(self.initial_data, list):
                unknown_keys = set(
                    [k for obj in self.initial_data for k in list(obj.keys())]
                ) - set(self.fields.keys())
            else:
                unknown_keys = set(
                    self.initial_data.keys()) - set(self.fields.keys())
            if (unknown_keys - self.skip):
                raise ValidationError(
                    "Got unknown fields: {}".format(unknown_keys))
        return data


class SplintSerializer(SplintSerializerMixin, serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(SplintSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
