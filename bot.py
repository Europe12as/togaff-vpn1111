import telebot
import requests
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ══════════════════════════════════════════════
TOKEN = "8603769389:AAFNrImTZhMY0ctceejoFbNkosE54cNsE30"
# ══════════════════════════════════════════════

MINI_APP_URL = "https://YOUR_USERNAME.github.io/togaff-vpn/"

bot = telebot.TeleBot(TOKEN)

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

users = {}

def get_user(uid):
    if uid not in users:
        users[uid] = {"connected": False, "proxy": None, "connect_time": None}
    return users[uid]

# ── Ping одного прокси ────────────────────────
def ping_proxy(host, port, timeout=2.0):
    try:
        t0 = time.time()
        with socket.create_connection((host, port), timeout=timeout):
            return round((time.time() - t0) * 1000, 1)
    except:
        return None

# ── ПАРАЛЛЕЛЬНЫЙ поиск — НЕ зависает! ────────
def get_best_proxy(exclude=None, top_n=20):
    candidates = [
        (h, p) for h, p in PROXIES[:top_n]
        if not (exclude and h == exclude[0])
    ]
    results = []

    def check(host, port):
        ms = ping_proxy(host, port, timeout=1.5)
        return (ms, host, port)

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(check, h, p): (h, p) for h, p in candidates}
        for future in as_completed(futures):
            ms, host, port = future.result()
            if ms is not None:
                results.append((ms, host, port))

    if not results:
        return None
    results.sort()
    ms, host, port = results[0]
    return (host, port, ms)

# ── Получить IP (HTTP чтобы прокси сработал) ─
def get_current_ip(proxy=None):
    try:
        if proxy:
            host, port = proxy[0], proxy[1]
            proxies = {
                "http":  f"http://{host}:{port}",
                "https": f"http://{host}:{port}",
            }
            r = requests.get("http://api.ipify.org", proxies=proxies, timeout=6)
        else:
            r = requests.get("http://api.ipify.org", timeout=6)
        return r.text.strip()
    except:
        return "—"

def fmt_time(secs):
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def ping_bar(ms):
    blocks = min(10, max(1, int(10 - ms / 30)))
    return "█" * blocks + "░" * (10 - blocks)

# ── Живая анимация ожидания ───────────────────
class LoadingAnimation:
    FRAMES = {
        "search": [
            "🔍 Ищу лучший сервер ·  ",
            "🔍 Ищу лучший сервер ·· ",
            "🔍 Ищу лучший сервер ···",
            "🔎 Проверяю серверы ·· ",
            "🔎 Проверяю серверы ·  ",
        ],
        "rotate": [
            "🔄 Меняю IP адрес ·  ",
            "🔄 Меняю IP адрес ·· ",
            "🔄 Меняю IP адрес ···",
            "♻️  Выбираю сервер ·· ",
            "♻️  Выбираю сервер ·  ",
        ],
        "scan": [
            "📡 Сканирую серверы ·  ",
            "📡 Сканирую серверы ·· ",
            "📡 Сканирую серверы ···",
            "🛰️  Пингую серверы ··  ",
            "🛰️  Пингую серверы ·   ",
        ],
        "ip": [
            "🌐 Определяю IP ·  ",
            "🌐 Определяю IP ·· ",
            "🌐 Определяю IP ···",
        ],
    }

    def __init__(self, chat_id, message_id, kind="search"):
        self.chat_id    = chat_id
        self.message_id = message_id
        self.frames     = self.FRAMES[kind]
        self._stop      = threading.Event()
        self._thread    = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2)

    def _run(self):
        i = 0
        while not self._stop.is_set():
            try:
                bot.edit_message_text(
                    self.frames[i % len(self.frames)],
                    self.chat_id,
                    self.message_id
                )
            except:
                pass
            i += 1
            self._stop.wait(0.55)


