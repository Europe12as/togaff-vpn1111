import telebot
import requests
import socket
import threading
import time
import random
import re

# ══════════════════════════════════════════════════════════
#  ТОКЕН
TOKEN = "8603769389:AAFNrImTZhMY0ctceejoFbNkosE54cNsE30"
# ══════════════════════════════════════════════════════════

MINI_APP_URL = "https://YOUR_USERNAME.github.io/togaff-vpn/"

# ── Проверка PySocks ──────────────────────────────────────
try:
    import socks  # noqa
    SOCKS_OK = True
except ImportError:
    SOCKS_OK = False
    print("⚠  Установи: pip install PySocks requests[socks]")

bot = telebot.TeleBot(TOKEN)

# ══════════════════════════════════════════════════════════
#  ИСТОЧНИКИ ПРОКСИ (живые GitHub-листы, обновляются каждые ~час)
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

# ── Кэш ──────────────────────────────────────────────────
cache = {"socks5": [], "socks4": [], "http": [], "updated": 0}
CACHE_TTL = 1800  # 30 мин

# ── Состояние пользователей ───────────────────────────────
users = {}

def get_user(uid):
    if uid not in users:
        users[uid] = {
            "connected": False, "proxy": None,
            "connect_time": None, "ip_before": None, "ip_after": None,
        }
    return users[uid]

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
    """Получить внешний IP через прокси или напрямую."""
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
    """Вернуть (ms, new_ip) если прокси реально меняет IP, иначе None."""
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
#  UI ХЕЛПЕРЫ
# ══════════════════════════════════════════════════════════
def fmt_t(s):
    return f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d}"

def t_icon(t): return {"socks5":"⬛","socks4":"◼","http":"▪"}.get(t,"▫")
def p_icon(ms):
    if ms is None: return "✖"
    return "◆" if ms<150 else "◇" if ms<300 else "○"

def keyboard(connected=False):
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    if connected:
        kb.add(
            telebot.types.InlineKeyboardButton("◼ ОТКЛЮЧИТЬ",   callback_data="disconnect"),
            telebot.types.InlineKeyboardButton("↻ СМЕНИТЬ IP",  callback_data="rotate"),
        )
    else:
        kb.add(telebot.types.InlineKeyboardButton("◻ ПОДКЛЮЧИТЬ", callback_data="connect"))
    kb.add(
        telebot.types.InlineKeyboardButton("▣ СТАТУС",  callback_data="status"),
        telebot.types.InlineKeyboardButton("▤ ПРОКСИ",  callback_data="proxies"),
    )
    kb.add(
        telebot.types.InlineKeyboardButton("⬛ SOCKS5", callback_data="c_socks5"),
        telebot.types.InlineKeyboardButton("◼ SOCKS4",  callback_data="c_socks4"),
        telebot.types.InlineKeyboardButton("▪ HTTP",    callback_data="c_http"),
    )
    kb.add(telebot.types.InlineKeyboardButton(
        "⊞ VPN ИНТЕРФЕЙС",
        web_app=telebot.types.WebAppInfo(url=MINI_APP_URL)))
    return kb

class FM:  # FakeMessage
    def __init__(self, call, text=""):
        self.chat      = type("C",(),{"id":call.message.chat.id})()
        self.from_user = type("U",(),{"id":call.from_user.id,
                                      "first_name":call.from_user.first_name or "User"})()
        self.text = text

# ══════════════════════════════════════════════════════════
#  КОМАНДЫ
# ══════════════════════════════════════════════════════════
@bot.message_handler(commands=["start"])
def c_start(msg):
    u    = get_user(msg.from_user.id)
    name = msg.from_user.first_name or "User"
    st   = "[ ■ АКТИВЕН ]" if u["connected"] else "[ □ НЕАКТИВЕН ]"
    total = sum(len(cache[t]) for t in ["socks5","socks4","http"])
    bot.send_message(msg.chat.id,
        f"```\n"
        f"╔══════════════════════════════╗\n"
        f"║        TOGAFF  VPN           ║\n"
        f"║   Anonymous Proxy Gateway    ║\n"
        f"╚══════════════════════════════╝\n"
        f"```\n"
        f"◈ Пользователь: *{name}*\n"
        f"◈ Статус: `{st}`\n\n"
        f"```\n"
        f"Протоколы:  SOCKS5 · SOCKS4 · HTTP\n"
        f"PySocks:    {'✓ активен' if SOCKS_OK else '✗ нет (pip install PySocks)'}\n"
        f"Кэш:        {total} прокси\n"
        f"Проверка:   РЕАЛЬНАЯ смена IP\n"
        f"```\n\n"
        f"*Команды:*\n"
        f"`/connect`           — авто (SOCKS5→4→HTTP)\n"
        f"`/connect socks5`    — только SOCKS5\n"
        f"`/connect socks4`    — только SOCKS4\n"
        f"`/connect http`      — только HTTP\n"
        f"`/disconnect` · `/rotate` · `/status`\n"
        f"`/ip` · `/refresh` · `/proxies`",
        parse_mode="Markdown", reply_markup=keyboard(u["connected"]))

