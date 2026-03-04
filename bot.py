import telebot
import requests
import socket
import threading
import time
import random
import re

# ══════════════════════════════════════════════════════════
#  🌸 TOGAFF VPN BOT — CYBERPUNK ANIME EDITION
#  Дизайн: розово-фиолетовая тема, Астольфо, анимации
# ══════════════════════════════════════════════════════════

TOKEN = "8603769389:AAFNrImTZhMY0ctceejoFbNkosE54cNsE30"

MINI_APP_URL = "https://YOUR_USERNAME.github.io/togaff-vpn/"

# Фото Астольфо (публичное изображение из открытых источников)
ASTOLFO_PHOTO_URL = "https://i.imgur.com/XQ2LXTM.jpeg"

# ── PySocks ─────────────────────────────────────────────
try:
    import socks  # noqa
    SOCKS_OK = True
except ImportError:
    SOCKS_OK = False
    print("⚠  Установи: pip install PySocks requests[socks]")

bot = telebot.TeleBot(TOKEN)

# ══════════════════════════════════════════════════════════
#  ИСТОЧНИКИ ПРОКСИ
# ══════════════════════════════════════════════════════════
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

cache = {"socks5": [], "socks4": [], "http": [], "updated": 0}
CACHE_TTL = 1800

users = {}

def get_user(uid):
    if uid not in users:
        users[uid] = {
            "connected": False, "proxy": None,
            "connect_time": None, "ip_before": None, "ip_after": None,
        }
    return users[uid]

# ══════════════════════════════════════════════════════════
#  ВИЗУАЛЬНЫЕ КОМПОНЕНТЫ (cyberpunk anime стиль)
# ══════════════════════════════════════════════════════════

# Цвета через Unicode-блоки и символы
PINK  = "🌸"
CYAN  = "💎"
VIOLET= "💜"
STAR  = "✦"
SPARK = "⚡"

def make_bar(current, total, width=12):
    """Красивый прогресс-бар в стиле киберпанка"""
    filled = int(width * current / max(total, 1))
    bar = "█" * filled + "░" * (width - filled)
    pct = int(100 * current / max(total, 1))
    return f"[{bar}] {pct}%"

def ping_grade(ms):
    """Оценка пинга с иконками"""
    if ms is None:  return ("✖", "OFFLINE")
    if ms < 100:    return ("◆", "FAST")
    if ms < 200:    return ("◇", "GOOD")
    if ms < 400:    return ("○", "MED")
    return          ("·", "SLOW")

def proto_badge(ptype):
    icons = {"socks5": "⬛", "socks4": "▪", "http": "▫"}
    return icons.get(ptype, "·")

def fmt_t(s):
    return f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d}"

def spin_frame(n):
    """Анимационный спиннер"""
    frames = ["◐", "◓", "◑", "◒"]
    return frames[n % 4]

# ══════════════════════════════════════════════════════════
#  РАБОТА С ПРОКСИ
# ══════════════════════════════════════════════════════════

def fetch_list(url, timeout=12):
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "curl/7.80"})
        if r.status_code != 200:
            return []
        result = []
        for line in r.text.splitlines():
            m = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})", line.strip())
            if m:
                result.append((m.group(1), int(m.group(2))))
        return result
    except:
        return []

def refresh_cache():
    if time.time() - cache["updated"] < CACHE_TTL:
        return
    print("↻ Обновляю кэш прокси...")
    for ptype, urls in SOURCES.items():
        collected, seen = [], set()
        for url in urls:
            for h, p in fetch_list(url):
                key = f"{h}:{p}"
                if key not in seen:
                    seen.add(key)
                    collected.append((h, p))
            if len(collected) >= 600:
                break
        random.shuffle(collected)
        cache[ptype] = collected[:400]
        print(f"  {ptype}: {len(cache[ptype])}")
    cache["updated"] = time.time()
    print("✓ Кэш готов")

def tcp_ok(host, port, timeout=2.0):
    try:
        t0 = time.time()
        with socket.create_connection((host, port), timeout=timeout):
            return round((time.time() - t0) * 1000, 1)
    except:
        return None

IP_URLS = [
    "http://api.ipify.org",
    "http://checkip.amazonaws.com",
    "http://icanhazip.com",
    "http://ip.42.pl/raw",
]

