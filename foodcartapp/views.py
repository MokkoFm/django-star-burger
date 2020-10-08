from django.templatetags.static import static
from django.http import JsonResponse
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product, Order, OrderProductItem
from rest_framework.serializers import ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework.renderers import JSONRenderer


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'ingridients': product.ingridients,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            },
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


class OrderProductItemSerializer(ModelSerializer):
    class Meta:
        model = OrderProductItem
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    products = OrderProductItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['products', 'firstname', 'lastname', 'phonenumber', 'address']


@api_view(['POST'])
def register_order(request):
    data = request.data
    print(data)
    serializer = OrderSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    order = Order.objects.create(
        firstname=serializer.validated_data['firstname'],
        lastname=serializer.validated_data['lastname'],
        phonenumber=serializer.validated_data['phonenumber'],
        address=serializer.validated_data['address'],
    )

    if serializer.validated_data['products'] == []:
        raise ValidationError('Expects not empty list of products')

    products = [(Product.objects.get(id=product['product']), product['quantity']) for product in data['products']]

    for product, quantity in products:
        OrderProductItem.objects.create(
            order=order,
            product=product,
            quantity=quantity
        )

    content = JSONRenderer().render(serializer.data, renderer_context={'indent':4})
    return Response(serializer.data)
