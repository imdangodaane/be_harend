from rest_framework import serializers
from .models import Login


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Login
        fields = ['userid', 'password', 'email']


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = Login
        fields = ['userid', 'password']