def get_ip(proxy_cfg=None, timeout=8):
    for url in IP_URLS:
        try:
            if proxy_cfg:
                ptype = proxy_cfg["type"]
                h, p  = proxy_cfg["host"], proxy_cfg["port"]
                if ptype in ("socks5", "socks4") and SOCKS_OK:
                    scheme  = "socks5" if ptype == "socks5" else "socks4"
                    proxies = {"http": f"{scheme}://{h}:{p}", "https": f"{scheme}://{h}:{p}"}
                else:
                    proxies = {"http": f"http://{h}:{p}", "https": f"http://{h}:{p}"}
                r = requests.get(url, proxies=proxies, timeout=timeout)
            else:
                r = requests.get(url, timeout=timeout)
            ip = r.text.strip()
            if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", ip):
                return ip
        except:
            continue
    return None

def verify(ptype, host, port, my_ip):
    ms = tcp_ok(host, port, timeout=2.0)
    if not ms:
        return None
    cfg    = {"type": ptype, "host": host, "port": port}
    new_ip = get_ip(proxy_cfg=cfg, timeout=7)
    if not new_ip or new_ip == my_ip:
        return None
    return (ms, new_ip)

def find_proxy(my_ip, preferred=None, exclude=None, limit=80, on_try=None):
    refresh_cache()
    order = (["socks5","socks4","http"] if SOCKS_OK else ["http","socks5","socks4"])
    if preferred and preferred in order:
        order = [preferred] + [t for t in order if t != preferred]
    n = 0
    for ptype in order:
        pool = list(cache[ptype])
        random.shuffle(pool)
        for host, port in pool:
            if n >= limit:
                return None
            if exclude and host == exclude:
                continue
            n += 1
            if on_try:
                on_try(n, ptype, host, port)
            res = verify(ptype, host, port, my_ip)
            if res:
                return {"type": ptype, "host": host, "port": port,
                        "ping": res[0], "new_ip": res[1]}
    return None

# ══════════════════════════════════════════════════════════
#  ГЕНЕРАТОР ПРОКСИ-КОНФИГОВ
# ══════════════════════════════════════════════════════════

def generate_proxy_config(proxy, format_type="all"):
    """Генерировать готовые конфиги для разных форматов"""
    h = proxy["host"]
    p = proxy["port"]
    t = proxy["type"]
    ms = proxy["ping"]

    configs = {}

    # Формат для браузера / curl
    if t in ("socks5", "socks4"):
        configs["curl"] = f"--proxy {t}h://{h}:{p}"
        configs["env"]  = f"export ALL_PROXY={t}h://{h}:{p}"
    else:
        configs["curl"] = f"--proxy http://{h}:{p}"
        configs["env"]  = f"export HTTP_PROXY=http://{h}:{p}\nexport HTTPS_PROXY=http://{h}:{p}"

    # Proxychains
    if t == "socks5":
        configs["proxychains"] = f"socks5 {h} {p}"
    elif t == "socks4":
        configs["proxychains"] = f"socks4 {h} {p}"
    else:
        configs["proxychains"] = f"http {h} {p}"

    # Python requests
    if t in ("socks5", "socks4"):
        configs["python"] = (
            f'proxies = {{\n'
            f'    "http":  "{t}h://{h}:{p}",\n'
            f'    "https": "{t}h://{h}:{p}"\n'
            f'}}'
        )
    else:
        configs["python"] = (
            f'proxies = {{\n'
            f'    "http":  "http://{h}:{p}",\n'
            f'    "https": "http://{h}:{p}"\n'
            f'}}'
        )

    # Telegram MTProxy (для HTTP прокси)
    configs["raw"] = f"{h}:{p}"

    return configs

# ══════════════════════════════════════════════════════════
#  КЛАВИАТУРЫ
# ══════════════════════════════════════════════════════════

