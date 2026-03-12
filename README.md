# 🛡️ NFTables Dashboard

[English version](README_ENG.md)

Легкий, безпечний і сучасний веб-дашборд для перегляду та керування конфігураціями фаєрвола `nftables` на Linux-серверах.

Створений спеціально для системних адміністраторів, які керують `nftables` безпосередньо (без `firewalld` чи інших обгорток) і потребують зручного візуального огляду своїх правил без необхідності читати складний термінальний вивід.

## ✨ Можливості
- **Нативний JSON API:** Безпосередня взаємодія з ядром через `nft -j list ruleset` (виключає помилки парсингу тексту, 100% точність).
- **Візуалізація правил:** Зручний перегляд таблиць (Tables), ланцюжків (Chains), хуків, політик та окремих правил із підсвіткою синтаксису (accept, drop, masquerade).
- **Миттєве резервне копіювання:** Створення бекапу поточного стану фаєрвола у `/etc/nftables.conf.backup` в один клік.
- **Високий рівень безпеки:** 
  - Надійна система авторизації (JWT токени).
  - Хешування паролів за допомогою `bcrypt`.
  - Вбудований захист від брутфорс-атак (Rate Limiting).
- **Сучасний дизайн (Glassmorphism):** Інтерфейс працює на базі одного HTML-файлу, використовує Tailwind CSS (через CDN) та Vanilla JS.
- **FastAPI Backend:** Швидкий та асинхронний бекенд на базі Python.

## ⚠️ Зауваження щодо безпеки
Цей додаток потребує прав `root` для виконання команд `nft`. **КАТЕГОРИЧНО НЕ РЕКОМЕНДУЄТЬСЯ** виставляти порт цього дашборду у відкритий інтернет. 
Він розроблений для локального запуску (`127.0.0.1`) і повинен бути доступний лише через захищені VPN-тунелі (наприклад, Tailscale, WireGuard), SSH-прокидання портів або налаштований Cloudflare Tunnel.

## 🚀 Встановлення та запуск

1. **Клонування репозиторію:**
   ```bash
   git clone https://github.com/weby-homelab/nftables-dashboard.git
   cd nftables-dashboard
   ```

2. **Створення віртуального середовища та встановлення залежностей:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Налаштування облікових даних:**
   Скопіюйте приклад або створіть файл `.env` у корені проєкту:
   ```env
   ADMIN_USERNAME=your_username
   ADMIN_PASSWORD_HASH=your_bcrypt_hash
   SECRET_KEY=your_random_secret_key
   ```
   *Щоб згенерувати bcrypt-хеш для пароля, скористайтеся командою:*
   `python -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_PASSWORD', bcrypt.gensalt()).decode())"`

4. **Запуск Дашборду (повинен працювати від root для доступу до nft):**
   ```bash
   sudo venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
   ```

5. **Доступ до Дашборду:**
   Відкрийте `http://127.0.0.1:8080` у вашому браузері (або налаштуйте проксі/тунель).

## 🛠 Розгортання як Systemd сервісу (Рекомендовано)

Для безперебійної роботи у фоновому режимі створіть systemd-сервіс:

Створіть файл `/etc/systemd/system/nftables-dashboard.service`:
```ini
[Unit]
Description=NFTables Web Dashboard
After=network.target

[Service]
User=root
WorkingDirectory=/root/geminicli/weby-homelab/nftables-dashboard
ExecStart=/root/geminicli/weby-homelab/nftables-dashboard/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

Увімкніть та запустіть сервіс:
```bash
systemctl daemon-reload
systemctl enable nftables-dashboard.service
systemctl start nftables-dashboard.service
```

---
*© 2026 Weby Homelab*