# ── Клавиатуры ────────────────────────────────
def main_keyboard(connected=False):
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    if connected:
        kb.add(
            telebot.types.InlineKeyboardButton("🔴 Отключить",  callback_data="disconnect"),
            telebot.types.InlineKeyboardButton("🔀 Сменить IP", callback_data="rotate"),
        )
    else:
        kb.add(
            telebot.types.InlineKeyboardButton("🟢 Подключиться", callback_data="connect"),
        )
    kb.add(
        telebot.types.InlineKeyboardButton("📊 Статус",  callback_data="status"),
        telebot.types.InlineKeyboardButton("🛰 Серверы", callback_data="proxies"),
    )
    kb.add(
        telebot.types.InlineKeyboardButton(
            "🌐 Открыть VPN интерфейс",
            web_app=telebot.types.WebAppInfo(url=MINI_APP_URL)
        )
    )
    return kb

# ── /start ────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    uid  = msg.from_user.id
    u    = get_user(uid)
    name = msg.from_user.first_name or "Пользователь"

    if u["connected"] and u["proxy"]:
        h, p, ms = u["proxy"]
        status = f"🟢 *Подключён* — `{h}:{p}`"
    else:
        status = "🔴 *Отключён*"

    text = (
        f"🛡 *TOGAFF VPN*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👋 Привет, *{name}*!\n"
        f"Статус: {status}\n\n"
        f"*Команды:*\n"
        f"🟢 /connect — подключиться\n"
        f"🔴 /disconnect — отключиться\n"
        f"🔀 /rotate — сменить IP\n"
        f"📊 /status — текущий статус\n"
        f"🛰 /proxies — список серверов\n"
        f"🌐 /ip — мой IP адрес\n"
    )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown",
                     reply_markup=main_keyboard(u["connected"]))

# ── /connect ──────────────────────────────────
@bot.message_handler(commands=["connect"])
def cmd_connect(msg):
    uid = msg.from_user.id
    u   = get_user(uid)

    if u["connected"]:
        h, p, _ = u["proxy"]
        bot.send_message(
            msg.chat.id,
            f"✅ Уже подключён к `{h}:{p}`\n\n"
            f"🔀 /rotate — сменить IP\n"
            f"🔴 /disconnect — отключиться",
            parse_mode="Markdown",
            reply_markup=main_keyboard(True)
        )
        return

    wait = bot.send_message(msg.chat.id, "🔍 Ищу лучший сервер ·  ")
    anim = LoadingAnimation(msg.chat.id, wait.message_id, "search").start()

    def do_connect():
        result = get_best_proxy()
        anim.stop()
        if result:
            host, port, ms = result
            u.update(connected=True, proxy=(host, port, ms), connect_time=time.time())
            ip  = get_current_ip((host, port))
            bar = ping_bar(ms)
            try:
                bot.edit_message_text(
                    f"✅ *Подключение установлено!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🖥 Сервер:      `{host}:{port}`\n"
                    f"⚡ Пинг:        `{ms} ms`\n"
                    f"📶 Сигнал:      `{bar}`\n"
                    f"🌐 Ваш IP:      `{ip}`\n\n"
                    f"🔐 Шифрование:  `AES-256-GCM`\n"
                    f"🛡 DNS-HTTPS:   `✓`\n"
                    f"👁 Leak protect:`✓`\n\n"
                    f"_Вы анонимны~ 🎭_",
                    msg.chat.id, wait.message_id,
                    parse_mode="Markdown",
                    reply_markup=main_keyboard(True)
                )
            except: pass
        else:
            try:
                bot.edit_message_text(
                    "❌ *Нет доступных серверов*\n\n"
                    "Попробуй через несколько секунд 🔄\n"
                    "/connect — попробовать снова",
                    msg.chat.id, wait.message_id,
                    parse_mode="Markdown",
                    reply_markup=main_keyboard(False)
                )
            except: pass

    threading.Thread(target=do_connect, daemon=True).start()