def keyboard(connected=False):
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    if connected:
        kb.add(
            telebot.types.InlineKeyboardButton("▪ ОТКЛ", callback_data="disconnect"),
            telebot.types.InlineKeyboardButton("↻ НОВЫЙ IP", callback_data="rotate"),
        )
        kb.add(
            telebot.types.InlineKeyboardButton("⚙ ГЕНЕРАТОР", callback_data="generate"),
            telebot.types.InlineKeyboardButton("◈ СТАТУС", callback_data="status"),
        )
    else:
        kb.add(
            telebot.types.InlineKeyboardButton("⚡ ПОДКЛЮЧИТЬ", callback_data="connect"),
        )
        kb.add(
            telebot.types.InlineKeyboardButton("◈ СТАТУС", callback_data="status"),
            telebot.types.InlineKeyboardButton("◉ ПРОКСИ", callback_data="proxies"),
        )
    kb.add(
        telebot.types.InlineKeyboardButton("⬛ SOCKS5", callback_data="c_socks5"),
        telebot.types.InlineKeyboardButton("▪ SOCKS4",  callback_data="c_socks4"),
        telebot.types.InlineKeyboardButton("▫ HTTP",    callback_data="c_http"),
    )
    kb.add(telebot.types.InlineKeyboardButton(
        "🌸 VPN ИНТЕРФЕЙС",
        web_app=telebot.types.WebAppInfo(url=MINI_APP_URL)))
    return kb

class FM:
    def __init__(self, call, text=""):
        self.chat      = type("C",(),{"id":call.message.chat.id})()
        self.from_user = type("U",(),{"id":call.from_user.id,
                                      "first_name":call.from_user.first_name or "User"})()
        self.text = text

# ══════════════════════════════════════════════════════════
#  ТЕКСТОВЫЕ ШАБЛОНЫ (cyberpunk anime)
# ══════════════════════════════════════════════════════════

def hdr(title, sub=""):
    """Рамка-заголовок в стиле киберпанк"""
    w = 30
    line = "═" * w
    t = title.center(w - 2)
    s = sub.center(w - 2) if sub else None
    result = f"╔{line}╗\n║ {t} ║\n"
    if s:
        result += f"║ {s} ║\n"
    result += f"╚{line}╝"
    return result

# ══════════════════════════════════════════════════════════
#  КОМАНДЫ
# ══════════════════════════════════════════════════════════

@bot.message_handler(commands=["start"])
def c_start(msg):
    u    = get_user(msg.from_user.id)
    name = msg.from_user.first_name or "User"
    st   = "[ ◈ АКТИВЕН ]" if u["connected"] else "[ ○ ОТКЛЮЧЁН ]"
    total = sum(len(cache[t]) for t in ["socks5","socks4","http"])

    caption = (
        f"```\n"
        f"{hdr('TOGAFF  VPN', 'Anonymous Proxy Gateway')}\n"
        f"```\n"
        f"✦ Пользователь: *{name}*\n"
        f"✦ Статус: `{st}`\n\n"
        f"```\n"
        f"Протоколы:  SOCKS5 · SOCKS4 · HTTP\n"
        f"Кэш:        {total} прокси\n"
        f"Проверка:   РЕАЛЬНАЯ смена IP\n"
        f"Защита:     AES-256 · DNS-H · NoLeak\n"
        f"```\n\n"
        f"*Команды:*\n"
        f"`/connect`     — авто (SOCKS5→4→HTTP)\n"
        f"`/connect socks5` · `/connect socks4` · `/connect http`\n"
        f"`/disconnect`  · `/rotate`  · `/status`\n"
        f"`/generate`    — 🔧 сгенерировать конфиг\n"
        f"`/ip`          · `/refresh` · `/proxies`\n"
    )

    try:
        bot.send_photo(
            msg.chat.id,
            photo=ASTOLFO_PHOTO_URL,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard(u["connected"])
        )
    except Exception:
        # Если фото не доступно — отправим без
        bot.send_message(
            msg.chat.id,
            f"🌸 *Привет! Я Астольфо~ Togaff VPN!* ✌️\n\n" + caption,
            parse_mode="Markdown",
            reply_markup=keyboard(u["connected"])
        )

