"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from store.views import (
    products,
    product_detail,
    register,
    login_view,
    profile,
    add_to_cart,
    cart_view,
    increase_cart,
    decrease_cart,
    remove_from_cart,
    checkout,
    orders_view,
    order_detail
)
urlpatterns = [
    path('admin/', admin.site.urls),

    path('products/', products),

    path(
        'product/<int:product_id>/',
        product_detail,
        name='product_detail'
    ),

    path('register/', register),

    path('login/', login_view),

    path('profile/', profile),

    path(
        'cart/add/<int:product_id>/',
        add_to_cart,
        name='add_to_cart'
    ),

    path(
        'cart/',
        cart_view,
        name='cart'
    ),
    path(
    'cart/increase/<int:cart_id>/',
    increase_cart,
    name='increase_cart'
),

path(
    'cart/decrease/<int:cart_id>/',
    decrease_cart,
    name='decrease_cart'
),

path(
    'cart/remove/<int:cart_id>/',
    remove_from_cart,
    name='remove_from_cart'
),
path('checkout/', checkout, name='checkout'),
path(
    'orders/',
    orders_view,
    name='orders'
),
path(
    'order/<int:order_id>/',
    order_detail,
    name='order_detail'
),
]