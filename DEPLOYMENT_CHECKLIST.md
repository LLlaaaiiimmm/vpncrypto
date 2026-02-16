## Deployment Checklist

**Domain:** joyyfeedback.com  
**Date:** ___________  
**Deployed by:** ___________

---

## Pre-Deployment (Client Responsibilities)

### VPS Server
- [ ] VPS арендован (Ubuntu 22.04 LTS / Debian 11+)
- [ ] Минимум: 2 CPU, 2GB RAM, 20GB SSD
- [ ] IP адрес получен: ___________________
- [ ] SSH доступ работает: `ssh root@[IP]`
- [ ] Sudo права предоставлены разработчику

### Domain & DNS
- [ ] Домен joyyfeedback.com куплен
- [ ] Доступ к DNS панели получен
- [ ] DNS записи настроены:
  - [ ] A    joyyfeedback.com        → [IP сервера]
  - [ ] A    www.joyyfeedback.com    → [IP сервера]
- [ ] DNS propagation завершен (проверка: `dig joyyfeedback.com`)

### OpenAI API (Optional)
- [ ] Аккаунт создан на https://platform.openai.com
- [ ] API ключ получен: sk-proj-...
- [ ] Баланс пополнен ($5-10)
- [ ] API ключ передан разработчику (безопасно)

---

## Server Setup (Developer Responsibilities)

### 1. Initial Server Configuration
- [ ] Подключение к серверу: `ssh root@[IP]`
- [ ] Система обновлена: `apt update && apt upgrade -y`
- [ ] Утилиты установлены: `apt install -y curl git ufw nano htop`
- [ ] Скрипт запущен: `./deploy_server.sh`

### 2. Docker Installation
- [ ] Docker установлен: `docker --version`
- [ ] Docker Compose установлен: `docker compose version`
- [ ] Docker работает: `systemctl status docker`

### 3. User & Directory Setup
- [ ] Пользователь budtender создан
- [ ] Пользователь добавлен в группу docker
- [ ] Директория /opt/budtender создана
- [ ] Права доступа настроены

### 4. Firewall Configuration
- [ ] UFW включен: `ufw status`
- [ ] Порт 22 (SSH) открыт
- [ ] Порт 80 (HTTP) открыт
- [ ] Порт 443 (HTTPS) открыт
- [ ] Порт 8000 закрыт (только через Nginx)

### 5. Repository Setup
- [ ] Репозиторий склонирован в /opt/budtender
- [ ] Все файлы на месте: `ls -la`
- [ ] Git настроен (если нужны обновления)

---

## Application Deployment

### 6. Environment Configuration
- [ ] .env файл создан: `cp .env.example .env`
- [ ] SECRET_KEY сгенерирован: `python3 generate_secret_key.py`
- [ ] .env настроен:
  - [ ] ENV=production
  - [ ] DEBUG=false
  - [ ] LOG_LEVEL=INFO
  - [ ] SECRET_KEY=[64 символа]
  - [ ] OPENAI_API_KEY=[если есть]
  - [ ] CORS_ORIGINS=https://joyyfeedback.com,https://www.joyyfeedback.com
  - [ ] TRUSTED_HOSTS=joyyfeedback.com,www.joyyfeedback.com
- [ ] Права доступа: `chmod 600 .env`
- [ ] Тесты пройдены: `python3 test_environment.py`

### 7. Docker Deployment
- [ ] Контейнеры собраны: `docker compose build`
- [ ] Контейнеры запущены: `docker compose up -d`
- [ ] Статус проверен: `docker compose ps`
- [ ] Healthcheck работает (status: healthy)
- [ ] Логи проверены: `docker compose logs`
- [ ] Приложение отвечает: `curl http://localhost:8000`

---

## Web Server Configuration

### 8. Nginx Setup
- [ ] Nginx установлен: `apt install -y nginx`
- [ ] Конфигурация создана: `/etc/nginx/sites-available/joyyfeedback.com`
- [ ] Символическая ссылка создана
- [ ] Дефолтный сайт удален
- [ ] Конфигурация проверена: `nginx -t`
- [ ] Nginx перезапущен: `systemctl restart nginx`
- [ ] Сайт доступен: `curl http://joyyfeedback.com`
- [ ] Скрипт запущен: `./deploy_nginx.sh`

### 9. SSL Certificate
- [ ] Certbot установлен: `apt install -y certbot python3-certbot-nginx`
- [ ] DNS проверен: `host joyyfeedback.com`
- [ ] Сертификат получен: `certbot --nginx -d joyyfeedback.com -d www.joyyfeedback.com`
- [ ] HTTPS работает: `curl -I https://joyyfeedback.com`
- [ ] HTTP редирект работает: `curl -I http://joyyfeedback.com`
- [ ] Автообновление настроено: `certbot renew --dry-run`
- [ ] Certbot timer активен: `systemctl status certbot.timer`
- [ ] Скрипт запущен: `./deploy_ssl.sh`

---

## Database & Backups

### 10. Database Setup
- [ ] База данных создана: `ls -la data/budtender.db`
- [ ] Таблицы созданы: `python3 test_database.py`
- [ ] WAL mode включен
- [ ] Индексы созданы
- [ ] Тестовые данные загружены (seed_data.py)

