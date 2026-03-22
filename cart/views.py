# cart/views.py
###
import json
from django.shortcuts import redirect, get_object_or_404, render
from django.http import JsonResponse
from django.contrib import messages
from .models import Cart, CartItem  # ← оба импорта
from catalog.models import Product
###

class SessionCart:
    """Класс для работы с корзиной в сессии (для анонимных пользователей)"""
    
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart
    
    def add(self, product_id, quantity=1, update_quantity=False):
        product_id = str(product_id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': None}
        
        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        
        if self.cart[product_id]['quantity'] <= 0:
            self.remove(product_id)
        else:
            if self.cart[product_id]['price'] is None:
                product = Product.objects.get(id=product_id)
                self.cart[product_id]['price'] = float(product.price)
        
        self.save()
    
    def remove(self, product_id):
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()
    
    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        
        for product in products:
            cart_item = cart[str(product.id)]
            cart_item['product'] = product
            cart_item['total_price'] = cart_item['quantity'] * float(product.price)
            yield cart_item
    
    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())
    
    def get_total_price(self):
        total = 0
        for item in self.cart.values():
            total += item['quantity'] * item.get('price', 0)
        return total
    
    def clear(self):
        self.cart = {}
        self.save()
    
    def save(self):
        self.session['cart'] = self.cart
        self.session.modified = True
    
    def get_items_count(self):
        return len(self.cart)
    
    def get_items(self):
        """Возвращает список товаров для переноса"""
        items = []
        for item in self:
            items.append({
                'product': item['product'],
                'quantity': item['quantity']
            })
        return items


def get_or_create_cart(request):
    """Получить или создать корзину для текущего пользователя/сессии"""
    if request.user.is_authenticated:
        from .models import Cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    else:
        return SessionCart(request)


def get_cart_items_count(request):
    """Возвращает количество товаров в корзине"""
    if request.user.is_authenticated:
        cart = get_or_create_cart(request)
        return cart.get_items_count() if hasattr(cart, 'get_items_count') else 0
    else:
        session_cart = SessionCart(request)
        return len(session_cart)

###

def migrate_session_cart_to_db(request, user_cart):
    """
    Перенести товары из сессионной корзины в корзину пользователя в БД
    ПРЕДВАРИТЕЛЬНО ОЧИЩАЯ СТАРУЮ ПОЛЬЗОВАТЕЛЬСКУЮ КОРЗИНУ
    """
    session_cart = SessionCart(request)

    print(f"\n🔄 [DIAGNOSTICS] Перенос корзины")
    print(f"   Товаров в сессии: {len(session_cart)}")
    print(f"   Товаров в корзине пользователя ДО: {user_cart.get_items_count()}")

    if len(session_cart) == 0:
        print("   ⏭️ Сессионная корзина пуста")
        return 0

    # ОЧИЩАЕМ старую корзину пользователя
    user_cart.items.all().delete()
    print(f"   🗑️ Старая корзина пользователя очищена")

    transferred = 0
    for item in session_cart.get_items():
        product = item['product']
        quantity = item['quantity']

        print(f"   📦 Перенос: {product.name} x {quantity}")

        CartItem.objects.create(
            cart=user_cart,
            product=product,
            quantity=quantity
        )
        transferred += 1

    # Очищаем сессионную корзину
    session_cart.clear()
    print(f"   🗑️ Сессионная корзина очищена")
    print(f"   Товаров в корзине пользователя ПОСЛЕ: {user_cart.get_items_count()}")
    print(f"✅ Перенесено товаров: {transferred}\n")

    return transferred
###



# Остальные функции (add_to_cart, remove_from_cart, etc.) остаются без изменений

#============================================
# Представления для работы с корзиной
# ============================================
def add_to_cart(request, product_id):
    """Добавить товар в корзину"""
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    if request.user.is_authenticated:
        # Авторизованный — работаем с БД
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
    else:
        # Анонимный — работаем с сессией
        session_cart = SessionCart(request)
        session_cart.add(product_id, quantity)

    return redirect('catalog')


def remove_from_cart(request, product_id):
    """Удалить товар из корзины"""
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        # Авторизованный — работаем с БД
        cart = get_or_create_cart(request)
        CartItem.objects.filter(cart=cart, product=product).delete()
    else:
        # Анонимный — работаем с сессией
        session_cart = SessionCart(request)
        session_cart.remove(product_id)

    return redirect('cart:cart_detail')


def update_cart(request, product_id):
    """Обновить количество товара"""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))

        if request.user.is_authenticated:
            # Авторизованный — работаем с БД
            cart = get_or_create_cart(request)
            cart_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
            if cart_item:
                if quantity > 0:
                    cart_item.quantity = quantity
                    cart_item.save()
                else:
                    cart_item.delete()
        else:
            # Анонимный — работаем с сессией
            session_cart = SessionCart(request)
            session_cart.add(product_id, quantity, update_quantity=True)

    return redirect('cart:cart_detail')


def clear_cart(request):
    """Очистить корзину"""
    if request.user.is_authenticated:
        # Авторизованный — работаем с БД
        cart = get_or_create_cart(request)
        cart.items.all().delete()
    else:
        # Анонимный — работаем с сессией
        session_cart = SessionCart(request)
        session_cart.clear()

    return redirect('cart:cart_detail')
# ============================================
def cart_detail(request):
    """Детальная страница корзины"""

    # 👇 ВАЖНО: если пользователь авторизован — берём корзину из БД
    if request.user.is_authenticated:
        # Для авторизованных — корзина в БД
        from .models import Cart
        cart, created = Cart.objects.get_or_create(user=request.user)

        # Получаем товары из БД
        cart_items = cart.items.all().select_related('product')
        total_price = cart.get_total_price()
        items_count = cart.get_items_count()  # количество позиций
        cart_length = len(cart_items)  # количество разных товаров

        print(f"\n🛒 [CART_DETAIL] Авторизованный пользователь")
        print(f"   Корзина ID: {cart.id}")
        print(f"   Товаров в БД: {cart.get_items_count()}")

    else:
        # Для анонимных — корзина в сессии
        session_cart = SessionCart(request)
        cart_items = list(session_cart)
        total_price = session_cart.get_total_price()
        items_count = len(session_cart)
        cart_length = len(cart_items)

        print(f"\n🛒 [CART_DETAIL] Анонимный пользователь")
        print(f"   Товаров в сессии: {items_count}")

        print(f"\n🛒 [CART_DETAIL] Детали корзины:")
        for item in cart_items:
            if request.user.is_authenticated:
                print(f"   - {item.product.name}: {item.quantity} шт")
            else:
                print(f"   - {item['product'].name}: {item['quantity']} шт")
        print(f"   Всего единиц: {items_count}")

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'items_count': items_count,
        'cart_length': cart_length,
        'is_authenticated': request.user.is_authenticated,
    }

    return render(request, 'cart/detail.html', context)
