# accounts/views.py
'''
from cart.views import get_or_create_cart, get_cart_items_count
from .forms import CustomUserCreationForm  # ← эта строка должна быть

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from cart.views import get_cart_items_count, migrate_session_cart_to_db
from cart.models import Cart as DBCart
'''
from cart.views import get_cart_items_count, migrate_session_cart_to_db
from cart.models import Cart as DBCart

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from .forms import CustomUserCreationForm
from .models import CustomUser
import uuid
#?
from django.contrib.auth.decorators import login_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)

        if user:
            if not user.is_active:
                messages.error(request, 'Аккаунт не активирован. Проверьте почту для подтверждения.')
                return redirect('accounts:login')

            login(request, user)
            messages.success(request, f'С возвращением, {user.email}!')
            return redirect('/')
        else:
            messages.error(request, 'Неверный email или пароль')

    return render(request, 'accounts/login.html')

###
# accounts/views.py
import sys


def register_view(request):
    """Регистрация с отправкой письма для подтверждения"""
    if request.user.is_authenticated:
        return redirect('profile')

    print("\n" + "=" * 60, file=sys.stderr)
    print("🔐 [REGISTER] Начало регистрации", file=sys.stderr)
    print(f"   Метод запроса: {request.method}", file=sys.stderr)

    if request.method == 'POST':
        print("   📥 POST данные:", file=sys.stderr)
        for key, value in request.POST.items():
            if key != 'password1' and key != 'password2':
                print(f"      {key}: {value}", file=sys.stderr)

        form = CustomUserCreationForm(request.POST)

        print("   📝 Форма создана", file=sys.stderr)
        print(f"   Форма валидна: {form.is_valid()}", file=sys.stderr)

        if form.is_valid():
            print("   ✅ Форма валидна, создаём пользователя", file=sys.stderr)

            user = form.save(commit=False)
            user.is_active = False
            user.email_verified = False
            user.email_verification_token = uuid.uuid4()
            user.save()

            print(f"   👤 Пользователь создан: {user.email}", file=sys.stderr)
            print(f"   🔑 Токен: {user.email_verification_token}", file=sys.stderr)

            # Формируем ссылку
            verification_link = request.build_absolute_uri(
                reverse('accounts:verify_email', args=[str(user.email_verification_token)])
            )
            print(f"   🔗 Ссылка: {verification_link}", file=sys.stderr)

            # Отправляем письмо
            try:
                send_mail(
                    subject='Подтверждение регистрации',
                    message=f'''Здравствуйте!

Для подтверждения регистрации на сайте ShopProject перейдите по ссылке:
{verification_link}

Если вы не регистрировались на нашем сайте, проигнорируйте это письмо.

С уважением,
Команда ShopProject''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                print("   ✉️ Письмо отправлено успешно", file=sys.stderr)
                messages.success(request, 'Письмо с подтверждением отправлено на ваш email. Проверьте почту!')
                return redirect('accounts:login')
            except Exception as e:
                print(f"   ❌ Ошибка отправки письма: {e}", file=sys.stderr)
                user.delete()
                messages.error(request, f'Ошибка при отправке письма: {e}')
        else:
            # Выводим ошибки формы
            print("   ❌ Ошибки формы:", file=sys.stderr)
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"      {field}: {error}", file=sys.stderr)
                    messages.error(request, f'{field}: {error}')
    else:
        form = CustomUserCreationForm()
        print("   📄 GET запрос, форма создана", file=sys.stderr)

    print("=" * 60 + "\n", file=sys.stderr)

    return render(request, 'accounts/register.html', {'form': form})
###




def verify_email(request, token):
    """Подтверждение email по токену"""
    try:
        user = CustomUser.objects.get(email_verification_token=token, is_active=False)
        user.is_active = True
        user.email_verified = True
        user.save()

        messages.success(request, 'Email успешно подтверждён! Теперь вы можете войти.')
        return redirect('accounts:login')
    except CustomUser.DoesNotExist:
        messages.error(request, 'Неверный или уже использованный токен подтверждения.')
        return redirect('accounts:register')
###
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
