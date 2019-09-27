import rest_framework.serializers as rest_framework_serializers
import rest_auth.registration.serializers as rest_auth_serializers

from .models import User, Author


class UserSerializer(rest_framework_serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']


class RegisterSerializer(rest_auth_serializers.RegisterSerializer):
    username = rest_auth_serializers.serializers.CharField(
        max_length=rest_auth_serializers.get_username_max_length(),
        min_length=rest_auth_serializers.allauth_settings.USERNAME_MIN_LENGTH,
        required=False,
        allow_blank=True
    )

    def validate_username(self, username):
        if username:
            username = rest_auth_serializers.get_adapter().clean_username(
                username
            )
        return username

    def save(self, request):
        return super().save(request)


class AuthorSerializer(rest_framework_serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'
