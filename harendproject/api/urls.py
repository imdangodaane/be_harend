from django.urls import path
from . import views

from .authenticate import views as authen_views
from .data import views as data_views
from .data.variants import views as var_views

urlpatterns = [
    path('', views.DefaultView),
    path('redirect', views.RedirectView),

    path('updatecode', data_views.update_code_view),
    path('getdata', data_views.get_data_view),
    path('getdata/products', data_views.get_products),
    path('getdata/products/<int:id>', data_views.get_product_by_id),
    path('getdata/orders', data_views.get_orders),

    path('data/variants/<int:id>', var_views.update_variant),

    path('data/variants/<int:id>/<int:percent>', var_views.toggle_promoting),
    path('data/variants/offpromote/<int:id>', var_views.turn_off_promoting),

    path('register', authen_views.RegisterView.as_view()),
    path('login', authen_views.LoginCheck.as_view()),
]
