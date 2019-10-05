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
from .serializers import UpdateCodeSerializer

from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# gzip_middleware = GZipMiddleware()

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
  def wrapper(request):
    # print('Decorator Function - Request: ')
    # print(request.headers)
    # print('END \n\n\n')
    try:
      request.headers['Authorization']
      # print(token)
    except KeyError:
      return unauthorized_request('token required')
    return function(request)
  return wrapper


def authorize_token(function):
  def wrapper(request):
    token = request.headers['Authorization']
    try:
      token_hash = token.split(' ')[1]
    except IndexError:
      return unauthorized_request('expired token')
    try:
      Token.objects.get(token=token_hash)
    except Token.DoesNotExist:
      return unauthorized_request('expired token')
    return function(request)
  return wrapper


def shop_required(function):
  def wrapper(request):
    token = request.headers['Authorization']
    user_token = Token.objects.get(token=token.split(' ')[1])
    try:
      Shop.objects.get(user=user_token.user)
    except Shop.DoesNotExist:
      return unauthorized_request('Shop not exist', 402)
    return function(request)
  return wrapper


def get_tokens_from_haravan(shop):
  url = '''https://{shopname}/admin/oauth/access_token'''.format(shopname=shop.name)
  payload = {
    'client_id': settings.APP_CLIENT_ID,
    'client_secret': settings.APP_CLIENT_SECRET,
    'redirect_uri': settings.APP_REDIRECT_URL,
    'grant_type': 'authorization_code',
    'code': shop.code,
  }
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
  }
  # print('===> Url: ', url)
  # print('===> Payload: ', payload)
  # print('===> Payload: ', json.dumps(payload))
  res = requests.post(url, data=payload, headers=headers)
  if res.content:
    tokens = json.loads(res.content.decode())
    # print('Tokens: ')
    # print(tokens)
    return tokens
  # print('Response after send code: (should get access_token and refresh_token)')
  # print(res.content)


def get_total_page(shop, key='products', params=None, _id=None):
  ref = {
    'products': 'products',
    'orders': 'orders',
  }
  headers = {
    'Authorization': 'Bearer ' + shop.access_token,
    'Accept': 'application/json',
  }
  try:
    url = '''https://{shopname}/admin/{type}/count.json'''.format(shopname=shop.name, type=ref[key])
  except KeyError:
    url = '''https://{shopname}/admin/{type}/count.json'''.format(shopname=shop.name, type='products')
  res = requests.get(url, headers=headers)
  try:
    res_data = json.loads(res.content.decode())
  except json.decoder.JSONDecodeError:
    # return HttpResponse(res.content.decode())
    return {'status': 'failed to get data'}
  total_page = math.ceil(res_data['count'] / 50)
  return total_page


def request_get_data_from_haravan(shop, page=1, key='products', params=None, _id=None):
  ref = {
    'products': 'products',
    'orders': 'orders',
  }
  headers = {
    'Authorization': 'Bearer ' + shop.access_token,
    'Accept': 'application/json',
  }
  if key == 'orders':
    fields = ''
  else:
    fields = '&fields=title,images,variants,updated_at,product_type,tags'
  # fields = ''
  try:
    url = '''https://{shopname}/admin/{type}.json?page={page}{fields}'''.format(shopname=shop.name, type=ref[key], page=page, fields=fields)
  except KeyError:
    url = '''https://{shopname}/admin/{type}.json'''.format(shopname=shop.name, type='products')
  if params:
    pass
  # _id = '1021643654'
  if _id:
    url = '''https://{shopname}/admin/{type}/{id}.json'''.format(shopname=shop.name, type=ref[key], id=_id)
  # ''' REQUEST '''
  print(url)
  res = requests.get(url, headers=headers)
  # print('===> res_data: ', res.content.decode())
  try:
    res_data = json.loads(res.content.decode())
  except json.decoder.JSONDecodeError:
    # return HttpResponse(res.content.decode())
    return {'status': 'failed to get data'}
  return res_data


def process_data(data):
  for product in data['products']:
    product['total_quantity'] = 0
    for variant in product['variants']:
      product['total_quantity'] += variant['inventory_quantity']
  return data


def get_image_id(product, variant):
  for image in product['images']:
    if variant['image_id'] == image['id']:
      return image
  return {'src': 'https://theme.hstatic.net/1000401023/1000509826/14/no_image.jpg?v=1'}


def is_traded(product, orders):
  for order in orders:
    for item in order['line_items']:
      # print('ProductID = ', product['id'], ' ', 'OrderItemID = ', item['id'])
      if product['id'] == item['variant_id']:
        return order['updated_at']


