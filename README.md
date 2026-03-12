# 🛡️ NiftyWall v1.1.0
*Making Linux Firewalls Transparent, Smart, and Beautiful.*

**NiftyWall** (колишній NFTables Dashboard) — це легкий, безпечний і сучасний веб-дашборд для перегляду та керування конфігураціями фаєрвола `nftables` на Linux-серверах.

Він працює напряму з ядром (без абстракцій типу `firewalld` чи `ufw`) і перетворює складний термінальний вивід на зручний інструмент з аналітикою в реальному часі.

## ✨ Що нового у версії 1.1.0

- **🌍 Інтелектуальна Геолокація:** Автоматичне визначення країни та міста для IP-адрес у ваших наборах (Sets). Тепер ви точно знаєте, звідки походять атаки або підключення.
- **📈 Живі графіки активності (Sparklines):** Візуалізація трафіку в реальному часі для кожного правила. Бачте сплески активності без оновлення сторінки.
- **⚙️ Керування динамічними наборами (Dynamic Sets):** Повноцінний інтерфейс для керування списками IP (наприклад, `banned4` або `allow_list`). Додавайте та видаляйте адреси одним кліком.
- **📜 Аудит-лог (Audit Log):** Повна історія всіх дій користувачів у системі. Хто, коли і яке правило змінив — тепер усе під контролем.
- **⚡ Оптимізація продуктивності:** Перехід на асинхронне фонове оновлення даних (polling) кожні 5 секунд.

## 🚀 Основні можливості

- **Візуальний аудит:** Повний огляд таблиць, ланцюжків та правил у зручному JSON-форматі.
- **Миттєве відкриття портів:** Швидка форма для додавання правил дозволу TCP/UDP трафіку.
- **Panic Mode:** Кнопка екстреного блокування всього вхідного трафіку, крім критично важливого (SSH, Tailscale).
- **Резервне копіювання:** Створення бекапу поточної конфігурації у `/etc/nftables.conf.backup`.
- **Безпека:** Авторизація через JWT-токени, захист від Brute Force та робота виключно на localhost (рекомендовано через SSH тунель або Cloudflare Tunnel).

## 🛠️ Встановлення

```bash
# 1. Клонування репозиторію
git clone https://github.com/weby-homelab/niftywall.git
cd niftywall

# 2. Створення віртуального середовища
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Налаштування середовища
cp .env.example .env
# Відредагуйте .env, вкажіть ваш пароль та згенеруйте надійний SECRET_KEY
```

### Запуск як Systemd-сервіс (Рекомендовано)
Створіть файл `/etc/systemd/system/niftywall.service`:

```ini
[Unit]
Description=NiftyWall Firewall Dashboard
After=network.target nftables.service

[Service]
User=root
Group=root
WorkingDirectory=/opt/niftywall
Environment="PATH=/opt/niftywall/venv/bin"
ExecStart=/opt/niftywall/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```
Потім запустіть: `systemctl enable --now niftywall.service`

## 📋 Системні вимоги

- Python 3.10+
- `nftables` (з правами root для виконання команд)
- `uvicorn`, `FastAPI`, `PyJWT`, `bcrypt`

---
© 2026 Weby Homelab. Створено для тих, хто цінує контроль та естетику в системному адмініструванні.