### 11. Backup Configuration
- [ ] Скрипт бэкапа работает: `python3 backup_database.py`
- [ ] Cron настроен: `./setup_backup_cron.sh`
- [ ] Cron проверен: `crontab -l`
- [ ] Директория бэкапов создана: `ls -la data/backups/`
- [ ] Тестовый бэкап создан
- [ ] Логи бэкапов настроены: `tail -f logs/backup.log`

---

## Security & Final Steps

### 12. Password Changes
- [ ] Дефолтные пароли изменены: `python3 change_passwords.py`
  - [ ] admin@weeden.com
  - [ ] founder@weeden.com
  - [ ] ceo@weeden.com
- [ ] Новые пароли сохранены в безопасном месте
- [ ] Пароли переданы заказчику (безопасно)

### 13. Security Verification
- [ ] .env не в git: `git status`
- [ ] .env права 600: `ls -la .env`
- [ ] Firewall активен: `ufw status`
- [ ] Только нужные порты открыты
- [ ] SSL сертификат валиден
- [ ] HTTPS редирект работает
- [ ] Rate limiting работает (тест: 11 отправок)

---

## Testing & Verification

### 14. Functional Testing
- [ ] Главная страница открывается: https://joyyfeedback.com
- [ ] Форма отправки работает
- [ ] Загрузка фото работает (до 5MB)
- [ ] Rate limiting работает (10 отправок/24ч)
- [ ] Thank you страница показывается
- [ ] Submission ID генерируется

### 15. Admin Panel Testing
- [ ] Админ панель открывается: https://joyyfeedback.com/admin/login
- [ ] Логин работает (новые пароли)
- [ ] Inbox показывает feedback
- [ ] Фильтры работают
- [ ] Статусы меняются
- [ ] Детальный просмотр работает
- [ ] Приватные заметки сохраняются
- [ ] CSV экспорт работает
- [ ] Analytics показывает данные
- [ ] User management работает (только Admin)

### 16. AI Pipeline Testing (if OpenAI enabled)
- [ ] AI обработка запускается
- [ ] Переводы генерируются (EN, RU)
- [ ] Саммари создается
- [ ] Теги присваиваются
- [ ] Fallback работает (без API key)

### 17. Performance Testing
- [ ] Страницы загружаются быстро (<2s)
- [ ] Healthcheck проходит: `docker ps`
- [ ] Логи чистые (нет ошибок): `docker compose logs`
- [ ] База данных оптимизирована: `python3 test_database.py`
- [ ] Nginx логи чистые: `tail -f /var/log/nginx/joyyfeedback_error.log`

---

## Monitoring & Maintenance

### 18. Monitoring Setup
- [ ] Логи доступны: `docker compose logs -f`
- [ ] Nginx логи доступны: `/var/log/nginx/`
- [ ] Backup логи доступны: `logs/backup.log`
- [ ] Disk space мониторится: `df -h`
- [ ] Docker stats работает: `docker stats`

### 19. Documentation
- [ ] README.md обновлен
- [ ] Доступы документированы
- [ ] Пароли сохранены (безопасно)
- [ ] Инструкции переданы заказчику
- [ ] Контакты для поддержки предоставлены

---

## Handover to Client

### 20. Access Transfer
- [ ] SSH доступ передан заказчику
- [ ] Админ пароли переданы (безопасно)
- [ ] OpenAI API key передан (если был предоставлен)
- [ ] DNS доступ подтвержден
- [ ] Certbot email настроен на заказчика

### 21. Training & Documentation
- [ ] Инструкция по использованию админ панели
- [ ] Инструкция по обновлению приложения
- [ ] Инструкция по восстановлению из бэкапа
- [ ] Инструкция по мониторингу
- [ ] Контакты для технической поддержки

### 22. Final Verification
- [ ] Заказчик может войти в админ панель
- [ ] Заказчик может просматривать feedback
- [ ] Заказчик может экспортировать CSV
- [ ] Заказчик понимает как работает система
- [ ] Все вопросы заказчика отвечены

---

## Post-Deployment

### 23. Monitoring (First Week)
- [ ] День 1: Проверка логов
- [ ] День 2: Проверка бэкапов
- [ ] День 3: Проверка SSL
- [ ] День 7: Проверка производительности
- [ ] Проблемы решены

### 24. Maintenance Schedule
- [ ] Еженедельно: Проверка логов
- [ ] Еженедельно: Проверка disk space
- [ ] Ежемесячно: Обновление системы
- [ ] Ежемесячно: Проверка бэкапов
- [ ] Ежеквартально: Ротация SECRET_KEY (опционально)

---

## Sign-Off

### Developer
- **Name:** ___________________
- **Date:** ___________________
- **Signature:** ___________________

### Client
- **Name:** ___________________
- **Date:** ___________________
- **Signature:** ___________________

---

## Notes

_Дополнительные заметки, проблемы, или особенности развертывания:_

_______________________________________________________________

_______________________________________________________________

_______________________________________________________________

_______________________________________________________________

---

**Deployment Status:** ⬜ In Progress  ⬜ Completed  ⬜ Issues

**Production URL:** https://joyyfeedback.com

**Deployment Date:** ___________

**Next Review Date:** ___________
