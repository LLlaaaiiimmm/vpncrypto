# Production Deployment Guide

**Date:** 2026-02-16  
**Section:** 2.4 Server Setup  
**Domain:** joyyfeedback.com

---

## Разделение ответственности

### 🔵 ЧТО НУЖНО ОТ ЗАКАЗЧИКА (Client Responsibilities)

#### 1. VPS Server
- [ ] **Арендовать VPS** (Ubuntu 22.04 LTS или Debian 11+)
  - Минимум: 2 CPU, 2GB RAM, 20GB SSD
  - Рекомендуется: 2 CPU, 4GB RAM, 40GB SSD
  - Провайдеры: DigitalOcean, Linode, Vultr, Hetzner
- [ ] **Получить IP адрес сервера**
- [ ] **Получить SSH доступ** (root или sudo user)

#### 2. Domain & DNS
- [ ] **Купить домен** joyyfeedback.com (если еще не куплен)
- [ ] **Доступ к DNS панели** (Cloudflare, Namecheap, GoDaddy и т.д.)
- [ ] **Настроить DNS записи:**
  ```
  A    joyyfeedback.com        → [IP сервера]
  A    www.joyyfeedback.com    → [IP сервера]
  ```
- [ ] **Дождаться DNS propagation** (обычно 5-30 минут)

#### 3. OpenAI API (опционально)
- [ ] **Создать аккаунт** на https://platform.openai.com
- [ ] **Получить API ключ** для AI функций
- [ ] **Пополнить баланс** ($5-10 для начала)

#### 4. Доступы для разработчика
- [ ] **SSH доступ к серверу:**
  ```bash
  ssh root@[IP сервера]
  # или
  ssh username@[IP сервера]
  ```
- [ ] **Sudo права** (если не root)

---

### 🟢 ЧТО ДЕЛАЕТ РАЗРАБОТЧИК (Developer Responsibilities)

#### 1. Подготовка сервера
- [ ] Обновление системы
- [ ] Установка Docker и Docker Compose
- [ ] Создание пользователя приложения
- [ ] Настройка firewall (ufw)
- [ ] Установка необходимых пакетов

#### 2. Развертывание приложения
- [ ] Клонирование репозитория
- [ ] Настройка .env файла
- [ ] Генерация SECRET_KEY
- [ ] Настройка прав доступа
- [ ] Запуск Docker контейнеров

#### 3. Настройка Nginx
- [ ] Установка Nginx
- [ ] Создание конфигурации для домена
- [ ] Настройка reverse proxy
- [ ] Настройка размера загружаемых файлов

#### 4. Настройка SSL/HTTPS
- [ ] Установка Certbot
- [ ] Получение SSL сертификата
- [ ] Настройка автообновления сертификата
- [ ] Проверка HTTPS

#### 5. Настройка бэкапов
- [ ] Настройка автоматических бэкапов БД
- [ ] Настройка cron jobs
- [ ] Проверка системы бэкапов

#### 6. Тестирование и передача
- [ ] Проверка всех функций
- [ ] Смена дефолтных паролей
- [ ] Передача доступов заказчику
- [ ] Инструкции по использованию

---

## Пошаговая инструкция для разработчика

### Шаг 1: Подключение к серверу

```bash
# Подключиться к серверу
ssh root@[IP_ADDRESS]

# Или с пользователем
ssh username@[IP_ADDRESS]
```

### Шаг 2: Обновление системы

```bash
# Обновить список пакетов
apt update

# Обновить установленные пакеты
apt upgrade -y

# Установить необходимые утилиты
apt install -y curl git ufw nano htop
```

### Шаг 3: Установка Docker

```bash
# Установить Docker
curl -fsSL https://get.docker.com | sh

# Добавить текущего пользователя в группу docker (если не root)
usermod -aG docker $USER

# Установить Docker Compose plugin
apt install -y docker-compose-plugin

# Проверить установку
docker --version
docker compose version
```

### Шаг 4: Создание пользователя приложения

```bash
# Создать пользователя budtender
useradd -m -s /bin/bash budtender

# Добавить в группу docker
usermod -aG docker budtender

# Создать директорию для приложения
mkdir -p /opt/budtender
chown budtender:budtender /opt/budtender
```

### Шаг 5: Настройка Firewall

```bash
# Включить UFW
ufw --force enable

# Разрешить SSH (ВАЖНО! Сделать до блокировки)
ufw allow 22/tcp

# Разрешить HTTP и HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Проверить статус
ufw status

# Порт 8000 НЕ открываем (только через Nginx)
```

### Шаг 6: Клонирование репозитория

```bash
# Переключиться на пользователя budtender
su - budtender

# Перейти в директорию
cd /opt/budtender

# Клонировать репозиторий
git clone [REPOSITORY_URL] .

# Или если репозиторий приватный:
# git clone https://username:token@github.com/username/repo.git .

# Проверить файлы
ls -la
```

### Шаг 7: Настройка окружения

