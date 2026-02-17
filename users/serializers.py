from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode


# Login Serializers
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            email=data['email'],
            password=data['password']
        )

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        data['user'] = user
        return data





# Signup Serializers
User = get_user_model()

class SignupSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        full_name = validated_data.pop('full_name')
        password = validated_data.pop('password')

        user = User.objects.create(
            email=validated_data['email'],
            first_name=full_name
        )
        user.set_password(password)
        user.save()

        return user





# Password Serializer
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordConfirmSerializer(serializers.Serializer):
    uid = serializers.IntegerField()
    password = serializers.CharField(write_only=True, min_length=6)

    def validate_uid(self, value):
        try:
            self.user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid user ID")
        return value

    def save(self, **kwargs):
        self.user.set_password(self.validated_data['password'])
        self.user.save()
        return self.user