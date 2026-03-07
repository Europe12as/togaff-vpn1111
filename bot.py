"""
  🌸 TOGAFF VPN · Astolfo Ultimate Edition 🌸
  pip install pyTelegramBotAPI requests[socks] PySocks pystyle
  python3 togaff_vpn_bot.py
"""

import telebot, requests, socket, threading, time, random, re, json, os
import zlib, base64, gzip, lzma, marshal, types, dis, io, struct, itertools
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

MY_VLESS_PROXIES = [
    "vless://02f62dd5-218f-4e9f-9c4b-f8a2e452533e@78.159.247.79:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.vk.com&fp=chrome&pbk=HxjD-7OeJUtrNFsW4PEqThSs6fujV9Mkl5Z4igx21k8&sid=ef&type=tcp#RU-GCN",
    "vless://02fb468f-21f2-460e-bfa1-ef52ae5e627f@95.163.182.172:443?encryption=none&flow=xtls-rprx-vision&fp=chrome&pbk=5bGFIWSo4vlrd9Tv1yFcpdpSjrjYYN20SOWHYfighHc&security=reality&sid=aad92345&sni=api-maps.yandex.ru&type=tcp#SE-CIDR",
    "vless://0339f151-d187-4d5e-b0eb-994cebf3f9ca@185.130.112.165:8448?flow=xtls-rprx-vision&encryption=none&type=tcp&security=reality&fp=random&sni=eh.vk.com&pbk=Ox4BT0R5103EpplP2y6TIVv0VC-xBR2-YT6EJ4YmkUw&spx=/#RU-9452",
    "vless://0eb0019b66404203a7e07701f61bf766@91.220.8.177:443?type=tcp&encryption=none&flow=xtls-rprx-vision&sni=m.vk.com&fp=chrome&security=reality&pbk=n0e-y_JNPYLzhJkFuhlq6-k1lgUG43cmiQXkP2Pv_wc&sid=aabbccdd#DE-Reality",
    "vless://0ec58af7-0098-430e-8efd-551322a7bb5d@5.188.143.238:50445?flow=xtls-rprx-vision&encryption=none&type=tcp&security=reality&fp=chrome&sni=celular.vk.com&pbk=ZSzB9TQPGNcCiC0WLmciF5Jc8doJDvdRgbqTi8SCoEM&sid=a1b2c3d4e5f6789a#RU-409",
    "vless://0a9fe7e0-e02d-42ca-bebd-ecb4292f180c@146.185.240.23:443?security=reality&encryption=none&pbk=zii4nGNapnFKL6SN8GzWNqFlElBvUCUFUThEP0kFH04&headerType=none&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=m.vk.ru&sid=c6ef72e4635d15a5#RU-383",
    "vless://11f81498-983c-401c-9e6c-b458999d498f@84.201.172.12:9443?flow=xtls-rprx-vision&encryption=none&type=tcp&security=reality&fp=chrome&sni=www.vk.com&pbk=59iHd67rGlyJBUpDq5NXC91EB0U4AXtSlOjAQsW2D14#RU-9386",
    "vless://12a57f4b-813d-4e0f-b15f-2234c71fd41d@158.160.189.247:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=m.vk.com&fp=chrome&pbk=Qddpg8luihgzgx4g4uMJklXzlrMCd8L1igJSWrRUvSc&sid=887c0d72e771a934&type=tcp#PL-166",
    "vless://07cd9dbe-21ac-4871-817d-c772687e4b7c@103.27.157.79:2053?encryption=none&flow=xtls-rprx-vision&fp=chrome&pbk=WckOSneVajAzpH0sZSAFAWPnmwuuEXKZrTICNj5_hHU&security=reality&sid=423bccc9c13fb509&sni=www.ibm.com&type=tcp#DE-Reality2",
    "vless://05732283-b4ee-4a86-920c-df9cf83d16c4@51.250.4.154:8443?flow=xtls-rprx-vision&encryption=none&type=tcp&security=reality&fp=chrome&sni=m.vk.com&pbk=4mshoogy3ikozr2hra8vckfts7ufmfey2txpnd4jfzm&sid=adcdd261d4e5aea1#RU-Reality2",
    "vless://0c62469a-009f-4050-bbc6-2be5d74e64f7@212.111.84.218:443?security=reality&encryption=none&pbk=x6cB3avjxjxzhNESk8iJTTCzOPKXnB0AbnjKSqKkang&headerType=none&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=maps.yandex.ru&sid=8f0a12bc34de5678#KZ-Reality",
    "vless://0ff8dbfb-d7ee-4a19-b22d-b652a8b52e22@212.111.84.82:443?security=reality&encryption=none&pbk=7zd9mJilgjOrg_ohtw23Vmio-pdnYqeP_r-kiWt87Cg&headerType=none&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=m.vk.ru&sid=f4b4a6365558ea2e#RU-421",
    "vless://0f6c83bc-34ba-4ca1-96e6-08b3620cbce5@145.223.69.171:443?encryption=none&security=reality&sni=www.vk.com&fp=firefox&pbk=JQHrZXZRnkZUOMdNHS7X1fPyMDqKjiQWlfTdntIOqzg&sid=a6b92e23&type=tcp#FR-VK",
    "vless://0f6c83bc-34ba-4ca1-96e6-08b3620cbce5@217.16.19.114:443?encryption=none&security=reality&sni=www.vk.com&fp=chrome&pbk=s0qb5ggFZN3X7QXWtgK4o7UgfS9DlpFC6JT6OWVs6X4&sid=a5d90165&type=tcp#RU-VK-1",
    "vless://126e5a65-e81a-46ce-bd61-605f32f1352e@91.217.10.166:9443?flow=xtls-rprx-vision&security=reality&sni=api.avito.ru&pbk=WvNaAxI0W__qfUKbtysH4IwF155YENlv3PG6crCmPkA&type=tcp#KZ-3",
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
#     ДЕОБФУСКАТОР — ПОЛНЫЙ (Rendy 1.0 + 2.0)
# ═══════════════════════════════════════

_deobf_note = "# DECODED BY @ArrhythmiaFucksn\n\n"
_comments_pat = r"#(.*?)\n"
_exec_pattern  = r"exec\(\(_\)\(b'([\s\S]+?)'\)\)"

# ── Карта компрессоров ────────────────────────────────────────────
_DECOMP_MAP = {
    "gzip": gzip.decompress,
    "lzma": lzma.decompress,
    "zlib": zlib.decompress,
}

# ── Rendy: все сигнатуры (1.0 + 2.0 A–H) ────────────────────────
_RENDY_SIGNATURES = [
    # 1.0 — gzip→lzma→zlib + реверс
    (re.compile(
        r"_=lambda __:__import__\('marshal'\)\.loads\("
        r"__import__\('gzip'\)\.decompress\("
        r"__import__\('lzma'\)\.decompress\("
        r"__import__\('zlib'\)\.decompress\("
        r"__import__\('base64'\)\.b64decode\(__\[::-1\]\)\)\)\)\)"
    ), ["gzip", "lzma", "zlib"], True, "1.0"),

    # 2.0 A — lzma→gzip→zlib + реверс
    (re.compile(
        r"_=lambda __:__import__\('marshal'\)\.loads\("
        r"__import__\('lzma'\)\.decompress\("
        r"__import__\('gzip'\)\.decompress\("
        r"__import__\('zlib'\)\.decompress\("
        r"__import__\('base64'\)\.b64decode\(__\[::-1\]\)\)\)\)\)"
    ), ["lzma", "gzip", "zlib"], True, "2.0A"),

    # 2.0 B — zlib→lzma→gzip + реверс
    (re.compile(
        r"_=lambda __:__import__\('marshal'\)\.loads\("
        r"__import__\('zlib'\)\.decompress\("
        r"__import__\('lzma'\)\.decompress\("
        r"__import__\('gzip'\)\.decompress\("
        r"__import__\('base64'\)\.b64decode\(__\[::-1\]\)\)\)\)\)"
    ), ["zlib", "lzma", "gzip"], True, "2.0B"),

    # 2.0 C — gzip→lzma→zlib БЕЗ реверса
    (re.compile(
        r"_=lambda __:__import__\('marshal'\)\.loads\("
        r"__import__\('gzip'\)\.decompress\("
        r"__import__\('lzma'\)\.decompress\("
        r"__import__\('zlib'\)\.decompress\("
        r"__import__\('base64'\)\.b64decode\(__\)\)\)\)\)"
    ), ["gzip", "lzma", "zlib"], False, "2.0C"),

    # 2.0 D — lzma→gzip→zlib БЕЗ реверса
    (re.compile(
        r"_=lambda __:__import__\('marshal'\)\.loads\("
        r"__import__\('lzma'\)\.decompress\("
        r"__import__\('gzip'\)\.decompress\("
        r"__import__\('zlib'\)\.decompress\("
        r"__import__\('base64'\)\.b64decode\(__\)\)\)\)\)"
    ), ["lzma", "gzip", "zlib"], False, "2.0D"),

    # 2.0 E — XOR-слой (детектируется отдельно ниже)
    # 2.0 F — 2 слоя: gzip→zlib + реверс
    (re.compile(
        r"_=lambda __:__import__\('marshal'\)\.loads\("
        r"__import__\('gzip'\)\.decompress\("
        r"__import__\('zlib'\)\.decompress\("
        r"__import__\('base64'\)\.b64decode\(__\[::-1\]\)\)\)\)"
    ), ["gzip", "zlib"], True, "2.0F"),

    # 2.0 G — 2 слоя: lzma→zlib + реверс
    (re.compile(
        r"_=lambda __:__import__\('marshal'\)\.loads\("
        r"__import__\('lzma'\)\.decompress\("
        r"__import__\('zlib'\)\.decompress\("
        r"__import__\('base64'\)\.b64decode\(__\[::-1\]\)\)\)\)"
    ), ["lzma", "zlib"], True, "2.0G"),

    # 2.0 H — 2 слоя: zlib→lzma + реверс
    (re.compile(
        r"_=lambda __:__import__\('marshal'\)\.loads\("
        r"__import__\('zlib'\)\.decompress\("
        r"__import__\('lzma'\)\.decompress\("
        r"__import__\('base64'\)\.b64decode\(__\[::-1\]\)\)\)\)"
    ), ["zlib", "lzma"], True, "2.0H"),
]

# Паттерны для извлечения payload из exec(_('...'))
_RENDY_PAYLOAD_PATS = [
    re.compile(r"exec\s*\(\s*_\s*\(\s*['\"]([A-Za-z0-9+/=\n\\]+)['\"]\s*\)\s*\)", re.DOTALL),
    re.compile(r"_\s*\(\s*['\"]([A-Za-z0-9+/=\n\\]{100,})['\"]\s*\)", re.DOTALL),
]


def _rendy_try_decode(enc: str, order: list, rev: bool) -> str | None:
    """Попытка декодировать Rendy payload с заданными параметрами."""
    try:
        enc_clean = enc.replace("\n", "").replace(" ", "").replace("\\n", "")
        raw = base64.b64decode(enc_clean[::-1] if rev else enc_clean)
        data = raw
        for step in order:
            data = _DECOMP_MAP[step](data)
        return marshal.loads(data).decode("utf-8", errors="replace")
    except Exception:
        return None


def _rendy_bruteforce(enc: str) -> str | None:
    """
    Брутфорс всех вариантов Rendy 2.0:
    - реверс / без реверса
    - все 6 перестановок 3 компрессоров
    - все 6 пар 2 компрессоров
    - XOR-слой
    """
    enc_clean = enc.replace("\n", "").replace(" ", "").replace("\\n", "")

    for rev in (True, False):
        try:
            raw = base64.b64decode(enc_clean[::-1] if rev else enc_clean)
        except Exception:
            continue

        # 3-слойный брутфорс (6 перестановок)
        for order in itertools.permutations(["gzip", "lzma", "zlib"]):
            try:
                data = raw
                for step in order:
                    data = _DECOMP_MAP[step](data)
                return marshal.loads(data).decode("utf-8", errors="replace")
            except Exception:
                continue

        # 2-слойный брутфорс (6 пар)
        for a, b in itertools.permutations(["gzip", "lzma", "zlib"], 2):
            try:
                data = _DECOMP_MAP[a](_DECOMP_MAP[b](raw))
                return marshal.loads(data).decode("utf-8", errors="replace")
            except Exception:
                continue

        # XOR-слой (Rendy 2.0E)
        for xkey in range(1, 256):
            try:
                xored = bytes([b ^ xkey for b in raw])
                for order in itertools.permutations(["gzip", "lzma", "zlib"]):
                    try:
                        data = xored
                        for step in order:
                            data = _DECOMP_MAP[step](data)
                        return marshal.loads(data).decode("utf-8", errors="replace")
                    except Exception:
                        continue
            except Exception:
                continue

    return None


def _rendy_extract_payload(code: str) -> str | None:
    """Ищет payload в exec(_('...')) или похожих конструкциях."""
    for pat in _RENDY_PAYLOAD_PATS:
        m = pat.search(code)
        if m:
            return m.group(1)
    # Fallback: большая base64-строка
    m = re.search(r"['\"]([A-Za-z0-9+/=]{200,})['\"]", code)
    if m:
        return m.group(1)
    return None


# ── Старые методы (base64/32/16 + compress) ──────────────────────
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


def detect_obfuscation(code: str) -> str | None:
    """Определяет метод обфускации. Возвращает строку-название или None."""
    # Сначала проверяем Rendy (приоритет)
    for sig_re, order, rev, version in _RENDY_SIGNATURES:
        if sig_re.search(code):
            return f"rendy{version} (marshal+{'→'.join(order)}+base64{'+rev' if rev else '+norev'})"
    # XOR-сигнатура Rendy 2.0E
    if re.search(r"marshal.*bytes\(\[.{0,60}\^.{0,60}for", code, re.DOTALL):
        return "rendy2.0E (marshal+xor+compress)"
    # Обобщённый детект Rendy без точной сигнатуры
    if re.search(r"_=lambda __:__import__\('marshal'\)\.loads\(", code):
        return "rendy_unknown (marshal+compress, bruteforce)"
    # Старые методы
    for pat, name in _obfuscation_patterns.items():
        if re.search(pat, code):
            return name
    return None


def deobfuscate_code(code: str) -> tuple:
    """
    Возвращает (deobfuscated_code, method_name) или (None, error_msg).
    Поддерживает: base64/32/16, zlib/gzip/lzma, комбо,
                  Rendy 1.0 и Rendy 2.0 (варианты A–H + XOR).
    """
    method = detect_obfuscation(code)
    if not method:
        return None, "Обфускация не обнаружена"

    try:
        result = None

        # ── Rendy (все версии) ──────────────────────────────────
        if "rendy" in method.lower():
            enc = _rendy_extract_payload(code)
            if enc is None:
                return None, f"Не найден payload ({method})"

            # Пробуем точный порядок из сигнатуры
            for sig_re, order, rev, version in _RENDY_SIGNATURES:
                if sig_re.search(code):
                    result = _rendy_try_decode(enc, order, rev)
                    if result:
                        break

            # Брутфорс если точный метод не дал результата
            if not result:
                result = _rendy_bruteforce(enc)

            if result is not None:
                return _deobf_note + result, method
            return None, f"Не удалось декодировать Rendy ({method})"

        # ── Классические методы ─────────────────────────────────
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

        if result is not None:
            return _deobf_note + result, method
        return None, f"Не удалось декодировать ({method})"

    except Exception as e:
        return None, f"Ошибка: {e}"

# ═══════════════════════════════════════
#        OPIUM MAILER
# ═══════════════════════════════════════
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

MAIL_SENDERS = {
    "dlatt6677@gmail.com":      "usun ruef otzx zcrh",
    "miranovseverov@gmail.com": "kdbc vmdb djxf pmiq",
    "alenaveterov@gmail.com":   "hmiq xwmr yfmw prsa",
}

def _send_one_email(receiver, sender_email, sender_password, subject, body, proxy=None):
    import socks as _socks_mod
    try:
        msg = MIMEMultipart()
        msg["From"]    = sender_email
        msg["To"]      = receiver
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        domain = sender_email.split("@")[-1]
        cfg = {
            "gmail.com":   ("smtp.gmail.com",    587),
            "rambler.ru":  ("smtp.rambler.ru",   587),
            "hotmail.com": ("smtp.office365.com",587),
            "mail.ru":     ("smtp.mail.ru",      587),
        }
        if domain not in cfg:
            return False, "неизвестный домен"
        host, port = cfg[domain]
        if proxy and SOCKS_OK:
            ptype = proxy.get("type", "http")
            ph    = proxy["host"]
            pp    = proxy["port"]
            pcode = (_socks_mod.SOCKS5 if ptype == "socks5"
                     else _socks_mod.SOCKS4 if ptype == "socks4"
                     else _socks_mod.HTTP)
            sock = _socks_mod.socksocket()
            sock.set_proxy(pcode, ph, pp)
            sock.settimeout(15)
            sock.connect((host, port))
            import ssl
            srv = smtplib.SMTP.__new__(smtplib.SMTP)
            srv._host = host
            srv.timeout = 15
            srv.sock = sock
            srv.file = None
            srv._tls_required = False
            srv.local_hostname = "localhost"
            srv.esmtp_features = {}
            srv.default_port = port
            srv.file = sock.makefile("rb")
            code_r, msg_r = srv.getreply()
            if code_r != 220:
                return False, f"SMTP {code_r}"
            srv.ehlo_or_helo_if_needed()
            srv.starttls()
            srv.ehlo()
            srv.login(sender_email, sender_password)
            srv.sendmail(sender_email, receiver, msg.as_string())
            srv.quit()
        else:
            srv = smtplib.SMTP(host, port, timeout=12)
            srv.starttls()
            srv.login(sender_email, sender_password)
            srv.sendmail(sender_email, receiver, msg.as_string())
            srv.quit()
        return True, "OK"
    except Exception as e:
        return False, str(e)[:60]

_mail_state:  dict = {}
_deobf_state: dict = {}

# ═══════════════════════════════════════
#              УТИЛИТЫ UI
# ═══════════════════════════════════════
def fmt_time(s):
    h = int(s // 3600); m = int((s % 3600) // 60); sc = int(s % 60)
    if h:   return f"{h}ч {m:02d}м {sc:02d}с"
    if m:   return f"{m}м {sc:02d}с"
    return f"{sc}с"

def ping_bar(ms):
    if ms is None:  return "⬜⬜⬜⬜⬜  нет данных"
    if ms < 80:     return "🟩🟩🟩🟩🟩  молниеносно~"
    if ms < 150:    return "🟩🟩🟩🟩⬜  отлично!"
    if ms < 250:    return "🟨🟨🟨⬜⬜  хорошо"
    if ms < 400:    return "🟧🟧⬜⬜⬜  средне"
    return                 "🟥⬜⬜⬜⬜  медленно..."

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
#           КЛАВИАТУРЫ
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
    k.add(telebot.types.InlineKeyboardButton("🔓 Деобфускатор", callback_data="deobf_menu"))
    k.add(telebot.types.InlineKeyboardButton("✉️ Mailer", callback_data="mail_menu"))
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
    per = 5; start = page * per; chunk = proxies[start:start + per]
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
    k.add(telebot.types.InlineKeyboardButton("🔍 Определить обфускацию", callback_data="deobf_detect"))
    k.add(telebot.types.InlineKeyboardButton("🔓 Деобфусцировать файл",  callback_data="deobf_run"))
    k.add(telebot.types.InlineKeyboardButton("◀ Назад",                  callback_data="back_main"))
    return k

def kb_mail(connected=False):
    k = telebot.types.InlineKeyboardMarkup(row_width=1)
    k.add(telebot.types.InlineKeyboardButton("✉️  Отправить письмо",  callback_data="mail_start"))
    k.add(telebot.types.InlineKeyboardButton("📋  Аккаунты",          callback_data="mail_accounts"))
    if not connected:
        k.add(telebot.types.InlineKeyboardButton("🔒  Подключить прокси", callback_data="connect"))
    else:
        k.add(telebot.types.InlineKeyboardButton("🔄  Сменить прокси",    callback_data="rotate"))
    k.add(telebot.types.InlineKeyboardButton("◀  Назад",             callback_data="back_main"))
    return k

class FMsg:
    def __init__(self, call, text=""):
        _cid = call.message.chat.id
        self.chat    = type("C", (), {"id": _cid})()
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
                    "first_name": name, "added": ts(), "uses": 0
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
            f"/deobf - деобфускатор\n"
            f"/vless - VLESS/Reality ссылки\n"
            f"/mail  - анонимный mailer\n"
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
#       /deobf — деобфускатор
# ═══════════════════════════════════════
@bot.message_handler(commands=["deobf"])
@access_required
def cmd_deobf(msg):
    _send(msg.chat.id,
        "🔓 Деобфускатор кода\n\n"
        "Поддерживаемые методы:\n"
        "• base64 / base32 / base16\n"
        "• zlib / gzip / lzma\n"
        "• base64+zlib / base64+gzip / base64+lzma\n"
        "• base32+zlib / base32+gzip / base32+lzma\n"
        "• base16+zlib / base16+gzip / base16+lzma\n"
        "• Rendy 1.0 (marshal+gzip→lzma→zlib+base64)\n"
        "• Rendy 2.0 A–H (все порядки компрессии)\n"
        "• Rendy 2.0 без реверса (norev)\n"
        "• Rendy 2.0E XOR-слой\n"
        "• Авто-брутфорс порядка слоёв\n\n"
        "Выбери действие:",
        kb_deobf())

@bot.message_handler(commands=["deobf_send"])
@access_required
def cmd_deobf_send(msg):
    uid = msg.from_user.id
    _deobf_state[uid] = "waiting"
    _send(msg.chat.id,
        "📎 Отправь .py файл для деобфускации\n\n"
        "Или напиши /cancel для отмены")

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
    if state not in ("waiting", "waiting_detect"):
        bot.send_message(msg.chat.id, "Чтобы деобфусцировать файл — нажми кнопку Деобфускатор или /deobf")
        return

    doc = msg.document
    if not doc.file_name.endswith(".py"):
        bot.send_message(msg.chat.id, "Только .py файлы!")
        return

    _deobf_state.pop(uid, None)
    wait = bot.send_message(msg.chat.id, "Анализирую файл...")

    def do():
        try:
            file_info  = bot.get_file(doc.file_id)
            downloaded = bot.download_file(file_info.file_path)
            code = downloaded.decode("utf-8", errors="replace")
            method = detect_obfuscation(code)

            if state == "waiting_detect":
                if method:
                    bot.edit_message_text(
                        f"Найдена обфускация: {method}\n\n"
                        f"Используй /deobf → Деобфусцировать файл для расшифровки",
                        msg.chat.id, wait.message_id)
                else:
                    bot.edit_message_text(
                        "Обфускация не обнаружена\n\nФайл чистый или метод неизвестен",
                        msg.chat.id, wait.message_id)
                return

            if not method:
                bot.edit_message_text(
                    "Обфускация не обнаружена\n\nФайл уже чистый или метод неизвестен",
                    msg.chat.id, wait.message_id)
                return

            bot.edit_message_text(
                f"Обнаружена: {method}\nДекодирую...",
                msg.chat.id, wait.message_id)

            result, info = deobfuscate_code(code)

            if result:
                out_name = f"decoded_{doc.file_name}"
                out_path = f"/tmp/{out_name}"
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(result)
                bot.edit_message_text(
                    f"Готово! Метод: {info}",
                    msg.chat.id, wait.message_id)
                with open(out_path, "rb") as f:
                    bot.send_document(msg.chat.id, f, visible_file_name=out_name,
                        caption=f"Decoded | Метод: {info}")
                try:
                    os.remove(out_path)
                except:
                    pass
            else:
                bot.edit_message_text(f"Не удалось: {info}", msg.chat.id, wait.message_id)

        except Exception as e:
            import traceback
            print(f"[deobf] ERR: {traceback.format_exc()}")
            try:
                bot.edit_message_text(f"Ошибка: {e}", msg.chat.id, wait.message_id)
            except:
                pass

    threading.Thread(target=do, daemon=True).start()

# ═══════════════════════════════════════
#        /mail — OpiumMailer
# ═══════════════════════════════════════
@bot.message_handler(commands=["mail"])
@access_required
def cmd_mail(msg):
    _send(msg.chat.id,
        "✉️  OpiumMailer\n\n"
        "📤  Анонимная рассылка через пул аккаунтов\n"
        f"📦  Аккаунтов в базе: {len(MAIL_SENDERS)}\n\n"
        "Выбери действие:",
        kb_mail())

@bot.message_handler(commands=["mail_cancel"])
def cmd_mail_cancel(msg):
    _mail_state.pop(msg.from_user.id, None)
    _send(msg.chat.id, "❌  Отменено~")

# ═══════════════════════════════════════
#       /vless — VLESS/Reality ссылки
# ═══════════════════════════════════════
@bot.message_handler(commands=["vless"])
@access_required
def cmd_vless(msg):
    if not MY_VLESS_PROXIES:
        _send(msg.chat.id, "Нет VLESS серверов~")
        return
    chunk_size = 5
    total  = len(MY_VLESS_PROXIES)
    header = (
        f"VLESS / XTLS-Reality серверы ({total} шт)\n\n"
        f"Вставляй в v2rayNG / Hiddify / Nekoray / Streisand\n"
        f"─────────────────────\n\n"
    )
    first = True
    for i in range(0, total, chunk_size):
        chunk = MY_VLESS_PROXIES[i:i+chunk_size]
        text  = (header if first else "") + "\n".join(chunk)
        first = False
        bot.send_message(msg.chat.id, text)

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
    if not is_admin(msg.from_user.id): return
    parts = msg.text.strip().split()
    if len(parts) < 2:
        _send(msg.chat.id, "Использование: /add <user_id> [Имя]"); return
    try:
        target = int(parts[1])
    except:
        _send(msg.chat.id, "❌ Неверный ID"); return
    banned_users.discard(target); banned_users.discard(str(target))
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
    if not is_admin(msg.from_user.id): return
    parts = msg.text.strip().split()
    if len(parts) < 2:
        _send(msg.chat.id, "/remove <user_id>"); return
    try:
        target = int(parts[1])
    except:
        _send(msg.chat.id, "❌ Неверный ID"); return
    key = str(target)
    if key in allowed_users:
        del allowed_users[key]; save_users()
        _send(msg.chat.id, f"✅ Удалён {target}")
    else:
        _send(msg.chat.id, f"Не найден {target}")

@bot.message_handler(commands=["ban"])
def cmd_ban(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.strip().split()
    if len(parts) < 2:
        _send(msg.chat.id, "/ban <user_id>"); return
    try:
        target = int(parts[1])
    except:
        _send(msg.chat.id, "❌ Неверный ID"); return
    banned_users.add(target)
    key = str(target)
    if key in allowed_users: del allowed_users[key]
    save_users()
    _send(msg.chat.id, f"🚫 Забанен {target}")

@bot.message_handler(commands=["unban"])
def cmd_unban(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.strip().split()
    if len(parts) < 2:
        _send(msg.chat.id, "/unban <user_id>"); return
    try:
        target = int(parts[1])
    except:
        _send(msg.chat.id, "❌ Неверный ID"); return
    banned_users.discard(target); banned_users.discard(str(target))
    save_users()
    _send(msg.chat.id, f"✅ Разбанен {target} 🌸")

@bot.message_handler(commands=["users"])
def cmd_users(msg):
    if not is_admin(msg.from_user.id): return
    _send_users_list(msg.chat.id)

def _send_users_list(chat_id, msg_id=None):
    if not allowed_users:
        text = "👥 Пользователи\n\nСписок пуст~"
    else:
        lines = [f"👥 Пользователи ({len(allowed_users)})\n\n"]
        for i, (uid_s, info) in enumerate(list(allowed_users.items())[:30], 1):
            uname  = info.get("username", "") or ""
            name   = info.get("first_name", "—")
            added  = info.get("added", "—")
            uses   = info.get("uses", 0)
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
            bot.edit_message_text(text, chat_id, msg_id, reply_markup=k); return
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
    if not wait: return
    cid = msg.chat.id; mid = wait.message_id; upd = _updater(cid, mid)

    def tcp_cb(done, total):
        upd(f"🔍 Сканирую серверы...\n\nЭтап 1/2: TCP-пинг\n{lbar(done,total)}  {done}/{total} хостов")

    def http_cb(done, total):
        upd(f"🔍 Сканирую серверы...\n\nЭтап 2/2: Проверка IP\n{lbar(done,total)}  {done}/{total} живых серверов")

    def do():
        my_ip   = get_my_ip() or ""
        results = build_smart_pool(my_ip, sample=SCAN_SAMPLE, tcp_cb=tcp_cb, http_cb=http_cb)
        if not results:
            _edit(cid, mid,
                "❌ Серверы не найдены\n\n"
                "Попробуй /refresh и повтори /scan~"); return
        lines = [f"⚡ Смарт-пул готов — {len(results)} серверов 🌸\n\n"]
        for i, r in enumerate(results[:7], 1):
            lines.append(
                f"{i}. {proto_icon(r['type'])} {r['host']}:{r['port']}\n"
                f"   {ping_bar(r['ping'])}  {r['ping']} ms\n\n")
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
            kb_main(True)); return

    wait = _send(msg.chat.id, "🔍 Определяю твой IP...")
    if not wait: return
    cid = msg.chat.id; mid = wait.message_id; upd = _updater(cid, mid)

    def do():
        my_ip = get_my_ip() or "unknown"
        u["ip_before"] = my_ip
        label  = pf.upper() if pf else "АВТО"
        fast_n = len([p for p in cache["top_fast"] if not pf or p["type"] == pf])
        if fast_n:
            upd(f"🔄 Подключаюсь [{label}]\n\nТвой IP: {my_ip}\n⚡ Проверяю {fast_n} быстрых серверов...")
        else:
            upd(f"🔄 Подключаюсь [{label}]\n\nТвой IP: {my_ip}\n🔍 Полный поиск (запусти /scan для ускорения)...")

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
        _send(msg.chat.id, "ℹ️ VPN не подключён~", kb_main(False)); return
    sess = fmt_time(time.time() - u["connect_time"]) if u["connect_time"] else "—"
    px   = u["proxy"]
    ib   = u.get("ip_before", "—"); ia = u.get("ip_after", "—")
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
        _send(msg.chat.id, "ℹ️ Сначала /connect~"); return
    wait = _send(msg.chat.id, "🔄 Меняю IP...")
    if not wait: return
    cid = msg.chat.id; mid = wait.message_id; upd = _updater(cid, mid)

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
        if not wait: return

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
        _send(msg.chat.id, "📦 База пуста\n\nИспользуй /refresh~"); return

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
    if not wait: return

    def do():
        if u["connected"] and u["proxy"]:
            px   = u["proxy"]
            ip   = get_ip_via(px["type"], px["host"], px["port"], timeout=9)
            mode = f"{px['type'].upper()} прокси"; icon = "🌍"
        else:
            ip   = get_my_ip(timeout=7); mode = "прямое соединение"; icon = "📍"
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
    if not wait: return

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
        _send_config(msg.chat.id, None, u["proxy"]); return
    wait = _send(msg.chat.id, "🔧 Генерирую конфиг...")
    if not wait: return
    cid = msg.chat.id; mid = wait.message_id; upd = _updater(cid, mid)

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
            bot.edit_message_text(text, chat_id, msg_id, reply_markup=kb_generate()); return
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

    if d == "vless_list":
        if not is_allowed(uid): bot.answer_callback_query(call.id, "Нет доступа"); return
        bot.answer_callback_query(call.id)
        cmd_vless(FMsg(call, "/vless")); return

    if d == "mail_menu":
        if not is_allowed(uid): bot.answer_callback_query(call.id, "🔒"); return
        bot.answer_callback_query(call.id)
        _mail_state.pop(uid, None)
        u_loc = get_user(uid)
        px = (u_loc.get("proxy") if u_loc.get("connected")
              else (cache["top_fast"][0] if cache["top_fast"] else None))
        px_txt = (f"🔒  Прокси: {px['host']}:{px['port']} ({px['type'].upper()})"
                  if px else "⚠️  Прокси не выбран — письмо уйдёт напрямую")
        text = (
            f"✉️  OpiumMailer\n"
            f"──────────────────────\n"
            f"📦  Аккаунтов: {len(MAIL_SENDERS)}\n"
            f"{px_txt}\n"
            f"──────────────────────\n"
            f"Выбери действие:"
        )
        try: bot.edit_message_text(text, cid, mid, reply_markup=kb_mail(u_loc.get("connected", False)))
        except: _send(cid, text, kb_mail(u_loc.get("connected", False)))
        return

    if d == "mail_start":
        if not is_allowed(uid): bot.answer_callback_query(call.id, "🔒"); return
        bot.answer_callback_query(call.id)
        k = telebot.types.InlineKeyboardMarkup()
        k.add(telebot.types.InlineKeyboardButton("❌ Отмена", callback_data="mail_cancel"))
        try:
            bot.edit_message_text(
                "✉️  Mailer — шаг 1/3\n\n📬  Введи email получателя:",
                cid, mid, reply_markup=k)
            _mail_state[uid] = {"step": "receiver", "msg_id": mid}
        except:
            m2 = _send(cid, "✉️  Mailer — шаг 1/3\n\n📬  Введи email получателя:", k)
            _mail_state[uid] = {"step": "receiver", "msg_id": m2.message_id if m2 else None}
        return

    if d == "mail_accounts":
        if not is_allowed(uid): bot.answer_callback_query(call.id, "🔒"); return
        bot.answer_callback_query(call.id)
        lines = ["📋  Аккаунты в базе\n──────────────────────\n"]
        for i, email in enumerate(MAIL_SENDERS.keys(), 1):
            lines.append(f"  {i}.  {email}")
        lines += [f"\n──────────────────────", f"Всего: {len(MAIL_SENDERS)}"]
        k = telebot.types.InlineKeyboardMarkup(row_width=1)
        k.add(
            telebot.types.InlineKeyboardButton("✉️  Отправить письмо", callback_data="mail_start"),
            telebot.types.InlineKeyboardButton("◀  Назад", callback_data="mail_menu"),
        )
        try: bot.edit_message_text("\n".join(lines), cid, mid, reply_markup=k)
        except: _send(cid, "\n".join(lines), k)
        return

    if d == "mail_cancel":
        _mail_state.pop(uid, None)
        bot.answer_callback_query(call.id, "Отменено")
        k = telebot.types.InlineKeyboardMarkup(row_width=1)
        k.add(
            telebot.types.InlineKeyboardButton("✉️  Отправить письмо", callback_data="mail_start"),
            telebot.types.InlineKeyboardButton("◀  Назад", callback_data="back_main"),
        )
        try: bot.edit_message_text("✉️  Mailer\n\n❌  Отменено~", cid, mid, reply_markup=k)
        except: _send(cid, "Отменено~")
        return

    # ─ Деобфускатор ─────────────────────
    if d == "deobf_menu":
        if not is_allowed(uid): bot.answer_callback_query(call.id, "🔒"); return
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(
                "🔓 Деобфускатор кода 🌸\n\n"
                "Поддерживаемые методы:\n"
                "• base64/32/16 · zlib · gzip · lzma\n"
                "• Комбо: base+zlib/gzip/lzma\n"
                "• Rendy 1.0 (marshal+gzip→lzma→zlib+b64)\n"
                "• Rendy 2.0 A–H (все порядки компрессии)\n"
                "• Rendy 2.0 без реверса (norev варианты)\n"
                "• Rendy 2.0E XOR-слой\n"
                "• Авто-брутфорс если сигнатура неизвестна\n\n"
                "Выбери действие:",
                cid, mid, reply_markup=kb_deobf())
        except:
            _send(cid, "🔓 Деобфускатор", kb_deobf())
        return

    if d == "deobf_detect":
        if not is_allowed(uid): bot.answer_callback_query(call.id, "🔒"); return
        bot.answer_callback_query(call.id)
        _deobf_state[uid] = "waiting_detect"
        _edit(cid, mid,
            "🔍 Отправь .py файл и я определю тип обфускации~\n\n"
            "(/cancel для отмены)")
        return

    if d == "deobf_run":
        if not is_allowed(uid): bot.answer_callback_query(call.id, "🔒"); return
        bot.answer_callback_query(call.id)
        _deobf_state[uid] = "waiting"
        _edit(cid, mid,
            "📎 Отправь .py файл для деобфускации~\n\n"
            "(/cancel для отмены)")
        return

    # ─ Ручной выбор прокси ──────────────
    if d.startswith("pick_"):
        if not is_allowed(uid): bot.answer_callback_query(call.id, "🔒"); return
        idx  = int(d.split("_")[1])
        fast = cache["top_fast"]
        if idx >= len(fast): bot.answer_callback_query(call.id, "⚠️ Устаревший список"); return
        px = fast[idx]
        bot.answer_callback_query(call.id, "⚡ Подключаюсь...")
        u = get_user(uid)
        old_ip = u.get("ip_after") if u["connected"] else None
        wait = _send(cid,
            f"🔄 Подключаюсь к выбранному серверу...\n\n"
            f"{proto_icon(px['type'])} {px['host']}:{px['port']}")
        if not wait: return

        def do():
            my_ip = get_my_ip() or "unknown"
            if not old_ip: u["ip_before"] = my_ip
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
        if not is_allowed(uid): bot.answer_callback_query(call.id, "🔒"); return
        page = int(d.split("_")[1])
        fast = cache["top_fast"]
        bot.answer_callback_query(call.id)
        try: bot.edit_message_reply_markup(cid, mid, reply_markup=kb_proxy_list(fast, page))
        except: pass
        return

    if d == "back_main":
        bot.answer_callback_query(call.id)
        cmd_start(FMsg(call, "/start")); return

    if d == "adm_panel":
        if not is_admin(uid): bot.answer_callback_query(call.id, "🚫"); return
        bot.answer_callback_query(call.id)
        try: bot.edit_message_text(_admin_text(), cid, mid, reply_markup=kb_admin())
        except: _send(cid, _admin_text(), kb_admin())
        return

    # ─ Кнопки админа ────────────────────
    if d.startswith("adm_") or d.startswith("ban_") or d.startswith("del_"):
        if not is_admin(uid): bot.answer_callback_query(call.id, "🚫"); return
        if d == "adm_users":
            bot.answer_callback_query(call.id); _send_users_list(cid, mid)
        elif d == "adm_banned":
            bot.answer_callback_query(call.id)
            text = (f"🚫 Бан-лист ({len(banned_users)})\n\n" +
                    "\n".join(f"• {u}" for u in list(banned_users)[:30])
                    if banned_users else "🚫 Бан-лист\n\nПуст~")
            k = telebot.types.InlineKeyboardMarkup()
            k.add(telebot.types.InlineKeyboardButton("◀ Назад", callback_data="adm_panel"))
            try: bot.edit_message_text(text, cid, mid, reply_markup=k)
            except: _send(cid, text, k)
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
            try: bot.edit_message_text(text, cid, mid, reply_markup=k)
            except: _send(cid, text, k)
        elif d == "adm_refresh":
            bot.answer_callback_query(call.id, "🔄 Запущено...")
            def bg(): cache["updated"] = 0; refresh_cache(force=True)
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
            t = int(d.split("_")[1]); banned_users.add(t)
            k = str(t)
            if k in allowed_users: del allowed_users[k]
            save_users(); bot.answer_callback_query(call.id, f"🚫 {t}")
            _send_users_list(cid, mid)
        elif d.startswith("del_"):
            t = int(d.split("_")[1]); k = str(t)
            if k in allowed_users: del allowed_users[k]; save_users()
            bot.answer_callback_query(call.id, f"✅ {t}")
            _send_users_list(cid, mid)
        return

    # ─ Кнопки пользователя ──────────────
    if not is_allowed(uid):
        bot.answer_callback_query(call.id, "🔒 Нет доступа~"); return

    if d == "regen":
        bot.answer_callback_query(call.id, "🔧 Ищу другой...")
        cmd_generate(FMsg(call, "/generate")); return

    table = {
        "connect":    ("/connect",        "⚡ Подключаюсь..."),
        "c_socks5":   ("/connect socks5", "🔵"),
        "c_socks4":   ("/connect socks4", "🟣"),
        "c_http":     ("/connect http",   "⚪"),
        "disconnect": ("/disconnect",     "🔴"),
        "rotate":     ("/rotate",         "🔄"),
        "status":     ("/status",         ""),
        "proxies":    ("/proxies",        ""),
        "generate":   ("/generate",       "🔧"),
    }
    if d not in table: return
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

# ─ Mail диалог (шаги) ──────────────────────────────────────────────
@bot.message_handler(func=lambda m: int(m.from_user.id) in _mail_state and m.text and not m.text.startswith("/"))
def handle_mail_step(msg):
    uid   = int(msg.from_user.id)
    state = _mail_state.get(uid, {})
    step  = state.get("step")
    cid   = msg.chat.id
    try: bot.delete_message(cid, msg.message_id)
    except: pass
    mid = state.get("msg_id")

    def upd(text, kb=None):
        if mid:
            try: bot.edit_message_text(text, cid, mid, reply_markup=kb); return
            except: pass
        m2 = _send(cid, text, kb)
        if m2: state["msg_id"] = m2.message_id; _mail_state[uid] = state

    if step == "receiver":
        t = msg.text.strip()
        if "@" not in t or "." not in t:
            k = telebot.types.InlineKeyboardMarkup()
            k.add(telebot.types.InlineKeyboardButton("❌ Отмена", callback_data="mail_cancel"))
            upd("✉️  Mailer — шаг 1/3\n\n⚠️  Это не похоже на email\nВведи корректный адрес:", k)
            return
        state["receiver"] = t; state["step"] = "subject"; _mail_state[uid] = state
        k = telebot.types.InlineKeyboardMarkup()
        k.add(telebot.types.InlineKeyboardButton("❌ Отмена", callback_data="mail_cancel"))
        upd(f"✉️  Mailer — шаг 2/3\n\n📬  Кому: {t}\n\n📝  Введи тему письма:", k)

    elif step == "subject":
        state["subject"] = msg.text.strip(); state["step"] = "body"; _mail_state[uid] = state
        k = telebot.types.InlineKeyboardMarkup()
        k.add(telebot.types.InlineKeyboardButton("❌ Отмена", callback_data="mail_cancel"))
        upd(f"✉️  Mailer — шаг 3/3\n\n📬  Кому: {state['receiver']}\n📋  Тема: {state['subject']}\n\n📄  Введи текст письма:", k)

    elif step == "body":
        state["body"] = msg.text.strip(); _mail_state.pop(uid, None)
        receiver = state["receiver"]; subject = state["subject"]; body = state["body"]
        u = get_user(uid)
        proxy = (u.get("proxy") if u.get("connected")
                 else (cache["top_fast"][0] if cache["top_fast"] else None))
        proxy_txt = (f"🔒 через {proxy['host']}:{proxy['port']}"
                     if proxy else "⚠️  без прокси (нет в пуле)")

        if mid:
            try:
                bot.edit_message_text(
                    f"📤  Отправляю письма...\n\n"
                    f"📬  Кому: {receiver}\n📋  Тема: {subject}\n\n"
                    f"{proxy_txt}\n{lbar(0,len(MAIL_SENDERS))}  0/{len(MAIL_SENDERS)}",
                    cid, mid)
            except: mid = None
        if not mid:
            m2 = _send(cid, f"📤  Отправляю письма...\n\n📬  Кому: {receiver}")
            mid = m2.message_id if m2 else None

        def do():
            ok = fail = 0; results = []; total = len(MAIL_SENDERS)
            for i, (email, pwd) in enumerate(MAIL_SENDERS.items(), 1):
                if mid:
                    try:
                        bot.edit_message_text(
                            f"📤  Отправляю...\n\n📬  Кому: {receiver}\n📋  Тема: {subject}\n\n"
                            f"{proxy_txt}\n{lbar(i-1,total)}  {i-1}/{total}\n⏳  {email}",
                            cid, mid)
                    except: pass
                res, reason = _send_one_email(receiver, email, pwd, subject, body, proxy)
                if res: ok += 1; results.append(f"✅  {email}")
                else:   fail += 1; results.append(f"❌  {email}  ({reason})")
                time.sleep(0.5)

            status_emoji = "📨" if ok > 0 else "💀"
            status_txt   = "Письма доставлены!" if ok > 0 else "Ни одно не ушло"
            report = (
                f"📊  Отчёт рассылки\n──────────────────────\n"
                f"📬  Кому:   {receiver}\n📋  Тема:   {subject}\n{proxy_txt}\n"
                f"──────────────────────\n" + "\n".join(results) +
                f"\n──────────────────────\n"
                f"✅  Успешно: {ok} / {total}\n❌  Ошибок:  {fail} / {total}\n"
                f"──────────────────────\n{status_emoji}  {status_txt}"
            )
            kb = telebot.types.InlineKeyboardMarkup(row_width=2)
            kb.add(
                telebot.types.InlineKeyboardButton("🔄  Отправить снова", callback_data="mail_start"),
                telebot.types.InlineKeyboardButton("◀  Меню", callback_data="mail_menu"),
            )
            if mid:
                try: bot.edit_message_text(report, cid, mid, reply_markup=kb); return
                except: pass
            _send(cid, report, kb)

        threading.Thread(target=do, daemon=True).start()

# ─ Рассылка ────────────────────────────────────────────────────────
@bot.message_handler(func=lambda m: m.from_user.id in _broadcast_state
                                    and _broadcast_state[m.from_user.id] is True
                                    and m.text != "/cancel")
def handle_broadcast(msg):
    if not is_admin(msg.from_user.id): return
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

# ─ /cancel ─────────────────────────────────────────────────────────
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
    print(f"  Rendy:   ✓ 1.0 + 2.0 A–H + XOR (8 сигнатур + брутфорс)")
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
