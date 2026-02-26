# books/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from PIL import Image
import os
import uuid


class User(AbstractUser):
    ROLE_CHOICES = (
        ('guest', 'Гость'),
        ('client', 'Авторизированный клиент'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    fio = models.CharField(max_length=200, blank=True, verbose_name='ФИО')

    # Переопределяем поля для избежания конфликтов
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='books_user_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='books_user_permissions_set',
        blank=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.fio or self.username} ({self.get_role_display()})"


class Category(models.Model):
    """ Категория товара (3НФ)"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Название категории')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    """Производитель (3НФ)"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Производитель')

    class Meta:
        verbose_name = 'Производитель'
        verbose_name_plural = 'Производители'

    def __str__(self):
        return self.name


class Supplier(models.Model):
    """ Поставщик (3НФ)"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Поставщик')

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'

    def __str__(self):
        return self.name


class PickupPoint(models.Model):
    """ Пункт выдачи заказов"""
    address = models.CharField(max_length=255, unique=True, verbose_name='Адрес')

    class Meta:
        verbose_name = 'Пункт выдачи'
        verbose_name_plural = 'Пункты выдачи'

    def __str__(self):
        return self.address


class Product(models.Model):
    """ Товар - обувь"""
    article = models.CharField(max_length=20, unique=True, verbose_name='Артикул')
    name = models.CharField(max_length=200, verbose_name='Наименование')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name='Категория')
    description = models.TextField(verbose_name='Описание')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, related_name='products',
                                     verbose_name='Производитель')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products', verbose_name='Поставщик')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    unit = models.CharField(max_length=20, default='пара', verbose_name='Единица измерения')
    stock_quantity = models.IntegerField(default=0, verbose_name='На складе')
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Скидка (%)')
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name='Фото')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['name']

    def __str__(self):
        return f"{self.article} - {self.name}"

    def save(self, *args, **kwargs):
        """ Обработка изображения: 300x200 + удаление старого"""
        if self.pk:
            try:
                old = Product.objects.get(pk=self.pk)
                if old.image and old.image != self.image and os.path.isfile(old.image.path):
                    os.remove(old.image.path)
            except:
                pass

        super().save(*args, **kwargs)

        if self.image:
            try:
                img = Image.open(self.image.path)
                img.thumbnail((300, 200), Image.Resampling.LANCZOS)
                img.save(self.image.path, quality=95)
            except Exception as e:
                print(f"Ошибка обработки изображения: {e}")

    def get_final_price(self):
        """ Цена со скидкой"""
        return self.price * (1 - self.discount / 100)

    def has_orders(self):
        """ Проверка: есть ли заказы с этим товаром"""
        return self.orders.exists()


class Order(models.Model):
    """ Заказ"""
    STATUS_CHOICES = (
        ('new', 'Новый'),
        ('processing', 'В работе'),
        ('completed', 'Завершен'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders', verbose_name='Товар')
    quantity = models.IntegerField(default=1, verbose_name='Количество')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Статус')
    delivery_address = models.ForeignKey(PickupPoint, on_delete=models.CASCADE, related_name='orders',
                                         verbose_name='Пункт выдачи')
    order_date = models.DateField(verbose_name='Дата заказа')
    delivery_date = models.DateField(verbose_name='Дата доставки')
    client = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='orders',
                               verbose_name='Клиент')
    code = models.CharField(max_length=10, unique=True, verbose_name='Код получения')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-order_date']

    def __str__(self):
        return f"Заказ №{self.id} - {self.product.name}"

    def save(self, *args, **kwargs):
        """ Автогенерация кода"""
        if not self.code:
            self.code = str(uuid.uuid4().hex[:6]).upper()
        super().save(*args, **kwargs)

