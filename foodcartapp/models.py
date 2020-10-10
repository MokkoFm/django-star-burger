from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Sum


class Restaurant(models.Model):
    name = models.CharField('название', max_length=50)
    address = models.CharField('адрес', max_length=100, blank=True)
    contact_phone = models.CharField('контактный телефон', max_length=50, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'


class ProductQuerySet(models.QuerySet):
    def available(self):
        return self.distinct().filter(menu_items__availability=True)


class ProductCategory(models.Model):
    name = models.CharField('название', max_length=50)

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField('название', max_length=50)
    category = models.ForeignKey(ProductCategory, null=True, blank=True, on_delete=models.SET_NULL,
                                 verbose_name='категория', related_name='products')
    price = models.DecimalField('цена', max_digits=8, decimal_places=2)
    image = models.ImageField('картинка')
    special_status = models.BooleanField('спец.предложение', default=False, db_index=True)
    ingridients = models.CharField('ингредиенты', max_length=200, blank=True)

    objects = ProductQuerySet.as_manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='menu_items')
    availability = models.BooleanField('в продаже', default=True, db_index=True)

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]


class Order(models.Model):
    STATUS = [
        ('NO', 'Необработанный'),
        ('YES', 'Обработанный'),
    ]

    firstname = models.CharField(max_length=50, verbose_name='имя')
    lastname = models.CharField(max_length=50, verbose_name='фамилия', blank=True)
    phonenumber = models.CharField(max_length=25, verbose_name='телефон')
    address = models.CharField(max_length=100, verbose_name='фамилия')
    status = models.CharField(max_length=3, choices=STATUS, default='NO')

    def __str__(self):
        return f"{self.lastname}: {self.address}"

    @property
    def cart_total(self):
        return self.order_items.all().aggregate(cart_total=Sum('product_total'))

    class Meta:
        verbose_name = "заказ на доставку"
        verbose_name_plural = "заказы на доставку"


class OrderProductItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='продукт в заказе', related_name='order')
    quantity = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(25)], verbose_name='количество')
    product_total = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='сумма одного товара', default=0)

    def __str__(self):
        return f"{self.product}: {self.quantity}"

    def save(self, *args, **kwargs):
        self.product_total = self.product.price * self.quantity
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "товар в заказе"
        verbose_name_plural = "товары в заказе"