# cart/views.py
import json
from django.shortcuts import redirect, get_object_or_404, render
from django.http import JsonResponse
from django.contrib import messages
from .models import Cart as DBCart, CartItem
from catalog.models import Product


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


def migrate_session_cart_to_db(request, user_cart):
    """
    Перенести товары из сессионной корзины в корзину пользователя в БД
    Вызывается при входе пользователя
    Возвращает количество перенесённых товаров
    """
    session_cart = SessionCart(request)
    
    print(f"\n🔄 [DIAGNOSTICS] Перенос корзины")
    print(f"   Товаров в сессии: {len(session_cart)}")
    
    if len(session_cart) == 0:
        print("   ⏭️ Сессионная корзина пуста")
        return 0
    
    transferred = 0
    for item in session_cart.get_items():
        product = item['product']
        quantity = item['quantity']
        
        print(f"   📦 Перенос: {product.name} x {quantity}")
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=user_cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
            print(f"      ➕ Добавлено к существующему (стало {cart_item.quantity})")
        else:
            print(f"      ✅ Создан новый")
        
        transferred += 1
    
    # Очищаем сессионную корзину после успешного переноса
    session_cart.clear()
    print(f"   🗑️ Сессионная корзина очищена")
    print(f"✅ Перенесено товаров: {transferred}\n")
    
    return transferred


# Остальные функции (add_to_cart, remove_from_cart, etc.) остаются без изменений

#============================================
# Представления для работы с корзиной
# ============================================

def add_to_cart(request, product_id):
    """Добавить товар в корзину (через сессионную корзину)"""
    cart = SessionCart(request)
    product = get_object_or_404(Product, id=product_id)
    
    # Получаем количество из POST-запроса, если есть
    quantity = int(request.POST.get('quantity', 1))
    
    cart.add(product_id, quantity)
    
    # Если это AJAX-запрос
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_total': cart.get_total_price(),
            'cart_count': len(cart)
        })
    
    return redirect('cart:cart_detail')


def remove_from_cart(request, product_id):
    """Удалить товар из корзины"""
    cart = SessionCart(request)
    cart.remove(product_id)
    return redirect('cart:cart_detail')


def update_cart(request, product_id):
    """Обновить количество товара"""
    if request.method == 'POST':
        cart = SessionCart(request)
        quantity = int(request.POST.get('quantity', 1))
        cart.add(product_id, quantity, update_quantity=True)
    return redirect('cart:cart_detail')


def cart_detail(request):
    """Детальная страница корзины"""
    cart = SessionCart(request)
    
    context = {
        'cart': cart,
        'cart_items': list(cart),  # через __iter__
        'total_price': cart.get_total_price(),
        'items_count': len(cart),
    }
    
    return render(request, 'cart/detail.html', context)


def clear_cart(request):
    """Очистить корзину"""
    cart = SessionCart(request)
    cart.clear()
    return redirect('cart:cart_detail')