```bash
# Запустить мастер настройки
python3 setup_production_env.py

# Или вручную:
cp .env.example .env
python3 generate_secret_key.py
nano .env

# Установить права доступа
chmod 600 .env

# Проверить конфигурацию
python3 test_environment.py
```

**Пример .env для продакшена:**
```bash
ENV=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=[сгенерированный ключ]
OPENAI_API_KEY=[ключ от заказчика]
RATE_LIMIT_MAX=10
CORS_ORIGINS=https://joyyfeedback.com,https://www.joyyfeedback.com
TRUSTED_HOSTS=joyyfeedback.com,www.joyyfeedback.com
```

### Шаг 8: Запуск приложения

```bash
# Собрать и запустить контейнеры
docker compose up -d --build

# Проверить статус
docker compose ps

# Проверить логи
docker compose logs -f

# Проверить healthcheck
docker ps
# Должно показать "healthy" в статусе

# Проверить доступность
curl http://localhost:8000
```

### Шаг 9: Установка и настройка Nginx

```bash
# Вернуться к root
exit

# Установить Nginx
apt install -y nginx

# Создать конфигурацию
nano /etc/nginx/sites-available/joyyfeedback.com
```

**Содержимое конфигурации:**
```nginx
server {
    listen 80;
    listen [::]:80;
    server_name joyyfeedback.com www.joyyfeedback.com;

    # Максимальный размер загружаемых файлов (6MB для запаса)
    client_max_body_size 6M;

    # Логи
    access_log /var/log/nginx/joyyfeedback_access.log;
    error_log /var/log/nginx/joyyfeedback_error.log;

    # Proxy к приложению
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Статические файлы (если нужно кэширование)
    location /static/ {
        proxy_pass http://localhost:8000/static/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Создать символическую ссылку
ln -s /etc/nginx/sites-available/joyyfeedback.com /etc/nginx/sites-enabled/

# Удалить дефолтный сайт
rm /etc/nginx/sites-enabled/default

# Проверить конфигурацию
nginx -t

# Перезапустить Nginx
systemctl restart nginx

# Проверить статус
systemctl status nginx

# Проверить доступность
curl http://joyyfeedback.com
```

### Шаг 10: Настройка SSL с Certbot

```bash
# Установить Certbot
apt install -y certbot python3-certbot-nginx

# Получить сертификат (интерактивно)
certbot --nginx -d joyyfeedback.com -d www.joyyfeedback.com

# Следовать инструкциям:
# 1. Ввести email для уведомлений
# 2. Согласиться с Terms of Service
# 3. Выбрать опцию 2 (Redirect HTTP to HTTPS)

# Проверить автообновление
certbot renew --dry-run

# Сертификат будет автоматически обновляться через systemd timer
systemctl status certbot.timer
```

### Шаг 11: Настройка автоматических бэкапов

```bash
# Переключиться на пользователя budtender
su - budtender
cd /opt/budtender

# Настроить cron для бэкапов
./setup_backup_cron.sh

# Выбрать опцию 1 (Daily at 2:00 AM)

# Проверить cron
crontab -l

# Тестовый бэкап
python3 backup_database.py

# Проверить бэкапы
ls -lh data/backups/
```

### Шаг 12: Смена дефолтных паролей

```bash
# Подключиться к контейнеру
docker compose exec bfs python

# В Python shell:
from app.database import get_db
from app.auth import get_password_hash
import sqlite3

db = sqlite3.connect("data/budtender.db")

# Сменить пароль admin
new_password = "НОВЫЙ_БЕЗОПАСНЫЙ_ПАРОЛЬ"
hashed = get_password_hash(new_password)
db.execute("UPDATE users SET password_hash = ? WHERE email = 'admin@weeden.com'", (hashed,))

# Сменить пароль founder
new_password = "НОВЫЙ_БЕЗОПАСНЫЙ_ПАРОЛЬ"
hashed = get_password_hash(new_password)
db.execute("UPDATE users SET password_hash = ? WHERE email = 'founder@weeden.com'", (hashed,))

# Сменить пароль CEO
new_password = "НОВЫЙ_БЕЗОПАСНЫЙ_ПАРОЛЬ"
hashed = get_password_hash(new_password)
db.execute("UPDATE users SET password_hash = ? WHERE email = 'ceo@weeden.com'", (hashed,))

db.commit()
db.close()
exit()
```

### Шаг 13: Финальная проверка

```bash
# Проверить все сервисы
systemctl status nginx
systemctl status docker
docker compose ps

# Проверить логи
docker compose logs --tail=50

# Проверить HTTPS
curl -I https://joyyfeedback.com

# Проверить редирект HTTP -> HTTPS
curl -I http://joyyfeedback.com

# Проверить healthcheck
docker ps

# Проверить бэкапы
ls -lh data/backups/

# Проверить cron
crontab -l
```

---

## Скрипты автоматизации

Создам скрипты для автоматизации развертывания:

