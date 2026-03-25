# accounts/views.py
from cart.views import SessionCart, migrate_session_cart_to_db, get_cart_items_count
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
import sys
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import ProfileForm
from cart.models import Cart
'''
import logging, os
print("🔧 Файл views.py загружен!")
# Настройка логирования в файл
logging.basicConfig(
    filename='/tmp/django_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s'
)
'''

@login_required
def profile_view(request):
    """Личный кабинет пользователя"""

    # Корзина пользователя
    user_cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items_count = user_cart.get_items_count()

    if request.method == 'POST':
        # Получаем данные из формы
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')

        # Сохраняем вручную
        request.user.phone = phone
        request.user.address = address
        request.user.save()

        messages.success(request, 'Профиль успешно обновлён!')
        return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)

    context = {
        'form': form,
        'cart_items_count': cart_items_count,
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)
@login_required
def change_password(request):
    """Изменение пароля"""
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 and password1 == password2:
            request.user.set_password(password1)
            request.user.save()
            update_session_auth_hash(request, request.user)  # сохраняем сессию
            messages.success(request, 'Пароль успешно изменён!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Пароли не совпадают или пустые')

    return render(request, 'accounts/change_password.html')


@login_required
def delete_account_request(request):
    """Запрос на удаление аккаунта (отправка письма с подтверждением)"""
    if request.method == 'POST':
        # Генерируем токен для удаления
        delete_token = uuid.uuid4()
        request.user.delete_token = delete_token
        request.user.save()

        # Ссылка для подтверждения удаления
        delete_link = request.build_absolute_uri(
            reverse('accounts:delete_account_confirm', args=[str(delete_token)])
        )

        try:
            send_mail(
                subject='Подтверждение удаления аккаунта',
                message=f'''Здравствуйте, {request.user.email}!

Вы запросили удаление аккаунта в ShopProject.
Если это действительно вы, перейдите по ссылке:
{delete_link}

Если вы не запрашивали удаление, просто проигнорируйте это письмо.

С уважением,
Команда ShopProject''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=False,
            )
            messages.success(request, 'Письмо с подтверждением удаления отправлено на ваш email.')
        except Exception as e:
            messages.error(request, f'Ошибка при отправке письма: {e}')

        return redirect('accounts:profile')

    return redirect('accounts:profile')


@login_required
def delete_account_confirm(request, token):
    """Подтверждение удаления аккаунта по токену"""
    try:
        user = CustomUser.objects.get(delete_token=token, is_active=True)
        user.delete()
        messages.success(request, 'Ваш аккаунт успешно удалён.')
        return redirect('/')
    except CustomUser.DoesNotExist:
        messages.error(request, 'Неверный или уже использованный токен удаления.')
        return redirect('accounts:profile')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)

        if user:
            if not user.is_active:
                messages.error(request, 'Аккаунт не активирован. Проверьте почту.')
                return redirect('accounts:login')

            # ========== ПЕРЕНОС КОРЗИНЫ ==========
            # Сохраняем сессионную корзину ДО входа
            session_cart = SessionCart(request)
            session_items_count = len(session_cart)
            print(f"\n🛒 [LOGIN] Сессионная корзина ДО входа: {session_items_count} товаров")

            # Выполняем вход
            login(request, user)

            # Получаем корзину пользователя в БД
            user_cart, created = DBCart.objects.get_or_create(user=user)
            print(f"   👤 Корзина пользователя: {'создана' if created else 'существовала'}")

            # Переносим товары
            if session_items_count > 0:
                transferred = migrate_session_cart_to_db(request, user_cart)
                print(f"   ✅ Перенесено товаров: {transferred}")
            else:
                print(f"   ⏭️ Нет товаров для переноса")
            # ========== КОНЕЦ ПЕРЕНОСА ==========

            messages.success(request, f'С возвращением, {user.email}!')

            # Умный редирект
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)

            if get_cart_items_count(request) > 0:
                return redirect('cart:cart_detail')

            return redirect('/')
        else:
            messages.error(request, 'Неверный email или пароль')

    return render(request, 'accounts/login.html')

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

def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('/')


def password_recover(request):
    """Запрос на восстановление пароля"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email, is_active=True)
            # Генерируем токен для сброса
            reset_token = uuid.uuid4()
            user.reset_token = reset_token
            user.save()

            # Ссылка для сброса
            reset_link = request.build_absolute_uri(
                reverse('accounts:password_reset', args=[str(reset_token)])
            )

            send_mail(
                subject='Восстановление пароля',
                message=f'''Здравствуйте, {user.email}!

Вы запросили восстановление пароля на сайте ShopProject.
Для установки нового пароля перейдите по ссылке:
{reset_link}

Если вы не запрашивали восстановление пароля, проигнорируйте это письмо.

С уважением,
Команда ShopProject''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            messages.success(request, 'Инструкции по восстановлению отправлены на ваш email.')
            return redirect('accounts:login')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Пользователь с таким email не найден.')

    return render(request, 'accounts/password_recover.html')


def password_reset(request, token):
    """Установка нового пароля по токену"""
    try:
        user = CustomUser.objects.get(reset_token=token, is_active=True)
    except CustomUser.DoesNotExist:
        messages.error(request, 'Неверная или истекшая ссылка для восстановления.')
        return redirect('accounts:recover')

    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 and password1 == password2:
            user.set_password(password1)
            user.reset_token = None  # очищаем токен
            user.save()
            messages.success(request, 'Пароль успешно изменён! Теперь вы можете войти.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Пароли не совпадают')

    return render(request, 'accounts/password_reset.html', {'token': token})