import telebot
import requests
import socket
import threading
import time
import random
import re
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ══════════════════════════════════════════════════════
#                    КОНФИГУРАЦИЯ
# ══════════════════════════════════════════════════════

TOKEN        = "8603769389:AAFNrImTZhMY0ctceejoFbNkosE54cNsE30"
MINI_APP_URL = "https://t.me/togaff_vpn_bot/app"

# ─── Администратор (твой Telegram ID) ─────────────────
ADMIN_IDS = {7321093872}   # ← сюда свой ID (узнать: @userinfobot)

# ─── Файлы для сохранения данных ──────────────────────
USERS_FILE  = "allowed_users.json"   # whitelist
BANNED_FILE = "banned_users.json"    # чёрный список

# ─── Параметры движка прокси ──────────────────────────
TOP_FAST_COUNT  = 50    # сколько лучших держим в горячем пуле
VERIFY_WORKERS  = 20    # потоков при параллельной проверке
SCAN_SAMPLE     = 120   # кандидатов для /scan
VERIFY_LIMIT    = 200   # макс попыток при /connect

# ─── Стикер на /start ─────────────────────────────────
WELCOME_STICKER = "CAACAgIAAxkBAAIBcWZ5X2QAAf3yYW9YcgABfBiXp7CRAAJ4AQACB8ShS1kN6VrwzFjRNgQ"

try:
    import socks        # PySocks
    SOCKS_OK = True
except ImportError:
    SOCKS_OK = False

bot = telebot.TeleBot(TOKEN, parse_mode=None)

# ══════════════════════════════════════════════════════
#             УПРАВЛЕНИЕ ДОСТУПОМ (WHITELIST)
# ══════════════════════════════════════════════════════

def _load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except:
        pass
    return default

def _save_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

# allowed_users = {uid: {"username":..., "first_name":..., "added":..., "uses":0}}
allowed_users: dict = _load_json(USERS_FILE, {})
banned_users:  set  = set(_load_json(BANNED_FILE, []))

_save_lock = threading.Lock()

def save_users():
    with _save_lock:
        _save_json(USERS_FILE,  {str(k): v for k, v in allowed_users.items()})
        _save_json(BANNED_FILE, list(banned_users))

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

def is_allowed(uid: int) -> bool:
    if is_admin(uid):
        return True
    if uid in banned_users:
        return False
    return str(uid) in allowed_users or uid in allowed_users

def _uid_key(uid):
    """Возвращает ключ из allowed_users или None."""
    if str(uid) in allowed_users:
        return str(uid)
    if uid in allowed_users:
        return uid
    return None