def get_days_traded_from_now(last_order):
  last_order = parse(str(last_order))
  last_order = last_order.replace(tzinfo=None)
  now = datetime.now()
  # print('=====')
  # print(now - last_order)
  # print('=====')
  return str((now - last_order).days)


def process_products2(data, orders=None, params=None):
  result = []
  # PARAMS FILTER
  if params:
    # QUANTITY FILTER
    try:
      quantity_from = int(params['quantityFrom'])
      quantity_to = int(params['quantityTo'])
    except (KeyError, ValueError):
      quantity_from = None
      quantity_to = None
  else:
    quantity_from = None
    quantity_to = None
  products = data['products']
  for product in products:
    for variant in product['variants']:
      # BASIC INFORMATION
      res = {
        'id': variant['id'],
        'product_name': product['title'] + ' - ' + variant['title'],
        'product_type': product['product_type'],
        'product_title': product['title'],
        'variant_title': variant['title'],
        'quantity': variant['inventory_quantity'],
        'last_updated': variant['updated_at'],
        'price': variant['price'],
        'image': get_image_id(product, variant),
        'compare_at_price': variant['compare_at_price'],
      }
      # ORDER SORT
      if orders:
        last_order = is_traded(res, orders)
        # print(last_order)
        if last_order:
          res['last_order'] = last_order
        else:
          res['last_order'] = 'null'
        # GET DAYS FROM LAST ORDER
        if res['last_order'] == 'null':
          res['traded_from_now'] = 'null'
        else:
          res['traded_from_now'] = get_days_traded_from_now(res['last_order'])
      # VARIANT UPDATE TO DATABASE
      try:
        db_variant = Variant.objects.get(variant_id=res['id'])
      except Variant.DoesNotExist:
        db_variant = Variant(variant_id=res['id'],
                              price=res['price'],
                              base_price=res['price'],
                              promotion_percent=0,
                              is_promoting=0)
        db_variant.save()
      # PROMOTION
      # try:
      #   promote_percent = round((1 - float(res['price']) / float(res['compare_at_price'])) * 100, 2)
      # except (TypeError, ZeroDivisionError):
      #   promote_percent = 0
      # res['promote_percent'] = promote_percent
      # if res['promote_percent'] > 0:
      #   res['is_promoting'] = 1
      # else:
      #   res['is_promoting'] = 0
      if db_variant.is_promoting == True:
        res['is_promoting'] = 1
        res['promote_percent'] = db_variant.promotion_percent
      else:
        res['is_promoting'] = 0
        res['promote_percent'] = 0
        if db_variant.base_price != res['price']:
          db_variant.base_price = res['price']
          db_variant.price = res['price']
          db_variant.save()
      res['base_price'] = db_variant.base_price
      # APPEND
      if quantity_from is not None and quantity_to is not None:
        if res['quantity'] >= quantity_from and res['quantity'] <= quantity_to:
          result.append(res)
          continue
      else:
        result.append(res)
  return result


def process_orders(data):
  result = []
  orders = data['orders']
  # HANDLE LOGIC
  result = orders
  return result


@csrf_exempt
@require_http_methods(['GET'])
@token_required
@authorize_token
def get_data_view(request):
  token = request.headers['Authorization']
  token_hash = token.split(' ')[1]
  user_token = Token.objects.get(token=token_hash)
  if user_token:
    # print('Got user token = ', user_token)
    # print('User: ', user_token.user)
    try:
      shop = Shop.objects.get(user=user_token.user)
    except Shop.DoesNotExist:
      return unauthorized_request('Shop not exist', 402)
    # print('Got shop: ')
    # print(shop)
    # print(shop.access_token)
    res_data = request_get_data_from_haravan(shop)
    # print(res_data)
    # print(type(res_data))
  return JsonResponse(res_data)


@csrf_exempt
@require_http_methods(['GET'])
@token_required
@authorize_token
@shop_required
def get_orders_local(request):
  result = []
  # AUTHORIZE
  token = request.headers['Authorization']
  user_token = Token.objects.get(token=token.split(' ')[1])
  shop = Shop.objects.get(user=user_token.user)
  total_page = get_total_page(shop, key='orders')
  for i in range(1, int(total_page)+1):
    res_data = request_get_data_from_haravan(shop, i, key='orders')
    res_data = process_orders(res_data)
    result += res_data
  return result


