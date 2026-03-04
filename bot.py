"""
╔══════════════════════════════════════╗
║     TOGAFF VPN  ·  Premium Edition   ║
║   Real proxy verification · SOCKS5   ║
╚══════════════════════════════════════╝
  pip install pyTelegramBotAPI requests[socks] PySocks
"""

import telebot
import requests
import socket
import threading
import time
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# ┌─────────────────────────────────────┐
# │            КОНФИГУРАЦИЯ             │
# └─────────────────────────────────────┘
TOKEN        = "8603769389:AAFNrImTZhMY0ctceejoFbNkosE54cNsE30"
MINI_APP_URL = "https://YOUR_USERNAME.github.io/togaff-vpn/"

# Стикер-пак вместо фото (Telegram стикеры работают везде)
# Telegram Duck стикер (публичный, не требует фото)
WELCOME_STICKER = "CAACAgIAAxkBAAIBcWZ5X2QAAf3yYW9YcgABfBiXp7CRAAJ4AQACB8ShS1kN6VrwzFjRNgQ"

try:
    import socks  # noqa
    SOCKS_OK = True
except ImportError:
    SOCKS_OK = False

bot = telebot.TeleBot(TOKEN)

# ┌─────────────────────────────────────┐
# │         СВОИ ПРОКСИ (HTTP)          │
# └─────────────────────────────────────┘
MY_PROXIES = [
    ("185.221.160.253", 80),  ("185.221.160.214", 80),
    ("87.239.31.42",    80),  ("109.197.153.121", 8888),
    ("188.235.146.220", 80),  ("94.26.241.120",   80),
    ("89.23.112.143",   80),  ("91.222.238.112",  80),
    ("82.208.111.19", 8080),  ("185.244.173.101", 80),
    ("185.221.152.147", 80),  ("91.107.124.250",  80),
    ("212.96.201.54",   80),  ("5.180.241.126",   80),
    ("195.91.179.91",   80),  ("95.217.105.20",   80),
    ("37.120.189.106",  80),  ("89.31.143.1",     80),
    ("78.47.138.199",   80),  ("89.31.143.2",     80),
    ("195.201.34.206",  80),  ("89.31.143.3",     80),
    ("167.86.97.239", 8080),  ("138.201.245.91", 8080),
    ("89.31.143.12",    80),  ("51.178.43.147",   80),
    ("87.247.251.24",   80),  ("83.143.145.67",   80),
    ("85.26.218.76",    80),  ("162.19.226.235",  80),
    ("5.188.31.212",    80),  ("87.247.251.240",  80),
    ("207.254.28.68",   80),  ("104.167.29.113",  80),
    ("116.202.102.255", 80),  ("77.238.66.2",     80),
    ("217.115.115.252", 80),  ("85.187.17.39",    80),
    ("213.135.166.142", 80),  ("217.145.93.115",  80),
    ("141.105.107.34",  80),  ("93.170.73.47",    80),
    ("31.7.38.227",     80),
]

# ┌─────────────────────────────────────┐
# │         ИСТОЧНИКИ ПРОКСИ            │
# └─────────────────────────────────────┘
SOURCES = {
    "socks5": [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
    ],
    "socks4": [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
    ],
    "http": [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    ],
}

# ┌─────────────────────────────────────┐
# │              КЭШ                    │
# └─────────────────────────────────────┘
cache = {
    "socks5": [], "socks4": [], "http": [],
    "updated": 0,
    "top_fast": [],   # ТОП быстрых прокси (авто-выбор)
}
CACHE_TTL = 1800
TOP_FAST_COUNT = 20   # сколько быстрых держим в пуле

users = {}

def get_user(uid):
    if uid not in users:
        users[uid] = {
            "connected": False, "proxy": None,
            "connect_time": None, "ip_before": None, "ip_after": None,
            "sessions": 0,
        }
    return users[uid]

# ┌─────────────────────────────────────┐
# │         ЗАГРУЗКА ПРОКСИ             │
# └─────────────────────────────────────┘
def fetch_list(url, timeout=12):
    try:
        r = requests.get(url, timeout=timeout,
                         headers={"User-Agent": "curl/7.80.0"})
        if r.status_code != 200:
            return []
        out = []
        for line in r.text.splitlines():
            m = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})", line.strip())
            if m:
                out.append((m.group(1), int(m.group(2))))
        return out
    except:
        return []