# Декоратор: проверяет доступ перед выполнением
def access_required(fn):
    def wrapper(msg_or_call, *args, **kwargs):
        if hasattr(msg_or_call, "from_user"):
            uid  = msg_or_call.from_user.id
            chat = msg_or_call.chat.id if hasattr(msg_or_call, "chat") else msg_or_call.message.chat.id
        else:
            uid  = msg_or_call.id
            chat = msg_or_call.id
        if not is_allowed(uid):
            bot.send_message(chat,
                "🔒  *Доступ закрыт*\n\n"
                "Этот бот работает только по приглашению.\n"
                "Обратись к администратору для получения доступа.",
                parse_mode="Markdown")
            return
        return fn(msg_or_call, *args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

# ══════════════════════════════════════════════════════
#                  СВОИ ПРОКСИ
# ══════════════════════════════════════════════════════

MY_PROXIES_HTTP = [
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

# ══════════════════════════════════════════════════════
#               ИСТОЧНИКИ ПРОКСИ
# ══════════════════════════════════════════════════════

SOURCES = {
    "socks5": [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks5.txt",
    ],
    "socks4": [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks4/data.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks4.txt",
    ],
    "http": [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
        "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
        "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
    ],
}

# ══════════════════════════════════════════════════════
#                     КЭШ
# ══════════════════════════════════════════════════════

cache = {
    "socks5": [], "socks4": [], "http": [],
    "updated": 0,
    "top_fast": [],      # отсортированный пул лучших (всегда актуален)
    "top_updated": 0,
    "scan_lock": threading.Lock(),
}
CACHE_TTL    = 1800
TOP_TTL      = 900     # пул быстрых протухает через 15 мин

users = {}

def get_user(uid):
    if uid not in users:
        users[uid] = {
            "connected": False, "proxy": None,
            "connect_time": None, "ip_before": None, "ip_after": None,
            "sessions": 0, "total_rotates": 0,
        }
    return users[uid]

# ══════════════════════════════════════════════════════
#               ЗАГРУЗКА И КЭШ ПРОКСИ
# ══════════════════════════════════════════════════════

def fetch_list(url, timeout=14):
    try:
        r = requests.get(url, timeout=timeout,
                         headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return []
        out = []
        for line in r.text.splitlines():
            # поддержка форматов: ip:port, socks5://ip:port
            line = re.sub(r"^(socks[45]|https?|connect)://", "", line.strip(), flags=re.I)
            m = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})", line)
            if m:
                out.append((m.group(1), int(m.group(2))))
        return out
    except:
        return []

def refresh_cache(force=False):
    if not force and time.time() - cache["updated"] < CACHE_TTL:
        return
    print("⟳  Загружаю списки прокси...")

    my_seen = {f"{h}:{p}" for h, p in MY_PROXIES_HTTP}
    my_list = list(MY_PROXIES_HTTP)

    with ThreadPoolExecutor(max_workers=8) as ex:
        for ptype, urls in SOURCES.items():
            base = list(my_list) if ptype == "http" else []
            seen = set(my_seen)  if ptype == "http" else set()

            futs = {ex.submit(fetch_list, url): url for url in urls}
            for fut in as_completed(futs):
                for h, p in fut.result():
                    k = f"{h}:{p}"
                    if k not in seen:
                        seen.add(k)
                        base.append((h, p))
                if len(base) >= 800:
                    break

            if ptype == "http":
                tail = base[len(my_list):]
                random.shuffle(tail)
                cache[ptype] = (my_list + tail)[:500]
            else:
                random.shuffle(base)
                cache[ptype] = base[:500]
            print(f"   {ptype}: {len(cache[ptype])}")

    cache["updated"] = time.time()
    print("✓  Кэш обновлён")

# ══════════════════════════════════════════════════════
#          ПРОВЕРКА ПРОКСИ — УМНЫЙ ДВИЖОК
# ══════════════════════════════════════════════════════

IP_CHECK_URLS = [
    "http://api.ipify.org",
    "http://checkip.amazonaws.com",
    "http://icanhazip.com",
    "http://ip.42.pl/raw",
    "http://ipecho.net/plain",
]

def tcp_ping(host, port, timeout=2.5):
    try:
        t0 = time.time()
        with socket.create_connection((host, port), timeout=timeout):
            return round((time.time() - t0) * 1000, 1)
    except:
        return None

def _proxy_cfg_to_requests(ptype, host, port):
    """Возвращает словарь proxies= для requests."""
    if ptype == "socks5" and SOCKS_OK:
        u = f"socks5h://{host}:{port}"
    elif ptype == "socks4" and SOCKS_OK:
        u = f"socks4://{host}:{port}"
    elif ptype == "https":
        u = f"https://{host}:{port}"
    else:
        u = f"http://{host}:{port}"
    return {"http": u, "https": u}

def get_ip_via(ptype, host, port, timeout=9):
    """Получить IP через конкретный прокси. Пробует несколько URL."""
    proxies = _proxy_cfg_to_requests(ptype, host, port)
    for url in IP_CHECK_URLS:
        try:
            r = requests.get(url, proxies=proxies, timeout=timeout,
                             headers={"User-Agent": "curl/7.80.0"})
            ip = r.text.strip().split()[0]
            if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", ip):
                return ip
        except:
            continue
    return None

def get_my_ip(timeout=7):
    for url in IP_CHECK_URLS:
        try:
            r = requests.get(url, timeout=timeout)
            ip = r.text.strip().split()[0]
            if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", ip):
                return ip
        except:
            continue
    return None

def verify_proxy(ptype, host, port, my_ip,
                 tcp_timeout=2.5, ip_timeout=9):
    """
    Полная верификация:
    1) TCP пинг (быстро)
    2) Реальный HTTP запрос через прокси → получаем новый IP
    3) Проверяем что IP изменился (не прозрачный прокси)
    Возвращает dict или None.
    """
    ms = tcp_ping(host, port, timeout=tcp_timeout)
    if ms is None:
        return None

    new_ip = get_ip_via(ptype, host, port, timeout=ip_timeout)
    if not new_ip:
        return None
    if my_ip and new_ip == my_ip:
        return None   # прозрачный прокси — пропускаем

    return {
        "type":   ptype,
        "host":   host,
        "port":   port,
        "ping":   ms,
        "new_ip": new_ip,
        "verified_at": time.time(),
    }

# ══════════════════════════════════════════════════════
#         СМАРТ-ПУЛ: авто-выбор быстрых прокси
# ══════════════════════════════════════════════════════

def _candidates_for_scan(sample):
    """Собирает кандидатов из всех протоколов для параллельной проверки."""
    order = (["socks5", "socks4", "http"] if SOCKS_OK
             else ["http", "socks4", "socks5"])
    per = max(sample // len(order), 10)
    cands = []
    for pt in order:
        pool = list(cache[pt])
        random.shuffle(pool)
        for h, p in pool[:per]:
            cands.append((pt, h, p))
    random.shuffle(cands)
    return cands

def build_smart_pool(my_ip=None, sample=SCAN_SAMPLE,
                     workers=VERIFY_WORKERS, status_cb=None):
    """
    Параллельно проверяет sample прокси.
    Обновляет cache["top_fast"] отсортированным по пингу списком.
    status_cb(done, total) — опциональный callback прогресса.
    """
    if my_ip is None:
        my_ip = get_my_ip() or ""

    refresh_cache()
    cands  = _candidates_for_scan(sample)
    total  = len(cands)
    done   = 0
    lock   = threading.Lock()
    results = []

    def check(args):
        nonlocal done
        pt, h, p = args
        r = verify_proxy(pt, h, p, my_ip, tcp_timeout=2.0, ip_timeout=7)
        with lock:
            done += 1
            if status_cb:
                status_cb(done, total)
        return r

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for res in as_completed([ex.submit(check, c) for c in cands]):
            r = res.result()
            if r:
                results.append(r)

    results.sort(key=lambda x: x["ping"])
    cache["top_fast"]    = results[:TOP_FAST_COUNT]
    cache["top_updated"] = time.time()
    print(f"✓  Смарт-пул: {len(cache['top_fast'])} прокси")
    return cache["top_fast"]

def smart_pool_fresh(my_ip=""):
    """Перестраивает пул если он устарел."""
    if time.time() - cache["top_updated"] > TOP_TTL:
        if not cache["scan_lock"].locked():
            def bg():
                with cache["scan_lock"]:
                    build_smart_pool(my_ip)
            threading.Thread(target=bg, daemon=True).start()

def find_best_proxy(my_ip, exclude_host=None, on_try=None,
                    ptype_filter=None):
    """
    Главная функция поиска:
    1) Берём из top_fast (проверенные, отсортированные по пингу)
    2) Дополняем полным перебором если не хватает
    Гарантирует настоящую смену IP.
    """
    # ── Шаг 1: из горячего пула ──────────────────────
    pool = [p for p in cache["top_fast"]
            if (not exclude_host or p["host"] != exclude_host)
            and (not ptype_filter or p["type"] == ptype_filter)]
    for px in pool:
        # Перепроверяем (мог протухнуть)
        r = verify_proxy(px["type"], px["host"], px["port"],
                         my_ip, tcp_timeout=2.0, ip_timeout=8)
        if r:
            return r

    # ── Шаг 2: полный перебор ────────────────────────
    refresh_cache()
    order = (["socks5", "socks4", "http"] if SOCKS_OK
             else ["http", "socks4", "socks5"])
    if ptype_filter:
        order = [ptype_filter]

    n = 0
    for pt in order:
        raw = list(cache[pt])
        random.shuffle(raw)
        for host, port in raw:
            if n >= VERIFY_LIMIT:
                return None
            if exclude_host and host == exclude_host:
                continue
            n += 1
            if on_try:
                on_try(n, pt, host, port)
            r = verify_proxy(pt, host, port, my_ip)
            if r:
                return r
    return None

# ══════════════════════════════════════════════════════
#                    УТИЛИТЫ UI
# ══════════════════════════════════════════════════════

def fmt_time(s):
    h  = int(s // 3600)
    m  = int((s % 3600) // 60)
    sc = int(s % 60)
    if h:   return f"{h}ч {m:02d}м {sc:02d}с"
    if m:   return f"{m}м {sc:02d}с"
    return  f"{sc}с"

def ping_bar(ms):
    if ms is None:    return "⬜⬜⬜⬜⬜  нет данных"
    if ms < 80:       return "🟩🟩🟩🟩🟩  молниеносно"
    if ms < 150:      return "🟩🟩🟩🟩⬜  отлично"
    if ms < 250:      return "🟨🟨🟨⬜⬜  хорошо"
    if ms < 400:      return "🟧🟧⬜⬜⬜  средне"
    return                   "🟥⬜⬜⬜⬜  медленно"

def proto_icon(pt):
    return {"socks5": "🔵", "socks4": "🟣", "http": "⚪", "https": "🔐"}.get(pt, "⚫")

def loading_bar(n, total=100, w=10):
    f = min(int(w * n / max(total, 1)), w)
    return "▰" * f + "▱" * (w - f)

def ts():
    return datetime.now().strftime("%d.%m %H:%M")

# ══════════════════════════════════════════════════════
#                    КЛАВИАТУРЫ
# ══════════════════════════════════════════════════════

def kb_main(connected=False):
    k = telebot.types.InlineKeyboardMarkup(row_width=2)
    if connected:
        k.add(
            telebot.types.InlineKeyboardButton("🔴  Отключить",   callback_data="disconnect"),
            telebot.types.InlineKeyboardButton("🔄  Сменить IP",  callback_data="rotate"),
        )
        k.add(
            telebot.types.InlineKeyboardButton("📋  Конфиг",      callback_data="generate"),
            telebot.types.InlineKeyboardButton("📊  Статус",      callback_data="status"),
        )
    else:
        k.add(telebot.types.InlineKeyboardButton(
            "⚡  Быстрое подключение", callback_data="connect"))
        k.add(
            telebot.types.InlineKeyboardButton("📊  Статус",      callback_data="status"),
            telebot.types.InlineKeyboardButton("🗂  Серверы",     callback_data="proxies"),
        )
    k.add(
        telebot.types.InlineKeyboardButton("🔵 SOCKS5", callback_data="c_socks5"),
        telebot.types.InlineKeyboardButton("🟣 SOCKS4",  callback_data="c_socks4"),
        telebot.types.InlineKeyboardButton("⚪ HTTP",    callback_data="c_http"),
    )
    k.add(telebot.types.InlineKeyboardButton(
        "🌐  Веб-панель",
        web_app=telebot.types.WebAppInfo(url=MINI_APP_URL)))
    return k

def kb_generate():
    k = telebot.types.InlineKeyboardMarkup(row_width=1)
    k.add(telebot.types.InlineKeyboardButton("🔄  Другой прокси",  callback_data="regen"))
    k.add(telebot.types.InlineKeyboardButton("◀  Главное меню",    callback_data="back_main"))
    return k

def kb_admin():
    k = telebot.types.InlineKeyboardMarkup(row_width=2)
    k.add(
        telebot.types.InlineKeyboardButton("👥  Пользователи",    callback_data="adm_users"),
        telebot.types.InlineKeyboardButton("🚫  Бан-лист",        callback_data="adm_banned"),
    )
    k.add(
        telebot.types.InlineKeyboardButton("📊  Статистика",      callback_data="adm_stats"),
        telebot.types.InlineKeyboardButton("🔄  Обновить базу",   callback_data="adm_refresh"),
    )
    k.add(
        telebot.types.InlineKeyboardButton("⚡  Запустить скан",  callback_data="adm_scan"),
        telebot.types.InlineKeyboardButton("📢  Рассылка",        callback_data="adm_broadcast"),
    )
    k.add(telebot.types.InlineKeyboardButton("◀  Назад",          callback_data="back_main"))
    return k

def kb_user_actions(uid):
    k = telebot.types.InlineKeyboardMarkup(row_width=2)
    k.add(
        telebot.types.InlineKeyboardButton("🚫  Забанить",   callback_data=f"ban_{uid}"),
        telebot.types.InlineKeyboardButton("❌  Удалить",    callback_data=f"del_{uid}"),
    )
    k.add(telebot.types.InlineKeyboardButton("◀  Назад",    callback_data="adm_users"))
    return k

class FMsg:
    """Псевдо-сообщение для вызова обработчиков из callback."""
    def __init__(self, call, text=""):
        self.chat      = type("C", (), {"id": call.message.chat.id})()
        self.from_user = type("U", (), {
            "id":         call.from_user.id,
            "first_name": call.from_user.first_name or "User",
            "username":   getattr(call.from_user, "username", None),
        })()
        self.text = text

# ══════════════════════════════════════════════════════
#                     /start
# ══════════════════════════════════════════════════════

@bot.message_handler(commands=["start"])
def cmd_start(msg):
    uid  = msg.from_user.id
    name = msg.from_user.first_name or "Гость"

    # Регистрация в whitelist если это admin
    if is_admin(uid):
        key = str(uid)
        if key not in allowed_users:
            allowed_users[key] = {
                "username":   getattr(msg.from_user, "username", ""),
                "first_name": name,
                "added":      ts(),
                "uses":       0,
            }
            save_users()

    if not is_allowed(uid):
        bot.send_message(msg.chat.id,
            "🔒  *Доступ закрыт*\n\n"
            "Этот бот работает только по приглашению.\n"
            "Напиши администратору и попроси добавить тебя.",
            parse_mode="Markdown")
        return

    # Инкрементируем счётчик использований
    key = _uid_key(uid)
    if key and key in allowed_users:
        allowed_users[key]["uses"] = allowed_users[key].get("uses", 0) + 1
        save_users()

    u     = get_user(uid)
    total = sum(len(cache[t]) for t in ["socks5","socks4","http"])
    fast  = len(cache["top_fast"])
    admin_badge = "  👑 *Администратор*\n" if is_admin(uid) else ""

    conn_line = (
        f"🟢  *Подключён* — `{u['proxy']['host']}`  {proto_icon(u['proxy']['type'])}"
        if u["connected"] and u["proxy"]
        else "🔴  *Не подключён*"
    )

    text = (
        f"👋  *Привет, {name}!*\n"
        f"{admin_badge}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡  *Togaff VPN*  ·  Ultimate\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{conn_line}\n\n"
        f"📦  Прокси в базе:    `{total}`\n"
        f"⚡  Лучших в пуле:   `{fast}`\n"
        f"🔒  Протоколы:  SOCKS5 · SOCKS4 · HTTP\n"
        f"✅  Верификация:  реальная смена IP\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋  *Команды*\n"
        f"`/connect`      — авто-подключение\n"
        f"`/connect s5`   — только SOCKS5\n"
        f"`/connect s4`   — только SOCKS4\n"
        f"`/connect http` — только HTTP\n"
        f"`/disconnect`   — отключиться\n"
        f"`/rotate`       — сменить IP\n"
        f"`/scan`         — найти быстрые серверы\n"
        f"`/status`       — текущий статус\n"
        f"`/ip`           — мой IP\n"
        f"`/generate`     — конфиг прокси\n"
        f"`/proxies`      — список серверов\n"
        f"`/refresh`      — обновить базу\n"
        + (f"`/admin`        — панель администратора\n" if is_admin(uid) else "")
    )

    try:
        bot.send_sticker(msg.chat.id, WELCOME_STICKER)
    except:
        pass

    bot.send_message(msg.chat.id, text,
                     parse_mode="Markdown",
                     reply_markup=kb_main(u["connected"]))

# ══════════════════════════════════════════════════════
#               ПАНЕЛЬ АДМИНИСТРАТОРА
# ══════════════════════════════════════════════════════

def _admin_main_text():
    total  = sum(len(cache[t]) for t in ["socks5","socks4","http"])
    fast   = len(cache["top_fast"])
    online = sum(1 for u in users.values() if u.get("connected"))
    return (
        f"👑  *Панель администратора*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥  Пользователей:   `{len(allowed_users)}`\n"
        f"🚫  В бане:          `{len(banned_users)}`\n"
        f"🟢  Онлайн сейчас:  `{online}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦  База прокси:    `{total}`\n"
        f"⚡  Смарт-пул:      `{fast}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"_Выбери действие:_"
    )

@bot.message_handler(commands=["admin"])
def cmd_admin(msg):
    if not is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "🚫  Нет доступа")
        return
    bot.send_message(msg.chat.id, _admin_main_text(),
                     parse_mode="Markdown",
                     reply_markup=kb_admin())

# ─── Добавить пользователя ─────────────────────────
@bot.message_handler(commands=["add"])
def cmd_add(msg):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.strip().split()
    if len(parts) < 2:
        bot.send_message(msg.chat.id,
            "ℹ️  Использование:\n"
            "`/add <user_id>` или `/add <user_id> Имя`",
            parse_mode="Markdown")
        return
    try:
        target = int(parts[1])
    except ValueError:
        bot.send_message(msg.chat.id, "❌  Неверный ID")
        return

    if target in banned_users:
        banned_users.discard(target)

    name = " ".join(parts[2:]) if len(parts) > 2 else f"User {target}"
    key  = str(target)
    allowed_users[key] = {
        "username":   "",
        "first_name": name,
        "added":      ts(),
        "uses":       0,
        "added_by":   msg.from_user.id,
    }
    save_users()

    bot.send_message(msg.chat.id,
        f"✅  Пользователь добавлен\n\n"
        f"🆔 ID: `{target}`\n"
        f"👤 Имя: {name}",
        parse_mode="Markdown")

    # Уведомить самого пользователя
    try:
        bot.send_message(target,
            "✅  *Доступ открыт!*\n\n"
            "Тебя добавили в Togaff VPN.\n"
            "Напиши /start для начала работы.",
            parse_mode="Markdown")
    except:
        pass

# ─── Удалить пользователя ──────────────────────────
@bot.message_handler(commands=["remove"])
def cmd_remove(msg):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.strip().split()
    if len(parts) < 2:
        bot.send_message(msg.chat.id, "ℹ️  `/remove <user_id>`", parse_mode="Markdown")
        return
    try:
        target = int(parts[1])
    except:
        bot.send_message(msg.chat.id, "❌  Неверный ID")
        return

    key = str(target)
    if key in allowed_users:
        del allowed_users[key]
        save_users()
        bot.send_message(msg.chat.id, f"✅  Пользователь `{target}` удалён", parse_mode="Markdown")
    else:
        bot.send_message(msg.chat.id, f"ℹ️  Пользователь `{target}` не найден", parse_mode="Markdown")

# ─── Заблокировать ─────────────────────────────────
@bot.message_handler(commands=["ban"])
def cmd_ban(msg):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.strip().split()
    if len(parts) < 2:
        bot.send_message(msg.chat.id, "ℹ️  `/ban <user_id>`", parse_mode="Markdown")
        return
    try:
        target = int(parts[1])
    except:
        bot.send_message(msg.chat.id, "❌  Неверный ID")
        return

    banned_users.add(target)
    key = str(target)
    if key in allowed_users:
        del allowed_users[key]
    save_users()
    bot.send_message(msg.chat.id,
        f"🚫  Пользователь `{target}` заблокирован", parse_mode="Markdown")

# ─── Разблокировать ────────────────────────────────
@bot.message_handler(commands=["unban"])
def cmd_unban(msg):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.strip().split()
    if len(parts) < 2:
        bot.send_message(msg.chat.id, "ℹ️  `/unban <user_id>`", parse_mode="Markdown")
        return
    try:
        target = int(parts[1])
    except:
        bot.send_message(msg.chat.id, "❌  Неверный ID")
        return
    banned_users.discard(target)
    save_users()
    bot.send_message(msg.chat.id,
        f"✅  Пользователь `{target}` разблокирован", parse_mode="Markdown")

# ─── Список пользователей (команда) ────────────────
@bot.message_handler(commands=["users"])
def cmd_users(msg):
    if not is_admin(msg.from_user.id):
        return
    _send_users_list(msg.chat.id)

def _send_users_list(chat_id, msg_id=None):
    if not allowed_users:
        text = "👥  *Пользователи*\n\nСписок пуст"
    else:
        lines = [f"👥  *Пользователи* (`{len(allowed_users)}`)\n\n"
                 f"━━━━━━━━━━━━━━━━━━━━━\n"]
        for i, (uid, info) in enumerate(list(allowed_users.items())[:30], 1):
            uname = info.get("username", "")
            name  = info.get("first_name", "—")
            added = info.get("added", "—")
            uses  = info.get("uses", 0)
            online= "🟢" if users.get(int(uid), {}).get("connected") else "⚪"
            ustr  = f"@{uname}" if uname else f"`{uid}`"
            lines.append(f"{online}  {i}. {name} {ustr}\n"
                         f"     Добавлен: {added} · Сессий: {uses}\n")
        if len(allowed_users) > 30:
            lines.append(f"\n_...и ещё {len(allowed_users)-30}_")
        text = "".join(lines)

    k = telebot.types.InlineKeyboardMarkup()
    k.add(telebot.types.InlineKeyboardButton("◀  Назад", callback_data="adm_panel"))
    if msg_id:
        try:
            bot.edit_message_text(text, chat_id, msg_id, parse_mode="Markdown", reply_markup=k)
            return
        except:
            pass
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=k)

def _send_banned_list(chat_id, msg_id=None):
    if not banned_users:
        text = "🚫  *Бан-лист*\n\nСписок пуст"
    else:
        lines = [f"🚫  *Бан-лист* (`{len(banned_users)}`)\n\n"]
        for uid in list(banned_users)[:30]:
            lines.append(f"• `{uid}`\n")
        text = "".join(lines)
    k = telebot.types.InlineKeyboardMarkup()
    k.add(telebot.types.InlineKeyboardButton("◀  Назад", callback_data="adm_panel"))
    if msg_id:
        try:
            bot.edit_message_text(text, chat_id, msg_id, parse_mode="Markdown", reply_markup=k)
            return
        except:
            pass
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=k)

# ── Рассылка ────────────────────────────────────────
_broadcast_state = {}   # uid → ждём текст

@bot.message_handler(commands=["broadcast"])
def cmd_broadcast(msg):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.split(None, 1)
    if len(parts) < 2:
        _broadcast_state[msg.from_user.id] = True
        bot.send_message(msg.chat.id,
            "📢  Отправь текст рассылки следующим сообщением\n"
            "(или /cancel для отмены)")
        return
    _do_broadcast(msg.chat.id, parts[1])

def _do_broadcast(admin_chat, text):
    ok = fail = 0
    for uid_str in list(allowed_users.keys()):
        try:
            bot.send_message(int(uid_str),
                f"📢  *Сообщение от администратора*\n\n{text}",
                parse_mode="Markdown")
            ok += 1
        except:
            fail += 1
    bot.send_message(admin_chat,
        f"✅  Рассылка завершена\n✔ Доставлено: {ok}\n✖ Ошибок: {fail}")

# ══════════════════════════════════════════════════════
#                    /scan
# ══════════════════════════════════════════════════════

@bot.message_handler(commands=["scan"])
@access_required
def cmd_scan(msg):
    wait = bot.send_message(msg.chat.id,
        "🔍  *Сканирую серверы...*\n\n"
        f"{loading_bar(0)}  инициализация",
        parse_mode="Markdown")

    last = [0.0]

    def on_progress(done, total):
        now = time.time()
        if now - last[0] < 2:
            return
        last[0] = now
        pct = int(done * 100 / max(total, 1))
        try:
            bot.edit_message_text(
                f"🔍  *Сканирую серверы...*\n\n"
                f"{loading_bar(pct)}  {done}/{total} проверено",
                msg.chat.id, wait.message_id, parse_mode="Markdown")
        except:
            pass

    def do():
        my_ip   = get_my_ip() or ""
        results = build_smart_pool(my_ip, sample=SCAN_SAMPLE,
                                   status_cb=on_progress)
        if not results:
            bot.edit_message_text(
                "❌  *Серверы не найдены*\n\n"
                "Попробуй `/refresh` и повтори `/scan`",
                msg.chat.id, wait.message_id, parse_mode="Markdown")
            return

        lines = [f"⚡  *Смарт-пул готов* — {len(results)} серверов\n\n"
                 f"━━━━━━━━━━━━━━━━━━━━━\n"
                 f"*Топ-{min(5,len(results))}:*\n\n"]
        for i, r in enumerate(results[:5], 1):
            lines.append(
                f"{i}. {proto_icon(r['type'])}  `{r['host']}:{r['port']}`\n"
                f"    {ping_bar(r['ping'])}  `{r['ping']} ms`\n\n"
            )
        lines.append("━━━━━━━━━━━━━━━━━━━━━\n"
                     "_Используются автоматически при /connect_")
        bot.edit_message_text(
            "".join(lines), msg.chat.id, wait.message_id,
            parse_mode="Markdown",
            reply_markup=kb_main(get_user(msg.from_user.id)["connected"]))

    threading.Thread(target=do, daemon=True).start()

# ══════════════════════════════════════════════════════
#                   /connect
# ══════════════════════════════════════════════════════

@bot.message_handler(commands=["connect"])
@access_required
def cmd_connect(msg):
    uid  = msg.from_user.id
    u    = get_user(uid)

    parts = (msg.text or "").strip().split()
    raw   = parts[1].lower() if len(parts) > 1 else None
    # Алиасы протоколов
    aliases = {"s5": "socks5", "socks5": "socks5",
               "s4": "socks4", "socks4": "socks4",
               "http": "http",  "https": "http"}
    pfilter = aliases.get(raw) if raw else None

    if u["connected"]:
        px = u["proxy"]
        bot.send_message(msg.chat.id,
            f"✅  *Уже подключён*\n\n"
            f"{proto_icon(px['type'])}  `{px['host']}:{px['port']}`\n\n"
            f"• /rotate — сменить IP\n• /disconnect — отключиться",
            parse_mode="Markdown", reply_markup=kb_main(True))
        return

    wait = bot.send_message(msg.chat.id,
        "🔍  *Определяю ваш IP...*", parse_mode="Markdown")

    def do():
        my_ip = get_my_ip() or "unknown"
        u["ip_before"] = my_ip

        label = pfilter.upper() if pfilter else "АВТО"
        fast_n = len([p for p in cache["top_fast"]
                      if not pfilter or p["type"] == pfilter])
        mode_txt = (f"Режим: `{label}` · в пуле: `{fast_n}` серверов"
                    if fast_n else f"Режим: `{label}` · полный поиск")

        bot.edit_message_text(
            f"🔄  *Поиск сервера [{label}]*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍  Ваш IP: `{my_ip}`\n"
            f"{mode_txt}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{loading_bar(0)}  начинаю...",
            msg.chat.id, wait.message_id, parse_mode="Markdown")

        info      = {"n": 0, "last_h": ""}
        last_edit = [0.0]

        def on_try(n, pt, h, p):
            info["n"]    = n
            info["last_h"] = f"{h}:{p}"
            now = time.time()
            if now - last_edit[0] >= 1.6:
                last_edit[0] = now
                try:
                    bot.edit_message_text(
                        f"🔄  *Поиск сервера [{label}]*\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📍  Ваш IP: `{my_ip}`\n"
                        f"{proto_icon(pt)}  Тест: `{h}:{p}`\n"
                        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"{loading_bar(min(n, VERIFY_LIMIT), VERIFY_LIMIT)}"
                        f"  попытка {n}",
                        msg.chat.id, wait.message_id, parse_mode="Markdown")
                except:
                    pass

        res = find_best_proxy(my_ip, ptype_filter=pfilter, on_try=on_try)

        if res:
            u.update(connected=True, proxy=res,
                     connect_time=time.time(), ip_after=res["new_ip"])
            u["sessions"] = u.get("sessions", 0) + 1

            # Фоновое обновление пула
            smart_pool_fresh(my_ip)

            bot.edit_message_text(
                f"✅  *Подключение установлено*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"{proto_icon(res['type'])}  Протокол:  `{res['type'].upper()}`\n"
                f"🖥  Сервер:    `{res['host']}:{res['port']}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📶  Качество соединения:\n"
                f"    {ping_bar(res['ping'])}  `{res['ping']} ms`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📍  IP до:      `{my_ip}`\n"
                f"🌍  IP сейчас:  `{res['new_ip']}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔒  AES‑256  ·  DNS‑HTTPS  ·  NoLeak",
                msg.chat.id, wait.message_id,
                parse_mode="Markdown",
                reply_markup=kb_main(True))
        else:
            bot.edit_message_text(
                f"❌  *Сервер не найден*\n\n"
                f"Проверено: `{info['n']}` серверов\n\n"
                f"Попробуй:\n"
                f"• `/scan` — найти лучшие серверы\n"
                f"• `/refresh` — обновить базу\n"
                f"• `/connect http` — только HTTP",
                msg.chat.id, wait.message_id,
                parse_mode="Markdown",
                reply_markup=kb_main(False))

    threading.Thread(target=do, daemon=True).start()

# ══════════════════════════════════════════════════════
#                  /disconnect
# ══════════════════════════════════════════════════════

@bot.message_handler(commands=["disconnect"])
@access_required
def cmd_disconnect(msg):
    u = get_user(msg.from_user.id)
    if not u["connected"]:
        bot.send_message(msg.chat.id,
            "ℹ️  VPN не подключён",
            reply_markup=kb_main(False))
        return

    sess = fmt_time(time.time() - u["connect_time"]) if u["connect_time"] else "—"
    px   = u["proxy"]
    ib   = u.get("ip_before", "—")
    ia   = u.get("ip_after",  "—")
    u.update(connected=False, proxy=None, connect_time=None)

    bot.send_message(msg.chat.id,
        f"🔴  *Сессия завершена*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{proto_icon(px['type'])}  `{px['host']}:{px['port']}`\n"
        f"⏱  Длительность:  `{sess}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍  Реальный IP:  `{ib}`\n"
        f"🌍  Был IP VPN:   `{ia}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"_Соединение завершено_",
        parse_mode="Markdown", reply_markup=kb_main(False))

# ══════════════════════════════════════════════════════
#                    /rotate
# ══════════════════════════════════════════════════════

@bot.message_handler(commands=["rotate"])
@access_required
def cmd_rotate(msg):
    u = get_user(msg.from_user.id)
    if not u["connected"]:
        bot.send_message(msg.chat.id, "ℹ️  Сначала /connect")
        return

    wait = bot.send_message(msg.chat.id,
        "🔄  *Меняю IP...*", parse_mode="Markdown")

    def do():
        my_ip   = u.get("ip_before") or get_my_ip() or "unknown"
        exclude = u["proxy"]["host"] if u["proxy"] else None
        old_ip  = u.get("ip_after", "—")

        info      = {"n": 0}
        last_edit = [0.0]

        def on_try(n, pt, h, p):
            info["n"] = n
            now = time.time()
            if now - last_edit[0] >= 1.6:
                last_edit[0] = now
                try:
                    bot.edit_message_text(
                        f"🔄  *Ищу новый IP*\n\n"
                        f"{proto_icon(pt)}  `{h}:{p}`\n"
                        f"{loading_bar(min(n, 80), 80)}  попытка {n}",
                        msg.chat.id, wait.message_id, parse_mode="Markdown")
                except:
                    pass

        res = find_best_proxy(my_ip, exclude_host=exclude, on_try=on_try)

        if res:
            u.update(proxy=res, connect_time=time.time(), ip_after=res["new_ip"])
            u["total_rotates"] = u.get("total_rotates", 0) + 1
            bot.edit_message_text(
                f"✅  *IP изменён*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"{proto_icon(res['type'])}  `{res['host']}:{res['port']}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📶  {ping_bar(res['ping'])}  `{res['ping']} ms`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🌍  Был:     `{old_ip}`\n"
                f"🌍  Новый:   `{res['new_ip']}`",
                msg.chat.id, wait.message_id,
                parse_mode="Markdown", reply_markup=kb_main(True))
        else:
            bot.edit_message_text(
                "❌  Нет доступных серверов\n\nПопробуй `/scan`",
                msg.chat.id, wait.message_id,
                parse_mode="Markdown", reply_markup=kb_main(True))

    threading.Thread(target=do, daemon=True).start()

# ══════════════════════════════════════════════════════
#                    /status
# ══════════════════════════════════════════════════════

@bot.message_handler(commands=["status"])
@access_required
def cmd_status(msg):
    u    = get_user(msg.from_user.id)
    tot  = sum(len(cache[t]) for t in ["socks5","socks4","http"])
    fast = len(cache["top_fast"])

    if u["connected"] and u["proxy"]:
        px   = u["proxy"]
        sess = fmt_time(time.time() - u["connect_time"]) if u["connect_time"] else "—"
        ms   = tcp_ping(px["host"], px["port"], timeout=2)
        anon = ("Высокая (SOCKS5)" if px["type"] == "socks5"
                else "Средняя (SOCKS4)" if px["type"] == "socks4"
                else "Базовая (HTTP)")
        text = (
            f"📊  *Статус VPN*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢  Статус:       *Активен*\n"
            f"{proto_icon(px['type'])}  Протокол:    `{px['type'].upper()}`\n"
            f"🖥  Сервер:       `{px['host']}:{px['port']}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📶  Качество:\n"
            f"    {ping_bar(ms)}  `{f'{ms} ms' if ms else 'нет связи'}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱  Сессия:       `{sess}`\n"
            f"🔄  Смен IP:      `{u.get('total_rotates', 0)}`\n"
            f"📍  IP до:        `{u.get('ip_before','—')}`\n"
            f"🌍  IP сейчас:    `{u.get('ip_after','—')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔐  Анонимность:  `{anon}`\n"
            f"🔒  AES‑256‑GCM:  ✅\n"
            f"🌐  DNS‑HTTPS:    ✅\n"
            f"🛡  Leak Protect: ✅\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦  База прокси:  `{tot}`\n"
            f"⚡  Смарт-пул:    `{fast}`"
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
            f"⚡  Смарт-пул:  `{fast}`\n\n"
            f"_/connect — подключиться_\n"
            f"_/scan — найти лучшие серверы_"
        )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown",
                     reply_markup=kb_main(u["connected"]))