@csrf_exempt
@require_http_methods(['GET'])
@token_required
@authorize_token
@shop_required
def get_orders(request):
  result = []
  # AUTHORIZE
  token = request.headers['Authorization']
  user_token = Token.objects.get(token=token.split(' ')[1])
  shop = Shop.objects.get(user=user_token.user)
  total_page = get_total_page(shop, key='orders')
  for i in range(1, int(total_page)+1):
    res_data = request_get_data_from_haravan(shop, i, key='orders')
    res_data = process_orders(res_data)
    result += res_data
  gzip_file_name = data_to_gzip(result)
  response = HttpResponse(open(gzip_file_name, 'rb'))
  response['Content-Encoding'] = 'gzip'
  return response


@csrf_exempt
@require_http_methods(['GET'])
@token_required
@authorize_token
@shop_required
def get_products(request):
  # result = {'products': []}
  result2 = []
  # AUTHORIZE
  token = request.headers['Authorization']
  user_token = Token.objects.get(token=token.split(' ')[1])
  shop = Shop.objects.get(user=user_token.user)
  total_page = get_total_page(shop)
  # OLD PROCESS DATA
  # for i in range(1, int(total_page)+1):
  #   res_data = request_get_data_from_haravan(shop, i)
  #   process_data(res_data)
  #   result['products'] += res_data['products']
  # result['products'].sort(key=lambda i: i['total_quantity'], reverse=True)
  # QUERY PARAMS
  query_params = request.GET.dict()
  # NEW PROCESS PRODUCTS
  orders = get_orders_local(request)
  for i in range(1, int(total_page)+1):
    res_data = request_get_data_from_haravan(shop, i)
    res_data = process_products2(res_data, orders, query_params)
    result2 += res_data
  result2.sort(key=lambda i: i['quantity'], reverse=True)
  # result2.sort(key=lambda i: i['traded_from_now'] != 'null', reverse=True)
  # PROCESS ORDERS
  # GZIP1
  # gzip_file_name = data_to_gzip(result)
  # response = HttpResponse(open(gzip_file_name, 'rb'))
  # response['Content-Encoding'] = 'gzip'
  # GZIP2
  gzip_file_name = data_to_gzip(result2)
  response = HttpResponse(open(gzip_file_name, 'rb'))
  response['Content-Encoding'] = 'gzip'
  # return JsonResponse(result)
  return response


# @csrf_exempt
# @require_http_methods(['GET'])
# @token_required
# @authorize_token
# @shop_required
def get_product_by_id(request, id):
  token = request.headers['Authorization']
  user_token = Token.objects.get(token=token.split(' ')[1])
  shop = Shop.objects.get(user=user_token.user)
  res_data = request_get_data_from_haravan(shop, _id=1043771404)
  # return res_data
  return JsonResponse(res_data)


@csrf_exempt
@require_http_methods(['POST'])
@token_required
@authorize_token
def update_code_view(request):
  # GET CODE AND SHOP NAME
  print(request.body)
  try:
    raw_data = json.loads(request.body.decode())
  except json.decoder.JSONDecodeError:
    return unauthorized_request('unable to parse params', 402)
  try:
    code = raw_data['code']
  except KeyError:
    return unauthorized_request('code required', 402)
  try:
    shop_name = raw_data['shop_name']
  except KeyError:
    return unauthorized_request('shop_name required', 402)
  # TOKEN
  token = request.headers['Authorization']
  token_hash = token.split(' ')[1]
  user_token = Token.objects.get(token=token_hash)
  # SHOP
  try:
    shop = Shop.objects.get(user=user_token.user)
    shop.name = shop_name
    shop.code = code
    shop.save()
  except Shop.DoesNotExist:
    shop = Shop(name=shop_name, user=user_token.user, code=code)
    shop.save()
  tokens = get_tokens_from_haravan(shop)
  print('Get tokens from haravans: ')
  print(tokens)
  print('\n\n\n')
  try:
    shop.access_token = tokens['access_token']
  except KeyError:
    return unauthorized_request('code expired', 402)
  try:
    shop.refresh_token = tokens['refresh_token']
  except KeyError:
    return unauthorized_request('code expired', 402)
  shop.save()
  print('access_token: ')
  print(tokens['access_token'])
  print('Saved access_token in shop: ')
  print(shop.access_token)
  print('\n\n\n\n\n')
  # print(shop.__dict__)
  return JsonResponse({'status': 'get access_token success'})


def test_query_params(request):
  print(request.GET.dict())
  query_params = request.GET.dict()
  return JsonResponse({'status': query_params})


