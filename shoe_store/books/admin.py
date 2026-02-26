# books/admin.py
from django.contrib import admin
from .models import User, Category, Manufacturer, Supplier, PickupPoint, Product, Order


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'fio', 'role', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['username', 'fio', 'email']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(PickupPoint)
class PickupPointAdmin(admin.ModelAdmin):
    list_display = ['address']
    search_fields = ['address']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['article', 'name', 'category', 'price', 'stock_quantity', 'discount']
    list_filter = ['category', 'manufacturer', 'supplier']
    search_fields = ['article', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'quantity', 'status', 'delivery_address', 'order_date', 'client']
    list_filter = ['status', 'delivery_address']
    search_fields = ['id', 'product__name', 'client__fio', 'code']
    readonly_fields = ['created_at', 'updated_at', 'code']