import json
import requests
import math
import gzip
from dateutil.parser import parse
from datetime import datetime

from rest_framework import generics

from api.authenticate.models import Login, Token, Shop
from api.data.variants.models import Variant
from api.authenticate.serializers import LoginSerializer

from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


def data_to_gzip(data):
    file_name = 'gz-warehouse/items.gz'
    with gzip.GzipFile(file_name, 'w') as fout:
        fout.write(json.dumps(data).encode('utf-8'))
    return file_name


def unauthorized_request(message, status_code=401):
  res = HttpResponse()
  res.content = json.dumps({'message': message})
  res.status_code = status_code
  return res


def token_required(function):
  def wrapper(request, *args, **kwargs):
    try:
      request.headers['Authorization']
    except KeyError:
      return unauthorized_request('token required')
    return function(request, *args, **kwargs)
  return wrapper


def authorize_token(function):
  def wrapper(request, *args, **kwargs):
    token = request.headers['Authorization']
    try:
      token_hash = token.split(' ')[1]
    except IndexError:
      return unauthorized_request('expired token')
    try:
      Token.objects.get(token=token_hash)
    except Token.DoesNotExist:
      return unauthorized_request('expired token')
    return function(request, *args, **kwargs)
  return wrapper


def shop_required(function):
  def wrapper(request, *args, **kwargs):
    token = request.headers['Authorization']
    user_token = Token.objects.get(token=token.split(' ')[1])
    try:
      Shop.objects.get(user=user_token.user)
    except Shop.DoesNotExist:
      return unauthorized_request('Shop not exist', 402)
    return function(request, *args, **kwargs)
  return wrapper


@csrf_exempt
@require_http_methods(['PUT'])
@token_required
@authorize_token
@shop_required
def update_variant(request, id):
  result = {}
  # AUTHORIZE
  token = request.headers['Authorization']
  user_token = Token.objects.get(token=token.split(' ')[1])
  shop = Shop.objects.get(user=user_token.user)
  # REQUEST
  headers = {
    'Authorization': 'Bearer ' + shop.access_token,
    'Content-Type': 'application/json',
  }
  print(headers)
  payload = {
    "variant": {
      "price": 950000,
      "compare_at_price": 1300000
    }
  }
  # print(payload)
  # print(json.dumps(payload))
  url = '''https://{shopname}/admin/variants/{id}.json'''.format(shopname=shop.name, id=id)
  # print(url)
  res = requests.put(url, json.dumps(payload), headers=headers)
  # print(res)
  try:
    res_data = json.loads(res.content.decode())
  except json.decoder.JSONDecodeError:
    # return HttpResponse(res.content.decode())
    return JsonResponse({'status': 'failed to get data'})
  result = res_data
  # GZIP
  gzip_file_name = data_to_gzip(result)
  response = HttpResponse(open(gzip_file_name, 'rb'))
  response['Content-Encoding'] = 'gzip'
  # return JsonResponse(result)
  return response


@csrf_exempt
@require_http_methods(['POST'])
@token_required
@authorize_token
@shop_required
def toggle_promoting(request, id, percent):
  # SHOULD TOGGLE PROMOTING WITH PERCENT
  try:
    variant = Variant.objects.get(variant_id=id)
  except Variant.DoesNotExist:
    return unauthorized_request('variant not found', 400)
  if variant.is_promoting:
    return unauthorized_request('variant is promoting', 400)
  else:
    # AUTHORIZE
    token = request.headers['Authorization']
    user_token = Token.objects.get(token=token.split(' ')[1])
    shop = Shop.objects.get(user=user_token.user)
    # REQUEST
    headers = {
      'Authorization': 'Bearer ' + shop.access_token,
      'Content-Type': 'application/json',
    }
    promote_price = int(variant.price * (1 - percent / 100))
    payload = {
      "variant": {
        "price": promote_price,
      }
    }
    url = '''https://{shopname}/admin/variants/{id}.json'''.format(shopname=shop.name, id=id)
    res = requests.put(url, json.dumps(payload), headers=headers)
    # print(res.status_code)
    if res.status_code == 200:
      variant.price = promote_price
      variant.is_promoting = True
      variant.promotion_percent = float(percent)
      variant.save()
    # GZIP
    gzip_file_name = data_to_gzip({'status': 'set promotion of variant success'})
    response = HttpResponse(open(gzip_file_name, 'rb'))
    response['Content-Encoding'] = 'gzip'
    return response


@csrf_exempt
@require_http_methods(['POST'])
@token_required
@authorize_token
@shop_required
def turn_off_promoting(request, id):
  # SHOULD TURN OFF PROMOTING
  try:
    variant = Variant.objects.get(variant_id=id)
  except Variant.DoesNotExist:
    return unauthorized_request('variant not found', 400)
  if not variant.is_promoting:
    return unauthorized_request('not promoting variant', 400)
  else:
    # AUTHORIZE
    token = request.headers['Authorization']
    user_token = Token.objects.get(token=token.split(' ')[1])
    shop = Shop.objects.get(user=user_token.user)
    # REQUEST
    headers = {
      'Authorization': 'Bearer ' + shop.access_token,
      'Content-Type': 'application/json',
    }
    payload = {
      "variant": {
        "price": variant.base_price,
      }
    }
    url = '''https://{shopname}/admin/variants/{id}.json'''.format(shopname=shop.name, id=id)
    res = requests.put(url, json.dumps(payload), headers=headers)
    # print(res.status_code)
    if res.status_code == 200:
      variant.price = variant.base_price
      variant.is_promoting = False
      variant_promotion_percent = 0
      variant.save()
    # GZIP
    gzip_file_name = data_to_gzip({'status': 'remove promotion of variant success'})
    response = HttpResponse(open(gzip_file_name, 'rb'))
    response['Content-Encoding'] = 'gzip'
    return response