# ══════════════════════════════════════════════════════
#                   /proxies
# ══════════════════════════════════════════════════════

@bot.message_handler(commands=["proxies"])
@access_required
def cmd_proxies(msg):
    uid   = msg.from_user.id
    total = sum(len(cache[t]) for t in ["socks5","socks4","http"])
    fast  = cache["top_fast"]

    if total == 0:
        bot.send_message(msg.chat.id,
            "📦  База пуста. Используй `/refresh`",
            parse_mode="Markdown")
        return

    lines = [f"🗂  *Серверы Togaff VPN*\n\n"
             f"━━━━━━━━━━━━━━━━━━━━━\n"]
    if fast:
        lines.append(f"⚡  *Лучшие серверы (топ {min(3,len(fast))})*\n\n")
        for r in fast[:3]:
            lines.append(
                f"  {proto_icon(r['type'])}  `{r['host']}:{r['port']}`\n"
                f"  {ping_bar(r['ping'])}  `{r['ping']} ms`\n\n")
        lines.append("━━━━━━━━━━━━━━━━━━━━━\n")

    for pt in ["socks5","socks4","http"]:
        cnt  = len(cache[pt])
        lines.append(f"{proto_icon(pt)}  *{pt.upper()}* — `{cnt}` серверов\n")
        for h, p in cache[pt][:4]:
            lines.append(f"   `{h}:{p}`\n")
        lines.append("\n")

    lines.append(f"━━━━━━━━━━━━━━━━━━━━━\n"
                 f"_Всего: {total} · /refresh для обновления_")

    bot.send_message(msg.chat.id, "".join(lines),
                     parse_mode="Markdown",
                     reply_markup=kb_main(get_user(uid)["connected"]))

