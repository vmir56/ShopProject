
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    """Модель товара для интернет-магазина"""
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)    
    name = models.CharField(
        max_length=200,
        verbose_name="Название товара",
        help_text="Введите название товара (до 200 символов)"
    )
    
    description = models.TextField(
        verbose_name="Описание",
        help_text="Подробное описание товара"
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена",
        help_text="Цена в рублях (до 99999999.99)"
    )
    
    image = models.ImageField(
        upload_to='products/',
        verbose_name="Изображение",
        help_text="Загрузите изображение товара",
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    class Meta:
        ordering = ['-created_at']  # Сортировка по дате (новые сверху)
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        """Возвращает URL для детальной страницы товара"""
        return reverse('shop:product_detail', args=[str(self.id)])
    
    def formatted_price(self):
        """Возвращает отформатированную цену с символом рубля"""
        return f"{self.price:,.2f} ₽".replace(',', ' ')