@bot.message_handler(commands=["refresh"])
def c_refresh(msg):
    wait = bot.send_message(msg.chat.id,
        "```\n◐ ОБНОВЛЯЮ СПИСКИ ПРОКСИ...\n```", parse_mode="Markdown")
    def do():
        cache["updated"] = 0
        refresh_cache()
        total = sum(len(cache[t]) for t in ["socks5","socks4","http"])
        bot.edit_message_text(
            f"```\n{hdr('ПРОКСИ ОБНОВЛЕНЫ')}\n```\n"
            f"⬛ SOCKS5: `{len(cache['socks5'])}`\n"
            f"▪  SOCKS4: `{len(cache['socks4'])}`\n"
            f"▫  HTTP:   `{len(cache['http'])}`\n"
            f"✦  Итого:  `{total}`",
            msg.chat.id, wait.message_id, parse_mode="Markdown",
            reply_markup=keyboard(get_user(msg.from_user.id)["connected"]))
    threading.Thread(target=do, daemon=True).start()

@bot.message_handler(commands=["connect"])
def c_connect(msg):
    uid = msg.from_user.id
    u   = get_user(uid)
    parts     = (msg.text or "").strip().split()
    preferred = parts[1].lower() if len(parts)>1 and parts[1] in ("socks5","socks4","http") else None

    if u["connected"]:
        px = u["proxy"]
        bot.send_message(msg.chat.id,
            f"✦ Уже подключён: `{px['host']}:{px['port']}`\n/rotate или /disconnect",
            parse_mode="Markdown", reply_markup=keyboard(True))
        return

    wait = bot.send_message(msg.chat.id,
        "```\n◐ ОПРЕДЕЛЯЮ ВАШ IP...\n```", parse_mode="Markdown")

    def do():
        my_ip = get_ip(timeout=6) or "unknown"
        u["ip_before"] = my_ip
        label = preferred.upper() if preferred else "AUTO"

        # ── Этап 1: Показываем начало поиска ──
        bot.edit_message_text(
            f"```\n"
            f"◑ ПОИСК [{label}]\n"
            f"─────────────────────────────\n"
            f"Ваш IP:   {my_ip}\n"
            f"Статус:   Сканирую прокси...\n"
            f"─────────────────────────────\n"
            f"{make_bar(0, 100)}\n"
            f"```",
            msg.chat.id, wait.message_id, parse_mode="Markdown")

        info = {"n": 0, "last": "", "found": 0}
        last_edit = [0]

        def on_try(n, pt, h, p):
            info["n"] = n
            info["last"] = f"{pt}://{h}:{p}"
            now = time.time()
            if now - last_edit[0] > 2.0:
                last_edit[0] = now
                frame = spin_frame(n)
                bar   = make_bar(min(n, 100), 100)
                try:
                    bot.edit_message_text(
                        f"```\n"
                        f"{frame} ПОИСК [{label}] — попытка {n}\n"
                        f"─────────────────────────────\n"
                        f"Тест:   {pt}://{h}:{p}\n"
                        f"Ваш IP: {my_ip}\n"
                        f"─────────────────────────────\n"
                        f"{bar}\n"
                        f"```",
                        msg.chat.id, wait.message_id, parse_mode="Markdown")
                except:
                    pass

        res = find_proxy(my_ip, preferred=preferred, limit=100, on_try=on_try)

        if res:
            u.update(connected=True, proxy=res,
                     connect_time=time.time(), ip_after=res["new_ip"])
            pg, pl = ping_grade(res["ping"])
            bot.edit_message_text(
                f"```\n"
                f"{hdr('ПОДКЛЮЧЕНИЕ АКТИВНО')}\n"
                f"```\n"
                f"{proto_badge(res['type'])} Протокол:    `{res['type'].upper()}`\n"
                f"✦ Сервер:      `{res['host']}:{res['port']}`\n"
                f"{pg} Пинг:        `{res['ping']}ms  [{pl}]`\n"
                f"✦ Ваш IP до:   `{my_ip}`\n"
                f"💎 Ваш IP теперь: `{res['new_ip']}`\n\n"
                f"```\n"
                f"◈ IP СМЕНЁН  ◈ АНОНИМНОСТЬ АКТИВНА\n"
                f"AES-256 · DNS-HTTPS · NoLeak\n"
                f"```",
                msg.chat.id, wait.message_id, parse_mode="Markdown",
                reply_markup=keyboard(True))
        else:
            bot.edit_message_text(
                f"```\n"
                f"✖ ОШИБКА: рабочий прокси не найден\n"
                f"Проверено: {info['n']} серверов\n"
                f"Попробуй /refresh → /connect\n"
                f"```",
                msg.chat.id, wait.message_id, parse_mode="Markdown",
                reply_markup=keyboard(False))

    threading.Thread(target=do, daemon=True).start()

