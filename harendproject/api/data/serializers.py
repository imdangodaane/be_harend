from rest_framework import serializers
from api.authenticate.models import Login

class UpdateCodeSerializer(serializers.ModelSerializer):
  class Meta:
    model = Login
    fields = ['code']