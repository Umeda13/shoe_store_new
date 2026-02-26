# books/management/commands/import_data.py
from django.core.management.base import BaseCommand
import pandas as pd
from django.contrib.auth.hashers import make_password
from books.models import User, Category, Manufacturer, Supplier, PickupPoint, Product, Order
from datetime import datetime
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Импорт данных из Excel файлов'

    def handle(self, *args, **kwargs):
        self.stdout.write('Начало импорта данных...')

        # Получаем базовую директорию проекта
        base_dir = settings.BASE_DIR

        # Импорт пользователей
        self.import_users(base_dir)

        # Импорт справочников
        self.import_suppliers(base_dir)
        self.import_manufacturers(base_dir)
        self.import_categories(base_dir)
        self.import_pickup_points(base_dir)

        # Импорт товаров
        self.import_products(base_dir)

        # Импорт заказов
        self.import_orders(base_dir)

        self.stdout.write(self.style.SUCCESS('Импорт завершен успешно!'))

    def import_users(self, base_dir):
        self.stdout.write('Импорт пользователей...')
        try:
            file_path = os.path.join(base_dir, 'import', 'user_import.xlsx')
            df = pd.read_excel(file_path)

            role_map = {
                'Администратор': 'admin',
                'Менеджер': 'manager',
                'Авторизированный клиент': 'client'
            }

            for _, row in df.iterrows():
                user, created = User.objects.update_or_create(
                    username=row['Логин'],
                    defaults={
                        'password': str(row['Пароль']),
                        'fio': row['ФИО'],
                        'role': role_map.get(row['Роль сотрудника'], 'client'),
                        'is_active': True
                    }
                )
                if created:
                    self.stdout.write(f'  Создан: {user.fio}')
                else:
                    self.stdout.write(f'  Обновлён: {user.fio}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  Ошибка импорта пользователей: {e}'))

    def import_suppliers(self, base_dir):
        self.stdout.write('Импорт поставщиков...')
        try:
            file_path = os.path.join(base_dir, 'import', 'Tovar.xlsx')
            df = pd.read_excel(file_path)
            suppliers = df['Поставщик'].unique()

            for supplier_name in suppliers:
                if pd.notna(supplier_name):
                    Supplier.objects.get_or_create(name=str(supplier_name))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  Ошибка импорта поставщиков: {e}'))

    def import_manufacturers(self, base_dir):
        self.stdout.write('Импорт производителей...')
        try:
            file_path = os.path.join(base_dir, 'import', 'Tovar.xlsx')
            df = pd.read_excel(file_path)
            manufacturers = df['Производитель'].unique()

            for mfg_name in manufacturers:
                if pd.notna(mfg_name):
                    Manufacturer.objects.get_or_create(name=str(mfg_name))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  Ошибка импорта производителей: {e}'))

    def import_categories(self, base_dir):
        self.stdout.write('Импорт категорий...')
        try:
            file_path = os.path.join(base_dir, 'import', 'Tovar.xlsx')
            df = pd.read_excel(file_path)
            categories = df['Категория товара'].unique()

            for cat_name in categories:
                if pd.notna(cat_name):
                    Category.objects.get_or_create(name=str(cat_name))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  Ошибка импорта категорий: {e}'))

    def import_pickup_points(self, base_dir):
        self.stdout.write('Импорт пунктов выдачи...')
        try:
            file_path = os.path.join(base_dir, 'import', 'Пункты выдачи_import.xlsx')
            df = pd.read_excel(file_path, header=None)

            for _, row in df.iterrows():
                if pd.notna(row[0]):
                    PickupPoint.objects.get_or_create(address=str(row[0]))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  Ошибка импорта пунктов выдачи: {e}'))

    def import_products(self, base_dir):
        self.stdout.write('Импорт товаров...')
        try:
            file_path = os.path.join(base_dir, 'import', 'Tovar.xlsx')
            df = pd.read_excel(file_path)

            for _, row in df.iterrows():
                category, _ = Category.objects.get_or_create(name=str(row['Категория товара']))
                manufacturer, _ = Manufacturer.objects.get_or_create(name=str(row['Производитель']))
                supplier, _ = Supplier.objects.get_or_create(name=str(row['Поставщик']))

                image_path = None
                if pd.notna(row['Фото']) and row['Фото']:
                    image_filename = str(row['Фото']).strip()
                    # Полный путь к файлу
                    full_path = os.path.join(base_dir, 'media', 'products', image_filename)

                    if os.path.exists(full_path):
                        image_path = f'products/{image_filename}'
                        self.stdout.write(self.style.SUCCESS(f'Фото найдено: {image_filename}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Фото НЕ найдено: {image_filename}'))
                        image_path = None

                Product.objects.update_or_create(
                    article=str(row['Артикул']),
                    defaults={
                        'name': str(row['Наименование товара']),
                        'category': category,
                        'description': str(row['Описание товара']),
                        'manufacturer': manufacturer,
                        'supplier': supplier,
                        'price': float(row['Цена']),
                        'unit': str(row['Единица измерения']),
                        'stock_quantity': int(row['Кол-во на складе']),
                        'discount': float(row['Действующая скидка']),
                        'image': image_path
                    }
                )
                self.stdout.write(f'  Товар: {row["Артикул"]} - {row["Наименование товара"]}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  Ошибка импорта товаров: {e}'))

    def import_orders(self, base_dir):
        self.stdout.write('Импорт заказов...')
        try:
            file_path = os.path.join(base_dir, 'import', 'Заказ_import.xlsx')
            df = pd.read_excel(file_path)

            status_map = {
                'Новый': 'new',
                'В работе': 'processing',
                'Завершен': 'completed'
            }

            for _, row in df.iterrows():
                try:
                    # Парсинг артикулов (формат: "А112Т4, 2, F635R4, 2")
                    articles = str(row['Артикул заказа']).split(',')

                    for i in range(0, len(articles), 2):
                        if i + 1 < len(articles):
                            article = articles[i].strip()
                            quantity = int(articles[i + 1].strip())

                            product = Product.objects.filter(article=article).first()
                            if product:
                                client = User.objects.filter(fio=str(row['ФИО авторизированного клиента'])).first()
                                pickup = PickupPoint.objects.filter(
                                    address__contains=str(row['Адрес пункта выдачи'])
                                ).first()

                                if pickup:
                                    Order.objects.get_or_create(
                                        code=str(row['Код для получения']),
                                        defaults={
                                            'product': product,
                                            'quantity': quantity,
                                            'status': status_map.get(str(row['Статус заказа']), 'new'),
                                            'delivery_address': pickup,
                                            'order_date': self.parse_date(row['Дата заказа']),
                                            'delivery_date': self.parse_date(row['Дата доставки']),
                                            'client': client
                                        }
                                    )
                                    self.stdout.write(f'  Заказ: {row["Код для получения"]}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Ошибка заказа: {e}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  Ошибка импорта заказов: {e}'))

    def parse_date(self, date_value):
        """Парсинг даты из разных форматов"""
        if pd.isna(date_value):
            return datetime.now().date()

        try:
            return pd.to_datetime(date_value).date()
        except:
            return datetime.now().date()

