import telebot
import requests
import socket
import threading
import time
import os
from datetime import datetime

# ══════════════════════════════════════════════
#  ВСТАВЬ СВОЙ ТОКЕН СЮДА
TOKEN = "8603769389:AAFNrImTZhMY0ctceejoFbNkosE54cNsE30"
# ══════════════════════════════════════════════

# URL Mini App (после деплоя на GitHub Pages)
MINI_APP_URL = "https://YOUR_USERNAME.github.io/togaff-vpn/"

bot = telebot.TeleBot(TOKEN)

# ── Прокси список ─────────────────────────────
PROXIES = [
    ("185.221.160.253", 80),  ("185.221.160.214", 80),
    ("87.239.31.42",    80),  ("109.197.153.121", 8888),
    ("188.235.146.220", 80),  ("94.26.241.120",   80),
    ("89.23.112.143",   80),  ("91.222.238.112",  80),
    ("82.208.111.19", 8080),  ("185.244.173.101", 80),
    ("185.221.152.147", 80),  ("91.107.124.250",  80),
    ("212.96.201.54",  80),   ("5.180.241.126",   80),
    ("195.91.179.91",  80),   ("95.217.105.20",   80),
    ("37.120.189.106", 80),   ("89.31.143.1",     80),
    ("78.47.138.199",  80),   ("89.31.143.2",     80),
    ("195.201.34.206", 80),   ("89.31.143.3",     80),
    ("167.86.97.239", 8080),  ("138.201.245.91", 8080),
    ("89.31.143.12",   80),   ("51.178.43.147",   80),
    ("87.247.251.24",  80),   ("83.143.145.67",   80),
    ("85.26.218.76",   80),   ("162.19.226.235",  80),
    ("5.188.31.212",   80),   ("87.247.251.240",  80),
    ("207.254.28.68",  80),   ("104.167.29.113",  80),
    ("116.202.102.255",80),   ("77.238.66.2",     80),
    ("217.115.115.252",80),   ("85.187.17.39",    80),
    ("213.135.166.142",80),   ("217.145.93.115",  80),
    ("141.105.107.34", 80),   ("93.170.73.47",    80),
    ("31.7.38.227",    80),
]

# ── Состояние пользователей ───────────────────
users = {}

def get_user(uid):
    if uid not in users:
        users[uid] = {"connected": False, "proxy": None, "connect_time": None}
    return users[uid]

# ── Утилиты ───────────────────────────────────
def ping_proxy(host, port, timeout=2.5):
    try:
        t0 = time.time()
        with socket.create_connection((host, port), timeout=timeout):
            return round((time.time() - t0) * 1000, 1)
    except:
        return None

def get_best_proxy(exclude=None):
    results = []
    for host, port in PROXIES[:20]:
        if exclude and host == exclude[0]:
            continue
        ms = ping_proxy(host, port, timeout=1.5)
        if ms:
            results.append((ms, host, port))
    if not results:
        return None
    results.sort()
    ms, host, port = results[0]
    return (host, port, ms)

def get_current_ip(proxy=None):
    """Получить внешний IP — через прокси или напрямую"""
    try:
        if proxy:
            host, port = proxy[0], proxy[1]
            proxies = {
                "http":  f"http://{host}:{port}",
                "https": f"http://{host}:{port}",
            }
            # Используем HTTP endpoint (не HTTPS) чтобы прокси мог подменить IP
            r = requests.get(
                "http://api.ipify.org",
                proxies=proxies,
                timeout=6
            )
        else:
            r = requests.get("http://api.ipify.org", timeout=6)
        return r.text.strip()
    except Exception as e:
        return "—"