# ══════════════════════════════════════════════════════
#                      /ip
# ══════════════════════════════════════════════════════

@bot.message_handler(commands=["ip"])
@access_required
def cmd_ip(msg):
    u    = get_user(msg.from_user.id)
    wait = bot.send_message(msg.chat.id,
        "🔍  *Определяю IP...*", parse_mode="Markdown")

    def do():
        if u["connected"] and u["proxy"]:
            px   = u["proxy"]
            ip   = get_ip_via(px["type"], px["host"], px["port"], timeout=9)
            mode = f"{px['type'].upper()} прокси"
            icon = "🌍"
        else:
            ip   = get_my_ip(timeout=7)
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

# ══════════════════════════════════════════════════════
#                   /refresh
# ══════════════════════════════════════════════════════

@bot.message_handler(commands=["refresh"])
@access_required
def cmd_refresh(msg):
    wait = bot.send_message(msg.chat.id,
        "🔄  *Обновляю базу прокси...*", parse_mode="Markdown")

    def do():
        cache["updated"] = 0
        refresh_cache(force=True)
        total = sum(len(cache[t]) for t in ["socks5","socks4","http"])
        bot.edit_message_text(
            f"✅  *База обновлена*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔵  SOCKS5: `{len(cache['socks5'])}`\n"
            f"🟣  SOCKS4: `{len(cache['socks4'])}`\n"
            f"⚪  HTTP:   `{len(cache['http'])}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦  Итого:  `{total}`\n\n"
            f"_/scan для поиска лучших серверов_",
            msg.chat.id, wait.message_id,
            parse_mode="Markdown",
            reply_markup=kb_main(get_user(msg.from_user.id)["connected"]))

    threading.Thread(target=do, daemon=True).start()