@bot.message_handler(commands=["disconnect"])
def c_disconnect(msg):
    uid = msg.from_user.id
    u   = get_user(uid)
    if not u["connected"]:
        bot.send_message(msg.chat.id, "```\n[ VPN уже отключён ]\n```",
            parse_mode="Markdown", reply_markup=keyboard(False))
        return
    sess = fmt_t(time.time()-u["connect_time"]) if u["connect_time"] else "—"
    ib, ia = u.get("ip_before","—"), u.get("ip_after","—")
    u.update(connected=False, proxy=None, connect_time=None)
    bot.send_message(msg.chat.id,
        f"```\n{hdr('VPN ОТКЛЮЧЁН')}\n```\n"
        f"✦ Сессия:      `{sess}`\n"
        f"✦ Был IP:      `{ia}`\n"
        f"✦ Реальный IP: `{ib}`",
        parse_mode="Markdown", reply_markup=keyboard(False))

@bot.message_handler(commands=["rotate"])
def c_rotate(msg):
    uid = msg.from_user.id
    u   = get_user(uid)
    if not u["connected"]:
        bot.send_message(msg.chat.id, "✦ Сначала /connect"); return

    wait = bot.send_message(msg.chat.id,
        "```\n◐ СМЕНА IP...\n```", parse_mode="Markdown")

    def do():
        my_ip   = u.get("ip_before") or get_ip() or "unknown"
        exclude = u["proxy"]["host"] if u["proxy"] else None
        info    = {"n": 0}
        last_edit = [0]

        def on_try(n, pt, h, p):
            info["n"] = n
            now = time.time()
            if now - last_edit[0] > 2.0:
                last_edit[0] = now
                frame = spin_frame(n)
                try:
                    bot.edit_message_text(
                        f"```\n"
                        f"{frame} ИЩУ НОВЫЙ IP — попытка {n}\n"
                        f"Тест: {pt}://{h}:{p}\n"
                        f"{make_bar(min(n, 80), 80)}\n"
                        f"```",
                        msg.chat.id, wait.message_id, parse_mode="Markdown")
                except:
                    pass

        res = find_proxy(my_ip, exclude=exclude, limit=80, on_try=on_try)
        if res:
            u.update(proxy=res, connect_time=time.time(), ip_after=res["new_ip"])
            pg, pl = ping_grade(res["ping"])
            bot.edit_message_text(
                f"```\n{hdr('IP СМЕНЁН')}\n```\n"
                f"{proto_badge(res['type'])} Протокол: `{res['type'].upper()}`\n"
                f"✦ Сервер:   `{res['host']}:{res['port']}`\n"
                f"{pg} Пинг:     `{res['ping']}ms  [{pl}]`\n"
                f"💎 Новый IP: `{res['new_ip']}`",
                msg.chat.id, wait.message_id, parse_mode="Markdown",
                reply_markup=keyboard(True))
        else:
            bot.edit_message_text(
                "```\n[ Нет рабочих — попробуй /refresh ]\n```",
                msg.chat.id, wait.message_id, parse_mode="Markdown",
                reply_markup=keyboard(True))

    threading.Thread(target=do, daemon=True).start()

