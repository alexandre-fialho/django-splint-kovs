from rest_framework.authentication import BaseAuthentication


class SplintAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        """
        Method required by the DRF in order to return 401 responses for authentication failures, instead of 403.

        More details in https://www.django-rest-framework.org/api-guide/authentication/#custom-authentication.
        """
        return "Bearer: api"