# ══════════════════════════════════════════════════════
#                  /generate
# ══════════════════════════════════════════════════════

@bot.message_handler(commands=["generate"])
@access_required
def cmd_generate(msg):
    u = get_user(msg.from_user.id)
    if u["connected"] and u["proxy"]:
        _send_config(msg.chat.id, None, u["proxy"])
        return

    wait = bot.send_message(msg.chat.id,
        "🔧  *Генерирую конфиг...*", parse_mode="Markdown")

    def do():
        my_ip     = get_my_ip() or "0.0.0.0"
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
                        f"{loading_bar(min(n,60),60)}  попытка {n}",
                        msg.chat.id, wait.message_id, parse_mode="Markdown")
                except:
                    pass

        res = find_best_proxy(my_ip, on_try=on_try)
        if res:
            _send_config(msg.chat.id, wait.message_id, res)
        else:
            bot.edit_message_text(
                "❌  Нет рабочего прокси\n\nПопробуй `/scan` → `/generate`",
                msg.chat.id, wait.message_id, parse_mode="Markdown")

    threading.Thread(target=do, daemon=True).start()

def _send_config(chat_id, msg_id, proxy):
    h, p, pt = proxy["host"], proxy["port"], proxy["type"]
    ms = proxy["ping"]

    s  = "socks5h" if pt == "socks5" else ("socks4" if pt == "socks4" else "http")
    pu = f"{s}://{h}:{p}"

    text = (
        f"📋  *Конфиг прокси*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{proto_icon(pt)}  `{h}:{p}`  ·  {pt.upper()}\n"
        f"📶  {ping_bar(ms)}  `{ms} ms`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔹  *curl / wget*\n"
        f"`--proxy {pu}`\n\n"
        f"🔹  *Shell / ENV*\n"
        f"```\nexport ALL_PROXY={pu}\nexport HTTP_PROXY={pu}\nexport HTTPS_PROXY={pu}\n```\n\n"
        f"🔹  *proxychains.conf*\n"
        f"`{pt.replace('socks5','socks5').replace('socks4','socks4')} {h} {p}`\n\n"
        f"🔹  *Python requests*\n"
        f"```python\nproxies = {{'http': '{pu}', 'https': '{pu}'}}\n```\n\n"
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

# ══════════════════════════════════════════════════════
#          ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ (рассылка)
# ══════════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.from_user.id in _broadcast_state
                                    and _broadcast_state[m.from_user.id] is True
                                    and m.text != "/cancel")
