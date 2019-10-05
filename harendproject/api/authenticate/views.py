import jwt
import base64
from datetime import datetime, timedelta, date
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from django.utils import timezone
from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Login, Token
from .serializers import RegisterSerializer, LoginSerializer

class RegisterView(generics.CreateAPIView):
  serializer_class = RegisterSerializer

  def post(self, request):
    try:
      req_data = request.data.copy()
      serializer = RegisterSerializer(data=req_data)
      if serializer.is_valid():
        data = dict(serializer.validated_data)
        try:
          if Login.objects.get(userid=data['userid']):
            return Response({ 'status': 'Username existed' }, status=406)
        except Login.DoesNotExist:
          try:
            if Login.objects.get(email=data['email']):
              return Response({ 'status': 'Email existed' }, status=406)
          except Login.MultipleObjectsReturned:
            return Response({ 'status': 'Email existed' }, status=406)
          except Login.DoesNotExist:
            new_user = Login(userid=data['userid'],
                            password=data['password'],
                            email=data['email'])
            new_user.save()
          return Response({ 'status': 'Success' }, status=200)   
        return Response({ 'status' : 'Wrong syntax' }, status=400)
    except Exception as e:
      # print(str(e))
      with open('~/error.log', 'a+') as f:
        f.write(str(e))


class LoginCheck(generics.CreateAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = get_object_or_404(Login, userid=serializer.validated_data['userid'])
            if user and user.password == serializer.validated_data['password']:
                create_at = timezone.now()
                expired_at = timezone.now() + timedelta(minutes=60)
                token = jwt.encode({
                    'id': user.userid,
                    'exp': str(expired_at)
                }, '42y0cvq)_2^twb2m=&#_ubvag9%@19ubm(u$55a(0(0srqa$&i', algorithm='HS256')
                try:
                    _token = Token.objects.get(user=user)
                    _token.token = token.decode('utf-8')
                    _token.create_at = create_at
                    _token.expired_at = expired_at
                except Token.DoesNotExist:
                    _token = Token(user=user, token=token.decode('utf-8'))
                _token.save()
                return Response({ 
                  'token': 'Bearer ' + token.decode('utf-8'),
                })
            return Response({'status': 'Password mismatch'}, status=401)
        return Response({ 'status' : 'Wrong format syntax. If you want to login, use two properties: userid, password.' }, status=400)