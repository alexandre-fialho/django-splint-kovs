import base64
import six
import uuid

from django.core.files.base import ContentFile
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


class SplintCreateListMixin:
    """Allows bulk creation of a resource."""

    def get_serializer(self, *args, **kwargs):
        """List serializer adding many kwargs."""
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)


class SplintBase64ImageField(serializers.ImageField):
    """
    A Django REST framework field for handling image-uploads through raw post data.
    It uses base64 for encoding and decoding the contents of the file.

    Heavily based on
    https://github.com/tomchristie/django-rest-framework/pull/1268

    Updated for Django REST framework 3.
    """

    def to_internal_value(self, data):
        """File conversion from base64."""
        # Check if this is a base64 string
        if isinstance(data, six.string_types):
            # Check if the base64 string is in the "data:" format
            if 'data:' in data and ';base64,' in data:
                # Break out the header from the base64 content
                header, data = data.split(';base64,')

            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail('invalid_image')

            # Generate file name:
            file_name = str(uuid.uuid4())[:12]  # 12 characters are enough.
            # Get the file name extension:
            file_extension = self.get_file_extension(file_name, decoded_file)

            complete_file_name = "%s.%s" % (file_name, file_extension, )

            data = ContentFile(decoded_file, name=complete_file_name)

        return super(SplintBase64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        """Return file extension."""
        import imghdr

        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension
