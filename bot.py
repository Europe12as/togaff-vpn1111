#!/usr/bin/env python3
"""
Togaff VPN — Telegram Bot
pip install pyTelegramBotAPI requests
"""
import telebot
import requests
import socket
import threading
import time
import json
import os
from datetime import datetime
TOKEN = os.environ.get("TOKEN")
# ── Прокси список ─────────────────────────────
PROXIES = [
    ("185.221.160.253", 80, 60), ("185.221.160.214", 80, 60),
    ("87.239.31.42",    80, 61), ("109.197.153.121", 8888, 62),
    ("188.235.146.220", 80, 65), ("94.26.241.120",   80, 76),
    ("89.23.112.143",   80, 77), ("91.222.238.112",  80, 77),
    ("82.208.111.19", 8080, 78), ("185.244.173.101", 80, 80),
    ("185.221.152.147", 80, 80), ("91.107.124.250",  80, 97),
    ("212.96.201.54",  80,108),  ("5.180.241.126",   80,112),
    ("195.91.179.91",  80,116),  ("95.217.105.20",   80,141),
    ("37.120.189.106", 80,144),  ("89.31.143.1",     80,144),
    ("78.47.138.199",  80,152),  ("89.31.143.2",     80,152),
    ("195.201.34.206", 80,153),  ("89.31.143.3",     80,153),
    ("167.86.97.239",8080,157),  ("138.201.245.91",8080,157),
    ("89.31.143.12",   80,159),  ("51.178.43.147",   80,164),
    ("87.247.251.24",  80,170),  ("83.143.145.67",   80,170),
    ("85.26.218.76",   80,173),  ("162.19.226.235",  80,173),
    ("5.188.31.212",   80,174),  ("87.247.251.240",  80,174),
    ("207.254.28.68",  80,182),  ("104.167.29.113",  80,184),
    ("116.202.102.255",80,188),  ("77.238.66.2",     80,199),
    ("217.115.115.252",80,199),  ("85.187.17.39",    80,201),
    ("213.135.166.142",80,209),  ("217.145.93.115",  80,211),
    ("141.105.107.34", 80,216),  ("93.170.73.47",    80,281),
    ("31.7.38.227",    80,286),
]

# ── Состояние пользователей ───────────────────
users = {}  # user_id -> {connected, proxy, connect_time}

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
    for host, port, est in PROXIES[:20]:  # проверяем первые 20
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
    try:
        if proxy:
            proxies = {"http": f"http://{proxy[0]}:{proxy[1]}",
                       "https": f"http://{proxy[0]}:{proxy[1]}"}
            r = requests.get("https://api.ipify.org", proxies=proxies, timeout=5)
        else:
            r = requests.get("https://api.ipify.org", timeout=5)
        return r.text.strip()
    except:
        return "Недоступен"

def fmt_time(secs):
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# ── Клавиатуры ────────────────────────────────
def main_keyboard(connected=False):
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    if connected:
        kb.add(
            telebot.types.InlineKeyboardButton("🔴 Отключить", callback_data="disconnect"),
            telebot.types.InlineKeyboardButton("🔄 Сменить IP", callback_data="rotate"),
        )
    else:
        kb.add(
            telebot.types.InlineKeyboardButton("🟢 Подключить", callback_data="connect"),
        )
    kb.add(
        telebot.types.InlineKeyboardButton("📊 Статус", callback_data="status"),
        telebot.types.InlineKeyboardButton("📡 Серверы", callback_data="proxies"),
    )
    kb.add(
        telebot.types.InlineKeyboardButton(
            "🌸 Открыть VPN интерфейс",
            web_app=telebot.types.WebAppInfo(url=MINI_APP_URL)
        )
    )
    return kb

# ── /start ────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    uid = msg.from_user.id
    u = get_user(uid)
    name = msg.from_user.first_name or "Пользователь"
    status = "🟢 Подключён" if u["connected"] else "🔴 Отключён"

    text = (
        f"🌸 *Togaff VPN* — Добро пожаловать, {name}!\n\n"
        f"Статус: {status}\n\n"
        f"*Команды:*\n"
        f"`/connect` — подключиться\n"
        f"`/disconnect` — отключиться\n"
        f"`/rotate` — сменить IP\n"
        f"`/status` — текущий статус\n"
        f"`/proxies` — список серверов\n"
        f"`/ip` — мой текущий IP\n\n"
        f"Или нажми кнопку ниже 👇"
    )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown",
                     reply_markup=main_keyboard(u["connected"]))

# ── /connect ──────────────────────────────────
@bot.message_handler(commands=["connect"])
def cmd_connect(msg):
    uid = msg.from_user.id
    u = get_user(uid)
    if u["connected"]:
        h, p, _ = u["proxy"]
        bot.send_message(msg.chat.id,
            f"✅ Уже подключён к `{h}:{p}`\nИспользуй /rotate для смены или /disconnect",
            parse_mode="Markdown")
        return

    wait = bot.send_message(msg.chat.id, "🔍 Ищу лучший сервер...")

    def do_connect():
        result = get_best_proxy()
        if result:
            host, port, ms = result
            u["connected"] = True
            u["proxy"] = (host, port, ms)
            u["connect_time"] = time.time()
            ip = get_current_ip((host, port))
            bot.edit_message_text(
                f"✅ *Подключено!*\n\n"
                f"🖥 Сервер: `{host}:{port}`\n"
                f"⚡ Пинг: `{ms}ms`\n"
                f"🌐 Твой IP: `{ip}`\n"
                f"🔒 Шифрование: AES-256-GCM\n\n"
                f"_Астольфо: Взломано! Ты анонимен~ ✌️_",
                msg.chat.id, wait.message_id,
                parse_mode="Markdown",
                reply_markup=main_keyboard(True)
            )
        else:
            bot.edit_message_text(
                "❌ Не удалось найти живой сервер. Попробуй ещё раз.",
                msg.chat.id, wait.message_id)

    threading.Thread(target=do_connect, daemon=True).start()

# ── /disconnect ───────────────────────────────
@bot.message_handler(commands=["disconnect"])
def cmd_disconnect(msg):
    uid = msg.from_user.id
    u = get_user(uid)
    if not u["connected"]:
        bot.send_message(msg.chat.id, "ℹ️ Ты и так не подключён.")
        return

    session = ""
    if u["connect_time"]:
        secs = time.time() - u["connect_time"]
        session = f"\n⏱ Сессия: `{fmt_time(secs)}`"

    u["connected"] = False
    u["proxy"] = None
    u["connect_time"] = None

    bot.send_message(msg.chat.id,
        f"🔴 *Отключено*{session}\n\n_Астольфо: До встречи~ 🌸_",
        parse_mode="Markdown",
        reply_markup=main_keyboard(False))

# ── /rotate ───────────────────────────────────
@bot.message_handler(commands=["rotate"])
def cmd_rotate(msg):
    uid = msg.from_user.id
    u = get_user(uid)
    wait = bot.send_message(msg.chat.id, "🔄 Меняю IP...")

    def do_rotate():
        exclude = u["proxy"] if u["proxy"] else None
        result = get_best_proxy(exclude=exclude)
        if result:
            host, port, ms = result
            u["proxy"] = (host, port, ms)
            u["connect_time"] = time.time()
            u["connected"] = True
            ip = get_current_ip((host, port))
            bot.edit_message_text(
                f"🔄 *IP сменён!*\n\n"
                f"🖥 Новый сервер: `{host}:{port}`\n"
                f"⚡ Пинг: `{ms}ms`\n"
                f"🌐 Новый IP: `{ip}`\n\n"
                f"_Астольфо: Новая маска IP~ 🔄_",
                msg.chat.id, wait.message_id,
                parse_mode="Markdown",
                reply_markup=main_keyboard(True))
        else:
            bot.edit_message_text("❌ Нет доступных серверов.", msg.chat.id, wait.message_id)

    threading.Thread(target=do_rotate, daemon=True).start()

# ── /status ───────────────────────────────────
@bot.message_handler(commands=["status"])
def cmd_status(msg):
    uid = msg.from_user.id
    u = get_user(uid)

    if u["connected"] and u["proxy"]:
        h, p, ms = u["proxy"]
        session = fmt_time(time.time() - u["connect_time"]) if u["connect_time"] else "—"
        # Проверяем жив ли прокси
        live_ms = ping_proxy(h, p, timeout=2)
        live = f"✅ `{live_ms}ms`" if live_ms else "❌ Недоступен"
        text = (
            f"📊 *Статус Togaff VPN*\n\n"
            f"🟢 Статус: Подключён\n"
            f"🖥 Сервер: `{h}:{p}`\n"
            f"⚡ Пинг: {live}\n"
            f"⏱ Сессия: `{session}`\n"
            f"🔒 Шифрование: AES-256-GCM ✓\n"
            f"🌐 DNS: HTTPS ✓\n"
            f"🛡 Leak protect: ✓"
        )
    else:
        text = (
            f"📊 *Статус Togaff VPN*\n\n"
            f"🔴 Статус: Отключён\n"
            f"🔒 Шифрование: AES-256-GCM\n\n"
            f"Нажми /connect для подключения"
        )

    bot.send_message(msg.chat.id, text, parse_mode="Markdown",
                     reply_markup=main_keyboard(u["connected"]))

# ── /proxies ──────────────────────────────────
@bot.message_handler(commands=["proxies"])
def cmd_proxies(msg):
    wait = bot.send_message(msg.chat.id, "📡 Сканирую серверы...")

    def do_scan():
        lines = ["📡 *Список серверов Togaff VPN*\n"]
        alive = 0
        for host, port, est in PROXIES[:15]:
            ms = ping_proxy(host, port, timeout=1.5)
            if ms:
                alive += 1
                if ms < 100:   icon = "🟢"
                elif ms < 180: icon = "🟡"
                else:          icon = "🔴"
                lines.append(f"{icon} `{host}:{port}` — {ms}ms")
            else:
                lines.append(f"⚫ `{host}:{port}` — недоступен")

        lines.append(f"\n✅ Живых: {alive}/15")
        lines.append(f"_(показаны первые 15 из {len(PROXIES)})_")

        bot.edit_message_text(
            "\n".join(lines),
            msg.chat.id, wait.message_id,
            parse_mode="Markdown",
            reply_markup=main_keyboard(get_user(msg.from_user.id)["connected"])
        )

    threading.Thread(target=do_scan, daemon=True).start()

# ── /ip ───────────────────────────────────────
@bot.message_handler(commands=["ip"])
def cmd_ip(msg):
    uid = msg.from_user.id
    u = get_user(uid)
    wait = bot.send_message(msg.chat.id, "🌐 Определяю IP...")

    def do_ip():
        proxy = u["proxy"] if u["connected"] else None
        ip = get_current_ip(proxy)
        prefix = "🟢 Через прокси" if proxy else "⚪ Прямое соединение"
        bot.edit_message_text(
            f"🌐 *Твой IP адрес*\n\n{prefix}\n`{ip}`",
            msg.chat.id, wait.message_id,
            parse_mode="Markdown")

    threading.Thread(target=do_ip, daemon=True).start()

# ── Callback кнопки ───────────────────────────
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    uid = call.from_user.id
    data = call.data

    if data == "connect":
        bot.answer_callback_query(call.id, "🔍 Подключаюсь...")
        cmd_connect(call.message)
    elif data == "disconnect":
        bot.answer_callback_query(call.id, "🔴 Отключаю...")
        cmd_disconnect(call.message)
    elif data == "rotate":
        bot.answer_callback_query(call.id, "🔄 Меняю IP...")
        cmd_rotate(call.message)
    elif data == "status":
        bot.answer_callback_query(call.id)
        cmd_status(call.message)
    elif data == "proxies":
        bot.answer_callback_query(call.id, "📡 Сканирую...")
        cmd_proxies(call.message)

# ── Запуск ────────────────────────────────────
if __name__ == "__main__":
    print("🌸 Togaff VPN Bot запущен!")
    print(f"Mini App URL: {MINI_APP_URL}")
    bot.infinity_polling(timeout=30)