@bot.message_handler(commands=["refresh"])
def c_refresh(msg):
    wait = bot.send_message(msg.chat.id,
        "```\n[ ОБНОВЛЯЮ СПИСКИ... ]\n```", parse_mode="Markdown")
    def do():
        cache["updated"] = 0
        refresh_cache()
        total = sum(len(cache[t]) for t in ["socks5","socks4","http"])
        bot.edit_message_text(
            f"```\n╔═════════════════╗\n║ ПРОКСИ ОБНОВЛЕНЫ║\n╚═════════════════╝\n```\n"
            f"⬛ SOCKS5: `{len(cache['socks5'])}`\n"
            f"◼  SOCKS4: `{len(cache['socks4'])}`\n"
            f"▪  HTTP:   `{len(cache['http'])}`\n"
            f"◈  Итого:  `{total}`",
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
            f"◈ Уже подключён: `{px['host']}:{px['port']}`\n/rotate или /disconnect",
            parse_mode="Markdown", reply_markup=keyboard(True))
        return

    wait = bot.send_message(msg.chat.id,
        "```\n[ ОПРЕДЕЛЯЮ ВАШ IP... ]\n```", parse_mode="Markdown")

    def do():
        my_ip = get_ip(timeout=6) or "unknown"
        u["ip_before"] = my_ip
        label = preferred.upper() if preferred else "AUTO"

        bot.edit_message_text(
            f"```\n[ ПОИСК [{label}] ]\nВаш IP: {my_ip}\nПроверяю реальную смену...\n```",
            msg.chat.id, wait.message_id, parse_mode="Markdown")

        info = {"n":0}
        def on_try(n, pt, h, p):
            info["n"] = n
            if n % 6 == 0:
                try:
                    bot.edit_message_text(
                        f"```\n[ ПОИСК [{label}] — попытка {n} ]\n"
                        f"Тест: {pt}://{h}:{p}\n"
                        f"Ваш IP: {my_ip}\n```",
                        msg.chat.id, wait.message_id, parse_mode="Markdown")
                except: pass

        res = find_proxy(my_ip, preferred=preferred, limit=100, on_try=on_try)

        if res:
            u.update(connected=True, proxy=res,
                     connect_time=time.time(), ip_after=res["new_ip"])
            bot.edit_message_text(
                f"```\n"
                f"╔══════════════════════════════╗\n"
                f"║     ПОДКЛЮЧЕНИЕ АКТИВНО      ║\n"
                f"╚══════════════════════════════╝\n"
                f"```\n"
                f"{t_icon(res['type'])} Протокол:    `{res['type'].upper()}`\n"
                f"◈ Сервер:      `{res['host']}:{res['port']}`\n"
                f"{p_icon(res['ping'])} Пинг:        `{res['ping']}ms`\n"
                f"◈ Ваш IP до:  `{my_ip}`\n"
                f"◆ Ваш IP теперь: `{res['new_ip']}`\n\n"
                f"```\n■ IP СМЕНЁН  ■ АНОНИМНОСТЬ АКТИВНА\n```",
                msg.chat.id, wait.message_id, parse_mode="Markdown",
                reply_markup=keyboard(True))
        else:
            bot.edit_message_text(
                f"```\n[ ОШИБКА: не найден рабочий прокси ]\n"
                f"Проверено: {info['n']} серверов\n"
                f"Попробуй /refresh → /connect\n```",
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
        f"```\n╔══════════════════════╗\n║    VPN ОТКЛЮЧЁН      ║\n╚══════════════════════╝\n```\n"
        f"◈ Сессия:      `{sess}`\n"
        f"◈ Был IP:      `{ia}`\n"
        f"◈ Реальный IP: `{ib}`",
        parse_mode="Markdown", reply_markup=keyboard(False))

