# cart/models.py
from django.db import models
from django.conf import settings
from catalog.models import Product

class Cart(models.Model):
    """Корзина покупок в БД (для авторизованных пользователей)"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f'Корзина {self.user.email}'

    def get_total_price(self):
        """Общая стоимость корзины"""
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_items(self):
        """Количество позиций (разных товаров)"""
        return self.items.count()

    def get_items_count(self):
        """Суммарное количество товаров"""
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """Товар в корзине"""
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'
        unique_together = ('cart', 'product')

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def get_total_price(self):
        return self.product.price * self.quantity