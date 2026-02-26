# books/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.db.models import Q
from .models import User, Product, Order, Category, Manufacturer, Supplier, PickupPoint
from .forms import ProductForm, OrderForm, LoginForm
from django.contrib.auth.decorators import login_required

def get_user_role(user):
    """ Определение роли пользователя"""
    if not user.is_authenticated:
        return 'guest'
    return user.role


def login_view(request):
    """ Страница входа - ПЕРВОЕ окно"""
    if request.user.is_authenticated:
        return redirect('books:product_list')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # ПРЯМОЕ СРАВНЕНИЕ ПАРОЛЯ (без хеширования)
            try:
                user = User.objects.get(username=username)
                if user.password == password:  # Простое сравнение строк
                    login(request, user)  # Создаёт сессию Django!
                    messages.success(request, f'Добро пожаловать, {user.fio or user.username}!')
                    return redirect('books:product_list')
                else:
                    messages.error(request, 'Неверный пароль')
            except User.DoesNotExist:
                messages.error(request, 'Пользователь не найден')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """ Выход на главный экран"""
    logout(request)  #  Очищает сессию
    messages.info(request, 'Вы успешно вышли из системы')
    return redirect('books:login')  #  Возврат на страницу входа


def product_list(request):
    """ Список товаров с ролями"""
    user_role = get_user_role(request.user)

    products = Product.objects.select_related('category', 'manufacturer', 'supplier').all()

    search_value = ''
    supplier_id = ''
    sort_by = 'name-asc'

    # Гость НЕ видит поиск/фильтр/сортировку
    if user_role != 'guest':
        search_value = request.GET.get('search', '')
        supplier_id = request.GET.get('supplier', '')
        sort_by = request.GET.get('sort', 'name-asc')

        if search_value:
            products = products.filter(
                Q(name__icontains=search_value) |
                Q(article__icontains=search_value) |
                Q(description__icontains=search_value) |
                Q(category__name__icontains=search_value) |
                Q(manufacturer__name__icontains=search_value) |
                Q(supplier__name__icontains=search_value)
            )

        if supplier_id:
            products = products.filter(supplier_id=supplier_id)

        if sort_by == 'stock-asc':
            products = products.order_by('stock_quantity')
        elif sort_by == 'stock-desc':
            products = products.order_by('-stock_quantity')
        elif sort_by == 'price-asc':
            products = products.order_by('price')
        elif sort_by == 'price-desc':
            products = products.order_by('-price')
        else:
            products = products.order_by('name')

    suppliers = Supplier.objects.all()

    return render(request, 'product_list.html', {
        'user_role': user_role,
        'products': products,
        'suppliers': suppliers,
        'search_value': search_value,
        'supplier_id': supplier_id,
        'sort_by': sort_by,
        'user': request.user if request.user.is_authenticated else None,
        'page_title': 'Список товаров'
    })


@login_required
def product_create(request):
    """Только администратор"""
    if request.user.role != 'admin':
        messages.error(request, 'У вас нет прав для выполнения этого действия')
        return redirect('books:product_list')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Товар успешно добавлен')
            return redirect('books:product_list')
    else:
        form = ProductForm()

    return render(request, 'product_form.html',
                  {'form': form, 'title': 'Добавить товар', 'user_role': get_user_role(request.user)})


@login_required
def product_update(request, pk):
    """Только администратор"""
    if request.user.role != 'admin':
        messages.error(request, 'У вас нет прав для выполнения этого действия')
        return redirect('books:product_list')

    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Товар успешно обновлен')
            return redirect('books:product_list')
    else:
        form = ProductForm(instance=product)

    return render(request, 'product_form.html',
                  {'form': form, 'title': 'Редактировать товар', 'user_role': get_user_role(request.user)})


@login_required
def product_delete(request, pk):
    """Только администратор + проверка заказов"""
    if request.user.role != 'admin':
        messages.error(request, 'У вас нет прав для выполнения этого действия')
        return redirect('books:product_list')

    product = get_object_or_404(Product, pk=pk)

    #  Нельзя удалить товар из заказа
    if product.has_orders():
        messages.error(request, f'Нельзя удалить "{product.name}", так как он присутствует в заказе!')
        return redirect('books:product_list')

    product.delete()
    messages.success(request, 'Товар успешно удален')
    return redirect('books:product_list')


@login_required
def order_list(request):
    """Менеджер + Администратор"""
    if request.user.role not in ['manager', 'admin']:
        messages.error(request, 'У вас нет прав для просмотра заказов')
        return redirect('books:product_list')

    user_role = get_user_role(request.user)
    orders = Order.objects.select_related('product', 'delivery_address', 'client').all()

    search_value = request.GET.get('search', '')
    status = request.GET.get('status', '')
    sort_by = request.GET.get('sort', 'address-asc')

    if search_value:
        orders = orders.filter(
            Q(id__icontains=search_value) |
            Q(product__name__icontains=search_value) |
            Q(product__article__icontains=search_value) |
            Q(client__fio__icontains=search_value) |
            Q(code__icontains=search_value)
        )

    if status:
        orders = orders.filter(status=status)

    if sort_by == 'address-asc':
        orders = orders.order_by('delivery_address__address')
    elif sort_by == 'address-desc':
        orders = orders.order_by('-delivery_address__address')
    elif sort_by == 'date-asc':
        orders = orders.order_by('order_date')
    elif sort_by == 'date-desc':
        orders = orders.order_by('-order_date')

    statuses = Order.STATUS_CHOICES
    pickup_points = PickupPoint.objects.all()

    return render(request, 'order_list.html', {
        'orders': orders,
        'statuses': statuses,
        'pickup_points': pickup_points,
        'search_value': search_value,
        'status': status,
        'sort_by': sort_by,
        'user': request.user,
        'user_role': user_role,
        'page_title': 'Список заказов'
    })


@login_required
def order_create(request):
    """Только администратор"""
    if request.user.role != 'admin':
        messages.error(request, 'У вас нет прав для выполнения этого действия')
        return redirect('books:order_list')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Заказ успешно создан')
            return redirect('books:order_list')
    else:
        form = OrderForm()

    return render(request, 'order_form.html',
                  {'form': form, 'title': 'Добавить заказ', 'user_role': get_user_role(request.user)})


@login_required
def order_delete(request, pk):
    """Только администратор"""
    if request.user.role != 'admin':
        messages.error(request, 'У вас нет прав для выполнения этого действия')
        return redirect('books:order_list')

    order = get_object_or_404(Order, pk=pk)
    order.delete()
    messages.success(request, 'Заказ успешно удален')
    return redirect('books:order_list')

