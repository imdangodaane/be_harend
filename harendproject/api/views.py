from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings

# CLIENT_ID = '2aa7763583bcd57e4dd65d4243a4289a'
# CLIENT_SECRET = '042c9f2e3ce5bcb7d92255a2400f2f69'
# CALLBACKURL = 'https://auth.expo.io/@anonymous/harend-65dd154c-89b8-42e5-8820-865690244aa5'
# SCOPE = 'read_content,write_content,read_products,write_products,read_orders,write_orders'

# Create your views here.

def DefaultView(request):
  return HttpResponse('Welcome to Harend-Server.')

def RedirectView(request):
  # print(request.GET)
  query_params = request.GET.dict()
  # print(query_params)
  try:
    query_params['shop']
  except KeyError:
    return JsonResponse({
      'status': 'redirect failed, shopName not found in request URL'
    })
  url = '''https://{shop}/admin/oauth/authorize?client_id={apikey}&scope={scope}&redirect_uri={callbackurl}&response_type=code'''
  # print('url', url)
  redirect_url = url.format(shop=query_params['shop'],
                            apikey=settings.APP_CLIENT_ID,
                            scope=settings.APP_SCOPE,
                            callbackurl=settings.APP_REDIRECT_URL)
  # print('redirect url: ', redirect_url)
  # return HttpResponse('Redirect test')
  return redirect(redirect_url)
