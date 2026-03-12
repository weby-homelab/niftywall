<p align="center">
  <a href="README_ENG.md">
    <img src="https://img.shields.io/badge/🇬🇧_English-00D4FF?style=for-the-badge&logo=readme&logoColor=white" alt="English README">
  </a>
  <a href="README.md">
    <img src="https://img.shields.io/badge/🇺🇦_Українська-FF4D00?style=for-the-badge&logo=readme&logoColor=white" alt="Українська версія">
  </a>
</p>

# 🛡️ NiftyWall v1.3.0
*Making Linux Firewalls Transparent, Smart, and Beautiful.*

**NiftyWall** (колишній NFTables Dashboard) — це легкий, безпечний і сучасний веб-дашборд для перегляду та керування конфігураціями фаєрвола `nftables` на Linux-серверах (зокрема Ubuntu 24.04).

Він працює напряму з ядром (без абстракцій типу `firewalld` чи `ufw`) і перетворює складний термінальний вивід на зручний інструмент з аналітикою в реальному часі. Ідеально підходить для серверів із Docker.

## ✨ Що нового у версії 1.3.0 (Anti-DDoS & NAT Edition)

- **🔀 Розумне керування NAT (Port Forwarding):** Повноцінна вкладка для прокидання портів (DNAT) ззовні до внутрішніх сервісів (наприклад, Docker-контейнерів). NiftyWall автоматично додає необхідні дозволи у ланцюжок `FORWARD`, гарантуючи, що трафік дійде до пункту призначення.
- **🛡️ Rule Builder з Anti-DDoS:** Модальне вікно для створення складних правил. Тепер ви можете не просто відкривати порти, але й налаштовувати жорсткі **Rate Limits** (наприклад, 30 запитів/сек) для захисту від флуду.
- **🕵️‍♂️ Інтеграція з Fail2Ban:** NiftyWall тепер читає `/var/log/fail2ban.log` та відображає причину блокування (наприклад, `Jail: sshd`) та точний час прямо напроти кожної забаненої IP-адреси на вкладці Dynamic Sets.
- **🌍 Інтелектуальна Геолокація:** Автоматичне визначення країни та міста для IP-адрес у ваших наборах (Sets).
- **📈 Живі графіки активності (Sparklines):** Візуалізація трафіку в реальному часі для кожного правила без оновлення сторінки (через Chart.js).
- **📜 Аудит-лог (Audit Log):** Повна історія всіх дій (хто, коли і яке правило створив або видалив).

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