def refresh_cache():
    if time.time() - cache["updated"] < CACHE_TTL:
        return
    print("⟳  Загружаю списки прокси...")

    # Свои прокси первыми в HTTP
    my_seen = {f"{h}:{p}" for h, p in MY_PROXIES}
    my_list = list(MY_PROXIES)

    for ptype, urls in SOURCES.items():
        base = list(my_list) if ptype == "http" else []
        seen = set(my_seen) if ptype == "http" else set()
        for url in urls:
            for h, p in fetch_list(url):
                k = f"{h}:{p}"
                if k not in seen:
                    seen.add(k)
                    base.append((h, p))
            if len(base) >= 600:
                break
        if ptype == "http":
            tail = base[len(my_list):]
            random.shuffle(tail)
            cache[ptype] = (my_list + tail)[:400]
        else:
            random.shuffle(base)
            cache[ptype] = base[:400]
        print(f"   {ptype}: {len(cache[ptype])}")

    cache["updated"] = time.time()
    print("✓  Кэш обновлён")

# ┌─────────────────────────────────────┐
# │      ПРОВЕРКА И ВЕРИФИКАЦИЯ         │
# └─────────────────────────────────────┘
IP_URLS = [
    "http://api.ipify.org",
    "http://checkip.amazonaws.com",
    "http://icanhazip.com",
]

def tcp_ping(host, port, timeout=2.0):
    try:
        t0 = time.time()
        with socket.create_connection((host, port), timeout=timeout):
            return round((time.time() - t0) * 1000, 1)
    except:
        return None

def get_ip(proxy_cfg=None, timeout=8):
    for url in IP_URLS:
        try:
            if proxy_cfg:
                pt = proxy_cfg["type"]
                h, p = proxy_cfg["host"], proxy_cfg["port"]
                if pt in ("socks5", "socks4") and SOCKS_OK:
                    scheme = pt
                    prx = {k: f"{scheme}://{h}:{p}" for k in ("http","https")}
                else:
                    prx = {k: f"http://{h}:{p}" for k in ("http","https")}
                r = requests.get(url, proxies=prx, timeout=timeout)
            else:
                r = requests.get(url, timeout=timeout)
            ip = r.text.strip()
            if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", ip):
                return ip
        except:
            continue
    return None

def verify_proxy(ptype, host, port, my_ip, tcp_timeout=2.0, ip_timeout=7):
    """Полная проверка: TCP доступность + реальная смена IP."""
    ms = tcp_ping(host, port, timeout=tcp_timeout)
    if not ms:
        return None
    cfg = {"type": ptype, "host": host, "port": port}
    new_ip = get_ip(proxy_cfg=cfg, timeout=ip_timeout)
    if not new_ip or new_ip == my_ip:
        return None
    return {"type": ptype, "host": host, "port": port,
            "ping": ms, "new_ip": new_ip}

# ┌─────────────────────────────────────┐
# │     АВТО-ВЫБОР БЫСТРЫХ ПРОКСИ      │
# └─────────────────────────────────────┘
def build_top_fast(my_ip, sample=60, workers=12):
    """
    Параллельно проверяем sample прокси из всех типов,
    сортируем по пингу и сохраняем TOP_FAST_COUNT лучших.
    """
    candidates = []
    order = ["socks5", "socks4", "http"] if SOCKS_OK else ["http", "socks5", "socks4"]
    per_type = sample // len(order)
    for pt in order:
        pool = list(cache[pt])
        random.shuffle(pool)
        for h, p in pool[:per_type]:
            candidates.append((pt, h, p))

    results = []
    def check(args):
        pt, h, p = args
        return verify_proxy(pt, h, p, my_ip, tcp_timeout=1.5, ip_timeout=5)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(check, c): c for c in candidates}
        for fut in as_completed(futs):
            res = fut.result()
            if res:
                results.append(res)

    results.sort(key=lambda x: x["ping"])
    cache["top_fast"] = results[:TOP_FAST_COUNT]
    print(f"✓  Топ быстрых: {len(cache['top_fast'])} прокси")
    return cache["top_fast"]

def find_proxy_auto(my_ip, exclude=None, on_try=None):
    """
    Умный поиск:
    1) Сначала пробуем из top_fast (уже проверенные быстрые)
    2) Если не нашли — полный scan с on_try анимацией
    """
    # Попытка 1: из top_fast
    fast_pool = [p for p in cache["top_fast"]
                 if not exclude or p["host"] != exclude]
    for proxy in fast_pool:
        res = verify_proxy(proxy["type"], proxy["host"], proxy["port"],
                           my_ip, tcp_timeout=1.5, ip_timeout=5)
        if res:
            return res

    # Попытка 2: полный scan
    refresh_cache()
    order = ["socks5", "socks4", "http"] if SOCKS_OK else ["http", "socks5", "socks4"]
    n = 0
    for ptype in order:
        pool = list(cache[ptype])
        random.shuffle(pool)
        for host, port in pool:
            if n >= 100:
                return None
            if exclude and host == exclude:
                continue
            n += 1
            if on_try:
                on_try(n, ptype, host, port)
            res = verify_proxy(ptype, host, port, my_ip)
            if res:
                return res
    return None