def handle_broadcast_text(msg):
    if not is_admin(msg.from_user.id):
        return
    _broadcast_state.pop(msg.from_user.id, None)
    _do_broadcast(msg.chat.id, msg.text)

# ══════════════════════════════════════════════════════
#                    CALLBACKS
# ══════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: True)
def on_callback(call):
    uid = call.from_user.id
    d   = call.data

    # ─── Кнопки без проверки доступа ───────────────────
    if d == "back_main":
        bot.answer_callback_query(call.id)
        cmd_start(FMsg(call, "/start"))
        return
    if d == "adm_panel":
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "🚫 Нет доступа")
            return
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(_admin_main_text(), call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode="Markdown", reply_markup=kb_admin())
        except:
            bot.send_message(call.message.chat.id, _admin_main_text(),
                             parse_mode="Markdown", reply_markup=kb_admin())
        return

    # ─── Кнопки администратора ─────────────────────────
    if d.startswith("adm_") or d.startswith("ban_") or d.startswith("del_"):
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "🚫 Нет доступа")
            return
        mid = call.message.message_id
        cid = call.message.chat.id

        if d == "adm_users":
            bot.answer_callback_query(call.id)
            _send_users_list(cid, mid)
        elif d == "adm_banned":
            bot.answer_callback_query(call.id)
            _send_banned_list(cid, mid)
        elif d == "adm_stats":
            bot.answer_callback_query(call.id)
            online  = sum(1 for u in users.values() if u.get("connected"))
            total   = sum(len(cache[t]) for t in ["socks5","socks4","http"])
            fast    = len(cache["top_fast"])
            bot.edit_message_text(
                f"📊  *Статистика*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👥  Пользователей:   `{len(allowed_users)}`\n"
                f"🟢  Онлайн:          `{online}`\n"
                f"🚫  В бане:          `{len(banned_users)}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📦  База прокси:    `{total}`\n"
                f"⚡  Смарт-пул:      `{fast}`\n"
                f"🔵  SOCKS5: `{len(cache['socks5'])}`\n"
                f"🟣  SOCKS4: `{len(cache['socks4'])}`\n"
                f"⚪  HTTP:   `{len(cache['http'])}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"_Обновлено: {ts()}_",
                cid, mid, parse_mode="Markdown",
                reply_markup=telebot.types.InlineKeyboardMarkup().add(
                    telebot.types.InlineKeyboardButton("◀ Назад", callback_data="adm_panel")))
        elif d == "adm_refresh":
            bot.answer_callback_query(call.id, "🔄 Обновляю...")
            def bg():
                cache["updated"] = 0
                refresh_cache(force=True)
            threading.Thread(target=bg, daemon=True).start()
            bot.send_message(cid, "🔄  Обновление базы запущено в фоне")
        elif d == "adm_scan":
            bot.answer_callback_query(call.id, "⚡ Запускаю скан...")
            cmd_scan(FMsg(call, "/scan"))
        elif d == "adm_broadcast":
            bot.answer_callback_query(call.id)
            _broadcast_state[uid] = True
            bot.send_message(cid, "📢  Отправь текст рассылки следующим сообщением\n(/cancel для отмены)")
        elif d.startswith("ban_"):
            target = int(d.split("_")[1])
            banned_users.add(target)
            key = str(target)
            if key in allowed_users:
                del allowed_users[key]
            save_users()
            bot.answer_callback_query(call.id, f"🚫 Забанен {target}")
            _send_users_list(cid, mid)
        elif d.startswith("del_"):
            target = int(d.split("_")[1])
            key    = str(target)
            if key in allowed_users:
                del allowed_users[key]
                save_users()
            bot.answer_callback_query(call.id, f"✅ Удалён {target}")
            _send_users_list(cid, mid)
        return

    # ─── Кнопки юзера (проверка доступа) ───────────────
    if not is_allowed(uid):
        bot.answer_callback_query(call.id, "🔒 Нет доступа")
        return

    if d == "regen":
        bot.answer_callback_query(call.id, "🔧 Ищу другой...")
        cmd_generate(FMsg(call, "/generate"))
        return

    table = {
        "connect":    ("/connect",         "⚡ Подключаюсь..."),
        "c_socks5":   ("/connect socks5",  "🔵 SOCKS5..."),
        "c_socks4":   ("/connect socks4",  "🟣 SOCKS4..."),
        "c_http":     ("/connect http",    "⚪ HTTP..."),
        "disconnect": ("/disconnect",      "🔴 Отключаю..."),
        "rotate":     ("/rotate",          "🔄 Меняю IP..."),
        "status":     ("/status",          ""),
        "proxies":    ("/proxies",         ""),
        "generate":   ("/generate",        "🔧 Генерирую..."),
    }
    if d not in table:
        return

    cmd_text, answer = table[d]
    bot.answer_callback_query(call.id, answer or None)

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

