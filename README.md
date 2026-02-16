# 🌿 Weeden Feedback System

**Anonymous feedback collection system with AI-powered analysis**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-31%2F31-success.svg)](test_rbac_auth.py)

---

## 📋 Описание

Система сбора анонимной обратной связи для Weeden с AI-анализом на базе OpenAI GPT-4. Поддерживает многоязычность, загрузку фото, RBAC авторизацию и полную анонимность пользователей.

### ✨ Ключевые функции

- 🔒 **100% Анонимность** - не собираем имена, телефоны, email
- 🌍 **Многоязычность** - автоматический перевод на английский и русский
- 🤖 **AI Анализ** - GPT-4 анализирует тональность и генерирует саммари
- 📸 **Загрузка фото** - поддержка JPG/PNG до 5MB
- 🛡️ **RBAC** - 3 роли (admin, founder, ceo) с разными правами
- 📊 **Analytics** - графики и статистика по категориям
- 🚀 **Rate Limiting** - защита от спама (10 сообщений/день с IP)
- 🎨 **Weeden Branding** - полное соответствие брендбуку

---

## 🎨 Дизайн

### Strain Color Coding
Категории feedback используют цвета cannabis strains:

| Категория | Strain | Цвет |
|-----------|--------|------|
| Complaint | Indica | 🟡 Yellow (#F6D14E) |
| Idea | Sativa | 🔵 Blue (#B5C8EC) |
| Recommendation | Hybrid | 🟣 Purple (#B085C6) |
| Other | - | ⚪ Gray |

### Логотипы
- 3 SVG логотипа (основной, темный фон, favicon)
- Cannabis leaf дизайн
- Inter font для всех страниц

---

## 🚀 Быстрый старт

### Требования
- Python 3.11+
- OpenAI API key (опционально)

### Установка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/LLlaaaiiimmm/vpncrypto.git
cd vpncrypto

# 2. Создать виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или .venv\Scripts\activate  # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить .env
cp .env.example .env
# Отредактировать .env (добавить SECRET_KEY и OPENAI_API_KEY)

# 5. Запустить приложение
python run.py
```

Приложение будет доступно на http://localhost:8000

### Демо аккаунты

| Email | Пароль | Роль |
|-------|--------|------|
| admin@weeden.com | admin12345! | Admin |
| founder@weeden.com | founder12345 | Founder |
| ceo@weeden.com | ceo1234567! | CEO |

---

## 📁 Структура проекта

```
vpncrypto/
├── app/
│   ├── static/
│   │   ├── css/style.css           # Weeden branding styles
│   │   └── images/                 # SVG logos + favicon
│   ├── templates/
│   │   ├── public/                 # Публичная форма
│   │   ├── admin/                  # Админ панель
│   │   └── errors/                 # Error страницы
│   ├── main.py                     # FastAPI приложение
│   ├── database.py                 # SQLite + миграции
│   ├── auth.py                     # JWT + RBAC
│   ├── ai_pipeline.py              # OpenAI интеграция
│   └── config.py                   # Конфигурация
├── data/
│   ├── budtender.db                # SQLite база (auto-created)
│   └── uploads/                    # Загруженные фото
├── tests/                          # 43 автоматических теста
├── deploy_*.sh                     # Скрипты деплоя
├── docker-compose.yml              # Docker setup
└── requirements.txt                # Python зависимости
```

---

## 🧪 Тестирование

```bash
# Запустить все тесты
python test_rbac_auth.py
python test_file_validation.py
python test_ai_pipeline.py
python test_critical_bugs.py
python test_rate_limit_cleanup.py
python test_database.py
python test_environment.py

# Или через pytest
pytest
```

**Результат:** 31/31 тестов пройдено (100%)

---

## 🐳 Docker

```bash
# Запустить с Docker
docker compose up --build

# Остановить
docker compose down
```

Приложение будет доступно на http://localhost:8000

---

## 🚀 Продакшн деплой

### Автоматический деплой (Ubuntu/Debian)

```bash
# 1. Подготовка сервера
sudo ./deploy_server.sh

# 2. Деплой приложения
./deploy_app.sh

# 3. Настройка Nginx
sudo ./deploy_nginx.sh

# 4. Настройка SSL
sudo ./deploy_ssl.sh
```

### Ручной деплой

См. полную документацию:
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - полное руководство
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - чеклист из 24 пунктов
- [SERVER_SETUP.md](SERVER_SETUP.md) - настройка сервера

---

## 📊 Функции

### Публичная форма
- ✅ Анонимная отправка feedback
- ✅ 4 категории (Complaint, Idea, Recommendation, Other)
- ✅ Загрузка фото (JPG/PNG, до 5MB)
- ✅ Многоязычность (любой язык → EN + RU)
- ✅ Rate limiting (10 сообщений/день)
- ✅ Уникальный submission ID

### Админ панель
- ✅ Inbox с фильтрами и поиском
- ✅ Детальный просмотр feedback
- ✅ Изменение статуса (New → Read → In Progress → Resolved/Rejected)
- ✅ Добавление заметок
- ✅ Analytics с графиками
- ✅ CSV Export
- ✅ User Management (только admin)
- ✅ Bulk actions

### AI Pipeline
- ✅ Автоматический перевод (OpenAI GPT-4)
- ✅ Sentiment analysis
- ✅ Генерация саммари
- ✅ Fallback mode (если OpenAI недоступен)
- ✅ Retry logic (2 попытки)
- ✅ Timeout 30s

### Безопасность
- ✅ JWT токены с expiration
- ✅ RBAC (3 роли)
- ✅ SQL injection защита
- ✅ XSS защита
- ✅ MIME validation
- ✅ File signature check
- ✅ Rate limiting
- ✅ IP hashing (SHA-256)

---

## 🔐 Безопасность

### Аудиты пройдены
- ✅ Section 1.1: Dependencies & SECRET_KEY
- ✅ Section 1.2: RBAC & Auth
- ✅ Section 1.3: File Validation
- ✅ Section 1.4: AI Pipeline
- ✅ Section 1.5: Critical Bugs

См. документацию:
- [SECURITY_AUDIT.md](SECURITY_AUDIT.md)
- [RBAC_AUTH_AUDIT.md](RBAC_AUTH_AUDIT.md)
- [FILE_VALIDATION_AUDIT.md](FILE_VALIDATION_AUDIT.md)

---

## 📚 Документация

### Для разработчиков
- [CHANGELOG.md](CHANGELOG.md) - история изменений
- [DATABASE_SETUP.md](DATABASE_SETUP.md) - настройка БД
- [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) - переменные окружения
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - руководство по тестированию

### Для дизайнеров
- [BRANDING_README.md](BRANDING_README.md) - навигация по брендингу
- [WEEDEN_BRANDING_CHANGES.md](WEEDEN_BRANDING_CHANGES.md) - полная документация
- [BEFORE_AFTER_COMPARISON.md](BEFORE_AFTER_COMPARISON.md) - визуальное сравнение
- [ADVANCED_BRANDING_FEATURES.md](ADVANCED_BRANDING_FEATURES.md) - SVG + strain colors

### Для деплоя
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - полное руководство
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - чеклист
- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - продакшн настройки

---

## 🛠️ Технологии

### Backend
- **FastAPI** 0.115.6 - современный Python web framework
- **SQLite** - легковесная БД с WAL mode
- **OpenAI** 1.59.5 - GPT-4 для AI анализа
- **python-jose** 3.5.0 - JWT токены
- **python-multipart** - загрузка файлов
- **python-magic** - MIME validation

### Frontend
- **Jinja2** 3.1.6 - шаблонизатор
- **Inter Font** - Google Fonts
- **Vanilla JS** - без фреймворков
- **SVG** - масштабируемые логотипы

### DevOps
- **Docker** + Docker Compose
- **Nginx** - reverse proxy
- **Certbot** - SSL сертификаты
- **Uvicorn** - ASGI сервер

---

## 📊 Статистика проекта

| Метрика | Значение |
|---------|----------|
| Строк кода | ~16,600 |
| Файлов | 87 |
| Тестов | 43 |
| Документов | 40+ |
| SVG логотипов | 3 |
| Языков | Python, HTML, CSS, JS |
| Версия | 2.0 |

---

## 🤝 Вклад

Проект разработан для Weeden. Для вопросов и предложений создавайте Issues.

---

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE)

---

## 🎉 Благодарности

- **Weeden** - за брендбук и требования
- **OpenAI** - за GPT-4 API
- **FastAPI** - за отличный framework
- **Community** - за open source инструменты

---

## 📞 Контакты

**Проект:** Budtender Feedback System  
**Клиент:** Weeden  
**Версия:** 2.0  
**Статус:** ✅ Production Ready

---

**🌿 Cannabis Freedom 🌿**