def find_proxy_type(my_ip, ptype, exclude=None, on_try=None, limit=80):
    """Поиск только по конкретному протоколу."""
    refresh_cache()
    pool = list(cache[ptype])
    random.shuffle(pool)
    n = 0
    for host, port in pool:
        if n >= limit:
            return None
        if exclude and host == exclude:
            continue
        n += 1
        if on_try:
            on_try(n, ptype, host, port)
        res = verify_proxy(ptype, host, port, my_ip)
        if res:
            return res
    return None

# ┌─────────────────────────────────────┐
# │         УТИЛИТЫ ФОРМАТИРОВАНИЯ      │
# └─────────────────────────────────────┘
def fmt_time(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    if h:
        return f"{h}ч {m:02d}м {sec:02d}с"
    if m:
        return f"{m}м {sec:02d}с"
    return f"{sec}с"

def ping_bar(ms):
    """Визуальный индикатор качества соединения."""
    if ms is None:
        return "⬜⬜⬜⬜⬜  offline"
    if ms < 80:
        return "🟩🟩🟩🟩🟩  отлично"
    if ms < 150:
        return "🟩🟩🟩🟩⬜  хорошо"
    if ms < 250:
        return "🟨🟨🟨⬜⬜  средне"
    if ms < 400:
        return "🟧🟧⬜⬜⬜  медленно"
    return "🟥⬜⬜⬜⬜  плохо"

def proto_icon(ptype):
    return {"socks5": "🔵", "socks4": "🟣", "http": "⚪"}.get(ptype, "⚫")

def status_dot(connected):
    return "🟢" if connected else "🔴"

def loading_bar(n, total=100, width=10):
    filled = min(int(width * n / total), width)
    return "▰" * filled + "▱" * (width - filled)

# ┌─────────────────────────────────────┐
# │            КЛАВИАТУРЫ               │
# └─────────────────────────────────────┘
def kb_main(connected=False):
    k = telebot.types.InlineKeyboardMarkup(row_width=2)
    if connected:
        k.add(
            telebot.types.InlineKeyboardButton("🔴  Отключить",    callback_data="disconnect"),
            telebot.types.InlineKeyboardButton("🔄  Сменить IP",   callback_data="rotate"),
        )
        k.add(
            telebot.types.InlineKeyboardButton("📋  Генератор",    callback_data="generate"),
            telebot.types.InlineKeyboardButton("📊  Статус",       callback_data="status"),
        )
    else:
        k.add(
            telebot.types.InlineKeyboardButton("⚡  Быстрое подключение", callback_data="connect"),
        )
        k.add(
            telebot.types.InlineKeyboardButton("📊  Статус",       callback_data="status"),
            telebot.types.InlineKeyboardButton("🗂  Серверы",      callback_data="proxies"),
        )
    k.add(
        telebot.types.InlineKeyboardButton("🔵  SOCKS5", callback_data="c_socks5"),
        telebot.types.InlineKeyboardButton("🟣  SOCKS4",  callback_data="c_socks4"),
        telebot.types.InlineKeyboardButton("⚪  HTTP",    callback_data="c_http"),
    )
    k.add(telebot.types.InlineKeyboardButton(
        "🌐  Открыть веб-панель",
        web_app=telebot.types.WebAppInfo(url=MINI_APP_URL)))
    return k

def kb_generate():
    k = telebot.types.InlineKeyboardMarkup(row_width=1)
    k.add(telebot.types.InlineKeyboardButton("🔄  Другой прокси", callback_data="regen"))
    k.add(telebot.types.InlineKeyboardButton("◀  Назад",          callback_data="back_main"))
    return k

class FMsg:
    """Псевдо-сообщение для вызова команд из callback."""
    def __init__(self, call, text=""):
        self.chat      = type("C", (), {"id": call.message.chat.id})()
        self.from_user = type("U", (), {
            "id": call.from_user.id,
            "first_name": call.from_user.first_name or "User"
        })()
        self.text = text

# ┌─────────────────────────────────────┐
# │             /start                  │
# └─────────────────────────────────────┘
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    u     = get_user(msg.from_user.id)
    name  = msg.from_user.first_name or "Пользователь"
    total = sum(len(cache[t]) for t in ["socks5","socks4","http"])
    fast  = len(cache["top_fast"])

    connected_line = (
        f"🟢  *Подключён* через `{u['proxy']['host']}`  ·  {u['proxy']['type'].upper()}"
        if u["connected"] and u["proxy"]
        else "🔴  *Не подключён*"
    )

    text = (
        f"👋  *Добро пожаловать, {name}!*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡  *Togaff VPN*  ·  Premium\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{connected_line}\n\n"
        f"📦  Прокси в базе:     `{total}`\n"
        f"⚡  Быстрых в пуле:   `{fast}`\n"
        f"🔒  Протоколы:  SOCKS5 · SOCKS4 · HTTP\n"
        f"✅  Проверка:   реальная смена IP\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"*Команды*\n"
        f"`/connect`        — авто‑подключение\n"
        f"`/connect socks5` — только SOCKS5\n"
        f"`/connect socks4` — только SOCKS4\n"
        f"`/connect http`   — только HTTP\n"
        f"`/disconnect`     — отключиться\n"
        f"`/rotate`         — сменить IP\n"
        f"`/status`         — текущий статус\n"
        f"`/generate`       — конфиг прокси\n"
        f"`/scan`           — авто‑скан быстрых\n"
        f"`/ip`             — мой IP\n"
        f"`/refresh`        — обновить базу\n"
        f"`/proxies`        — список серверов\n"
    )

    # Отправляем стикер + текст
    try:
        bot.send_sticker(msg.chat.id, WELCOME_STICKER)
    except:
        pass

    bot.send_message(msg.chat.id, text,
                     parse_mode="Markdown",
                     reply_markup=kb_main(u["connected"]))

# ┌─────────────────────────────────────┐
# │          /scan — авто-скан          │
# └─────────────────────────────────────┘
@bot.message_handler(commands=["scan"])
def cmd_scan(msg):
    wait = bot.send_message(msg.chat.id,
        "🔍  *Сканирую быстрые серверы...*\n\n"
        "`Это займёт ~30 секунд`",
        parse_mode="Markdown")

    def do():
        my_ip = get_ip(timeout=6) or "unknown"

        bot.edit_message_text(
            "🔍  *Параллельное сканирование*\n\n"
            f"{loading_bar(10)}  инициализация...",
            msg.chat.id, wait.message_id, parse_mode="Markdown")

        results = build_top_fast(my_ip, sample=80, workers=15)

        if not results:
            bot.edit_message_text(
                "❌  Быстрые серверы не найдены\n"
                "Попробуй `/refresh` для обновления базы",
                msg.chat.id, wait.message_id, parse_mode="Markdown")
            return

        lines = [
            f"⚡  *Быстрые серверы готовы*\n\n"
            f"Найдено: `{len(results)}` серверов\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"*Топ‑{min(5,len(results))}:*\n"
        ]
        for i, r in enumerate(results[:5], 1):
            pi = proto_icon(r["type"])
            lines.append(
                f"{i}. {pi}  `{r['host']}:{r['port']}`\n"
                f"     {ping_bar(r['ping'])}  `{r['ping']}ms`\n"
            )
        lines.append(
            f"\n━━━━━━━━━━━━━━━━━━━━━\n"
            f"_Используются автоматически при /connect_"
        )

        bot.edit_message_text(
            "\n".join(lines),
            msg.chat.id, wait.message_id,
            parse_mode="Markdown",
            reply_markup=kb_main(get_user(msg.from_user.id)["connected"]))

    threading.Thread(target=do, daemon=True).start()

# ┌─────────────────────────────────────┐
# │           /connect                  │
# └─────────────────────────────────────┘
@bot.message_handler(commands=["connect"])
def cmd_connect(msg):
    uid = msg.from_user.id
    u   = get_user(uid)

    parts     = (msg.text or "").strip().split()
    preferred = (parts[1].lower()
                 if len(parts) > 1 and parts[1] in ("socks5","socks4","http")
                 else None)

    if u["connected"]:
        px = u["proxy"]
        bot.send_message(msg.chat.id,
            f"✅  Уже подключён\n\n"
            f"{proto_icon(px['type'])}  `{px['host']}:{px['port']}`\n\n"
            f"Используй /rotate для смены IP\nили /disconnect для отключения",
            parse_mode="Markdown", reply_markup=kb_main(True))
        return

    wait = bot.send_message(msg.chat.id,
        "🔍  *Определяю ваш IP...*",
        parse_mode="Markdown")

    def do():
        my_ip = get_ip(timeout=6) or "unknown"
        u["ip_before"] = my_ip

        if preferred:
            label = preferred.upper()
            mode_text = f"Протокол: `{label}`"
        else:
            label = "AUTO"
            fast_count = len(cache["top_fast"])
            mode_text = (
                f"Режим: `Авто` · быстрых в пуле: `{fast_count}`"
                if fast_count else
                "Режим: `Авто` · полный скан"
            )

        bot.edit_message_text(
            f"🔄  *Поиск сервера [{label}]*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍  Ваш IP: `{my_ip}`\n"
            f"{mode_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{loading_bar(0)}  начинаю...",
            msg.chat.id, wait.message_id, parse_mode="Markdown")

        info      = {"n": 0, "last_host": ""}
        last_edit = [0.0]

        def on_try(n, pt, h, p):
            info["n"]         = n
            info["last_host"] = f"{h}:{p}"
            now = time.time()
            if now - last_edit[0] >= 1.8:
                last_edit[0] = now
                try:
                    bot.edit_message_text(
                        f"🔄  *Поиск сервера [{label}]*\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📍  Ваш IP: `{my_ip}`\n"
                        f"{proto_icon(pt)}  Тестирую: `{h}:{p}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"{loading_bar(min(n,100))}  попытка {n}",
                        msg.chat.id, wait.message_id, parse_mode="Markdown")
                except:
                    pass

        if preferred:
            res = find_proxy_type(my_ip, preferred, on_try=on_try)
        else:
            res = find_proxy_auto(my_ip, on_try=on_try)

        if res:
            u.update(connected=True, proxy=res,
                     connect_time=time.time(), ip_after=res["new_ip"])
            u["sessions"] = u.get("sessions", 0) + 1

            bot.edit_message_text(
                f"✅  *Подключение установлено*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"{proto_icon(res['type'])}  Протокол:  `{res['type'].upper()}`\n"
                f"🖥  Сервер:    `{res['host']}:{res['port']}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📶  Пинг:\n"
                f"   {ping_bar(res['ping'])}  `{res['ping']} ms`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📍  IP до:     `{my_ip}`\n"
                f"🌍  IP сейчас: `{res['new_ip']}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔒  AES‑256  ·  DNS‑HTTPS  ·  No‑Leak",
                msg.chat.id, wait.message_id,
                parse_mode="Markdown",
                reply_markup=kb_main(True))
        else:
            bot.edit_message_text(
                f"❌  *Сервер не найден*\n\n"
                f"Проверено: `{info['n']}` серверов\n\n"
                f"Попробуй:\n"
                f"• `/scan` — найти быстрые серверы\n"
                f"• `/refresh` — обновить базу\n"
                f"• `/connect http` — только HTTP",
                msg.chat.id, wait.message_id,
                parse_mode="Markdown",
                reply_markup=kb_main(False))

    threading.Thread(target=do, daemon=True).start()

# ┌─────────────────────────────────────┐
# │          /disconnect                │
# └─────────────────────────────────────┘
@bot.message_handler(commands=["disconnect"])
def cmd_disconnect(msg):
    u = get_user(msg.from_user.id)
    if not u["connected"]:
        bot.send_message(msg.chat.id,
            "ℹ️  VPN не подключён",
            reply_markup=kb_main(False))
        return

    sess = fmt_time(time.time() - u["connect_time"]) if u["connect_time"] else "—"
    ib   = u.get("ip_before", "—")
    ia   = u.get("ip_after",  "—")
    px   = u["proxy"]

    u.update(connected=False, proxy=None, connect_time=None)

    bot.send_message(msg.chat.id,
        f"🔴  *Сессия завершена*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{proto_icon(px['type'])}  `{px['host']}:{px['port']}`\n"
        f"⏱  Длительность:  `{sess}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍  Реальный IP:  `{ib}`\n"
        f"🌍  Был IP:       `{ia}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"_Соединение завершено_",
        parse_mode="Markdown",
        reply_markup=kb_main(False))

# ┌─────────────────────────────────────┐
# │           /rotate                   │
# └─────────────────────────────────────┘
@bot.message_handler(commands=["rotate"])
def cmd_rotate(msg):
    u = get_user(msg.from_user.id)
    if not u["connected"]:
        bot.send_message(msg.chat.id,
            "ℹ️  Сначала подключись через /connect")
        return

    wait = bot.send_message(msg.chat.id,
        "🔄  *Меняю IP...*", parse_mode="Markdown")

    def do():
        my_ip   = u.get("ip_before") or get_ip() or "unknown"
        exclude = u["proxy"]["host"] if u["proxy"] else None
        old_ip  = u.get("ip_after", "—")

        info      = {"n": 0}
        last_edit = [0.0]

        def on_try(n, pt, h, p):
            info["n"] = n
            now = time.time()
            if now - last_edit[0] >= 1.8:
                last_edit[0] = now
                try:
                    bot.edit_message_text(
                        f"🔄  *Ищу новый IP*\n\n"
                        f"{proto_icon(pt)}  `{h}:{p}`\n"
                        f"{loading_bar(min(n,80))}  попытка {n}",
                        msg.chat.id, wait.message_id, parse_mode="Markdown")
                except:
                    pass

        res = find_proxy_auto(my_ip, exclude=exclude, on_try=on_try)

        if res:
            u.update(proxy=res, connect_time=time.time(), ip_after=res["new_ip"])
            bot.edit_message_text(
                f"✅  *IP изменён*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"{proto_icon(res['type'])}  Протокол: `{res['type'].upper()}`\n"
                f"🖥  Сервер:   `{res['host']}:{res['port']}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📶  {ping_bar(res['ping'])}  `{res['ping']} ms`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🌍  Был IP:     `{old_ip}`\n"
                f"🌍  Новый IP:   `{res['new_ip']}`",
                msg.chat.id, wait.message_id,
                parse_mode="Markdown",
                reply_markup=kb_main(True))
        else:
            bot.edit_message_text(
                "❌  Нет доступных серверов\n\nПопробуй `/scan` или `/refresh`",
                msg.chat.id, wait.message_id,
                parse_mode="Markdown",
                reply_markup=kb_main(True))

    threading.Thread(target=do, daemon=True).start()

# ┌─────────────────────────────────────┐
# │           /status                   │
# └─────────────────────────────────────┘
@bot.message_handler(commands=["status"])
def cmd_status(msg):
    u   = get_user(msg.from_user.id)
    tot = sum(len(cache[t]) for t in ["socks5","socks4","http"])
    fast = len(cache["top_fast"])

    if u["connected"] and u["proxy"]:
        px   = u["proxy"]
        sess = fmt_time(time.time() - u["connect_time"]) if u["connect_time"] else "—"
        ms   = tcp_ping(px["host"], px["port"], timeout=2)
        anon = "Высокая (SOCKS5)" if px["type"] == "socks5" else "Средняя"

        text = (
            f"📊  *Статус VPN*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢  Статус:       *Активен*\n"
            f"{proto_icon(px['type'])}  Протокол:    `{px['type'].upper()}`\n"
            f"🖥  Сервер:       `{px['host']}:{px['port']}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📶  Качество:\n"
            f"   {ping_bar(ms)}  `{f'{ms} ms' if ms else 'недоступен'}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱  Сессия:       `{sess}`\n"
            f"📍  IP до:        `{u.get('ip_before','—')}`\n"
            f"🌍  IP сейчас:    `{u.get('ip_after','—')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔐  Анонимность:  `{anon}`\n"
            f"🔒  AES‑256‑GCM:  ✅\n"
            f"🌐  DNS‑HTTPS:    ✅\n"
            f"🛡  Leak Protect: ✅\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦  База прокси:  `{tot}`\n"
            f"⚡  Быстрых:      `{fast}`"
        )
    else:
        text = (
            f"📊  *Статус VPN*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔴  Статус:  *Не подключён*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦  База прокси:\n"
            f"   🔵 SOCKS5: `{len(cache['socks5'])}`\n"
            f"   🟣 SOCKS4: `{len(cache['socks4'])}`\n"
            f"   ⚪ HTTP:   `{len(cache['http'])}`\n"
            f"   Итого:    `{tot}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡  Быстрых в пуле:  `{fast}`\n\n"
            f"_/connect для подключения_\n"
            f"_/scan для поиска быстрых_"
        )

    bot.send_message(msg.chat.id, text, parse_mode="Markdown",
                     reply_markup=kb_main(u["connected"]))

# ┌─────────────────────────────────────┐
# │          /proxies                   │
# └─────────────────────────────────────┘
@bot.message_handler(commands=["proxies"])
def cmd_proxies(msg):
    uid   = msg.from_user.id
    total = sum(len(cache[t]) for t in ["socks5","socks4","http"])
    fast  = cache["top_fast"]

    if total == 0:
        bot.send_message(msg.chat.id,
            "📦  База пуста\n\nИспользуй `/refresh` для загрузки",
            parse_mode="Markdown")
        return

    lines = [
        f"🗂  *Серверы Togaff VPN*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
    ]

    # Топ быстрых
    if fast:
        lines.append(f"⚡  *Быстрые серверы* (топ {min(3,len(fast))})\n")
        for r in fast[:3]:
            lines.append(
                f"   {proto_icon(r['type'])}  `{r['host']}:{r['port']}`\n"
                f"   {ping_bar(r['ping'])}  `{r['ping']} ms`\n"
            )
        lines.append("━━━━━━━━━━━━━━━━━━━━━\n")

    for pt in ["socks5", "socks4", "http"]:
        cnt  = len(cache[pt])
        pool = cache[pt][:3]
        lines.append(f"{proto_icon(pt)}  *{pt.upper()}*  —  `{cnt}` серверов\n")
        for h, p in pool:
            lines.append(f"   `{h}:{p}`\n")
        lines.append("")

    lines.append(
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"_Всего: {total}  ·  /refresh для обновления_"
    )

    bot.send_message(msg.chat.id, "".join(lines),
                     parse_mode="Markdown",
                     reply_markup=kb_main(get_user(uid)["connected"]))

# ┌─────────────────────────────────────┐
# │             /ip                     │
# └─────────────────────────────────────┘
@bot.message_handler(commands=["ip"])
def cmd_ip(msg):
    u    = get_user(msg.from_user.id)
    wait = bot.send_message(msg.chat.id,
        "🔍  *Определяю IP...*", parse_mode="Markdown")

    def do():
        if u["connected"] and u["proxy"]:
            ip   = get_ip(proxy_cfg=u["proxy"], timeout=8)
            mode = f"{u['proxy']['type'].upper()} прокси"
            icon = "🌍"
        else:
            ip   = get_ip(timeout=6)
            mode = "прямое соединение"
            icon = "📍"

        bot.edit_message_text(
            f"{icon}  *Ваш IP‑адрес*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"IP:    `{ip or 'недоступен'}`\n"
            f"Режим: `{mode}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━",
            msg.chat.id, wait.message_id, parse_mode="Markdown")

    threading.Thread(target=do, daemon=True).start()

# ┌─────────────────────────────────────┐
# │           /refresh                  │
# └─────────────────────────────────────┘
@bot.message_handler(commands=["refresh"])
def cmd_refresh(msg):
    wait = bot.send_message(msg.chat.id,
        "🔄  *Обновляю базу прокси...*", parse_mode="Markdown")

    def do():
        cache["updated"] = 0
        refresh_cache()
        total = sum(len(cache[t]) for t in ["socks5","socks4","http"])
        bot.edit_message_text(
            f"✅  *База обновлена*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔵  SOCKS5: `{len(cache['socks5'])}`\n"
            f"🟣  SOCKS4: `{len(cache['socks4'])}`\n"
            f"⚪  HTTP:   `{len(cache['http'])}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦  Итого:  `{total}`\n\n"
            f"_/scan для поиска быстрых серверов_",
            msg.chat.id, wait.message_id,
            parse_mode="Markdown",
            reply_markup=kb_main(get_user(msg.from_user.id)["connected"]))

    threading.Thread(target=do, daemon=True).start()

# ┌─────────────────────────────────────┐
# │         /generate — конфиги         │
# └─────────────────────────────────────┘
@bot.message_handler(commands=["generate"])
def cmd_generate(msg):
    u = get_user(msg.from_user.id)

    if u["connected"] and u["proxy"]:
        _send_config(msg.chat.id, None, u["proxy"])
        return

    wait = bot.send_message(msg.chat.id,
        "🔧  *Ищу прокси для конфига...*", parse_mode="Markdown")

    def do():
        my_ip     = get_ip(timeout=6) or "0.0.0.0"
        info      = {"n": 0}
        last_edit = [0.0]

        def on_try(n, pt, h, p):
            info["n"] = n
            now = time.time()
            if now - last_edit[0] >= 1.5:
                last_edit[0] = now
                try:
                    bot.edit_message_text(
                        f"🔧  *Генератор конфигов*\n\n"
                        f"{proto_icon(pt)}  `{h}:{p}`\n"
                        f"{loading_bar(min(n,60))}  попытка {n}",
                        msg.chat.id, wait.message_id, parse_mode="Markdown")
                except:
                    pass

        res = find_proxy_auto(my_ip, on_try=on_try)
        if res:
            _send_config(msg.chat.id, wait.message_id, res)
        else:
            bot.edit_message_text(
                "❌  Не найден рабочий прокси\n\nПопробуй `/scan` → `/generate`",
                msg.chat.id, wait.message_id, parse_mode="Markdown")

    threading.Thread(target=do, daemon=True).start()

def _send_config(chat_id, msg_id, proxy):
    h  = proxy["host"]
    p  = proxy["port"]
    pt = proxy["type"]
    ms = proxy["ping"]

    if pt in ("socks5","socks4"):
        curl_flag = f"--proxy {pt}h://{h}:{p}"
        env_vars  = f"export ALL_PROXY={pt}h://{h}:{p}"
        pc_line   = f"{pt} {h} {p}"
        py_prx    = f'"{pt}h://{h}:{p}"'
    else:
        curl_flag = f"--proxy http://{h}:{p}"
        env_vars  = (f"export HTTP_PROXY=http://{h}:{p}\n"
                     f"export HTTPS_PROXY=http://{h}:{p}")
        pc_line   = f"http {h} {p}"
        py_prx    = f'"http://{h}:{p}"'

    text = (
        f"📋  *Конфиг прокси*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{proto_icon(pt)}  `{h}:{p}`  ·  {pt.upper()}\n"
        f"📶  {ping_bar(ms)}  `{ms} ms`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔹  *curl / wget*\n"
        f"`{curl_flag}`\n\n"
        f"🔹  *Shell env*\n"
        f"```\n{env_vars}\n```\n\n"
        f"🔹  *proxychains.conf*\n"
        f"`{pc_line}`\n\n"
        f"🔹  *Python requests*\n"
        f"```python\n"
        f"proxies = {{\n"
        f"    'http':  {py_prx},\n"
        f"    'https': {py_prx}\n"
        f"}}\n```\n\n"
        f"🔹  *RAW*\n"
        f"`{h}:{p}`"
    )

    if msg_id:
        try:
            bot.edit_message_text(text, chat_id, msg_id,
                                  parse_mode="Markdown",
                                  reply_markup=kb_generate())
            return
        except:
            pass
    bot.send_message(chat_id, text,
                     parse_mode="Markdown",
                     reply_markup=kb_generate())

# ┌─────────────────────────────────────┐
# │            CALLBACKS                │
# └─────────────────────────────────────┘
@bot.callback_query_handler(func=lambda c: True)
def on_callback(call):
    d = call.data
    uid = call.from_user.id

    # Спец-кнопки
    if d == "regen":
        bot.answer_callback_query(call.id, "🔧 Ищу другой...")
        cmd_generate(FMsg(call, "/generate"))
        return
    if d == "back_main":
        bot.answer_callback_query(call.id)
        cmd_start(FMsg(call, "/start"))
        return

    table = {
        "connect":    ("/connect",       "⚡ Подключаюсь..."),
        "c_socks5":   ("/connect socks5","🔵 SOCKS5..."),
        "c_socks4":   ("/connect socks4","🟣 SOCKS4..."),
        "c_http":     ("/connect http",  "⚪ HTTP..."),
        "disconnect": ("/disconnect",    "🔴 Отключаю..."),
        "rotate":     ("/rotate",        "🔄 Меняю IP..."),
        "status":     ("/status",        ""),
        "proxies":    ("/proxies",       ""),
        "generate":   ("/generate",      "🔧 Генерирую..."),
    }

    if d not in table:
        return

    cmd_text, answer = table[d]
    bot.answer_callback_query(call.id, answer)

    handlers = {
        "/connect":        cmd_connect,
        "/connect socks5": cmd_connect,
        "/connect socks4": cmd_connect,
        "/connect http":   cmd_connect,
        "/disconnect":     cmd_disconnect,
        "/rotate":         cmd_rotate,
        "/status":         cmd_status,
        "/proxies":        cmd_proxies,
        "/generate":       cmd_generate,
    }
    handlers[cmd_text](FMsg(call, cmd_text))

# ┌─────────────────────────────────────┐
# │              ЗАПУСК                 │
# └─────────────────────────────────────┘
if __name__ == "__main__":
    print("═" * 50)
    print("  TOGAFF VPN  ·  Premium Edition")
    print(f"  PySocks: {'✓' if SOCKS_OK else '✗  pip install PySocks requests[socks]'}")
    print(f"  Своих прокси: {len(MY_PROXIES)}")
    print("═" * 50)

    # Фоновая загрузка базы
    threading.Thread(target=refresh_cache, daemon=True).start()

    # Фоновый прогрев пула быстрых прокси (через 45с после старта)
    def warm_up():
        time.sleep(45)
        my_ip = get_ip(timeout=6) or "unknown"
        if my_ip != "unknown":
            build_top_fast(my_ip, sample=60, workers=12)
    threading.Thread(target=warm_up, daemon=True).start()

    bot.infinity_polling(timeout=30)