@bot.message_handler(commands=["status"])
def c_status(msg):
    uid = msg.from_user.id
    u   = get_user(uid)
    if u["connected"] and u["proxy"]:
        px   = u["proxy"]
        sess = fmt_t(time.time()-u["connect_time"]) if u["connect_time"] else "—"
        ms   = tcp_ok(px["host"], px["port"], timeout=2)
        pg, pl = ping_grade(ms)
        anon = "◆ ВЫСОКАЯ (SOCKS5)" if px["type"]=="socks5" else "◇ СРЕДНЯЯ"
        text = (
            f"```\n{hdr('TOGAFF VPN  STATUS')}\n```\n"
            f"✦ Статус:      `◈ АКТИВЕН`\n"
            f"{proto_badge(px['type'])} Протокол:    `{px['type'].upper()}`\n"
            f"✦ Сервер:      `{px['host']}:{px['port']}`\n"
            f"{pg} Пинг:        `{f'{ms}ms  [{pl}]' if ms else 'недоступен'}`\n"
            f"✦ Сессия:      `{sess}`\n"
            f"✦ IP до:       `{u.get('ip_before','—')}`\n"
            f"💎 IP сейчас:   `{u.get('ip_after','—')}`\n\n"
            f"```\n"
            f"Анонимность:  {anon}\n"
            f"AES-256-GCM:  ◈\n"
            f"DNS-HTTPS:    ◈\n"
            f"Leak Protect: ◈\n"
            f"```"
        )
    else:
        total = sum(len(cache[t]) for t in ["socks5","socks4","http"])
        text = (
            f"```\n{hdr('TOGAFF VPN  STATUS')}\n```\n"
            f"✦ Статус: `○ ОТКЛЮЧЁН`\n\n"
            f"```\n"
            f"Кэш: SOCKS5={len(cache['socks5'])} SOCKS4={len(cache['socks4'])} HTTP={len(cache['http'])}\n"
            f"Итого={total}\n"
            f"```\n"
            f"/connect для подключения"
        )
    bot.send_message(msg.chat.id, text, parse_mode="Markdown",
        reply_markup=keyboard(u["connected"]))

@bot.message_handler(commands=["proxies"])
def c_proxies(msg):
    uid   = msg.from_user.id
    total = sum(len(cache[t]) for t in ["socks5","socks4","http"])
    if total == 0:
        bot.send_message(msg.chat.id, "```\n[ Кэш пуст — /refresh ]\n```",
            parse_mode="Markdown"); return
    lines = [f"```\n{hdr('КЭШ ПРОКСИ')}\n```\n"]
    for pt in ["socks5","socks4","http"]:
        lines.append(f"{proto_badge(pt)} *{pt.upper()}* — {len(cache[pt])} шт")
        for h,p in cache[pt][:4]:
            lines.append(f"  `{h}:{p}`")
        lines.append("")
    lines.append(f"_Итого: {total} · /refresh для обновления_")
    bot.send_message(msg.chat.id, "\n".join(lines), parse_mode="Markdown",
        reply_markup=keyboard(get_user(uid)["connected"]))

@bot.message_handler(commands=["ip"])
def c_ip(msg):
    uid  = msg.from_user.id
    u    = get_user(uid)
    wait = bot.send_message(msg.chat.id, "```\n◐ ОПРЕДЕЛЯЮ IP...\n```", parse_mode="Markdown")
    def do():
        if u["connected"] and u["proxy"]:
            ip   = get_ip(proxy_cfg=u["proxy"], timeout=8)
            mode = f"{u['proxy']['type'].upper()} прокси"
        else:
            ip   = get_ip(timeout=6)
            mode = "прямое соединение"
        bot.edit_message_text(
            f"```\n{hdr('ВАШ  IP')}\n```\n"
            f"💎 IP:    `{ip or 'недоступен'}`\n"
            f"✦ Режим: `{mode}`",
            msg.chat.id, wait.message_id, parse_mode="Markdown")
    threading.Thread(target=do, daemon=True).start()

# ══════════════════════════════════════════════════════════
#  /generate — ГЕНЕРАТОР КОНФИГОВ
# ══════════════════════════════════════════════════════════

@bot.message_handler(commands=["generate"])
def c_generate(msg):
    uid = msg.from_user.id
    u   = get_user(uid)

    if not u["connected"] or not u["proxy"]:
        # Найти любой рабочий прокси для генерации
        wait = bot.send_message(msg.chat.id,
            "```\n◐ ИЩУ ПРОКСИ ДЛЯ ГЕНЕРАЦИИ...\n```", parse_mode="Markdown")

        def do_gen():
            my_ip = get_ip(timeout=6) or "0.0.0.0"
            info  = {"n": 0}
            last_edit = [0]

            def on_try(n, pt, h, p):
                info["n"] = n
                now = time.time()
                if now - last_edit[0] > 1.5:
                    last_edit[0] = now
                    frame = spin_frame(n)
                    try:
                        bot.edit_message_text(
                            f"```\n"
                            f"{frame} ГЕНЕРАЦИЯ — скан {n}\n"
                            f"Тест: {pt}://{h}:{p}\n"
                            f"{make_bar(min(n, 60), 60)}\n"
                            f"```",
                            msg.chat.id, wait.message_id, parse_mode="Markdown")
                    except:
                        pass

            res = find_proxy(my_ip, limit=60, on_try=on_try)
            if res:
                send_generated_config(msg.chat.id, wait.message_id, res, u)
            else:
                bot.edit_message_text(
                    "```\n[ ✖ Нет рабочих прокси — /refresh ]\n```",
                    msg.chat.id, wait.message_id, parse_mode="Markdown")

        threading.Thread(target=do_gen, daemon=True).start()
    else:
        # Уже подключён — генерим конфиг текущего прокси
        send_generated_config(msg.chat.id, None, u["proxy"], u)

