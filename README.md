# 🎮 Discord Clone

> Полнофункциональный клон Discord с чатом в реальном времени, серверами, каналами, личными сообщениями и системой друзей.

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-4.2-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub issues](https://img.shields.io/github/issues/NIOJJN/Discord-Clone)](https://github.com/NIOJJN/Discord-Clone/issues)
[![GitHub stars](https://img.shields.io/github/stars/NIOJJN/Discord-Clone)](https://github.com/NIOJJN/Discord-Clone/stargazers)

---

## 📸 Скриншоты

> *Скриншоты будут добавлены позже*

---

## ✨ Возможности

### 🔐 Пользователи и безопасность
- Регистрация и авторизация пользователей
- Профили с аватарами и статусами
- Система друзей (запросы, принятие, отклонение)
- Безопасное хранение паролей

### 💬 Общение в реальном времени
- Чат в реальном времени через **WebSocket**
- Личные сообщения между пользователями
- Система уведомлений при упоминаниях
- Закрепление и поиск сообщений
- Редактирование и удаление сообщений

### 🏠 Серверы и каналы
- Создание серверов с категориями
- Текстовые и голосовые каналы
- Роли на сервере (владелец, админ, модератор, участник)
- Приглашения на сервер по уникальному коду

### 🎨 Интерфейс
- Тёмная тема в стиле Discord
- Адаптивный дизайн для всех устройств
- Интуитивно понятный интерфейс

---

## 🛠 Технологии

| Технология | Назначение |
|:-----------|:-----------|
| **Django 4.2** | Backend-фреймворк |
| **Django Channels** | WebSocket для real-time чата |
| **Daphne** | ASGI-сервер |
| **Redis** | Бэкенд для Channels |
| **WhiteNoise** | Раздача статических файлов |
| **Bootstrap 5** | CSS-фреймворк |
| **Font Awesome** | Иконки |
| **SQLite** | База данных (по умолчанию) |

---

## 🚀 Быстрый старт

### 📋 Требования

- Python 3.9 или выше
- Redis Server
- Git

### 📦 Установка

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/NIOJJN/Discord-Clone.git
cd Discord-Clone

# 2. Создайте виртуальное окружение
python -m venv venv

# 3. Активируйте виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 4. Установите зависимости
pip install -r requirements.txt

# 5. Настройте переменные окружения
cp .env.example .env
# Отредактируйте .env (укажите SECRET_KEY и другие параметры)

# 6. Выполните миграции
python manage.py migrate

# 7. Создайте суперпользователя (администратора)
python manage.py createsuperuser

# 8. Запустите Redis (в отдельном терминале)
redis-server

# 9. Запустите сервер разработки
daphne -b 0.0.0.0 -p 8000 discord_clone.asgi:application
