# accounts/views.py
from django.shortcuts import render, redirect



from django.contrib.auth.decorators import login_required
from cart.views import get_or_create_cart, get_cart_items_count
from .forms import CustomUserCreationForm  # ← эта строка должна быть


from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from cart.views import get_cart_items_count, migrate_session_cart_to_db
from cart.models import Cart as DBCart

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        
        if user:
            print(f"\n🔐 [DIAGNOSTICS] Вход пользователя: {user.email}")
            
            # Сохраняем текущую сессионную корзину ДО входа
            from cart.views import SessionCart
            session_cart_before = SessionCart(request)
            session_items_count = len(session_cart_before)
            print(f"   📦 Товаров в сессионной корзине ДО входа: {session_items_count}")
            
            # Выполняем вход
            login(request, user)
            
            # Получаем или создаём корзину пользователя в БД
            user_cart, created = DBCart.objects.get_or_create(user=user)
            print(f"   👤 Корзина пользователя: {'создана' if created else 'существовала'}")
            
            # Переносим товары из сессии в БД
            if session_items_count > 0:
                transferred = migrate_session_cart_to_db(request, user_cart)
                print(f"   ✅ Перенесено товаров: {transferred}")
            else:
                print(f"   ⏭️ Нет товаров для переноса")
            
            messages.success(request, f'С возвращением, {user.email}!')
            
            # Умный редирект
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            
            # Проверяем корзину после переноса
            if get_cart_items_count(request) > 0:
                return redirect('cart:cart_detail')
            
            return redirect('/')
        else:
            messages.error(request, 'Неверный email или пароль')
    
    return render(request, 'accounts/login.html')



def register_view(request):
    """Регистрация нового пользователя"""
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('profile')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile_view(request):
    """Личный кабинет пользователя"""
    from cart.models import Cart
    from cart.views import get_or_create_cart
    
    user_cart = get_or_create_cart(request)
    
    context = {
        'user': request.user,
        'cart': user_cart,
        'cart_items_count': user_cart.get_items_count() if user_cart else 0,
    }
    return render(request, 'accounts/profile.html', context)

def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('/')


#(в конец файла)
from django.contrib.auth import login
from .forms import CustomUserCreationForm  # создадим форму


def register_view(request):
    """Регистрация нового пользователя"""
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Автоматически входим после регистрации
            login(request, user)
            return redirect('profile')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})