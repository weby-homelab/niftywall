<p align="center">
  <a href="README_ENG.md">
    <img src="https://img.shields.io/badge/🇬🇧_English-00D4FF?style=for-the-badge&logo=readme&logoColor=white" alt="English README">
  </a>
  <a href="README.md">
    <img src="https://img.shields.io/badge/🇺🇦_Українська-FF4D00?style=for-the-badge&logo=readme&logoColor=white" alt="Українська версія">
  </a>
</p>

# 🛡️ NiftyWall v1.4.1
*Making Linux Firewalls Transparent, Smart, and Beautiful.*

**NiftyWall** (колишній NFTables Dashboard) — це легкий, безпечний і сучасний веб-дашборд для перегляду та керування конфігураціями фаєрвола `nftables` на Linux-серверах (зокрема Ubuntu 24.04).

Він працює напряму з ядром (без абстракцій типу `firewalld` чи `ufw`) і перетворює складний термінальний вивід на зручний інструмент з аналітикою в реальному часі. Ідеально підходить для серверів із Docker.

## ✨ Що нового у версії 1.4.1 (Smart Clone & Edit)

- **📝 Smart Clone (Редагування правил):** Тепер ви можете редагувати будь-яке існуюче правило! Кнопка "Clone" біля правила автоматично заповнює форму Rule Builder усіма параметрами старого правила. Ви можете змінити порт, IP або ліміт і в один клік створити оновлену версію.
- **🕰️ Машина часу (Auto-Snapshots):** Відчуйте себе в безпеці! Перед кожною зміною фаєрвола NiftyWall автоматично робить знімок поточної конфігурації.
- **🔀 Розумне керування NAT (Port Forwarding):** Повноцінна вкладка для прокидання портів (DNAT) ззовні до внутрішніх сервісів. NiftyWall автоматично додає необхідні дозволи у ланцюжок `FORWARD`.
- **🛡️ Rule Builder з Anti-DDoS:** Модальне вікно для створення складних правил з лімітуванням трафіку.
- **🕵️‍♂️ Інтеграція з Fail2Ban:** Відображення причин блокування (Jails) та часу прямо на вкладці Dynamic Sets.
- **🌍 Інтелектуальна Геолокація:** Автоматичне визначення країни та міста для IP-адрес.
- **📈 Живі графіки активності (Sparklines):** Візуалізація трафіку в реальному часі для кожного правила.
- **📜 Аудит-лог (Audit Log):** Повна історія всіх дій користувачів.

## 🚀 Основні можливості

- **Human-Readable Форматування:** Замість "сирого" JSON-виводу nftables ви бачите зрозумілі кольорові бейджі (`TCP Port = 80, 443`, `DNAT ➔ 172.17.0.2`).
- **Керування динамічними наборами (Dynamic Sets):** Інтерфейс для керування списками IP (наприклад, `banned4` або `allow_list`).
- **Panic Mode:** Кнопка екстреного блокування всього вхідного трафіку, крім критично важливого (SSH, Tailscale).
- **Резервне копіювання:** Створення бекапу поточної конфігурації у `/etc/nftables.conf.backup`.
- **Безпека:** Авторизація через JWT-токени, захист від Brute Force та робота виключно на localhost.

## 🛠️ Встановлення (Ubuntu 24.04)

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
# Відредагуйте .env, вкажіть ваш пароль та згенеруйте надійний SECRET_KEY (наприклад, через openssl rand -hex 32)
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
Потім запустіть: `systemctl daemon-reload && systemctl enable --now niftywall.service`

## 📋 Системні вимоги

- Ubuntu 24.04 (або інший сучасний Linux з `nftables` 1.0.9+)
- Python 3.10+
- Права `root` для виконання команд `nft`.

---
© 2026 Weby Homelab. Створено для тих, хто цінує контроль та естетику в системному адмініструванні.