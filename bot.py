"""
  🌸 TOGAFF VPN · Astolfo Ultimate Edition 🌸
  pip install pyTelegramBotAPI requests[socks] PySocks pystyle
  python3 togaff_vpn_bot.py
"""

import telebot, requests, socket, threading, time, random, re, json, os
import zlib, base64, gzip, lzma, marshal, types, dis, io, struct
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ═══════════════════════════════════════
#            КОНФИГУРАЦИЯ
# ═══════════════════════════════════════
TOKEN        = "8603769389:AAFNrImTZhMY0ctceejoFbNkosE54cNsE30"
MINI_APP_URL = "https://t.me/togaff_vpn_bot/app"
ADMIN_IDS    = {7321093872}

USERS_FILE   = "allowed_users.json"
BANNED_FILE  = "banned_users.json"

WELCOME_PHOTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "astolfo.png")

TOP_FAST_COUNT = 30
VERIFY_WORKERS = 40
SCAN_SAMPLE    = 200
VERIFY_LIMIT   = 300
CACHE_TTL      = 1800
TOP_TTL        = 900

try:
    import socks
    SOCKS_OK = True
except ImportError:
    SOCKS_OK = False

bot = telebot.TeleBot(TOKEN, parse_mode=None)

# ═══════════════════════════════════════
#           ДОСТУП / WHITELIST
# ═══════════════════════════════════════
def _load(path, default):
    try:
        if os.path.exists(path):
            return json.load(open(path, encoding="utf-8"))
    except:
        pass
    return default

def _save(path, data):
    try:
        json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    except:
        pass

allowed_users: dict = _load(USERS_FILE, {})
banned_users:  set  = set(_load(BANNED_FILE, []))
_save_lock = threading.Lock()

def save_users():
    with _save_lock:
        _save(USERS_FILE,  {str(k): v for k, v in allowed_users.items()})
        _save(BANNED_FILE, list(banned_users))

def is_admin(uid):
    return int(uid) in ADMIN_IDS

def is_banned(uid):
    return int(uid) in {int(b) for b in banned_users}

def is_allowed(uid):
    uid = int(uid)
    if is_admin(uid):
        return True
    if is_banned(uid):
        return False
    return str(uid) in allowed_users or uid in allowed_users

def access_required(fn):
    def wrapper(obj, *a, **kw):
        try:
            uid  = obj.from_user.id
            chat = obj.chat.id if hasattr(obj, "chat") and obj.chat else obj.message.chat.id
        except:
            return
        if not is_allowed(uid):
            _send(chat,
                "🌸 Привет, анон!\n\n"
                "🔒 Доступ закрыт — бот работает только по приглашению.\n"
                "Напиши администратору чтобы получить доступ~ 💕")
            return
        return fn(obj, *a, **kw)
    wrapper.__name__ = fn.__name__
    return wrapper

def ts():
    return datetime.now().strftime("%d.%m %H:%M")

# ═══════════════════════════════════════
#            МОИ ПРОКСИ
# ═══════════════════════════════════════
MY_PROXIES_HTTP = [
    ("185.221.160.253", 80), ("185.221.160.214", 80), ("87.239.31.42", 80),
    ("109.197.153.121", 8888), ("188.235.146.220", 80), ("94.26.241.120", 80),
    ("89.23.112.143", 80), ("91.222.238.112", 80), ("82.208.111.19", 8080),
    ("185.244.173.101", 80), ("185.221.152.147", 80), ("91.107.124.250", 80),
    ("212.96.201.54", 80), ("5.180.241.126", 80), ("195.91.179.91", 80),
    ("95.217.105.20", 80), ("37.120.189.106", 80), ("89.31.143.1", 80),
    ("78.47.138.199", 80), ("89.31.143.2", 80), ("195.201.34.206", 80),
    ("89.31.143.3", 80), ("167.86.97.239", 8080), ("138.201.245.91", 8080),
    ("89.31.143.12", 80), ("51.178.43.147", 80), ("87.247.251.24", 80),
    ("83.143.145.67", 80), ("85.26.218.76", 80), ("162.19.226.235", 80),
    ("5.188.31.212", 80), ("87.247.251.240", 80), ("207.254.28.68", 80),
    ("104.167.29.113", 80), ("116.202.102.255", 80), ("77.238.66.2", 80),
    ("217.115.115.252", 80), ("85.187.17.39", 80), ("213.135.166.142", 80),
    ("217.145.93.115", 80), ("141.105.107.34", 80), ("93.170.73.47", 80),
    ("31.7.38.227", 80),
]



# ═══════════════════════════════════════
#          ИСТОЧНИКИ ПРОКСИ
# ═══════════════════════════════════════
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

# ═══════════════════════════════════════
#               КЭШ
# ═══════════════════════════════════════
cache = {
    "socks5": [], "socks4": [], "http": [],
    "updated": 0, "top_fast": [], "top_updated": 0,
    "scan_lock": threading.Lock(),
}
users = {}

def get_user(uid):
    uid = int(uid)
    if uid not in users:
        users[uid] = {
            "connected": False, "proxy": None, "connect_time": None,
            "ip_before": None, "ip_after": None,
            "sessions": 0, "total_rotates": 0,
            "bytes_up": 0, "bytes_down": 0,
        }
    return users[uid]

# ═══════════════════════════════════════
#         ЗАГРУЗКА ПРОКСИ
# ═══════════════════════════════════════
def fetch_list(url, timeout=14):
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return []
        out = []
        for line in r.text.splitlines():
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
    print("🌸 Загружаю прокси...")
    my_seen = {f"{h}:{p}" for h, p in MY_PROXIES_HTTP}
    my_list = list(MY_PROXIES_HTTP)
    with ThreadPoolExecutor(max_workers=8) as ex:
        for ptype, urls in SOURCES.items():
            base = list(my_list) if ptype == "http" else []
            seen = set(my_seen) if ptype == "http" else set()
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
            print(f"  {ptype}: {len(cache[ptype])}")
    cache["updated"] = time.time()
    print("✅ Кэш обновлён")

# ═══════════════════════════════════════
#       ПРОВЕРКА ПРОКСИ
# ═══════════════════════════════════════
IP_URLS = [
    "http://api.ipify.org",
    "http://checkip.amazonaws.com",
    "http://icanhazip.com",
    "http://ip.42.pl/raw",
    "http://ipecho.net/plain",
]

def tcp_ping(host, port, timeout=1.5):
    try:
        t0 = time.time()
        with socket.create_connection((host, port), timeout=timeout):
            pass
        return round((time.time() - t0) * 1000, 1)
    except:
        return None

def _proxy_url(ptype, host, port):
    if ptype == "socks5" and SOCKS_OK:
        return f"socks5h://{host}:{port}"
    if ptype == "socks4" and SOCKS_OK:
        return f"socks4://{host}:{port}"
    return f"http://{host}:{port}"

def get_ip_via(ptype, host, port, timeout=7):
    prx = {"http": _proxy_url(ptype, host, port), "https": _proxy_url(ptype, host, port)}
    for url in IP_URLS:
        try:
            r = requests.get(url, proxies=prx, timeout=timeout,
                             headers={"User-Agent": "curl/7.80.0"})
            ip = r.text.strip().split()[0]
            if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", ip):
                return ip
        except:
            continue
    return None

def get_my_ip(timeout=7):
    for url in IP_URLS:
        try:
            r = requests.get(url, timeout=timeout)
            ip = r.text.strip().split()[0]
            if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", ip):
                return ip
        except:
            continue
    return None

def verify_proxy(ptype, host, port, my_ip, tcp_t=1.5, ip_t=7):
    ms = tcp_ping(host, port, timeout=tcp_t)
    if ms is None:
        return None
    new_ip = get_ip_via(ptype, host, port, timeout=ip_t)
    if not new_ip:
        return None
    if my_ip and new_ip == my_ip:
        return None
    return {"type": ptype, "host": host, "port": port, "ping": ms,
            "new_ip": new_ip, "verified_at": time.time()}

# ═══════════════════════════════════════
#       СМАРТ-ПУЛ
# ═══════════════════════════════════════
def _all_candidates(ptype_filter=None):
    order = (["socks5", "socks4", "http"] if SOCKS_OK else ["http", "socks4", "socks5"])
    if ptype_filter:
        order = [ptype_filter]
    out = []
    seen = set()
    if not ptype_filter or ptype_filter == "http":
        for h, p in MY_PROXIES_HTTP:
            if (h, p) not in seen:
                seen.add((h, p))
                out.append(("http", h, p))
    for pt in order:
        pool = list(cache[pt])
        random.shuffle(pool)
        for h, p in pool:
            if (h, p) not in seen:
                seen.add((h, p))
                out.append((pt, h, p))
    return out

def _tcp_scan(candidates, workers=60, timeout=1.2):
    results = []
    lock = threading.Lock()

    def chk(args):
        pt, h, p = args
        ms = tcp_ping(h, p, timeout=timeout)
        if ms is not None:
            with lock:
                results.append((ms, pt, h, p))

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(as_completed([ex.submit(chk, c) for c in candidates]))
    results.sort()
    return [(pt, h, p, ms) for ms, pt, h, p in results]

def build_smart_pool(my_ip=None, sample=SCAN_SAMPLE,
                     workers=VERIFY_WORKERS, tcp_cb=None, http_cb=None):
    if my_ip is None:
        my_ip = get_my_ip() or ""
    refresh_cache()
    all_c = _all_candidates()
    random.shuffle(all_c)
    cands = all_c[:sample]
    total = len(cands)
    tcp_done = [0]
    lock = threading.Lock()

    def tcp_chk(args):
        pt, h, p = args
        ms = tcp_ping(h, p, timeout=1.2)
        with lock:
            tcp_done[0] += 1
            if tcp_cb:
                tcp_cb(tcp_done[0], total)
        return (ms, pt, h, p) if ms else None

    alive_raw = []
    with ThreadPoolExecutor(max_workers=60) as ex:
        for res in as_completed([ex.submit(tcp_chk, c) for c in cands]):
            r = res.result()
            if r:
                alive_raw.append(r)
    alive_raw.sort()
    alive = [(pt, h, p, ms) for ms, pt, h, p in alive_raw]
    print(f"  TCP живых: {len(alive)}/{total}")
    if not alive:
        return []

    http_total = len(alive)
    http_done = [0]
    lock2 = threading.Lock()
    results = []
    rlock = threading.Lock()

    def http_chk(args):
        pt, h, p, ms = args
        new_ip = get_ip_via(pt, h, p, timeout=7)
        with lock2:
            http_done[0] += 1
            if http_cb:
                http_cb(http_done[0], http_total)
        if not new_ip or new_ip == my_ip:
            return None
        return {"type": pt, "host": h, "port": p, "ping": ms,
                "new_ip": new_ip, "verified_at": time.time()}

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for res in as_completed([ex.submit(http_chk, a) for a in alive]):
            r = res.result()
            if r:
                with rlock:
                    results.append(r)

    results.sort(key=lambda x: x["ping"])
    cache["top_fast"] = results[:TOP_FAST_COUNT]
    cache["top_updated"] = time.time()
    print(f"🌸 Смарт-пул: {len(cache['top_fast'])} прокси")
    return cache["top_fast"]