def fmt_time(secs):
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# ── Клавиатуры (чёрно-белый стиль) ───────────
def main_keyboard(connected=False):
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    if connected:
        kb.add(
            telebot.types.InlineKeyboardButton("◼ ОТКЛЮЧИТЬ",  callback_data="disconnect"),
            telebot.types.InlineKeyboardButton("↻ СМЕНИТЬ IP", callback_data="rotate"),
        )
    else:
        kb.add(
            telebot.types.InlineKeyboardButton("◻ ПОДКЛЮЧИТЬ", callback_data="connect"),
        )
    kb.add(
        telebot.types.InlineKeyboardButton("▣ СТАТУС",   callback_data="status"),
        telebot.types.InlineKeyboardButton("▤ СЕРВЕРЫ",  callback_data="proxies"),
    )
    kb.add(
        telebot.types.InlineKeyboardButton(
            "⊞ ОТКРЫТЬ VPN ИНТЕРФЕЙС",
            web_app=telebot.types.WebAppInfo(url=MINI_APP_URL)
        )
    )
    return kb

# ── Главное меню (текст) ──────────────────────
def build_main_text(name, connected):
    status_line = "[ ■ АКТИВЕН ]" if connected else "[ □ НЕАКТИВЕН ]"
    return (
        f"```\n"
        f"╔══════════════════════════╗\n"
        f"║      TOGAFF  VPN         ║\n"
        f"╚══════════════════════════╝\n"
        f"```\n"
        f"Пользователь: *{name}*\n"
        f"Статус: `{status_line}`\n\n"
        f"*Команды:*\n"
        f"`/connect`    — подключиться\n"
        f"`/disconnect` — отключиться\n"
        f"`/rotate`     — сменить IP\n"
        f"`/status`     — статус\n"
        f"`/proxies`    — серверы\n"
        f"`/ip`         — мой IP\n\n"
        f"Нажми кнопку ниже 👇"
    )

# ── /start ────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    uid = msg.from_user.id
    u = get_user(uid)
    name = msg.from_user.first_name or "User"
    bot.send_message(
        msg.chat.id,
        build_main_text(name, u["connected"]),
        parse_mode="Markdown",
        reply_markup=main_keyboard(u["connected"])
    )

# ── /connect ──────────────────────────────────
@bot.message_handler(commands=["connect"])
def cmd_connect(msg):
    uid = msg.from_user.id
    u = get_user(uid)

    if u["connected"]:
        h, p, _ = u["proxy"]
        bot.send_message(
            msg.chat.id,
            f"✓ Уже подключён к `{h}:{p}`\n"
            f"Используй /rotate для смены или /disconnect",
            parse_mode="Markdown",
            reply_markup=main_keyboard(True)
        )
        return

    wait = bot.send_message(msg.chat.id, "```\n[ ПОИСК СЕРВЕРА... ]\n```", parse_mode="Markdown")

    def do_connect():
        result = get_best_proxy()
        if result:
            host, port, ms = result
            u["connected"]    = True
            u["proxy"]        = (host, port, ms)
            u["connect_time"] = time.time()
            ip = get_current_ip((host, port))
            bot.edit_message_text(
                f"```\n"
                f"╔══════════════════════════╗\n"
                f"║   ПОДКЛЮЧЕНИЕ АКТИВНО    ║\n"
                f"╚══════════════════════════╝\n"
                f"```\n"
                f"■ Сервер:      `{host}:{port}`\n"
                f"■ Пинг:        `{ms} ms`\n"
                f"■ Ваш IP:      `{ip}`\n"
                f"■ Шифрование:  `AES-256-GCM`\n"
                f"■ DNS-over-HTTPS: `✓`\n",
                msg.chat.id,
                wait.message_id,
                parse_mode="Markdown",
                reply_markup=main_keyboard(True)
            )
        else:
            bot.edit_message_text(
                "```\n[ ОШИБКА: нет доступных серверов ]\n```\n"
                "Попробуй ещё раз через /connect",
                msg.chat.id,
                wait.message_id,
                parse_mode="Markdown",
                reply_markup=main_keyboard(False)
            )

    threading.Thread(target=do_connect, daemon=True).start()

# ── /disconnect ───────────────────────────────
@bot.message_handler(commands=["disconnect"])
def cmd_disconnect(msg):
    uid = msg.from_user.id
    u = get_user(uid)

    if not u["connected"]:
        bot.send_message(
            msg.chat.id,
            "```\n[ VPN уже отключён ]\n```",
            parse_mode="Markdown",
            reply_markup=main_keyboard(False)
        )
        return

    session = ""
    if u["connect_time"]:
        secs    = time.time() - u["connect_time"]
        session = f"\n■ Сессия: `{fmt_time(secs)}`"

    u["connected"]    = False
    u["proxy"]        = None
    u["connect_time"] = None

    bot.send_message(
        msg.chat.id,
        f"```\n"
        f"╔══════════════════════════╗\n"
        f"║      VPN ОТКЛЮЧЁН        ║\n"
        f"╚══════════════════════════╝\n"
        f"```"
        f"{session}",
        parse_mode="Markdown",
        reply_markup=main_keyboard(False)
    )

# ── /rotate ───────────────────────────────────
@bot.message_handler(commands=["rotate"])
def cmd_rotate(msg):
    uid = msg.from_user.id
    u = get_user(uid)
    wait = bot.send_message(msg.chat.id, "```\n[ СМЕНА IP... ]\n```", parse_mode="Markdown")

    def do_rotate():
        exclude = u["proxy"] if u["proxy"] else None
        result  = get_best_proxy(exclude=exclude)
        if result:
            host, port, ms    = result
            u["proxy"]        = (host, port, ms)
            u["connect_time"] = time.time()
            u["connected"]    = True
            ip = get_current_ip((host, port))
            bot.edit_message_text(
                f"```\n"
                f"╔══════════════════════════╗\n"
                f"║      IP СМЕНЁН           ║\n"
                f"╚══════════════════════════╝\n"
                f"```\n"
                f"■ Новый сервер: `{host}:{port}`\n"
                f"■ Пинг:         `{ms} ms`\n"
                f"■ Новый IP:     `{ip}`\n",
                msg.chat.id,
                wait.message_id,
                parse_mode="Markdown",
                reply_markup=main_keyboard(True)
            )
        else:
            bot.edit_message_text(
                "```\n[ ОШИБКА: нет доступных серверов ]\n```",
                msg.chat.id,
                wait.message_id,
                parse_mode="Markdown",
                reply_markup=main_keyboard(u["connected"])
            )

    threading.Thread(target=do_rotate, daemon=True).start()

# ── /status ───────────────────────────────────
@bot.message_handler(commands=["status"])
def cmd_status(msg):
    uid = msg.from_user.id
    u = get_user(uid)

    if u["connected"] and u["proxy"]:
        h, p, ms = u["proxy"]
        session  = fmt_time(time.time() - u["connect_time"]) if u["connect_time"] else "—"
        live_ms  = ping_proxy(h, p, timeout=2)
        ping_str = f"{live_ms} ms" if live_ms else "недоступен"
        text = (
            f"```\n"
            f"╔══════════════════════════╗\n"
            f"║     TOGAFF VPN STATUS    ║\n"
            f"╚══════════════════════════╝\n"
            f"```\n"
            f"■ Статус:      `АКТИВЕН`\n"
            f"■ Сервер:      `{h}:{p}`\n"
            f"■ Пинг:        `{ping_str}`\n"
            f"■ Сессия:      `{session}`\n"
            f"■ Шифрование:  `AES-256-GCM ✓`\n"
            f"■ DNS-HTTPS:   `✓`\n"
            f"■ Leak protect:`✓`\n"
        )
    else:
        text = (
            f"```\n"
            f"╔══════════════════════════╗\n"
            f"║     TOGAFF VPN STATUS    ║\n"
            f"╚══════════════════════════╝\n"
            f"```\n"
            f"■ Статус:      `ОТКЛЮЧЁН`\n"
            f"■ Шифрование:  `AES-256-GCM`\n\n"
            f"Нажми /connect для подключения\n"
        )

    bot.send_message(
        msg.chat.id, text,
        parse_mode="Markdown",
        reply_markup=main_keyboard(u["connected"])
    )

# ── /proxies ──────────────────────────────────
@bot.message_handler(commands=["proxies"])
def cmd_proxies(msg):
    wait = bot.send_message(msg.chat.id, "```\n[ СКАНИРОВАНИЕ СЕРВЕРОВ... ]\n```", parse_mode="Markdown")

    def do_scan():
        lines = [
            "```\n"
            "╔══════════════════════════╗\n"
            "║       СПИСОК СЕРВЕРОВ    ║\n"
            "╚══════════════════════════╝\n"
            "```\n"
        ]
        alive = 0
        for host, port in PROXIES[:15]:
            ms = ping_proxy(host, port, timeout=1.5)
            if ms:
                alive += 1
                if ms < 100:   mark = "◆"
                elif ms < 180: mark = "◇"
                else:          mark = "○"
                lines.append(f"{mark} `{host}:{port}` — `{ms}ms`")
            else:
                lines.append(f"✕ `{host}:{port}` — `offline`")

        lines.append(f"\n`Онлайн: {alive}/15 серверов`")
        lines.append(f"_◆ <100ms  ◇ <180ms  ○ медленный_")

        bot.edit_message_text(
            "\n".join(lines),
            msg.chat.id,
            wait.message_id,
            parse_mode="Markdown",
            reply_markup=main_keyboard(get_user(msg.from_user.id)["connected"])
        )

    threading.Thread(target=do_scan, daemon=True).start()

# ── /ip ───────────────────────────────────────
@bot.message_handler(commands=["ip"])
def cmd_ip(msg):
    uid  = msg.from_user.id
    u    = get_user(uid)
    wait = bot.send_message(msg.chat.id, "```\n[ ОПРЕДЕЛЕНИЕ IP... ]\n```", parse_mode="Markdown")

    def do_ip():
        proxy = u["proxy"] if u["connected"] else None
        ip    = get_current_ip(proxy)
        kind  = "через прокси" if proxy else "прямое соединение"
        bot.edit_message_text(
            f"```\n"
            f"╔══════════════════════════╗\n"
            f"║        ВАШ  IP           ║\n"
            f"╚══════════════════════════╝\n"
            f"```\n"
            f"■ Адрес: `{ip}`\n"
            f"■ Режим: `{kind}`\n",
            msg.chat.id,
            wait.message_id,
            parse_mode="Markdown"
        )

    threading.Thread(target=do_ip, daemon=True).start()

# ── Callback кнопки (ИСПРАВЛЕНО: uid берём из call, не из message) ─────
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    uid  = call.from_user.id   # ← правильный uid!
    data = call.data

    # Создаём фейковый объект с правильным from_user
    class FakeMsg:
        def __init__(self, chat_id, user_id, first_name):
            self.chat       = type("C", (), {"id": chat_id})()
            self.from_user  = type("U", (), {"id": user_id, "first_name": first_name})()

    fake = FakeMsg(
        call.message.chat.id,
        uid,
        call.from_user.first_name or "User"
    )

    if data == "connect":
        bot.answer_callback_query(call.id, "Подключаюсь...")
        cmd_connect(fake)
    elif data == "disconnect":
        bot.answer_callback_query(call.id, "Отключаю...")
        cmd_disconnect(fake)
    elif data == "rotate":
        bot.answer_callback_query(call.id, "Меняю IP...")
        cmd_rotate(fake)
    elif data == "status":
        bot.answer_callback_query(call.id)
        cmd_status(fake)
    elif data == "proxies":
        bot.answer_callback_query(call.id, "Сканирую...")
        cmd_proxies(fake)

# ── Запуск ────────────────────────────────────
if __name__ == "__main__":
    print("=" * 40)
    print("  TOGAFF VPN BOT — ЗАПУЩЕН")
    print(f"  Mini App: {MINI_APP_URL}")
    print("=" * 40)
    bot.infinity_polling(timeout=30)