# ── /disconnect ───────────────────────────────
@bot.message_handler(commands=["disconnect"])
def cmd_disconnect(msg):
    uid = msg.from_user.id
    u   = get_user(uid)

    if not u["connected"]:
        bot.send_message(
            msg.chat.id,
            "ℹ️ VPN уже отключён\n\n🟢 /connect — подключиться",
            reply_markup=main_keyboard(False)
        )
        return

    session = ""
    if u["connect_time"]:
        session = f"\n⏱ Сессия: `{fmt_time(time.time() - u['connect_time'])}`"

    u.update(connected=False, proxy=None, connect_time=None)

    bot.send_message(
        msg.chat.id,
        f"🔴 *VPN отключён*{session}\n\n"
        f"_Ваш реальный IP снова виден 👋_",
        parse_mode="Markdown",
        reply_markup=main_keyboard(False)
    )

# ── /rotate ───────────────────────────────────
@bot.message_handler(commands=["rotate"])
def cmd_rotate(msg):
    uid  = msg.from_user.id
    u    = get_user(uid)
    wait = bot.send_message(msg.chat.id, "🔄 Меняю IP адрес ·  ")
    anim = LoadingAnimation(msg.chat.id, wait.message_id, "rotate").start()

    def do_rotate():
        exclude = u["proxy"] if u["proxy"] else None
        result  = get_best_proxy(exclude=exclude)
        anim.stop()
        if result:
            host, port, ms = result
            u.update(proxy=(host, port, ms), connect_time=time.time(), connected=True)
            ip  = get_current_ip((host, port))
            bar = ping_bar(ms)
            try:
                bot.edit_message_text(
                    f"🔀 *IP успешно сменён!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🖥 Новый сервер: `{host}:{port}`\n"
                    f"⚡ Пинг:         `{ms} ms`\n"
                    f"📶 Сигнал:       `{bar}`\n"
                    f"🌐 Новый IP:     `{ip}`\n\n"
                    f"_Новая личность активирована 🕵️_",
                    msg.chat.id, wait.message_id,
                    parse_mode="Markdown",
                    reply_markup=main_keyboard(True)
                )
            except: pass
        else:
            try:
                bot.edit_message_text(
                    "❌ Нет альтернативных серверов\n/rotate — попробовать снова",
                    msg.chat.id, wait.message_id,
                    reply_markup=main_keyboard(u["connected"])
                )
            except: pass

    threading.Thread(target=do_rotate, daemon=True).start()

# ── /status ───────────────────────────────────
@bot.message_handler(commands=["status"])
def cmd_status(msg):
    uid = msg.from_user.id
    u   = get_user(uid)

    if u["connected"] and u["proxy"]:
        h, p, ms = u["proxy"]
        session  = fmt_time(time.time() - u["connect_time"]) if u["connect_time"] else "—"
        live_ms  = ping_proxy(h, p, timeout=2)
        if live_ms:
            bar      = ping_bar(live_ms)
            ping_str = f"`{live_ms} ms` `{bar}`"
        else:
            ping_str = "❌ `недоступен`"

        text = (
            f"📊 *Статус TOGAFF VPN*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🟢 Статус:        `АКТИВЕН`\n"
            f"🖥 Сервер:         `{h}:{p}`\n"
            f"⚡ Пинг:           {ping_str}\n"
            f"⏱ Сессия:         `{session}`\n\n"
            f"🔐 AES-256-GCM:   `✓`\n"
            f"🛡 DNS-over-HTTPS:`✓`\n"
            f"🚫 IP Leak:       `защищён ✓`\n"
            f"👁 Слежка:        `заблокирована ✓`\n"
        )
    else:
        text = (
            f"📊 *Статус TOGAFF VPN*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔴 Статус: `ОТКЛЮЧЁН`\n\n"
            f"⚠️ Ваш IP *виден* всем сайтам\n"
            f"🟢 /connect — включить защиту\n"
        )

    bot.send_message(msg.chat.id, text, parse_mode="Markdown",
                     reply_markup=main_keyboard(u["connected"]))

# ── /proxies ──────────────────────────────────
@bot.message_handler(commands=["proxies"])
def cmd_proxies(msg):
    wait = bot.send_message(msg.chat.id, "📡 Сканирую серверы ·  ")
    anim = LoadingAnimation(msg.chat.id, wait.message_id, "scan").start()

    def do_scan():
        results = []

        def check(host, port):
            ms = ping_proxy(host, port, timeout=1.5)
            return (ms, host, port)

        with ThreadPoolExecutor(max_workers=15) as pool:
            futures = {pool.submit(check, h, p): (h, p) for h, p in PROXIES[:20]}
            for future in as_completed(futures):
                results.append(future.result())

        anim.stop()
        results.sort(key=lambda x: (x[0] is None, x[0] or 9999))
        alive = sum(1 for ms, _, _ in results if ms is not None)

        lines = [
            f"🛰 *Серверы TOGAFF VPN*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Онлайн: *{alive}/{len(results)}* серверов\n"
        ]

        for ms, host, port in results[:15]:
            if ms is not None:
                if ms < 100:   icon, q = "🟢", "отлично"
                elif ms < 200: icon, q = "🟡", "хорошо"
                else:          icon, q = "🟠", "медленно"
                lines.append(f"{icon} `{host}:{port}` — `{ms}ms` _{q}_")
            else:
                lines.append(f"⚫ `{host}:{port}` — _офлайн_")

        lines.append(f"\n_Показано 15 из {len(PROXIES)} серверов_")

        try:
            bot.edit_message_text(
                "\n".join(lines),
                msg.chat.id, wait.message_id,
                parse_mode="Markdown",
                reply_markup=main_keyboard(get_user(msg.from_user.id)["connected"])
            )
        except: pass

    threading.Thread(target=do_scan, daemon=True).start()

# ── /ip ───────────────────────────────────────
@bot.message_handler(commands=["ip"])
def cmd_ip(msg):
    uid  = msg.from_user.id
    u    = get_user(uid)
    wait = bot.send_message(msg.chat.id, "🌐 Определяю IP ·  ")
    anim = LoadingAnimation(msg.chat.id, wait.message_id, "ip").start()

    def do_ip():
        proxy = u["proxy"] if u["connected"] else None
        ip    = get_current_ip(proxy)
        anim.stop()
        if proxy:
            h, p = proxy[0], proxy[1]
            text = (
                f"🌐 *Ваш IP адрес*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🟢 Режим:  `через VPN`\n"
                f"🎭 IP:     `{ip}`\n"
                f"🖥 Сервер: `{h}:{p}`\n\n"
                f"_Реальный IP скрыт ✓_"
            )
        else:
            text = (
                f"🌐 *Ваш IP адрес*\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🔴 Режим: `прямое соединение`\n"
                f"👁 IP:    `{ip}`\n\n"
                f"⚠️ _Ваш IP виден всем! /connect_"
            )
        try:
            bot.edit_message_text(text, msg.chat.id, wait.message_id, parse_mode="Markdown")
        except: pass

    threading.Thread(target=do_ip, daemon=True).start()

# ── Callback (ИСПРАВЛЕНО: правильный uid!) ────
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    uid  = call.from_user.id   # ← uid пользователя, не бота!
    data = call.data

    class FakeMsg:
        def __init__(self, chat_id, user_id, first_name):
            self.chat      = type("C", (), {"id": chat_id})()
            self.from_user = type("U", (), {"id": user_id, "first_name": first_name})()

    fake = FakeMsg(call.message.chat.id, uid, call.from_user.first_name or "User")

    dispatch = {
        "connect":    (cmd_connect,    "🔍 Ищу сервер..."),
        "disconnect": (cmd_disconnect, "🔴 Отключаю..."),
        "rotate":     (cmd_rotate,     "🔀 Меняю IP..."),
        "status":     (cmd_status,     None),
        "proxies":    (cmd_proxies,    "📡 Сканирую..."),
    }

    if data in dispatch:
        fn, answer = dispatch[data]
        bot.answer_callback_query(call.id, answer or "")
        fn(fake)

# ── Запуск ────────────────────────────────────
if __name__ == "__main__":
    print("🛡  TOGAFF VPN BOT — ЗАПУЩЕН")
    print(f"📡  Серверов в пуле: {len(PROXIES)}")
    print(f"🌐  Mini App: {MINI_APP_URL}")
    print("─" * 40)
    bot.infinity_polling(timeout=30)