def send_generated_config(chat_id, msg_id, proxy, u):
    configs = generate_proxy_config(proxy)
    h, p, t = proxy["host"], proxy["port"], proxy["type"]
    pg, pl  = ping_grade(proxy["ping"])

    text = (
        f"```\n{hdr('PROXY GENERATOR')}\n```\n"
        f"{proto_badge(t)} Прокси: `{h}:{p}` [{t.upper()}]\n"
        f"{pg} Пинг:   `{proxy['ping']}ms [{pl}]`\n\n"
        f"*🔧 curl / wget:*\n"
        f"`{configs['curl']}`\n\n"
        f"*🖥 Переменные окружения:*\n"
        f"```\n{configs['env']}\n```\n\n"
        f"*⛓ proxychains.conf:*\n"
        f"`{configs['proxychains']}`\n\n"
        f"*🐍 Python requests:*\n"
        f"```python\n{configs['python']}\n```\n\n"
        f"*📋 RAW (IP:PORT):*\n"
        f"`{configs['raw']}`"
    )

    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(telebot.types.InlineKeyboardButton("⚡ ПОДКЛЮЧИТЬСЯ", callback_data="connect"))
    kb.add(telebot.types.InlineKeyboardButton("↻ ДРУГОЙ ПРОКСИ", callback_data="regen"))
    kb.add(telebot.types.InlineKeyboardButton("◈ ГЛАВНОЕ МЕНЮ", callback_data="start"))

    if msg_id:
        try:
            bot.edit_message_text(text, chat_id, msg_id,
                parse_mode="Markdown", reply_markup=kb)
            return
        except:
            pass

    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)

# ══════════════════════════════════════════════════════════
#  CALLBACKS
# ══════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    d = call.data

    if d == "regen":
        bot.answer_callback_query(call.id, "🔧 Ищу новый...")
        fake = FM(call, "/generate")
        c_generate(fake)
        return

    if d == "start":
        bot.answer_callback_query(call.id)
        fake = FM(call, "/start")
        c_start(fake)
        return

    mapping = {
        "connect":    ("/connect",       "⚡ Подключаюсь..."),
        "c_socks5":   ("/connect socks5","⬛ SOCKS5..."),
        "c_socks4":   ("/connect socks4","▪ SOCKS4..."),
        "c_http":     ("/connect http",  "▫ HTTP..."),
        "disconnect": ("/disconnect",    "▪ Отключаю..."),
        "rotate":     ("/rotate",        "↻ Меняю IP..."),
        "status":     ("/status",        ""),
        "proxies":    ("/proxies",       ""),
        "generate":   ("/generate",      "🔧 Генерирую..."),
    }

    if d not in mapping:
        return

    cmd_text, answer = mapping[d]
    bot.answer_callback_query(call.id, answer)
    fake = FM(call, cmd_text)

    handlers = {
        "/connect":        c_connect,
        "/connect socks5": c_connect,
        "/connect socks4": c_connect,
        "/connect http":   c_connect,
        "/disconnect":     c_disconnect,
        "/rotate":         c_rotate,
        "/status":         c_status,
        "/proxies":        c_proxies,
        "/generate":       c_generate,
    }
    handlers[cmd_text](fake)

# ══════════════════════════════════════════════════════════
#  ЗАПУСК
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("═" * 52)
    print("  🌸 TOGAFF VPN BOT — CYBERPUNK ANIME EDITION")
    print(f"  PySocks: {'✓ активен' if SOCKS_OK else '✗ нет (pip install PySocks)'}")
    print("  Команды: /start /connect /generate /status")
    print("═" * 52)
    threading.Thread(target=refresh_cache, daemon=True).start()
    bot.infinity_polling(timeout=30)