def smart_pool_refresh_bg(my_ip=""):
    if time.time() - cache["top_updated"] > TOP_TTL and not cache["scan_lock"].locked():
        def bg():
            with cache["scan_lock"]:
                build_smart_pool(my_ip, sample=SCAN_SAMPLE // 2)
        threading.Thread(target=bg, daemon=True).start()

def find_best_proxy(my_ip, exclude=None, ptype_filter=None, on_try=None):
    pool = [p for p in cache["top_fast"]
            if (not exclude or p["host"] != exclude)
            and (not ptype_filter or p["type"] == ptype_filter)]

    if pool:
        found = [None]
        stop = threading.Event()
        lock = threading.Lock()

        def recheck(px):
            if stop.is_set():
                return
            r = verify_proxy(px["type"], px["host"], px["port"], my_ip, tcp_t=1.5, ip_t=7)
            if r and not stop.is_set():
                with lock:
                    if found[0] is None:
                        found[0] = r
                        stop.set()

        with ThreadPoolExecutor(max_workers=min(len(pool), 20)) as ex:
            for f in as_completed([ex.submit(recheck, px) for px in pool]):
                if stop.is_set():
                    break
        if found[0]:
            return found[0]

    refresh_cache()
    all_c = _all_candidates(ptype_filter)
    if exclude:
        all_c = [(pt, h, p) for pt, h, p in all_c if h != exclude]

    batch = 80
    n = 0
    for i in range(0, min(len(all_c), VERIFY_LIMIT * 2), batch):
        chunk = all_c[i:i + batch]
        alive = _tcp_scan(chunk, workers=60, timeout=1.2)
        n += len(chunk)
        if on_try:
            on_try(n,
                   alive[0][0] if alive else "http",
                   alive[0][1] if alive else "...",
                   alive[0][3] if alive else 0)
        if not alive:
            continue

        found = [None]
        stop = threading.Event()
        lock = threading.Lock()

        def http_find(args):
            pt, h, p, ms = args
            if stop.is_set():
                return
            new_ip = get_ip_via(pt, h, p, timeout=7)
            if new_ip and new_ip != my_ip and not stop.is_set():
                with lock:
                    if found[0] is None:
                        found[0] = {"type": pt, "host": h, "port": p, "ping": ms,
                                    "new_ip": new_ip, "verified_at": time.time()}
                        stop.set()

        with ThreadPoolExecutor(max_workers=VERIFY_WORKERS) as ex:
            for f in as_completed([ex.submit(http_find, a) for a in alive]):
                if stop.is_set():
                    break
        if found[0]:
            return found[0]
    return None

# ═══════════════════════════════════════
#     ДЕОБФУСКАТОР v1 (встроенный)
# ═══════════════════════════════════════
_exec_pattern = r"exec\(\(_\)\(b'([\s\S]+?)'\)\)"
_comments_pat = r"#(.*?)\n"
_deobf_note   = "# DECODED BY @ArrhythmiaFucksn\n\n"

_obfuscation_patterns = {
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b64decode\(__\[::-1\]\);": "base64",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b32decode\(__\[::-1\]\);": "base32",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b16decode\(__\[::-1\]\);": "base16",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('zlib'\)\.decompress\(__\[::-1\]\);":  "zlib",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('gzip'\)\.decompress\(__\[::-1\]\);":  "gzip",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('lzma'\)\.decompress\(__\[::-1\]\);":  "lzma",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('zlib'\)\.decompress\(s*__import__\('base64'\)\.b64decode\(__\[::-1\]\)\);": "base64+zlib",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('gzip'\)\.decompress\(s*__import__\('base64'\)\.b64decode\(__\[::-1\]\)\);": "base64+gzip",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('lzma'\)\.decompress\(s*__import__\('base64'\)\.b64decode\(__\[::-1\]\)\);": "base64+lzma",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('zlib'\)\.decompress\(s*__import__\('base64'\)\.b32decode\(__\[::-1\]\)\);": "base32+zlib",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('gzip'\)\.decompress\(s*__import__\('base64'\)\.b32decode\(__\[::-1\]\)\);": "base32+gzip",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('lzma'\)\.decompress\(s*__import__\('base64'\)\.b32decode\(__\[::-1\]\)\);": "base32+lzma",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('zlib'\)\.decompress\(s*__import__\('base64'\)\.b16decode\(__\[::-1\]\)\);": "base16+zlib",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('gzip'\)\.decompress\(s*__import__\('base64'\)\.b16decode\(__\[::-1\]\)\);": "base16+gzip",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('lzma'\)\.decompress\(s*__import__\('base64'\)\.b16decode\(__\[::-1\]\)\);": "base16+lzma",
    r"_=lambda __:__import__\('marshal'\)\.loads\(__import__\('gzip'\)\.decompress\(__import__\('lzma'\)\.decompress\(__import__\('zlib'\)\.decompress\(__import__\('base64'\)\.b64decode\(__\[::-1\]\)\)\)\)\);exec\(_\('(.*?)'\)\)": "rendy (marshal+gzip+lzma+zlib+base64)",
}

def _strip_comments(code: str) -> str:
    return re.sub(_comments_pat, "", code)

def _deobf_b64(code: str) -> str:
    def dec(m):
        s = m.group(1)
        pad = len(s) % 4
        if pad:
            s += "=" * (8 - pad)
        return base64.b64decode(s[::-1]).decode("utf-8", errors="replace")
    while re.search(_exec_pattern, code):
        code = re.sub(_exec_pattern, dec, code)
        code = re.sub(r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b64decode\(__\[::-1\]\);", "", code)
    return _strip_comments(code).strip()

def _deobf_b32(code: str) -> str:
    def dec(m):
        s = m.group(1)
        pad = len(s) % 4
        if pad:
            s += "=" * (8 - pad)
        return base64.b32decode(s[::-1]).decode("utf-8", errors="replace")
    while re.search(_exec_pattern, code):
        code = re.sub(_exec_pattern, dec, code)
        code = re.sub(r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b32decode\(__\[::-1\]\);", "", code)
    return _strip_comments(code).strip()

def _deobf_b16(code: str) -> str:
    def dec(m):
        return base64.b16decode(m.group(1)[::-1]).decode("utf-8", errors="replace")
    while re.search(_exec_pattern, code):
        code = re.sub(_exec_pattern, dec, code)
        code = re.sub(r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b16decode\(__\[::-1\]\);", "", code)
    return _strip_comments(code).strip()

def _deobf_combo(code: str, base_fn, compress_mod) -> str:
    def dec(m):
        s = m.group(1)
        pad = len(s) % 4
        if pad:
            s += "=" * (8 - pad)
        decoded = base_fn(s[::-1])
        return compress_mod.decompress(decoded).decode("utf-8", errors="replace")
    while re.search(_exec_pattern, code):
        code = re.sub(_exec_pattern, dec, code)
    return _strip_comments(code).strip()

def detect_obfuscation(code: str) -> str:
    for pat, name in _obfuscation_patterns.items():
        if re.search(pat, code):
            return name
    return None

def deobfuscate_code(code: str) -> tuple:
    """Returns (deobfuscated_code, method_name) or (None, error_msg)"""
    method = detect_obfuscation(code)
    if not method:
        return None, "Обфускация не обнаружена"
    try:
        result = None
        if method == "base64":
            result = _deobf_b64(code)
        elif method == "base32":
            result = _deobf_b32(code)
        elif method == "base16":
            result = _deobf_b16(code)
        elif method == "base64+zlib":
            result = _deobf_combo(code, base64.b64decode, zlib)
        elif method == "base64+gzip":
            result = _deobf_combo(code, base64.b64decode, gzip)
        elif method == "base64+lzma":
            result = _deobf_combo(code, base64.b64decode, lzma)
        elif method == "base32+zlib":
            result = _deobf_combo(code, base64.b32decode, zlib)
        elif method == "base32+gzip":
            result = _deobf_combo(code, base64.b32decode, gzip)
        elif method == "base32+lzma":
            result = _deobf_combo(code, base64.b32decode, lzma)
        elif method == "base16+zlib":
            result = _deobf_combo(code, base64.b16decode, zlib)
        elif method == "base16+gzip":
            result = _deobf_combo(code, base64.b16decode, gzip)
        elif method == "base16+lzma":
            result = _deobf_combo(code, base64.b16decode, lzma)
        elif "rendy" in method:
            pat = r"_=lambda __:__import__\('marshal'\)\.loads\(.+?\);exec\(_\('(.*?)'\)\)"
            m = re.search(pat, code)
            if m:
                enc = m.group(1)
                raw = base64.b64decode(enc[::-1])
                raw = zlib.decompress(raw)
                raw = lzma.decompress(raw)
                raw = gzip.decompress(raw)
                result = marshal.loads(raw).decode("utf-8", errors="replace")
        if result is not None:
            return _deobf_note + result, method
        return None, f"Не удалось декодировать ({method})"
    except Exception as e:
        return None, f"Ошибка: {e}"

# ═══════════════════════════════════════
#   ДЕОБФУСКАТОР v2 — Ренди 2.0
#   Universal Python Deobfuscator
#   marshal/gzip/lzma/zlib/base64 + XOR
#   + state-machine + call-wrappers
# ═══════════════════════════════════════

XOR_ADJ = 2

def r2_try_base64(data: bytes):
    try:
        return base64.b64decode(data)
    except Exception:
        return None

def r2_try_zlib(data: bytes):
    try:
        return zlib.decompress(data)
    except Exception:
        return None

def r2_try_gzip(data: bytes):
    try:
        return gzip.decompress(data)
    except Exception:
        return None

def r2_try_lzma(data: bytes):
    try:
        return lzma.decompress(data)
    except Exception:
        return None

def r2_try_marshal(data: bytes):
    for offset in (0, 4, 8, 12, 16):
        try:
            code = marshal.loads(data[offset:])
            if isinstance(code, types.CodeType):
                out = io.StringIO()
                dis.dis(code, file=out)
                return out.getvalue()
        except Exception:
            continue
    return None

def r2_try_decompress_chain(data: bytes, depth: int = 0, max_depth: int = 8) -> bytes:
    if depth >= max_depth:
        return data
    for fn in (r2_try_base64, r2_try_zlib, r2_try_gzip, r2_try_lzma):
        result = fn(data)
        if result and result != data:
            return r2_try_decompress_chain(result, depth + 1, max_depth)
    return data

def r2_extract_layer1(source: str) -> str:
    patterns = [
        r"(?:__[a-z_]+__\s*=\s*)?(?:exec|eval)\s*\(\s*(?:.*?\.)?(?:decompress|loads|decode)\s*\([^)]*?['\"]([ A-Za-z0-9+/=\n]+)['\"]",
        r"(?:exec|eval)\s*\([^)]*?b['\"]([0-9a-fA-F\\x]+)['\"]",
    ]
    for p in patterns:
        m = re.search(p, source, re.DOTALL)
        if m:
            candidate = m.group(1).encode()
            result = r2_try_decompress_chain(candidate)
            try:
                decoded = result.decode('utf-8')
                if len(decoded) > 50 and ('def ' in decoded or 'import' in decoded):
                    return decoded
            except Exception:
                pass

    blob_pat = re.compile(r"b['\"]([ A-Za-z0-9+/=]{200,})['\"]")
    for m in blob_pat.finditer(source):
        candidate = m.group(1).encode()
        result = r2_try_decompress_chain(candidate)
        try:
            decoded = result.decode('utf-8')
            if 'def ' in decoded or 'import' in decoded:
                return decoded
        except Exception:
            pass
    return source

def r2_decode_xor(hex_str: str, key: int, adj: int = None) -> str:
    if adj is None:
        adj = XOR_ADJ
    raw = bytes.fromhex(hex_str)
    return bytes([b ^ (key ^ adj) for b in raw]).decode('utf-8', errors='replace')

def r2_detect_wrapper_names(source: str) -> list:
    pattern = re.compile(
        r'def\s+(\w+)\s*\(\s*\w+\s*,\s*\w+\s*,\s*\w+\s*\)\s*:[^\n]*\n'
        r'(?:.*?\n)*?.*?raise\s+\w+\s*\(\s*\w+\s*,\s*\w+\s*,\s*\w+\s*\)',
        re.MULTILINE
    )
    names = pattern.findall(source)
    if names:
        return list(set(names))
    return ['俩瀒唼', '摒嬻揿', '獄壧厮', '饜蝶曅', '雽蒃请']

def r2_find_and_decode_xor(line: str) -> tuple:
    count = 0
    iter_var = r'\w+'
    xor_pattern = re.compile(
        iter_var + r'\s*\^\s*\((\d+)\s*\^'
        r'[^\n]*?'
        r"bytes\.fromhex[,\s\[('\"]*([0-9a-fA-F]+)['\"]"
    )
    while True:
        m = xor_pattern.search(line)
        if not m:
            break
        key = int(m.group(1))
        hex_str = m.group(2)
        decoded_repr = repr(r2_decode_xor(hex_str, key))
        hex_quote_pos = line.find(f"'{hex_str}'")
        if hex_quote_pos == -1:
            hex_quote_pos = line.find(f'"{hex_str}"')
        if hex_quote_pos == -1:
            break
        decode_end = line.find(".decode, ['utf-8'], {})", hex_quote_pos)
        if decode_end != -1:
            end_pos = decode_end + len(".decode, ['utf-8'], {})")
        else:
            decode_end = line.find(".decode(['utf-8'])", hex_quote_pos)
            if decode_end != -1:
                end_pos = decode_end + len(".decode(['utf-8'])")
            else:
                decode_end = line.find(".decode('utf-8')", hex_quote_pos)
                if decode_end != -1:
                    end_pos = decode_end + len(".decode('utf-8')")
                else:
                    break
        WRAPPER_NAMES = r2_detect_wrapper_names(line) or ['俩瀒唼', '摒嬻揿', '獄壧厮', '饜蝶曅']
        wrapper_positions = []
        for w in WRAPPER_NAMES:
            pos = 0
            while True:
                p = line.find(w, pos)
                if p == -1 or p >= hex_quote_pos:
                    break
                wrapper_positions.append(p)
                pos = p + len(w)
        if not wrapper_positions:
            break
        wrapper_positions.sort()
        start_pos = None
        for wp in reversed(wrapper_positions):
            wnames_found = [w for w in WRAPPER_NAMES if line[wp:wp+len(w)] == w]
            wname_len = len(wnames_found[0]) if wnames_found else 3
            open_paren = wp + wname_len
            if open_paren >= len(line) or line[open_paren] != '(':
                continue
            depth = 0
            for cp in range(open_paren, min(end_pos, len(line))):
                if line[cp] == '(':
                    depth += 1
                elif line[cp] == ')':
                    depth -= 1
            if depth == 0:
                start_pos = wp
                break
        if start_pos is None:
            inner_start = line.rfind('bytes', 0, hex_quote_pos)
            if inner_start != -1:
                for wp in reversed(wrapper_positions):
                    if wp < inner_start:
                        start_pos = wp
                        break
            if start_pos is None:
                break
        count += 1
        line = line[:start_pos] + decoded_repr + line[end_pos:]
    return line, count

def r2_decode_all_xor_strings(source: str) -> str:
    lines = source.split('\n')
    total = 0
    result = []
    for line in lines:
        if 'fromhex' in line and ('噴蜥巀' in line or '^' in line):
            new_line, count = r2_find_and_decode_xor(line)
            total += count
            result.append(new_line)
        else:
            result.append(line)
    return '\n'.join(result)

def r2_simplify_wrappers(source: str, wrapper_names: list) -> str:
    if not wrapper_names:
        return source
    WRAPPERS_RE = '(?:' + '|'.join(re.escape(w) for w in wrapper_names) + ')'
    simple = re.compile(WRAPPERS_RE + r'\(([^,\n]+?),\s*\[([^\[\]\n]*?)\],\s*\{\}\)')
    def simple_r(m):
        fn = m.group(1).strip()
        args = m.group(2).strip()
        return f'{fn}({args})' if args else f'{fn}()'
    kw = re.compile(WRAPPERS_RE + r'\(([^,\n]+?),\s*\[([^\[\]\n]*?)\],\s*\{([^{}\n]+?)\}\)')
    def kw_r(m):
        fn = m.group(1).strip()
        args = m.group(2).strip()
        kw_str = re.sub(r"'(\w+)':\s*", r'\1=', m.group(3).strip())
        return f'{fn}({args}, {kw_str})' if args else f'{fn}({kw_str})'
    for _ in range(12):
        new = simple.sub(simple_r, source)
        new = kw.sub(kw_r, new)
        if new == source:
            break
        source = new
    return source

def r2_remove_state_machine(source: str) -> str:
    final = []
    i = 0
    lines = source.split('\n')
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if re.match(r'^while \w+ != \d+:\s*$', s):
            i += 1; continue
        if re.match(r'^(?:if|elif) \w+ == \d{5,9}:\s*$', s):
            i += 1; continue
        if re.match(r'^\w+ = \d{5,9}\s*$', s):
            i += 1; continue
        if re.match(r'^if \(\w+ \* \w+ \+ \w+\) % 2 == 0:\s*$', s):
            indent = len(line) - len(line.lstrip())
            i += 1
            while i < len(lines):
                bl = lines[i]
                bs = bl.strip()
                bi = len(bl) - len(bl.lstrip()) if bs else 0
                if bs and bi <= indent:
                    break
                if bs:
                    final.append(bl[4:] if bl.startswith('    ') else bl)
                i += 1
            continue
        if s == 'else:' and i + 1 < len(lines):
            ns = lines[i + 1].strip()
            if re.match(r'^\w+ = \d{1,4}\s*$', ns):
                i += 2; continue
        final.append(line)
        i += 1
    return '\n'.join(final)

def r2_remove_dummy_vars(source: str) -> str:
    lines = source.split('\n')
    result = []
    for line in lines:
        s = line.strip()
        m = re.match(r'^(\w+)\s*=\s*(\d{1,4})\s*$', s)
        if m:
            varname = m.group(1)
            occurrences = len(re.findall(r'\b' + re.escape(varname) + r'\b', source))
            if occurrences <= 2:
                continue
        result.append(line)
    return '\n'.join(result)

def r2_simplify_getattr(source: str) -> str:
    pattern = re.compile(r"getattr\((\w+),\s*'([a-zA-Z_]\w*)'\)")
    source = pattern.sub(lambda m: f"{m.group(1)}.{m.group(2)}", source)
    pattern2 = re.compile(r'getattr\((\w+),\s*"([a-zA-Z_]\w*)"\)')
    source = pattern2.sub(lambda m: f"{m.group(1)}.{m.group(2)}", source)
    return source

def r2_simplify_imports(source: str) -> str:
    pattern = re.compile(r"getattr\(__import__\('(\w+)'\),\s*'([a-zA-Z_]\w*)'\)")
    return pattern.sub(lambda m: f"__import__('{m.group(1)}').{m.group(2)}", source)

def r2_cleanup(source: str) -> str:
    source = re.sub(r'\n{4,}', '\n\n\n', source)
    source = re.sub(r'[ \t]+\n', '\n', source)
    lines = source.split('\n')
    result = []
    skip_until_indent = None
    for line in lines:
        s = line.strip()
        indent = len(line) - len(line.lstrip()) if s else -1
        if skip_until_indent is not None:
            if s and indent <= skip_until_indent:
                skip_until_indent = None
            else:
                if s:
                    continue
        if s and re.match(r'^(return|raise)\b', s):
            skip_until_indent = indent
        result.append(line)
    return '\n'.join(result)

def rendy2_deobfuscate(source: str, xor_adj: int = 2) -> str:
    """Ренди 2.0 — Universal Python Deobfuscator. Возвращает деобфусцированный код."""
    global XOR_ADJ
    XOR_ADJ = xor_adj
    wrapper_names = r2_detect_wrapper_names(source)
    source = r2_extract_layer1(source)
    source = r2_decode_all_xor_strings(source)
    source = r2_simplify_wrappers(source, wrapper_names)
    source = r2_remove_state_machine(source)
    source = r2_remove_dummy_vars(source)
    source = r2_simplify_getattr(source)
    source = r2_simplify_imports(source)
    source = r2_cleanup(source)
    return source

# ═══════════════════════════════════════
#              УТИЛИТЫ UI  🌸
# ═══════════════════════════════════════
def fmt_time(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sc = int(s % 60)
    if h:
        return f"{h}ч {m:02d}м {sc:02d}с"
    if m:
        return f"{m}м {sc:02d}с"
    return f"{sc}с"

def ping_bar(ms):
    if ms is None:   return "⬜⬜⬜⬜⬜  нет данных"
    if ms < 80:      return "🟩🟩🟩🟩🟩  молниеносно~"
    if ms < 150:     return "🟩🟩🟩🟩⬜  отлично!"
    if ms < 250:     return "🟨🟨🟨⬜⬜  хорошо"
    if ms < 400:     return "🟧🟧⬜⬜⬜  средне"
    return                  "🟥⬜⬜⬜⬜  медленно..."

def proto_icon(pt):
    return {"socks5": "🔵", "socks4": "🟣", "http": "⚪", "https": "🔐"}.get(pt, "⚫")

def lbar(n, total=100, w=10):
    f = min(int(w * n / max(total, 1)), w)
    return "▰" * f + "▱" * (w - f)

ASTOLFO_ART = (
    "╔══════════════════════╗\n"
    "║  🌸 TOGAFF VPN 🌸   ║\n"
    "║    (\\(\\  ∧＿∧        ║\n"
    "║   (｡•ω•｡)つ━━✿✿✿    ║\n"
    "║  Astolfo Edition 💕  ║\n"
    "╚══════════════════════╝"
)

# ═══════════════════════════════════════
#     ОТПРАВКА / РЕДАКТИРОВАНИЕ
# ═══════════════════════════════════════
def _send(chat_id, text, kb=None):
    try:
        return bot.send_message(chat_id, text, reply_markup=kb)
    except Exception as e:
        print(f"[send ERR] {e}")
        return None

def _edit(chat_id, msg_id, text, kb=None):
    try:
        return bot.edit_message_text(text, chat_id, msg_id, reply_markup=kb)
    except Exception as e:
        print(f"[edit ERR] {e}")

def _updater(chat_id, msg_id):
    last = [0.0]
    def upd(text, kb=None, force=False):
        now = time.time()
        if not force and now - last[0] < 2.0:
            return
        last[0] = now
        _edit(chat_id, msg_id, text, kb)
    return upd

# ═══════════════════════════════════════
#           КЛАВИАТУРЫ  🌸
# ═══════════════════════════════════════
def kb_main(connected=False):
    k = telebot.types.InlineKeyboardMarkup(row_width=2)
    if connected:
        k.add(
            telebot.types.InlineKeyboardButton("🔴 Отключить",   callback_data="disconnect"),
            telebot.types.InlineKeyboardButton("🔄 Сменить IP",  callback_data="rotate"),
        )
        k.add(
            telebot.types.InlineKeyboardButton("📋 Конфиг",      callback_data="generate"),
            telebot.types.InlineKeyboardButton("📊 Статус",      callback_data="status"),
        )
    else:
        k.add(telebot.types.InlineKeyboardButton("⚡ Быстрое подключение", callback_data="connect"))
        k.add(
            telebot.types.InlineKeyboardButton("📊 Статус",     callback_data="status"),
            telebot.types.InlineKeyboardButton("🗂 Серверы",    callback_data="proxies"),
        )
    k.add(
        telebot.types.InlineKeyboardButton("🔵 SOCKS5", callback_data="c_socks5"),
        telebot.types.InlineKeyboardButton("🟣 SOCKS4",  callback_data="c_socks4"),
        telebot.types.InlineKeyboardButton("⚪ HTTP",    callback_data="c_http"),
    )
    k.add(telebot.types.InlineKeyboardButton("🔓 Деобфускатор (АВТО)", callback_data="deobf_menu"))
    return k

def kb_generate():
    k = telebot.types.InlineKeyboardMarkup(row_width=1)
    k.add(telebot.types.InlineKeyboardButton("🔄 Другой прокси", callback_data="regen"))
    k.add(telebot.types.InlineKeyboardButton("◀ Назад",          callback_data="back_main"))
    return k

def kb_admin():
    k = telebot.types.InlineKeyboardMarkup(row_width=2)
    k.add(
        telebot.types.InlineKeyboardButton("👥 Пользователи",  callback_data="adm_users"),
        telebot.types.InlineKeyboardButton("🚫 Бан-лист",      callback_data="adm_banned"),
    )
    k.add(
        telebot.types.InlineKeyboardButton("📊 Статистика",    callback_data="adm_stats"),
        telebot.types.InlineKeyboardButton("🔄 Обновить базу", callback_data="adm_refresh"),
    )
    k.add(
        telebot.types.InlineKeyboardButton("⚡ Скан серверов", callback_data="adm_scan"),
        telebot.types.InlineKeyboardButton("📢 Рассылка",      callback_data="adm_broadcast"),
    )
    k.add(telebot.types.InlineKeyboardButton("◀ Назад",         callback_data="back_main"))
    return k

def kb_proxy_list(proxies, page=0):
    k = telebot.types.InlineKeyboardMarkup(row_width=1)
    per = 5
    start = page * per
    chunk = proxies[start:start + per]
    for i, p in enumerate(chunk):
        label = f"{proto_icon(p['type'])} {p['host']}:{p['port']}  {p['ping']}ms"
        k.add(telebot.types.InlineKeyboardButton(label, callback_data=f"pick_{start + i}"))
    row = []
    if page > 0:
        row.append(telebot.types.InlineKeyboardButton("◀", callback_data=f"pxpage_{page-1}"))
    if start + per < len(proxies):
        row.append(telebot.types.InlineKeyboardButton("▶", callback_data=f"pxpage_{page+1}"))
    if row:
        k.add(*row)
    k.add(telebot.types.InlineKeyboardButton("◀ Назад", callback_data="back_main"))
    return k

def kb_deobf():
    k = telebot.types.InlineKeyboardMarkup(row_width=1)
    k.add(telebot.types.InlineKeyboardButton("⚡ АВТО (v1 → v2 fallback)",    callback_data="deobf_auto"))
    k.add(telebot.types.InlineKeyboardButton("🔍 Определить метод",            callback_data="deobf_detect"))
    k.add(telebot.types.InlineKeyboardButton("🔓 Только v1 (base/zlib/rendy)", callback_data="deobf_run"))
    k.add(telebot.types.InlineKeyboardButton("🔓 Только v2 (Ренди 2.0)",       callback_data="deobf2_run"))
    k.add(telebot.types.InlineKeyboardButton("◀ Назад",                        callback_data="back_main"))
    return k

def kb_deobf2():
    k = telebot.types.InlineKeyboardMarkup(row_width=1)
    k.add(telebot.types.InlineKeyboardButton("🔓 Деобфусцировать (Ренди 2.0)", callback_data="deobf2_run"))
    k.add(telebot.types.InlineKeyboardButton("◀ Назад",                         callback_data="back_main"))
    return k

# Состояние деобфускатора по юзеру
# waiting        = v1 полная деобфускация
# waiting_detect = v1 только определение
# waiting_v2     = v2 Ренди 2.0
_deobf_state = {}

class FMsg:
    def __init__(self, call, text=""):
        _cid = call.message.chat.id
        self.chat = type("C", (), {"id": _cid})()
        self.message = type("M", (), {"chat": self.chat, "message_id": call.message.message_id})()
        self.from_user = type("U", (), {
            "id": call.from_user.id,
            "first_name": call.from_user.first_name or "User",
            "username": getattr(call.from_user, "username", None),
        })()
        self.text = text

# ═══════════════════════════════════════
#               /start
# ═══════════════════════════════════════
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    try:
        uid  = int(msg.from_user.id)
        name = msg.from_user.first_name or "анон"
        print(f"[start] uid={uid} admin={is_admin(uid)} allowed={is_allowed(uid)}")

        if is_admin(uid):
            key = str(uid)
            if key not in allowed_users:
                allowed_users[key] = {
                    "username":   getattr(msg.from_user, "username", "") or "",
                    "first_name": name,
                    "added":      ts(),
                    "uses":       0
                }
                save_users()

        if not is_allowed(uid):
            bot.send_message(msg.chat.id,
                f"{ASTOLFO_ART}\n\n"
                "Привет! Доступ закрыт~\n\n"
                "Бот работает только по приглашению.\n"
                "Обратись к администратору")
            return

        key = str(uid)
        if key in allowed_users:
            allowed_users[key]["uses"] = allowed_users[key].get("uses", 0) + 1
            save_users()

        u     = get_user(uid)
        total = sum(len(cache[t]) for t in ["socks5", "socks4", "http"])
        fast  = len(cache["top_fast"])
        conn_line = (f"Подключён — {u['proxy']['host']} ({u['proxy']['type'].upper()})"
                     if u["connected"] and u["proxy"] else "Не подключён")
        adm_badge = " [ADMIN]" if is_admin(uid) else ""

        text = (
            f"{ASTOLFO_ART}\n\n"
            f"Привет, {name}!{adm_badge}\n\n"
            f"Togaff VPN - Astolfo Edition\n"
            f"──────────────────────\n"
            f"{conn_line}\n\n"
            f"Прокси в базе: {total}\n"
            f"Лучших в пуле: {fast}\n\n"
            f"──────────────────────\n"
            f"Команды:\n"
            f"/connect - подключение\n"
            f"/disconnect - отключиться\n"
            f"/rotate - сменить IP\n"
            f"/pick - выбрать прокси\n"
            f"/scan - найти серверы\n"
            f"/status - статус\n"
            f"/ip - мой IP\n"
            f"/generate - конфиг\n"
            f"/proxies - список серверов\n"
            f"/refresh - обновить базу\n"
            f"/deobf  - авто деобфускатор\n"
            f"/deobf2 - Ренди 2.0 (universal)\n"
        )
        if is_admin(uid):
            text += "/admin - панель админа\n"

        if os.path.exists(WELCOME_PHOTO):
            try:
                with open(WELCOME_PHOTO, "rb") as f:
                    bot.send_photo(msg.chat.id, f)
            except Exception as e:
                print(f"[start] фото: {e}")

        bot.send_message(msg.chat.id, text, reply_markup=kb_main(u["connected"]))

    except Exception as e:
        import traceback
        print(f"[start] ОШИБКА: {e}\n{traceback.format_exc()}")
        try:
            bot.send_message(msg.chat.id, "Бот работает! Попробуй /start ещё раз")
        except:
            pass

# ═══════════════════════════════════════
#       /deobf — деобфускатор v1
# ═══════════════════════════════════════
@bot.message_handler(commands=["deobf"])
@access_required
def cmd_deobf(msg):
    uid = msg.from_user.id
    _deobf_state[uid] = "waiting_auto"
    _send(msg.chat.id,
        "🔓 Авто-деобфускатор 🌸\n\n"
        "Режим АВТО: сначала пробует v1, если не вышло — автоматически запускает Ренди 2.0\n\n"
        "Поддерживаемые методы:\n"
        "v1:\n"
        "  • base64 / base32 / base16\n"
        "  • zlib / gzip / lzma\n"
        "  • base64+zlib / base64+gzip / base64+lzma\n"
        "  • base32+zlib / base32+gzip / base32+lzma\n"
        "  • base16+zlib / base16+gzip / base16+lzma\n"
        "  • Rendy obf (marshal+gzip+lzma+zlib+base64)\n\n"
        "v2 (Ренди 2.0 fallback):\n"
        "  • XOR строки + state-machine\n"
        "  • Call-wrappers + dummy vars\n"
        "  • getattr chains + cleanup\n\n"
        "📎 Отправь .py файл:",
        kb_deobf())

# ═══════════════════════════════════════
#    /deobf2 — Ренди 2.0 Universal
# ═══════════════════════════════════════
@bot.message_handler(commands=["deobf2"])
@access_required
def cmd_deobf2(msg):
    _send(msg.chat.id,
        "🔓 Деобфускатор v2 — Ренди 2.0\n\n"
        "Universal Python Deobfuscator\n"
        "──────────────────────\n"
        "Снимает слои:\n"
        "• marshal / gzip / lzma / zlib / base64\n"
        "• XOR-encoded строки\n"
        "• State-machine control flow\n"
        "• Call-wrapper функции\n"
        "• Dead branches / dummy переменные\n"
        "• getattr() chains\n\n"
        "Отправь .py файл для деобфускации:",
        kb_deobf2())

# ═══════════════════════════════════════
#   Обработка документов (.py файлов)
# ═══════════════════════════════════════
@bot.message_handler(content_types=["document"])
def handle_document(msg):
    uid = int(msg.from_user.id)

    if not is_allowed(uid):
        bot.send_message(msg.chat.id, "Доступ закрыт~")
        return

    state = _deobf_state.get(uid)

    if state not in ("waiting", "waiting_detect", "waiting_v2", "waiting_auto"):
        bot.send_message(msg.chat.id,
            "Чтобы деобфусцировать файл — нажми кнопку Деобфускатор или /deobf / /deobf2")
        return

    doc = msg.document
    if not doc.file_name.endswith(".py"):
        bot.send_message(msg.chat.id, "Только .py файлы!")
        return

    _deobf_state.pop(uid, None)
    wait = bot.send_message(msg.chat.id, "🔍 Читаю файл...")

    def do():
        try:
            file_info  = bot.get_file(doc.file_id)
            downloaded = bot.download_file(file_info.file_path)
            code = downloaded.decode("utf-8", errors="replace")
            lines_in  = code.count('\n') + 1
            chars_in  = len(code)

            # ══════════════════════════════════════
            # РЕЖИМ: только определение (v1 detect)
            # ══════════════════════════════════════
            if state == "waiting_detect":
                bot.edit_message_text("🔍 Определяю метод обфускации...", msg.chat.id, wait.message_id)
                method_v1 = detect_obfuscation(code)

                # Дополнительно проверяем признаки v2
                has_xor    = bool(re.search(r'bytes\.fromhex', code) and re.search(r'\^\s*\(\d+\s*\^', code))
                has_sm     = bool(re.search(r'while \w+ != \d+:', code))
                has_wrap   = bool(re.search(r'def \w+\s*\(\s*\w+\s*,\s*\w+\s*,\s*\w+\s*\)\s*:', code))
                has_exec   = bool(re.search(r'exec\s*\(', code))
                has_b64bl  = bool(re.search(r"b'[A-Za-z0-9+/=]{200,}'", code))

                lines_det = [
                    f"🔬 Анализ: {doc.file_name}\n",
                    f"──────────────────────\n",
                    f"📄 Строк: {lines_in}  |  Символов: {chars_in:,}\n",
                    f"──────────────────────\n",
                ]
                if method_v1:
                    lines_det.append(f"✅ v1 метод: {method_v1}\n")
                    lines_det.append(f"→ Используй /deobf для расшифровки\n")
                else:
                    lines_det.append(f"❌ v1 паттерн: не обнаружен\n")

                lines_det.append(f"\n🔎 Признаки v2 (Ренди 2.0):\n")
                lines_det.append(f"  XOR строки:     {'✅ да' if has_xor else '❌ нет'}\n")
                lines_det.append(f"  State-machine:  {'✅ да' if has_sm else '❌ нет'}\n")
                lines_det.append(f"  Call-wrappers:  {'✅ да' if has_wrap else '❌ нет'}\n")
                lines_det.append(f"  exec() вызовы: {'✅ да' if has_exec else '❌ нет'}\n")
                lines_det.append(f"  Base64 блоки:   {'✅ да' if has_b64bl else '❌ нет'}\n")

                v2_score = sum([has_xor, has_sm, has_wrap, has_exec, has_b64bl])
                if v2_score >= 2:
                    lines_det.append(f"\n🟡 Вероятно нужен v2 (Ренди 2.0)\n")
                    lines_det.append(f"→ Используй /deobf2\n")
                elif not method_v1:
                    lines_det.append(f"\n⚪ Обфускация не распознана\n")
                    lines_det.append(f"   Файл чист или метод неизвестен\n")

                bot.edit_message_text("".join(lines_det), msg.chat.id, wait.message_id)
                return

            # ══════════════════════════════════════
            # РЕЖИМ: Ренди 2.0 (v2 принудительно)
            # ══════════════════════════════════════
            if state == "waiting_v2":
                bot.edit_message_text(
                    f"🔓 Ренди 2.0 — обрабатываю...\n\n"
                    f"📄 Файл: {doc.file_name}\n"
                    f"📊 Строк: {lines_in} | Символов: {chars_in:,}\n\n"
                    f"⏳ Этапы:\n"
                    f"  1. Binary payload extraction\n"
                    f"  2. XOR string decoding\n"
                    f"  3. Call-wrapper simplification\n"
                    f"  4. State-machine removal\n"
                    f"  5. Dummy variable removal\n"
                    f"  6. getattr() simplification\n"
                    f"  7. Final cleanup\n",
                    msg.chat.id, wait.message_id)
                try:
                    result = rendy2_deobfuscate(code)
                    out_name = f"rendy2_{doc.file_name}"
                    out_path = f"/tmp/{out_name}"
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(result)
                    lines_out = result.count('\n') + 1
                    chars_out = len(result)
                    reduction_l = round(100 * (1 - lines_out / max(lines_in, 1)))
                    reduction_c = round(100 * (1 - chars_out / max(chars_in, 1)))
                    bot.edit_message_text(
                        f"✅ Ренди 2.0 — готово! 🌸\n\n"
                        f"📄 Файл: {doc.file_name}\n"
                        f"──────────────────────\n"
                        f"📊 Строк:    {lines_in:,} → {lines_out:,}  ({reduction_l}% меньше)\n"
                        f"💬 Символов: {chars_in:,} → {chars_out:,}  ({reduction_c}% меньше)\n"
                        f"──────────────────────\n"
                        f"Метод: Universal (7 слоёв)\n",
                        msg.chat.id, wait.message_id)
                    with open(out_path, "rb") as f:
                        bot.send_document(msg.chat.id, f, visible_file_name=out_name,
                            caption=(
                                f"🔓 Ренди 2.0 | {doc.file_name}\n"
                                f"Строк: {lines_in}→{lines_out} ({reduction_l}%↓) | "
                                f"Символов: {chars_in:,}→{chars_out:,} ({reduction_c}%↓)"
                            ))
                    try:
                        os.remove(out_path)
                    except:
                        pass
                except Exception as e:
                    import traceback
                    tb = traceback.format_exc()
                    print(f"[deobf v2] ERR:\n{tb}")
                    bot.edit_message_text(
                        f"❌ Ошибка Ренди 2.0:\n{e}\n\nФайл: {doc.file_name}",
                        msg.chat.id, wait.message_id)
                return

            # ══════════════════════════════════════
            # РЕЖИМ: АВТО или v1 — пробуем v1,
            #        если не вышло — авто v2
            # ══════════════════════════════════════
            is_auto = (state == "waiting_auto")

            # Шаг 1: определяем v1
            bot.edit_message_text(
                f"🔍 {'[АВТО] ' if is_auto else ''}Анализирую {doc.file_name}...\n\n"
                f"📊 Строк: {lines_in} | Символов: {chars_in:,}\n\n"
                f"⏳ Шаг 1/2: определяю метод обфускации...",
                msg.chat.id, wait.message_id)

            method_v1 = detect_obfuscation(code)

            # Шаг 2а: v1 нашёл — декодируем v1
            if method_v1:
                bot.edit_message_text(
                    f"🔍 {'[АВТО] ' if is_auto else ''}Анализирую {doc.file_name}...\n\n"
                    f"✅ Метод: {method_v1}\n\n"
                    f"⏳ Шаг 2/2: декодирую...",
                    msg.chat.id, wait.message_id)

                result, info = deobfuscate_code(code)

                if result:
                    out_name = f"decoded_{doc.file_name}"
                    out_path = f"/tmp/{out_name}"
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(result)
                    lines_out = result.count('\n') + 1
                    chars_out = len(result)
                    reduction_l = round(100 * (1 - lines_out / max(lines_in, 1)))
                    reduction_c = round(100 * (1 - chars_out / max(chars_in, 1)))
                    bot.edit_message_text(
                        f"✅ Декодировано (v1)! 🌸\n\n"
                        f"📄 Файл: {doc.file_name}\n"
                        f"──────────────────────\n"
                        f"🔑 Метод:    {info}\n"
                        f"📊 Строк:    {lines_in:,} → {lines_out:,}  ({reduction_l}% меньше)\n"
                        f"💬 Символов: {chars_in:,} → {chars_out:,}  ({reduction_c}% меньше)\n"
                        f"──────────────────────",
                        msg.chat.id, wait.message_id)
                    with open(out_path, "rb") as f:
                        bot.send_document(msg.chat.id, f, visible_file_name=out_name,
                            caption=(
                                f"🔓 v1 | Метод: {info}\n"
                                f"Строк: {lines_in}→{lines_out} ({reduction_l}%↓)"
                            ))
                    try:
                        os.remove(out_path)
                    except:
                        pass
                    return

                # v1 метод найден, но декодировать не вышло — fallback на v2 если авто
                if is_auto:
                    bot.edit_message_text(
                        f"⚠️ [АВТО] v1 ({method_v1}) не смог декодировать.\n\n"
                        f"🔄 Переключаюсь на Ренди 2.0...",
                        msg.chat.id, wait.message_id)
                else:
                    bot.edit_message_text(
                        f"❌ v1 не смог декодировать: {info}\n\n"
                        f"Попробуй /deobf2 (Ренди 2.0) для этого файла~",
                        msg.chat.id, wait.message_id)
                    return

            elif not is_auto:
                # v1 не нашёл паттерн и не авто-режим
                bot.edit_message_text(
                    f"❌ v1: обфускация не распознана\n\n"
                    f"Файл: {doc.file_name}\n\n"
                    f"Попробуй /deobf2 (Ренди 2.0) — он умеет больше~",
                    msg.chat.id, wait.message_id)
                return
            else:
                bot.edit_message_text(
                    f"🔄 [АВТО] v1 паттерн не найден.\n\n"
                    f"⏳ Запускаю Ренди 2.0 (universal)...",
                    msg.chat.id, wait.message_id)

            # ── АВТО-ФОЛЛБЭК: запускаем Ренди 2.0 ──
            bot.edit_message_text(
                f"🔓 [АВТО → Ренди 2.0] Обрабатываю...\n\n"
                f"📄 Файл: {doc.file_name}\n"
                f"📊 Строк: {lines_in:,} | Символов: {chars_in:,}\n\n"
                f"⏳ Этапы:\n"
                f"  1. Binary payload extraction\n"
                f"  2. XOR string decoding\n"
                f"  3. Call-wrapper simplification\n"
                f"  4. State-machine removal\n"
                f"  5. Dummy variable removal\n"
                f"  6. getattr() simplification\n"
                f"  7. Final cleanup\n",
                msg.chat.id, wait.message_id)

            try:
                result = rendy2_deobfuscate(code)
                out_name = f"auto_rendy2_{doc.file_name}"
                out_path = f"/tmp/{out_name}"
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(result)
                lines_out = result.count('\n') + 1
                chars_out = len(result)
                reduction_l = round(100 * (1 - lines_out / max(lines_in, 1)))
                reduction_c = round(100 * (1 - chars_out / max(chars_in, 1)))
                bot.edit_message_text(
                    f"✅ [АВТО → Ренди 2.0] Готово! 🌸\n\n"
                    f"📄 Файл: {doc.file_name}\n"
                    f"──────────────────────\n"
                    f"🔑 Метод:    v1 не подошёл → Ренди 2.0 (7 слоёв)\n"
                    f"📊 Строк:    {lines_in:,} → {lines_out:,}  ({reduction_l}% меньше)\n"
                    f"💬 Символов: {chars_in:,} → {chars_out:,}  ({reduction_c}% меньше)\n"
                    f"──────────────────────",
                    msg.chat.id, wait.message_id)
                with open(out_path, "rb") as f:
                    bot.send_document(msg.chat.id, f, visible_file_name=out_name,
                        caption=(
                            f"🔓 АВТО | Ренди 2.0\n"
                            f"Строк: {lines_in}→{lines_out} ({reduction_l}%↓) | "
                            f"Символов: {chars_in:,}→{chars_out:,} ({reduction_c}%↓)"
                        ))
                try:
                    os.remove(out_path)
                except:
                    pass
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                print(f"[deobf auto-v2] ERR:\n{tb}")
                bot.edit_message_text(
                    f"❌ Ренди 2.0 ошибка:\n{e}\n\nФайл: {doc.file_name}",
                    msg.chat.id, wait.message_id)

        except Exception as e:
            import traceback
            print(f"[deobf] ERR: {traceback.format_exc()}")
            try:
                bot.edit_message_text(f"Ошибка обработки: {e}", msg.chat.id, wait.message_id)
            except:
                pass

    threading.Thread(target=do, daemon=True).start()

# ═══════════════════════════════════════
#         /pick — ручной выбор прокси
# ═══════════════════════════════════════
@bot.message_handler(commands=["pick"])
@access_required
def cmd_pick(msg):
    fast = cache["top_fast"]
    if not fast:
        _send(msg.chat.id,
            "⚠️ Пул пуст\n\n"
            "Сначала запусти /scan чтобы найти серверы~")
        return
    _send(msg.chat.id,
          f"🗂 Выбери прокси из топ-{len(fast)}\n\nОтсортированы по скорости:",
          kb_proxy_list(fast, page=0))

# ═══════════════════════════════════════
#              /admin
# ═══════════════════════════════════════
def _admin_text():
    tot    = sum(len(cache[t]) for t in ["socks5", "socks4", "http"])
    online = sum(1 for u in users.values() if u.get("connected"))
    return (
        f"👑 Панель администратора\n\n"
        f"──────────────────────\n"
        f"👥 Пользователей:   {len(allowed_users)}\n"
        f"🚫 В бане:          {len(banned_users)}\n"
        f"🟢 Онлайн сейчас:  {online}\n"
        f"──────────────────────\n"
        f"📦 База прокси:    {tot}\n"
        f"⚡ Смарт-пул:      {len(cache['top_fast'])}\n"
        f"──────────────────────\n"
        f"Выбери действие~"
    )

@bot.message_handler(commands=["admin"])
def cmd_admin(msg):
    if not is_admin(msg.from_user.id):
        _send(msg.chat.id, "🚫 Нет доступа~")
        return
    _send(msg.chat.id, _admin_text(), kb_admin())

@bot.message_handler(commands=["add"])
def cmd_add(msg):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.strip().split()
    if len(parts) < 2:
        _send(msg.chat.id, "Использование: /add <user_id> [Имя]")
        return
    try:
        target = int(parts[1])
    except:
        _send(msg.chat.id, "❌ Неверный ID")
        return
    banned_users.discard(target)
    banned_users.discard(str(target))
    name = " ".join(parts[2:]) if len(parts) > 2 else f"User {target}"
    allowed_users[str(target)] = {
        "username": "", "first_name": name,
        "added": ts(), "uses": 0, "added_by": msg.from_user.id
    }
    save_users()
    _send(msg.chat.id, f"✅ Добавлен\nID: {target}\nИмя: {name} 🌸")
    try:
        bot.send_message(target,
            "🌸 Привет! Тебя добавили в Togaff VPN!\n\n"
            "Напиши /start чтобы начать~ 💕")
    except:
        pass

@bot.message_handler(commands=["remove"])
def cmd_remove(msg):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.strip().split()
    if len(parts) < 2:
        _send(msg.chat.id, "/remove <user_id>")
        return
    try:
        target = int(parts[1])
    except:
        _send(msg.chat.id, "❌ Неверный ID")
        return
    key = str(target)
    if key in allowed_users:
        del allowed_users[key]
        save_users()
        _send(msg.chat.id, f"✅ Удалён {target}")
    else:
        _send(msg.chat.id, f"Не найден {target}")

@bot.message_handler(commands=["ban"])
def cmd_ban(msg):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.strip().split()
    if len(parts) < 2:
        _send(msg.chat.id, "/ban <user_id>")
        return
    try:
        target = int(parts[1])
    except:
        _send(msg.chat.id, "❌ Неверный ID")
        return
    banned_users.add(target)
    key = str(target)
    if key in allowed_users:
        del allowed_users[key]
    save_users()
    _send(msg.chat.id, f"🚫 Забанен {target}")

@bot.message_handler(commands=["unban"])
def cmd_unban(msg):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.strip().split()
    if len(parts) < 2:
        _send(msg.chat.id, "/unban <user_id>")
        return
    try:
        target = int(parts[1])
    except:
        _send(msg.chat.id, "❌ Неверный ID")
        return
    banned_users.discard(target)
    banned_users.discard(str(target))
    save_users()
    _send(msg.chat.id, f"✅ Разбанен {target} 🌸")

@bot.message_handler(commands=["users"])
def cmd_users(msg):
    if not is_admin(msg.from_user.id):
        return
    _send_users_list(msg.chat.id)

def _send_users_list(chat_id, msg_id=None):
    if not allowed_users:
        text = "👥 Пользователи\n\nСписок пуст~"
    else:
        lines = [f"👥 Пользователи ({len(allowed_users)})\n\n"]
        for i, (uid_s, info) in enumerate(list(allowed_users.items())[:30], 1):
            uname = info.get("username", "") or ""
            name  = info.get("first_name", "—")
            added = info.get("added", "—")
            uses  = info.get("uses", 0)
            try:
                online = "🟢" if users.get(int(uid_s), {}).get("connected") else "⚪"
            except:
                online = "⚪"
            ustr = f"@{uname}" if uname else f"ID:{uid_s}"
            lines.append(f"{online} {i}. {name} {ustr}\n   Добавлен: {added} · Сессий: {uses}\n\n")
        if len(allowed_users) > 30:
            lines.append(f"...и ещё {len(allowed_users)-30}")
        text = "".join(lines)
    k = telebot.types.InlineKeyboardMarkup()
    k.add(telebot.types.InlineKeyboardButton("◀ Назад", callback_data="adm_panel"))
    if msg_id:
        try:
            bot.edit_message_text(text, chat_id, msg_id, reply_markup=k)
            return
        except:
            pass
    _send(chat_id, text, k)

_broadcast_state = {}

# ═══════════════════════════════════════
#               /scan
# ═══════════════════════════════════════
@bot.message_handler(commands=["scan"])
@access_required
def cmd_scan(msg):
    wait = _send(msg.chat.id, "🔍 Сканирую серверы...\n\nЭтап 1/2: TCP-пинг\n" + lbar(0) + "  0/0")
    if not wait:
        return
    cid = msg.chat.id
    mid = wait.message_id
    upd = _updater(cid, mid)

    def tcp_cb(done, total):
        upd(f"🔍 Сканирую серверы...\n\nЭтап 1/2: TCP-пинг\n{lbar(done,total)}  {done}/{total} хостов")

    def http_cb(done, total):
        upd(f"🔍 Сканирую серверы...\n\nЭтап 2/2: Проверка IP\n{lbar(done,total)}  {done}/{total} живых серверов")

    def do():
        my_ip = get_my_ip() or ""
        results = build_smart_pool(my_ip, sample=SCAN_SAMPLE, tcp_cb=tcp_cb, http_cb=http_cb)
        if not results:
            _edit(cid, mid,
                "❌ Серверы не найдены\n\n"
                "Попробуй /refresh и повтори /scan~")
            return
        lines = [f"⚡ Смарт-пул готов — {len(results)} серверов 🌸\n\n"]
        for i, r in enumerate(results[:7], 1):
            lines.append(
                f"{i}. {proto_icon(r['type'])} {r['host']}:{r['port']}\n"
                f"   {ping_bar(r['ping'])}  {r['ping']} ms\n\n"
            )
        lines.append("Используются автоматически при /connect\nДля ручного выбора: /pick")
        _edit(cid, mid, "".join(lines), kb_main(get_user(msg.from_user.id)["connected"]))

    threading.Thread(target=do, daemon=True).start()

# ═══════════════════════════════════════
#             /connect
# ═══════════════════════════════════════
@bot.message_handler(commands=["connect"])
@access_required
def cmd_connect(msg):
    uid   = int(msg.from_user.id)
    u     = get_user(uid)
    parts = (msg.text or "").strip().split()
    raw   = parts[1].lower() if len(parts) > 1 else None
    aliases = {"s5": "socks5", "socks5": "socks5", "s4": "socks4",
                "socks4": "socks4", "http": "http", "https": "http"}
    pf = aliases.get(raw) if raw else None

    if u["connected"]:
        px = u["proxy"]
        _send(msg.chat.id,
            f"✅ Уже подключён~\n\n"
            f"{proto_icon(px['type'])} {px['host']}:{px['port']}\n\n"
            f"• /rotate — сменить IP\n• /disconnect — отключиться",
            kb_main(True))
        return

    wait = _send(msg.chat.id, "🔍 Определяю твой IP...")
    if not wait:
        return
    cid = msg.chat.id
    mid = wait.message_id
    upd = _updater(cid, mid)

    def do():
        my_ip = get_my_ip() or "unknown"
        u["ip_before"] = my_ip
        label   = pf.upper() if pf else "АВТО"
        fast_n  = len([p for p in cache["top_fast"] if not pf or p["type"] == pf])

        if fast_n:
            upd(f"🔄 Подключаюсь [{label}]\n\nТвой IP: {my_ip}\n⚡ Проверяю {fast_n} быстрых серверов...")
        else:
            upd(f"🔄 Подключаюсь [{label}]\n\nТвой IP: {my_ip}\n🔍 Полный поиск...")

        n_info = {"n": 0}

        def on_try(n, pt, h, p):
            n_info["n"] = n
            upd(f"🔄 Подключаюсь [{label}]\n\nТвой IP: {my_ip}\n"
                f"{proto_icon(pt)} Тест: {h}:{p}\n"
                f"{lbar(min(n,200),200)}  попытка {n}")

        res = find_best_proxy(my_ip, ptype_filter=pf, on_try=on_try)

        if res:
            u.update(connected=True, proxy=res, connect_time=time.time(), ip_after=res["new_ip"])
            u["sessions"] = u.get("sessions", 0) + 1
            smart_pool_refresh_bg(my_ip)
            _edit(cid, mid,
                f"✅ Подключение установлено! 🌸\n\n"
                f"──────────────────────\n"
                f"{proto_icon(res['type'])} Протокол:  {res['type'].upper()}\n"
                f"🖥 Сервер:    {res['host']}:{res['port']}\n"
                f"──────────────────────\n"
                f"📶 Качество:\n"
                f"   {ping_bar(res['ping'])}  {res['ping']} ms\n"
                f"──────────────────────\n"
                f"📍 IP до:      {my_ip}\n"
                f"🌍 IP сейчас:  {res['new_ip']}\n"
                f"──────────────────────\n"
                f"🔒 Защита активна~ 💕",
                kb_main(True))
        else:
            _edit(cid, mid,
                f"❌ Сервер не найден\n\n"
                f"Проверено: {n_info['n']} серверов\n\n"
                f"Попробуй:\n"
                f"• /scan  — найти быстрые серверы\n"
                f"• /refresh — обновить базу\n"
                f"• /connect http — только HTTP",
                kb_main(False))

    threading.Thread(target=do, daemon=True).start()

# ═══════════════════════════════════════
#           /disconnect
# ═══════════════════════════════════════
@bot.message_handler(commands=["disconnect"])
@access_required
def cmd_disconnect(msg):
    u = get_user(msg.from_user.id)
    if not u["connected"]:
        _send(msg.chat.id, "ℹ️ VPN не подключён~", kb_main(False))
        return
    sess = fmt_time(time.time() - u["connect_time"]) if u["connect_time"] else "—"
    px   = u["proxy"]
    ib   = u.get("ip_before", "—")
    ia   = u.get("ip_after", "—")
    u.update(connected=False, proxy=None, connect_time=None)
    _send(msg.chat.id,
        f"🔴 Сессия завершена\n\n"
        f"──────────────────────\n"
        f"{proto_icon(px['type'])} {px['host']}:{px['port']}\n"
        f"⏱ Длительность:  {sess}\n"
        f"──────────────────────\n"
        f"📍 Реальный IP:  {ib}\n"
        f"🌍 Был IP VPN:   {ia}\n"
        f"──────────────────────\n"
        f"Пока~ 🌸",
        kb_main(False))

# ═══════════════════════════════════════
#             /rotate
# ═══════════════════════════════════════
@bot.message_handler(commands=["rotate"])
@access_required
def cmd_rotate(msg):
    u = get_user(msg.from_user.id)
    if not u["connected"]:
        _send(msg.chat.id, "ℹ️ Сначала /connect~")
        return
    wait = _send(msg.chat.id, "🔄 Меняю IP...")
    if not wait:
        return
    cid = msg.chat.id
    mid = wait.message_id
    upd = _updater(cid, mid)

    def do():
        my_ip  = u.get("ip_before") or get_my_ip() or "unknown"
        excl   = u["proxy"]["host"] if u["proxy"] else None
        old_ip = u.get("ip_after", "—")
        n_info = {"n": 0}

        def on_try(n, pt, h, p):
            n_info["n"] = n
            upd(f"🔄 Меняю IP...\n\n{proto_icon(pt)} {h}:{p}\n{lbar(min(n,200),200)}  попытка {n}")

        res = find_best_proxy(my_ip, exclude=excl, on_try=on_try)
        if res:
            u.update(proxy=res, connect_time=time.time(), ip_after=res["new_ip"])
            u["total_rotates"] = u.get("total_rotates", 0) + 1
            _edit(cid, mid,
                f"✅ IP изменён! 🌸\n\n"
                f"──────────────────────\n"
                f"{proto_icon(res['type'])} {res['host']}:{res['port']}\n"
                f"──────────────────────\n"
                f"📶 {ping_bar(res['ping'])}  {res['ping']} ms\n"
                f"──────────────────────\n"
                f"🌍 Был:     {old_ip}\n"
                f"🌍 Новый:   {res['new_ip']}",
                kb_main(True))
        else:
            _edit(cid, mid, "❌ Нет доступных серверов\n\nПопробуй /scan~", kb_main(True))

    threading.Thread(target=do, daemon=True).start()

# ═══════════════════════════════════════
#              /status
# ═══════════════════════════════════════
@bot.message_handler(commands=["status"])
@access_required
def cmd_status(msg):
    u    = get_user(msg.from_user.id)
    tot  = sum(len(cache[t]) for t in ["socks5", "socks4", "http"])
    fast = len(cache["top_fast"])

    if u["connected"] and u["proxy"]:
        px   = u["proxy"]
        sess = fmt_time(time.time() - u["connect_time"]) if u["connect_time"] else "—"
        wait = _send(msg.chat.id, "📊 Получаю статус...")
        if not wait:
            return

        def do():
            ms   = tcp_ping(px["host"], px["port"], timeout=2.5)
            anon = ("Высокая (SOCKS5)" if px["type"] == "socks5"
                    else "Средняя (SOCKS4)" if px["type"] == "socks4"
                    else "Базовая (HTTP)")
            ping_str = f"{ms} ms" if ms else "сервер недоступен"
            _edit(msg.chat.id, wait.message_id,
                f"📊 Статус VPN 🌸\n\n"
                f"──────────────────────\n"
                f"🟢 Статус:     АКТИВЕН\n"
                f"{proto_icon(px['type'])} Протокол:  {px['type'].upper()}\n"
                f"🖥 Сервер:     {px['host']}:{px['port']}\n"
                f"──────────────────────\n"
                f"📶 Качество:\n"
                f"   {ping_bar(ms)}  {ping_str}\n"
                f"──────────────────────\n"
                f"⏱ Сессия:      {sess}\n"
                f"🔄 Смен IP:    {u.get('total_rotates',0)}\n"
                f"📍 IP до VPN:  {u.get('ip_before','—')}\n"
                f"🌍 IP сейчас:  {u.get('ip_after','—')}\n"
                f"──────────────────────\n"
                f"🔐 Анонимность: {anon}\n"
                f"🔒 Защита:     активна~\n"
                f"──────────────────────\n"
                f"📦 База:       {tot} прокси\n"
                f"⚡ Пул:        {fast} быстрых",
                kb_main(True))

        threading.Thread(target=do, daemon=True).start()
    else:
        _send(msg.chat.id,
            f"📊 Статус VPN\n\n"
            f"──────────────────────\n"
            f"🔴 Статус:  НЕ ПОДКЛЮЧЁН\n"
            f"──────────────────────\n"
            f"📦 База прокси:\n"
            f"   🔵 SOCKS5: {len(cache['socks5'])}\n"
            f"   🟣 SOCKS4: {len(cache['socks4'])}\n"
            f"   ⚪ HTTP:   {len(cache['http'])}\n"
            f"   Итого:    {tot}\n"
            f"──────────────────────\n"
            f"⚡ Смарт-пул:  {fast} серверов\n\n"
            f"/connect — подключиться\n"
            f"/scan — найти лучшие серверы~",
            kb_main(False))

# ═══════════════════════════════════════
#             /proxies
# ═══════════════════════════════════════
@bot.message_handler(commands=["proxies"])
@access_required
def cmd_proxies(msg):
    tot  = sum(len(cache[t]) for t in ["socks5", "socks4", "http"])
    fast = cache["top_fast"]
    if tot == 0:
        _send(msg.chat.id, "📦 База пуста\n\nИспользуй /refresh~")
        return

    lines = ["🗂 Серверы Togaff VPN 🌸\n\n"]
    if fast:
        lines.append(f"⚡ Быстрые серверы (топ {min(3,len(fast))}):\n\n")
        for r in fast[:3]:
            lines.append(f"  {proto_icon(r['type'])} {r['host']}:{r['port']}\n"
                         f"  {ping_bar(r['ping'])}  {r['ping']} ms\n\n")
        lines.append("──────────────────────\n")

    for pt in ["socks5", "socks4", "http"]:
        lines.append(f"{proto_icon(pt)} {pt.upper()} — {len(cache[pt])} серверов\n")
        for h, p in cache[pt][:3]:
            lines.append(f"   {h}:{p}\n")
        lines.append("\n")
    lines.append(f"Всего: {tot}  ·  /refresh для обновления\n/pick для ручного выбора~")

    _send(msg.chat.id, "".join(lines), kb_main(get_user(msg.from_user.id)["connected"]))

# ═══════════════════════════════════════
#               /ip
# ═══════════════════════════════════════
@bot.message_handler(commands=["ip"])
@access_required
def cmd_ip(msg):
    u    = get_user(msg.from_user.id)
    wait = _send(msg.chat.id, "🔍 Определяю IP...")
    if not wait:
        return

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
        _edit(msg.chat.id, wait.message_id,
            f"{icon} Твой IP-адрес 🌸\n\n"
            f"──────────────────────\n"
            f"IP:    {ip or 'недоступен'}\n"
            f"Режим: {mode}\n"
            f"──────────────────────")

    threading.Thread(target=do, daemon=True).start()

# ═══════════════════════════════════════
#            /refresh
# ═══════════════════════════════════════
@bot.message_handler(commands=["refresh"])
@access_required
def cmd_refresh(msg):
    wait = _send(msg.chat.id, "🔄 Обновляю базу прокси...")
    if not wait:
        return

    def do():
        cache["updated"] = 0
        refresh_cache(force=True)
        tot = sum(len(cache[t]) for t in ["socks5", "socks4", "http"])
        _edit(msg.chat.id, wait.message_id,
            f"✅ База обновлена! 🌸\n\n"
            f"──────────────────────\n"
            f"🔵 SOCKS5: {len(cache['socks5'])}\n"
            f"🟣 SOCKS4: {len(cache['socks4'])}\n"
            f"⚪ HTTP:   {len(cache['http'])}\n"
            f"──────────────────────\n"
            f"📦 Итого:  {tot}\n\n"
            f"/scan — найти лучшие серверы~",
            kb_main(get_user(msg.from_user.id)["connected"]))

    threading.Thread(target=do, daemon=True).start()

# ═══════════════════════════════════════
#            /generate
# ═══════════════════════════════════════
@bot.message_handler(commands=["generate"])
@access_required
def cmd_generate(msg):
    u = get_user(msg.from_user.id)
    if u["connected"] and u["proxy"]:
        _send_config(msg.chat.id, None, u["proxy"])
        return
    wait = _send(msg.chat.id, "🔧 Генерирую конфиг...")
    if not wait:
        return
    cid = msg.chat.id
    mid = wait.message_id
    upd = _updater(cid, mid)

    def do():
        my_ip  = get_my_ip() or "0.0.0.0"
        n_info = {"n": 0}

        def on_try(n, pt, h, p):
            n_info["n"] = n
            upd(f"🔧 Генератор конфигов\n\n{proto_icon(pt)} {h}:{p}\n{lbar(min(n,60),60)}  попытка {n}")

        res = find_best_proxy(my_ip, on_try=on_try)
        if res:
            _send_config(cid, mid, res)
        else:
            _edit(cid, mid, "❌ Нет рабочего прокси\n\nПопробуй /scan~")

    threading.Thread(target=do, daemon=True).start()

def _send_config(chat_id, msg_id, proxy):
    h, p, pt = proxy["host"], proxy["port"], proxy["type"]
    ms = proxy["ping"]
    pu = _proxy_url(pt, h, p)
    text = (
        f"📋 Конфиг прокси 🌸\n\n"
        f"──────────────────────\n"
        f"{proto_icon(pt)} {h}:{p}  ·  {pt.upper()}\n"
        f"📶 {ping_bar(ms)}  {ms} ms\n"
        f"──────────────────────\n\n"
        f"curl / wget:\n--proxy {pu}\n\n"
        f"Shell (ENV):\nexport ALL_PROXY={pu}\n\n"
        f"proxychains.conf:\n{pt} {h} {p}\n\n"
        f"Python requests:\nproxies={{'http':'{pu}','https':'{pu}'}}\n\n"
        f"RAW:\n{h}:{p}"
    )
    if msg_id:
        try:
            bot.edit_message_text(text, chat_id, msg_id, reply_markup=kb_generate())
            return
        except:
            pass
    _send(chat_id, text, kb_generate())

# ═══════════════════════════════════════
#            CALLBACKS
# ═══════════════════════════════════════
@bot.callback_query_handler(func=lambda c: True)
def on_callback(call):
    uid = int(call.from_user.id)
    d   = call.data
    cid = call.message.chat.id
    mid = call.message.message_id

    # ─ Деобфускатор (меню) ──────────────
    if d == "deobf_menu":
        if not is_allowed(uid):
            bot.answer_callback_query(call.id, "🔒")
            return
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(
                "🔓 Деобфускатор 🌸\n\n"
                "⚡ АВТО — пробует v1, при неудаче сразу v2\n\n"
                "v1 методы:\n"
                "  • base64/32/16 · zlib · gzip · lzma\n"
                "  • Комбо: base+zlib/gzip/lzma\n"
                "  • Rendy obf (marshal+gzip+lzma+zlib+base64)\n\n"
                "v2 (Ренди 2.0):\n"
                "  • XOR строки · State-machine\n"
                "  • Call-wrappers · Dummy vars\n"
                "  • getattr chains · Binary payload\n\n"
                "Выбери режим:",
                cid, mid, reply_markup=kb_deobf())
        except:
            _send(cid, "🔓 Деобфускатор", kb_deobf())
        return

    if d == "deobf_auto":
        if not is_allowed(uid):
            bot.answer_callback_query(call.id, "🔒")
            return
        bot.answer_callback_query(call.id)
        _deobf_state[uid] = "waiting_auto"
        _edit(cid, mid,
            "⚡ АВТО-деобфускатор активирован 🌸\n\n"
            "Порядок: v1 (base/zlib/rendy) → если не вышло → Ренди 2.0\n\n"
            "📎 Отправь .py файл:")
        return

    if d == "deobf_detect":
        if not is_allowed(uid):
            bot.answer_callback_query(call.id, "🔒")
            return
        bot.answer_callback_query(call.id)
        _deobf_state[uid] = "waiting_detect"
        _edit(cid, mid,
            "🔍 Отправь .py файл и я определю тип обфускации~\n\n"
            "(/cancel для отмены)")
        return

    if d == "deobf_run":
        if not is_allowed(uid):
            bot.answer_callback_query(call.id, "🔒")
            return
        bot.answer_callback_query(call.id)
        _deobf_state[uid] = "waiting"
        _edit(cid, mid,
            "📎 Отправь .py файл для деобфускации (v1)~\n\n"
            "(/cancel для отмены)")
        return

    # ─ Деобфускатор v2 (Ренди 2.0) ──────
    if d == "deobf2_menu":
        if not is_allowed(uid):
            bot.answer_callback_query(call.id, "🔒")
            return
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(
                "🔓 Деобфускатор v2 — Ренди 2.0 🌸\n\n"
                "Universal Python Deobfuscator\n"
                "──────────────────────\n"
                "• marshal / gzip / lzma / zlib / base64\n"
                "• XOR-encoded строки\n"
                "• State-machine control flow\n"
                "• Call-wrapper функции\n"
                "• Dead branches / dummy переменные\n"
                "• getattr() chains\n\n"
                "Отправь .py файл:",
                cid, mid, reply_markup=kb_deobf2())
        except:
            _send(cid, "🔓 Ренди 2.0", kb_deobf2())
        return

    if d == "deobf2_run":
        if not is_allowed(uid):
            bot.answer_callback_query(call.id, "🔒")
            return
        bot.answer_callback_query(call.id)
        _deobf_state[uid] = "waiting_v2"
        _edit(cid, mid,
            "📎 Отправь .py файл для Ренди 2.0~\n\n"
            "(/cancel для отмены)")
        return

    # ─ Ручной выбор прокси ──────────────
    if d.startswith("pick_"):
        if not is_allowed(uid):
            bot.answer_callback_query(call.id, "🔒")
            return
        idx  = int(d.split("_")[1])
        fast = cache["top_fast"]
        if idx >= len(fast):
            bot.answer_callback_query(call.id, "⚠️ Устаревший список")
            return
        px = fast[idx]
        bot.answer_callback_query(call.id, "⚡ Подключаюсь...")
        u = get_user(uid)
        old_ip = u.get("ip_after") if u["connected"] else None
        wait = _send(cid,
            f"🔄 Подключаюсь к выбранному серверу...\n\n"
            f"{proto_icon(px['type'])} {px['host']}:{px['port']}")
        if not wait:
            return

        def do():
            my_ip = get_my_ip() or "unknown"
            if not old_ip:
                u["ip_before"] = my_ip
            res = verify_proxy(px["type"], px["host"], px["port"], my_ip, tcp_t=2, ip_t=9)
            if res:
                u.update(connected=True, proxy=res, connect_time=time.time(), ip_after=res["new_ip"])
                u["sessions"] = u.get("sessions", 0) + 1
                _edit(cid, wait.message_id,
                    f"✅ Подключён! 🌸\n\n"
                    f"──────────────────────\n"
                    f"{proto_icon(res['type'])} {res['host']}:{res['port']}\n"
                    f"──────────────────────\n"
                    f"📶 {ping_bar(res['ping'])}  {res['ping']} ms\n"
                    f"──────────────────────\n"
                    f"📍 IP до:     {my_ip}\n"
                    f"🌍 IP сейчас: {res['new_ip']} 💕",
                    kb_main(True))
            else:
                _edit(cid, wait.message_id,
                    f"❌ Сервер недоступен\n\n{px['host']}:{px['port']}\n\nВыбери другой~",
                    kb_proxy_list(fast, 0))

        threading.Thread(target=do, daemon=True).start()
        return

    if d.startswith("pxpage_"):
        if not is_allowed(uid):
            bot.answer_callback_query(call.id, "🔒")
            return
        page = int(d.split("_")[1])
        fast = cache["top_fast"]
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_reply_markup(cid, mid, reply_markup=kb_proxy_list(fast, page))
        except:
            pass
        return

    if d == "back_main":
        bot.answer_callback_query(call.id)
        cmd_start(FMsg(call, "/start"))
        return

    if d == "adm_panel":
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "🚫")
            return
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(_admin_text(), cid, mid, reply_markup=kb_admin())
        except:
            _send(cid, _admin_text(), kb_admin())
        return

    # ─ Кнопки админа ────────────────────
    if d.startswith("adm_") or d.startswith("ban_") or d.startswith("del_"):
        if not is_admin(uid):
            bot.answer_callback_query(call.id, "🚫")
            return
        if d == "adm_users":
            bot.answer_callback_query(call.id)
            _send_users_list(cid, mid)
        elif d == "adm_banned":
            bot.answer_callback_query(call.id)
            text = (f"🚫 Бан-лист ({len(banned_users)})\n\n" +
                    "\n".join(f"• {u}" for u in list(banned_users)[:30])
                    if banned_users else "🚫 Бан-лист\n\nПуст~")
            k = telebot.types.InlineKeyboardMarkup()
            k.add(telebot.types.InlineKeyboardButton("◀ Назад", callback_data="adm_panel"))
            try:
                bot.edit_message_text(text, cid, mid, reply_markup=k)
            except:
                _send(cid, text, k)
        elif d == "adm_stats":
            bot.answer_callback_query(call.id)
            online = sum(1 for u in users.values() if u.get("connected"))
            tot    = sum(len(cache[t]) for t in ["socks5", "socks4", "http"])
            text   = (f"📊 Статистика 🌸\n\n"
                      f"👥 Пользователей: {len(allowed_users)}\n"
                      f"🟢 Онлайн: {online}\n"
                      f"🚫 В бане: {len(banned_users)}\n\n"
                      f"📦 База: {tot}\n"
                      f"⚡ Пул: {len(cache['top_fast'])}\n"
                      f"🔵 SOCKS5: {len(cache['socks5'])}\n"
                      f"🟣 SOCKS4: {len(cache['socks4'])}\n"
                      f"⚪ HTTP: {len(cache['http'])}\n\n"
                      f"Обновлено: {ts()}")
            k = telebot.types.InlineKeyboardMarkup()
            k.add(telebot.types.InlineKeyboardButton("◀ Назад", callback_data="adm_panel"))
            try:
                bot.edit_message_text(text, cid, mid, reply_markup=k)
            except:
                _send(cid, text, k)
        elif d == "adm_refresh":
            bot.answer_callback_query(call.id, "🔄 Запущено...")
            def bg():
                cache["updated"] = 0
                refresh_cache(force=True)
            threading.Thread(target=bg, daemon=True).start()
            _send(cid, "🔄 Обновление базы запущено в фоне~")
        elif d == "adm_scan":
            bot.answer_callback_query(call.id, "⚡ Запускаю...")
            cmd_scan(FMsg(call, "/scan"))
        elif d == "adm_broadcast":
            bot.answer_callback_query(call.id)
            _broadcast_state[uid] = True
            _send(cid, "📢 Отправь текст рассылки следующим сообщением\n(/cancel для отмены)")
        elif d.startswith("ban_"):
            t = int(d.split("_")[1])
            banned_users.add(t)
            k = str(t)
            if k in allowed_users:
                del allowed_users[k]
            save_users()
            bot.answer_callback_query(call.id, f"🚫 {t}")
            _send_users_list(cid, mid)
        elif d.startswith("del_"):
            t = int(d.split("_")[1])
            k = str(t)
            if k in allowed_users:
                del allowed_users[k]
                save_users()
            bot.answer_callback_query(call.id, f"✅ {t}")
            _send_users_list(cid, mid)
        return

    # ─ Кнопки пользователя ──────────────
    if not is_allowed(uid):
        bot.answer_callback_query(call.id, "🔒 Нет доступа~")
        return

    if d == "regen":
        bot.answer_callback_query(call.id, "🔧 Ищу другой...")
        cmd_generate(FMsg(call, "/generate"))
        return

    table = {
        "connect":    ("/connect",       "⚡ Подключаюсь..."),
        "c_socks5":   ("/connect socks5","🔵"),
        "c_socks4":   ("/connect socks4","🟣"),
        "c_http":     ("/connect http",  "⚪"),
        "disconnect": ("/disconnect",    "🔴"),
        "rotate":     ("/rotate",        "🔄"),
        "status":     ("/status",        ""),
        "proxies":    ("/proxies",       ""),
        "generate":   ("/generate",      "🔧"),
    }
    if d not in table:
        return
    cmd, ans = table[d]
    bot.answer_callback_query(call.id, ans or None)
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
    handlers[cmd](FMsg(call, cmd))

# ─ Рассылка ─────────────────────────────
@bot.message_handler(func=lambda m: m.from_user.id in _broadcast_state
                                    and _broadcast_state[m.from_user.id] is True
                                    and m.text != "/cancel")
def handle_broadcast(msg):
    if not is_admin(msg.from_user.id):
        return
    _broadcast_state.pop(msg.from_user.id, None)
    ok = fail = 0
    for uid_str in list(allowed_users.keys()):
        try:
            bot.send_message(int(uid_str),
                f"📢 Сообщение от администратора 🌸\n\n{msg.text}")
            ok += 1
        except:
            fail += 1
    _send(msg.chat.id, f"✅ Рассылка\n✔ Доставлено: {ok}\n✖ Ошибок: {fail}")

# ─ /cancel ──────────────────────────────
@bot.message_handler(commands=["cancel"])
def cmd_cancel(msg):
    uid = msg.from_user.id
    _deobf_state.pop(uid, None)
    _broadcast_state.pop(uid, None)
    _send(msg.chat.id, "❌ Отменено~")

# ═══════════════════════════════════════
#              ЗАПУСК
# ═══════════════════════════════════════
if __name__ == "__main__":
    print("=" * 55)
    print("  🌸 TOGAFF VPN · Astolfo Ultimate Edition 🌸")
    print(f"  PySocks: {'✓ SOCKS5/4 активны' if SOCKS_OK else '✗ pip install PySocks requests[socks]'}")
    print(f"  Фото:    {'✓ '+WELCOME_PHOTO if os.path.exists(WELCOME_PHOTO) else '✗ нет файла '+WELCOME_PHOTO}")
    print(f"  Admins:  {ADMIN_IDS}")
    print(f"  Users:   {len(allowed_users)}")
    print("=" * 55)

    def startup():
        print("🌸 Загружаю базу...")
        refresh_cache()
        time.sleep(3)
        print("🌸 Прогреваю смарт-пул...")
        my_ip = get_my_ip() or ""
        build_smart_pool(my_ip, sample=SCAN_SAMPLE, workers=VERIFY_WORKERS)

    def auto_refresh():
        while True:
            time.sleep(TOP_TTL)
            my_ip = get_my_ip() or ""
            if my_ip:
                print("🌸 Авто-обновление пула...")
                build_smart_pool(my_ip, sample=SCAN_SAMPLE // 2, workers=VERIFY_WORKERS)

    threading.Thread(target=startup,      daemon=True).start()
    threading.Thread(target=auto_refresh, daemon=True).start()
    bot.infinity_polling(timeout=30, long_polling_timeout=20)