# ══════════════════════════════════════════════════════
#                      ЗАПУСК
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("═" * 56)
    print("  TOGAFF VPN  ·  Ultimate Edition")
    print(f"  PySocks:      {'✓  SOCKS5/4 активны' if SOCKS_OK else '✗  pip install PySocks requests[socks]'}")
    print(f"  Admin IDs:    {ADMIN_IDS}")
    print(f"  Своих прокси: {len(MY_PROXIES_HTTP)}")
    print(f"  Whitelist:    {len(allowed_users)} пользователей")
    print("═" * 56)

    # ── Фоновый старт: загрузка базы + прогрев пула ──
    def startup():
        print("⟳  Загружаю базу прокси...")
        refresh_cache()
        time.sleep(5)
        print("⚡  Прогреваю смарт-пул...")
        my_ip = get_my_ip() or ""
        build_smart_pool(my_ip, sample=SCAN_SAMPLE, workers=VERIFY_WORKERS)

    threading.Thread(target=startup, daemon=True).start()

    # ── Авто-обновление пула каждые 15 минут ─────────
    def auto_refresh():
        while True:
            time.sleep(TOP_TTL)
            my_ip = get_my_ip() or ""
            if my_ip:
                print("♻  Авто-обновление смарт-пула...")
                build_smart_pool(my_ip, sample=SCAN_SAMPLE // 2,
                                 workers=VERIFY_WORKERS)

    threading.Thread(target=auto_refresh, daemon=True).start()

    bot.infinity_polling(timeout=30, long_polling_timeout=20)

