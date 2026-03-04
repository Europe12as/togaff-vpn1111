# 🌸 Togaff VPN — Telegram Bot + Mini App

## Что внутри
- `bot.py` — Telegram бот с командами
- `index.html` — Mini App (VPN интерфейс прямо в Telegram)
- `.github/workflows/deploy.yml` — авто-деплой на GitHub Pages

---

## Шаг 1 — Создай бота в Telegram

1. Напиши [@BotFather](https://t.me/BotFather)
2. `/newbot`
3. Имя: `Togaff VPN`
4. Username: `togaffvpn_bot` (или любой свободный)
5. Скопируй токен: `123456789:ABCdef...`

---

## Шаг 2 — Задеплой Mini App на GitHub Pages

1. Создай репозиторий на GitHub (назови `togaff-vpn`, **Public**)
2. Загрузи все файлы из этой папки
3. Зайди в репозиторий → **Settings → Pages**
4. Source: выбери **GitHub Actions**
5. Перейди во вкладку **Actions** → запусти `Deploy Mini App`
6. После деплоя получишь URL вида:
   `https://ТВОй_НИКНЕЙМ.github.io/togaff-vpn/`

---

## Шаг 3 — Настрой бота

Открой `bot.py` и замени две строки вверху:

```python
TOKEN = "СЮДА_ВСТАВЬ_ТОКЕН_ОТ_BOTFATHER"
MINI_APP_URL = "https://ТВОй_НИКНЕЙМ.github.io/togaff-vpn/"
```

---

## Шаг 4 — Зарегистрируй Mini App в BotFather

1. Напиши [@BotFather](https://t.me/BotFather)
2. `/newapp`
3. Выбери своего бота
4. Вставь URL: `https://ТВОй_НИКНЕЙМ.github.io/togaff-vpn/`
5. Готово!

---

## Шаг 5 — Запусти бота

```bash
pip install pyTelegramBotAPI requests
python bot.py
```

Или на сервере (чтобы работал 24/7):
```bash
# Установи на любой VPS/сервер
nohup python bot.py &
```

---

## Команды бота

| Команда | Действие |
|---------|---------|
| `/start` | Главное меню с кнопками |
| `/connect` | Подключиться к лучшему прокси |
| `/disconnect` | Отключиться |
| `/rotate` | Сменить IP |
| `/status` | Текущий статус и пинг |
| `/proxies` | Список живых серверов |
| `/ip` | Мой текущий IP |

---

## Кнопка Mini App

После настройки в боте появится кнопка **"🌸 Открыть VPN интерфейс"**
которая открывает полноценный UI прямо внутри Telegram!
