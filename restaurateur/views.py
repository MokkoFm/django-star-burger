from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from foodcartapp.models import Product, Restaurant, Order

from django.core.cache import cache
import requests
from geopy import distance
from operator import itemgetter
from environs import Env
env = Env()
env.read_env()


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id]
                                for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def fetch_coordinates(apikey, place):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    params = {"geocode": place, "apikey": apikey, "format": "json"}
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    places_found = response.json(
    )['response']['GeoObjectCollection']['featureMember']
    most_relevant = places_found[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def serialize_restaurants(restaurants, apikey):
    serialized_restaurants = []
    for restaurant in restaurants:
        serialized_restaurants.append(
            {
                'name': restaurant.name,
                'menu_items': [menu_item.product.name for menu_item in restaurant.menu_items.all() if menu_item.availability],
                'coords': cache.get_or_set(f'restaurant-{restaurant.id}', fetch_coordinates(apikey, restaurant.address), 60*15)
            }
        )
    return serialized_restaurants


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    apikey = env('APIKEY')
    orders = Order.objects.all()
    orders_items = []
    restaurants = Restaurant.objects.all()

    for order in orders:
        serialized_restaurants = serialize_restaurants(restaurants, apikey)
        order_items = set(
            [item.product.name for item in order.order_items.all()])
        order_coords = cache.get_or_set(
            f'order-{order.id}', fetch_coordinates(apikey, order.address), 30)
        possible_restaurants = []
        for restaurant in serialized_restaurants:
            restaurant['distance'] = round(distance.distance(
                restaurant['coords'], order_coords).km, 2)
            if order_items.issubset(restaurant['menu_items']):
                possible_restaurants.append(restaurant)

        sorted_possible_restaurants = sorted(
            possible_restaurants, key=itemgetter('distance'))

        order_info = {
            'id': order.id,
            'cart_total': order.cart_total['cart_total'],
            'firstname': order.firstname,
            'lastname': order.lastname,
            'phonenumber': order.phonenumber,
            'address': order.address,
            'status': order.get_status_display(),
            'comment': order.comment,
            'payment_method': order.get_payment_method_display(),
            'restaurants': sorted_possible_restaurants,
        }
        orders_items.append(order_info)

    return render(request, template_name='order_items.html', context={
        'order_items': orders_items,
    })