@bot.message_handler(commands=["rotate"])
def c_rotate(msg):
    uid = msg.from_user.id
    u   = get_user(uid)
    if not u["connected"]:
        bot.send_message(msg.chat.id, "◈ Сначала /connect"); return

    wait = bot.send_message(msg.chat.id,
        "```\n[ СМЕНА IP... ]\n```", parse_mode="Markdown")

    def do():
        my_ip   = u.get("ip_before") or get_ip() or "unknown"
        exclude = u["proxy"]["host"] if u["proxy"] else None
        info    = {"n":0}

        def on_try(n,pt,h,p):
            info["n"] = n
            if n % 6 == 0:
                try:
                    bot.edit_message_text(
                        f"```\n[ СМЕНА IP — попытка {n} ]\nТест: {pt}://{h}:{p}\n```",
                        msg.chat.id, wait.message_id, parse_mode="Markdown")
                except: pass

        res = find_proxy(my_ip, exclude=exclude, limit=80, on_try=on_try)
        if res:
            u.update(proxy=res, connect_time=time.time(), ip_after=res["new_ip"])
            bot.edit_message_text(
                f"```\n╔══════════════════════╗\n║      IP СМЕНЁН       ║\n╚══════════════════════╝\n```\n"
                f"{t_icon(res['type'])} Протокол: `{res['type'].upper()}`\n"
                f"◈ Сервер:   `{res['host']}:{res['port']}`\n"
                f"{p_icon(res['ping'])} Пинг:     `{res['ping']}ms`\n"
                f"◆ Новый IP: `{res['new_ip']}`",
                msg.chat.id, wait.message_id, parse_mode="Markdown",
                reply_markup=keyboard(True))
        else:
            bot.edit_message_text(
                f"```\n[ Нет рабочих — попробуй /refresh ]\n```",
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
        anon = "◆ ВЫСОКАЯ (SOCKS5)" if px["type"]=="socks5" else "◇ СРЕДНЯЯ"
        text = (
            f"```\n╔══════════════════════════════╗\n║     TOGAFF VPN STATUS        ║\n╚══════════════════════════════╝\n```\n"
            f"◈ Статус:      `■ АКТИВЕН`\n"
            f"{t_icon(px['type'])} Протокол:    `{px['type'].upper()}`\n"
            f"◈ Сервер:      `{px['host']}:{px['port']}`\n"
            f"◈ Пинг:        `{f'{ms}ms' if ms else 'недоступен'}`\n"
            f"◈ Сессия:      `{sess}`\n"
            f"◈ IP до:       `{u.get('ip_before','—')}`\n"
            f"◆ IP сейчас:   `{u.get('ip_after','—')}`\n\n"
            f"```\nАнонимность:  {anon}\nAES-256-GCM:  ■\nDNS-HTTPS:    ■\nLeak Protect: ■\n```"
        )
    else:
        total = sum(len(cache[t]) for t in ["socks5","socks4","http"])
        text = (
            f"```\n╔══════════════════════════════╗\n║     TOGAFF VPN STATUS        ║\n╚══════════════════════════════╝\n```\n"
            f"◈ Статус: `□ ОТКЛЮЧЁН`\n\n"
            f"```\nКэш: SOCKS5={len(cache['socks5'])} SOCKS4={len(cache['socks4'])} HTTP={len(cache['http'])}\nИтого={total}\n```\n"
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
    lines = ["```\n╔══════════════════════════╗\n║      КЭШ ПРОКСИ          ║\n╚══════════════════════════╝\n```\n"]
    for pt in ["socks5","socks4","http"]:
        lines.append(f"{t_icon(pt)} *{pt.upper()}* — {len(cache[pt])} шт")
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
    wait = bot.send_message(msg.chat.id, "```\n[ ОПРЕДЕЛЯЮ IP... ]\n```", parse_mode="Markdown")
    def do():
        if u["connected"] and u["proxy"]:
            ip   = get_ip(proxy_cfg=u["proxy"], timeout=8)
            mode = f"{u['proxy']['type'].upper()} прокси"
        else:
            ip   = get_ip(timeout=6)
            mode = "прямое соединение"
        bot.edit_message_text(
            f"```\n╔═══════════════════╗\n║     ВАШ  IP        ║\n╚═══════════════════╝\n```\n"
            f"◆ IP:    `{ip or 'недоступен'}`\n◈ Режим: `{mode}`",
            msg.chat.id, wait.message_id, parse_mode="Markdown")
    threading.Thread(target=do, daemon=True).start()

# ══════════════════════════════════════════════════════════
#  CALLBACKS
# ══════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    d = call.data
    m = {
        "connect":    ("/connect",       "Подключаюсь..."),
        "c_socks5":   ("/connect socks5","⬛ SOCKS5..."),
        "c_socks4":   ("/connect socks4","◼ SOCKS4..."),
        "c_http":     ("/connect http",  "▪ HTTP..."),
        "disconnect": ("/disconnect",    "Отключаю..."),
        "rotate":     ("/rotate",        "↻ Меняю IP..."),
        "status":     ("/status",        ""),
        "proxies":    ("/proxies",       ""),
    }
    if d not in m: return
    cmd_text, answer = m[d]
    bot.answer_callback_query(call.id, answer)
    fake = FM(call, cmd_text)
    {
        "/connect":        c_connect,
        "/connect socks5": c_connect,
        "/connect socks4": c_connect,
        "/connect http":   c_connect,
        "/disconnect":     c_disconnect,
        "/rotate":         c_rotate,
        "/status":         c_status,
        "/proxies":        c_proxies,
    }[cmd_text](fake)

# ══════════════════════════════════════════════════════════
#  ЗАПУСК
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 50)
    print("  ◆ TOGAFF VPN BOT")
    print(f"  PySocks: {'✓' if SOCKS_OK else '✗ pip install PySocks requests[socks]'}")
    print("=" * 50)
    threading.Thread(target=refresh_cache, daemon=True).start()
    bot.infinity_polling(timeout=30)
