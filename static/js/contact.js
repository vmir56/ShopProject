// shop/static/shop/js/contact.js
document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.getElementById('contact-form');
    const submitBtn = document.getElementById('submit-btn');
    const alertDiv = document.getElementById('message-alert');
    const messageField = document.getElementById('id_message');
    const messageCounter = document.getElementById('message-counter');
    
    // Счётчик символов для сообщения
    if (messageField && messageCounter) {
        messageField.addEventListener('input', function() {
            const count = this.value.length;
            messageCounter.textContent = `Символов: ${count}/500`;
            
            if (count > 500) {
                messageCounter.classList.add('text-danger');
            } else if (count < 10) {
                messageCounter.classList.add('text-warning');
            } else {
                messageCounter.classList.remove('text-danger', 'text-warning');
            }
        });
    }
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Скрываем предыдущие ошибки
            document.querySelectorAll('.text-danger').forEach(el => {
                el.classList.add('d-none');
                el.textContent = '';
            });
            
            alertDiv.classList.add('d-none');
            alertDiv.textContent = '';
            
            // Блокируем кнопку
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Отправка...';
            
            // Получаем данные формы
            const formData = new FormData(contactForm);
            
            // Отправляем Ajax-запрос
            fetch('/contact/ajax/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Успех
                    alertDiv.classList.remove('alert-danger', 'd-none');
                    alertDiv.classList.add('alert-success');
                    alertDiv.textContent = data.message;
                    contactForm.reset();
                    
                    // Скрываем через 5 секунд
                    setTimeout(() => {
                        alertDiv.classList.add('d-none');
                    }, 5000);
                } else {
                    // Ошибки валидации
                    if (data.errors) {
                        for (let field in data.errors) {
                            const errorDiv = document.getElementById(`error-${field}`);
                            if (errorDiv) {
                                errorDiv.classList.remove('d-none');
                                errorDiv.textContent = data.errors[field][0].message;
                            }
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                alertDiv.classList.remove('alert-success', 'd-none');
                alertDiv.classList.add('alert-danger');
                alertDiv.textContent = 'Произошла ошибка при отправке. Попробуйте позже.';
            })
            .finally(() => {
                // Разблокируем кнопку
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Отправить';
            });
        });
    }
});