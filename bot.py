"""
  🔓 Деобфускатор Python · Astolfo Edition 🌸
  pip install pyTelegramBotAPI
  python3 deobf_bot.py
"""

import telebot, threading, time, re, json, os, io, struct
import zlib, base64, gzip, lzma, marshal, types, dis
from datetime import datetime

# ═══════════════════════════════════════
#            КОНФИГУРАЦИЯ
# ═══════════════════════════════════════
TOKEN     = "8603769389:AAFNrImTZhMY0ctceejoFbNkosE54cNsE30"
ADMIN_IDS = {7321093872}

USERS_FILE  = "allowed_users.json"
BANNED_FILE = "banned_users.json"

WELCOME_PHOTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "astolfo.png")

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
banned_users:  dict = _load(BANNED_FILE, {})

def save_users():
    _save(USERS_FILE,  allowed_users)
    _save(BANNED_FILE, banned_users)

def is_admin(uid):   return int(uid) in ADMIN_IDS
def is_banned(uid):  return str(uid) in banned_users
def is_allowed(uid): return is_admin(uid) or (str(uid) in allowed_users and not is_banned(uid))

def access_required(fn):
    def wrapper(msg):
        uid = msg.from_user.id
        if not is_allowed(uid):
            bot.send_message(msg.chat.id,
                "Привет! Доступ закрыт~\nБот работает только по приглашению.\nОбратись к администратору")
            return
        return fn(msg)
    wrapper.__name__ = fn.__name__
    return wrapper

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

bot = telebot.TeleBot(TOKEN, parse_mode=None)

# ═══════════════════════════════════════════════════════
#
#   ДЕОБФУСКАТОР v1 — lambda + exec обфускации
#
#  Поддерживает:
#   base64 / base32 / base16
#   zlib / gzip / lzma
#   base64+zlib/gzip/lzma   base32+zlib/gzip/lzma
#   base16+zlib/gzip/lzma
#   rendy (marshal+gzip+lzma+zlib+base64)
# ═══════════════════════════════════════════════════════

_exec_pattern = r"""exec\(\s*\(?\s*_+\s*\)?\s*\(\s*b['"]([\s\S]+?)['"]\s*\)\s*\)"""
_deobf_note   = "# DECODED BY @ArrhythmiaFucksn\n\n"

_obfuscation_patterns = {
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b64decode\(__\[::-1\]\)\s*;": "base64",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b32decode\(__\[::-1\]\)\s*;": "base32",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b16decode\(__\[::-1\]\)\s*;": "base16",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('zlib'\)\.decompress\(__\[::-1\]\)\s*;":  "zlib",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('gzip'\)\.decompress\(__\[::-1\]\)\s*;":  "gzip",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('lzma'\)\.decompress\(__\[::-1\]\)\s*;":  "lzma",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('zlib'\)\.decompress\(\s*__import__\('base64'\)\.b64decode\(__\[::-1\]\)\s*\)\s*;": "base64+zlib",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('gzip'\)\.decompress\(\s*__import__\('base64'\)\.b64decode\(__\[::-1\]\)\s*\)\s*;": "base64+gzip",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('lzma'\)\.decompress\(\s*__import__\('base64'\)\.b64decode\(__\[::-1\]\)\s*\)\s*;": "base64+lzma",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('zlib'\)\.decompress\(\s*__import__\('base64'\)\.b32decode\(__\[::-1\]\)\s*\)\s*;": "base32+zlib",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('gzip'\)\.decompress\(\s*__import__\('base64'\)\.b32decode\(__\[::-1\]\)\s*\)\s*;": "base32+gzip",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('lzma'\)\.decompress\(\s*__import__\('base64'\)\.b32decode\(__\[::-1\]\)\s*\)\s*;": "base32+lzma",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('zlib'\)\.decompress\(\s*__import__\('base64'\)\.b16decode\(__\[::-1\]\)\s*\)\s*;": "base16+zlib",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('gzip'\)\.decompress\(\s*__import__\('base64'\)\.b16decode\(__\[::-1\]\)\s*\)\s*;": "base16+gzip",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('lzma'\)\.decompress\(\s*__import__\('base64'\)\.b16decode\(__\[::-1\]\)\s*\)\s*;": "base16+lzma",
    r"_\s*=\s*lambda\s*__\s*:\s*__import__\('marshal'\)\.loads\(\s*__import__\('gzip'\)\.decompress\(\s*__import__\('lzma'\)\.decompress\(\s*__import__\('zlib'\)\.decompress\(\s*__import__\('base64'\)\.b64decode\(\s*__\[::-1\]\s*\)\s*\)\s*\)\s*\)\s*\)\s*;": "rendy (marshal+gzip+lzma+zlib+base64)",
}

def _b64_pad(s: str) -> str:
    pad = len(s) % 4
    if pad:
        s += "=" * (4 - pad)
    return s

def _strip_comments(code: str) -> str:
    result_lines = []
    for line in code.split("\n"):
        in_single = False
        in_double = False
        out = []
        i = 0
        while i < len(line):
            c = line[i]
            if c == "'" and not in_double:
                in_single = not in_single
                out.append(c)
            elif c == '"' and not in_single:
                in_double = not in_double
                out.append(c)
            elif c == "#" and not in_single and not in_double:
                break
            else:
                out.append(c)
            i += 1
        result_lines.append("".join(out).rstrip())
    return "\n".join(result_lines)

def _deobf_b64(code):
    def dec(m):
        try:
            return base64.b64decode(_b64_pad(m.group(1))[::-1]).decode("utf-8", errors="replace")
        except Exception as e:
            return f"# [v1 b64 err: {e}]\n"
    prev = None
    while prev != code and re.search(_exec_pattern, code):
        prev = code
        code = re.sub(_exec_pattern, dec, code)
        code = re.sub(r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b64decode\(__\[::-1\]\)\s*;?", "", code)
    return _strip_comments(code).strip()

def _deobf_b32(code):
    def dec(m):
        try:
            return base64.b32decode(_b64_pad(m.group(1))[::-1]).decode("utf-8", errors="replace")
        except Exception as e:
            return f"# [v1 b32 err: {e}]\n"
    prev = None
    while prev != code and re.search(_exec_pattern, code):
        prev = code
        code = re.sub(_exec_pattern, dec, code)
        code = re.sub(r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b32decode\(__\[::-1\]\)\s*;?", "", code)
    return _strip_comments(code).strip()

def _deobf_b16(code):
    def dec(m):
        try:
            return base64.b16decode(m.group(1)[::-1].upper()).decode("utf-8", errors="replace")
        except Exception as e:
            return f"# [v1 b16 err: {e}]\n"
    prev = None
    while prev != code and re.search(_exec_pattern, code):
        prev = code
        code = re.sub(_exec_pattern, dec, code)
        code = re.sub(r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b16decode\(__\[::-1\]\)\s*;?", "", code)
    return _strip_comments(code).strip()

def _deobf_compress_only(code, compress_mod, mod_name):
    def dec(m):
        try:
            raw = m.group(1).encode("latin-1")
            return compress_mod.decompress(raw[::-1]).decode("utf-8", errors="replace")
        except Exception as e:
            return f"# [v1 {mod_name} err: {e}]\n"
    prev = None
    while prev != code and re.search(_exec_pattern, code):
        prev = code
        code = re.sub(_exec_pattern, dec, code)
        code = re.sub(r"_\s*=\s*lambda\s*__\s*:\s*__import__\('" + mod_name + r"'\)\.decompress\(__\[::-1\]\)\s*;?", "", code)
    return _strip_comments(code).strip()

def _deobf_combo(code, base_fn, compress_mod, base_name, compress_name):
    def dec(m):
        try:
            decoded = base_fn(_b64_pad(m.group(1))[::-1])
            return compress_mod.decompress(decoded).decode("utf-8", errors="replace")
        except Exception as e:
            return f"# [v1 {base_name}+{compress_name} err: {e}]\n"
    lambda_pat = (
        r"_\s*=\s*lambda\s*__\s*:\s*__import__\('" + compress_name + r"'\)\.decompress\(\s*"
        r"__import__\('base64'\)\." + base_name + r"decode\(__\[::-1\]\)\s*\)\s*;?"
    )
    prev = None
    while prev != code and re.search(_exec_pattern, code):
        prev = code
        code = re.sub(_exec_pattern, dec, code)
        code = re.sub(lambda_pat, "", code)
    return _strip_comments(code).strip()

def _deobf_rendy(code):
    pat_main = (
        r"_\s*=\s*lambda\s*__\s*:.*?marshal.*?\n?"
        r"exec\s*\(\s*_\s*\(\s*['\"]([\s\S]+?)['\"]\s*\)\s*\)"
    )
    m = re.search(pat_main, code, re.DOTALL)
    if not m:
        m = re.search(r"exec\s*\(\s*_\s*\(\s*['\"]([A-Za-z0-9+/=\n]+)['\"]\s*\)\s*\)", code, re.DOTALL)
    if not m:
        return None
    try:
        enc = m.group(1).replace("\n", "").replace(" ", "")
        enc = _b64_pad(enc)
        raw = base64.b64decode(enc[::-1])
        raw = zlib.decompress(raw)
        raw = lzma.decompress(raw)
        raw = gzip.decompress(raw)
        code_obj = marshal.loads(raw)
        if isinstance(code_obj, bytes):
            return code_obj.decode("utf-8", errors="replace")
        if isinstance(code_obj, types.CodeType):
            buf = io.StringIO()
            dis.dis(code_obj, file=buf)
            return f"# [marshal CodeType — дизассемблировано]\n{buf.getvalue()}"
        return str(code_obj)
    except Exception:
        return None

def detect_obfuscation(code):
    for pat, name in _obfuscation_patterns.items():
        if re.search(pat, code):
            return name
    if re.search(_exec_pattern, code):
        if "b64decode" in code:
            if "zlib" in code: return "base64+zlib"
            if "gzip" in code: return "base64+gzip"
            if "lzma" in code: return "base64+lzma"
            return "base64"
        if "b32decode" in code:
            if "zlib" in code: return "base32+zlib"
            if "gzip" in code: return "base32+gzip"
            if "lzma" in code: return "base32+lzma"
            return "base32"
        if "b16decode" in code:
            if "zlib" in code: return "base16+zlib"
            if "gzip" in code: return "base16+gzip"
            if "lzma" in code: return "base16+lzma"
            return "base16"
        if "zlib" in code:   return "zlib"
        if "gzip" in code:   return "gzip"
        if "lzma" in code:   return "lzma"
    return None

def deobfuscate_code(code):
    method = detect_obfuscation(code)
    if not method:
        return None, "Обфускация не обнаружена"
    try:
        result = None
        if   method == "base64":      result = _deobf_b64(code)
        elif method == "base32":      result = _deobf_b32(code)
        elif method == "base16":      result = _deobf_b16(code)
        elif method == "zlib":        result = _deobf_compress_only(code, zlib, "zlib")
        elif method == "gzip":        result = _deobf_compress_only(code, gzip, "gzip")
        elif method == "lzma":        result = _deobf_compress_only(code, lzma, "lzma")
        elif method == "base64+zlib": result = _deobf_combo(code, base64.b64decode, zlib,  "b64", "zlib")
        elif method == "base64+gzip": result = _deobf_combo(code, base64.b64decode, gzip,  "b64", "gzip")
        elif method == "base64+lzma": result = _deobf_combo(code, base64.b64decode, lzma,  "b64", "lzma")
        elif method == "base32+zlib": result = _deobf_combo(code, base64.b32decode, zlib,  "b32", "zlib")
        elif method == "base32+gzip": result = _deobf_combo(code, base64.b32decode, gzip,  "b32", "gzip")
        elif method == "base32+lzma": result = _deobf_combo(code, base64.b32decode, lzma,  "b32", "lzma")
        elif method == "base16+zlib": result = _deobf_combo(code, base64.b16decode, zlib,  "b16", "zlib")
        elif method == "base16+gzip": result = _deobf_combo(code, base64.b16decode, gzip,  "b16", "gzip")
        elif method == "base16+lzma": result = _deobf_combo(code, base64.b16decode, lzma,  "b16", "lzma")
        elif "rendy" in method:       result = _deobf_rendy(code)
        if result is not None:
            return _deobf_note + result, method
        return None, f"Не удалось декодировать ({method})"
    except Exception as e:
        import traceback
        print(f"[deobf v1] ERR ({method}):\n{traceback.format_exc()}")
        return None, f"Ошибка ({method}): {e}"


# ═══════════════════════════════════════════════════════
#
#   ДЕОБФУСКАТОР v2 — Ренди 2.0
#   Universal Python Deobfuscator
#
#  25+ техник:
#  01  Бинарный payload (b64+zlib+gzip+lzma+marshal)
#  02  XOR строки (bytes.fromhex ^ key)
#  03  __import__('x') → x
#  04  getattr(obj,'name') → obj.name
#  05  WRAPPER(fn,[args],{kw}) → fn(*args,**kw)
#  06  __identity_func__()()(val) → val
#  07  Unicode/китайские имена → _vN
#  08  Dummy vars (большие числа)
#  09  Anti-debug time-checks
#  10  Anti-debug IsDebuggerPresent/gettrace
#  11  Защитные классы (__UltraProtection__ и т.д.)
#  12  Защитные функции (__tarpit__ и т.д.)
#  13  Пустой boilerplate (try:pass/except:pass)
#  14  State-machine (while VAR!=N / if VAR==N)
#  15  Unreachable code (после return/raise)
#  16  Lambda-пустышки
#  17  __check_N__/__var_N__ присваивания
#  18  Мусорные списки (500+ одинаковых элементов)
#  19  Константные выражения
#  20  Statement literals (строки-мусор в теле)
#  21  Lambda anti-debug guards
#  22  _vN(fmt,[args],{}) → fmt(args)
#  23  Вложенный getattr(obj,'m')(args)
#  24  Повтор после unicode-rename
#  25  Финальная очистка
# ═══════════════════════════════════════════════════════

XOR_ADJ = 2

# ── 01  Binary payload ──────────────────────────────
def r2_try_b64(d):
    try: r = base64.b64decode(d); return r if len(r)>10 else None
    except: return None
def r2_try_zlib(d):
    try: return zlib.decompress(d)
    except: return None
def r2_try_gzip(d):
    try: return gzip.decompress(d)
    except: return None
def r2_try_lzma(d):
    try: return lzma.decompress(d)
    except: return None
def r2_try_marshal(d):
    try:
        obj = marshal.loads(d)
        if isinstance(obj, bytes): return obj
        if isinstance(obj, types.CodeType):
            buf = io.StringIO(); dis.dis(obj, file=buf)
            return buf.getvalue().encode()
        return str(obj).encode()
    except: return None

def r2_decompress_chain(data, depth=0, maxd=10):
    if depth >= maxd: return data
    for fn in (r2_try_b64, r2_try_zlib, r2_try_gzip, r2_try_lzma, r2_try_marshal):
        r = fn(data)
        if r and r != data:
            return r2_decompress_chain(r, depth+1, maxd)
    return data

def r2_extract_layer1(source):
    for pat in [
        r"b['\"]([A-Za-z0-9+/=\n ]{200,})['\"]",
        r"(?:exec|eval)\s*\([^)]*?['\"]([A-Za-z0-9+/=\n ]{40,})['\"]",
    ]:
        for m in re.finditer(pat, source, re.DOTALL):
            raw = m.group(1).replace('\n','').replace(' ','').encode()
            result = r2_decompress_chain(raw)
            try:
                decoded = result.decode('utf-8')
                if len(decoded) > 50 and ('def ' in decoded or 'import' in decoded):
                    return decoded
            except: pass
    return source

# ── 02  XOR строки ──────────────────────────────────
def r2_decode_xor(hex_str, key, adj=None):
    if adj is None: adj = XOR_ADJ
    try: return ''.join(chr(b ^ (key ^ adj)) for b in bytes.fromhex(hex_str))
    except: return None

def r2_decode_xor_strings(source):
    pat = re.compile(
        r"bytes\.fromhex\(['\"]([0-9a-fA-F]+)['\"]\)"
        r"(?:\s*\.\s*decode\([^)]*\))?\s*\^\s*(?:(?:\w+\s*\^\s*)+)?(\d+)")
    def repl(m):
        try:
            d = r2_decode_xor(m.group(1), int(m.group(2)))
            return repr(d) if d else m.group(0)
        except: return m.group(0)
    return pat.sub(repl, source)

# ── 03  __import__('x') → x ─────────────────────────
def r2_simplify_imports(source):
    source = re.sub(r"__import__\s*\(['\"](\w+)['\"]\)\s*\.\s*(\w+)", lambda m: f"{m.group(1)}.{m.group(2)}", source)
    source = re.sub(r"__import__\s*\(['\"](\w+)['\"]\)", lambda m: m.group(1), source)
    return source

# ── 04  getattr → obj.name ──────────────────────────
def r2_simplify_getattr(source):
    prev = None; p = 0
    while prev != source and p < 20:
        prev = source; p += 1
        source = re.sub(
            r"getattr\s*\(\s*([A-Za-z_][\w.\[\]'\"]*)\s*,\s*['\"](\w+)['\"]\s*\)",
            lambda m: f"{m.group(1)}.{m.group(2)}", source)
        source = re.sub(
            r"getattr\s*\(\s*('[^']*'|\"[^\"]*\")\s*,\s*['\"](\w+)['\"]\s*\)",
            lambda m: f"{m.group(1)}.{m.group(2)}", source)
    return source

# ── 05  Call-wrappers ────────────────────────────────
def r2_detect_wrappers(source):
    return re.findall(
        r"def\s+(\w+)\s*\([^)]+\)\s*:\s*\n"
        r"(?:[ \t]+\w+\s*=\s*[\w.()]+\s*\n)?[ \t]+(?:pass\s*\n)?[ \t]*try\s*:\s*\n"
        r"[ \t]+raise\s+(?:Exception|BaseException|ValueError|TypeError|KeyError|RuntimeError)",
        source)

def r2_simplify_wrappers(source, names):
    if not names: return source
    prev = None; p = 0
    while prev != source and p < 25:
        prev = source; p += 1
        for n in names:
            ne = re.escape(n)
            source = re.sub(ne + r'\s*\(\s*([^,\[\]{}()]+?)\s*,\s*\[\s*\]\s*,\s*\{\s*\}\s*\)',
                lambda m: f'{m.group(1).strip()}()', source)
            source = re.sub(ne + r'\s*\(\s*([^,\[\]{}()]+?)\s*,\s*\[([^\[\]]+)\]\s*,\s*\{\s*\}\s*\)',
                lambda m: f'{m.group(1).strip()}({m.group(2).strip()})', source)
            source = re.sub(ne + r'\s*\(\s*([^,\[\]{}()]+?)\s*,\s*\[\s*\]\s*,\s*\{([^{}]+)\}\s*\)',
                lambda m: f'{m.group(1).strip()}({m.group(2).strip()})', source)
            source = re.sub(ne + r'\s*\(\s*([^,\[\]{}()]+?)\s*,\s*\[([^\[\]]+)\]\s*,\s*\{([^{}]+)\}\s*\)',
                lambda m: f'{m.group(1).strip()}({m.group(2).strip()}, {m.group(3).strip()})', source)
    return source

# ── 05b  Переименованные wrappers _vN ────────────────
def r2_expand_vn_wrappers(source):
    prev = None; p = 0
    while prev != source and p < 25:
        prev = source; p += 1
        source = re.sub(
            r'_v\d+\s*\(\s*([A-Za-z_][\w.\[\]\'\"]*(?:\s*\([^()]*\))?)\s*,\s*\[\s*\]\s*,\s*\{\s*\}\s*\)',
            lambda m: f'{m.group(1).strip()}()', source)
        source = re.sub(
            r'_v\d+\s*\(\s*([A-Za-z_][\w.\[\]\'\"]*(?:\s*\([^()]*\))?)\s*,\s*\[([^\[\]]+)\]\s*,\s*\{\s*\}\s*\)',
            lambda m: f'{m.group(1).strip()}({m.group(2).strip()})', source)
        source = re.sub(
            r'_v\d+\s*\(\s*([A-Za-z_][\w.\[\]\'\"]*(?:\s*\([^()]*\))?)\s*,\s*\[\s*\]\s*,\s*\{([^{}]+)\}\s*\)',
            lambda m: f'{m.group(1).strip()}({m.group(2).strip()})', source)
        source = re.sub(
            r'_v\d+\s*\(\s*([A-Za-z_][\w.\[\]\'\"]*(?:\s*\([^()]*\))?)\s*,\s*\[([^\[\]]+)\]\s*,\s*\{([^{}]+)\}\s*\)',
            lambda m: f'{m.group(1).strip()}({m.group(2).strip()}, {m.group(3).strip()})', source)
        source = re.sub(
            r"_v\d+\s*\(\s*('[^']*'\.[a-z]+)\s*,\s*\[([^\[\]]+)\]\s*,\s*\{\s*\}\s*\)",
            lambda m: f'{m.group(1)}({m.group(2)})', source)
        source = re.sub(
            r'_v\d+\s*\(\s*("[^"]*"\.[a-z]+)\s*,\s*\[([^\[\]]+)\]\s*,\s*\{\s*\}\s*\)',
            lambda m: f'{m.group(1)}({m.group(2)})', source)
    return source

# ── 06  Identity func ────────────────────────────────
def r2_detect_identity(source):
    names = set()
    for m in re.finditer(
        r"def\s+(\w+)\s*\(\s*(\w+)\s*\)\s*:\s*\n(?:[ \t]+\w+\s*=\s*[\w.()]+\s*\n[ \t]+)?[ \t]+return\s+\2\b",
        source
    ): names.add(m.group(1))
    names.add('__identity_func__')
    return names

def r2_simplify_identity(source):
    names = r2_detect_identity(source)
    prev = None; p = 0
    while prev != source and p < 20:
        prev = source; p += 1
        for n in names:
            if n not in source: continue
            source = re.sub(re.escape(n) + r'\s*\(\s*([^()]+?)\s*\)', lambda m: m.group(1), source)
    return source

# ── 07  Unicode → _vN ───────────────────────────────
def r2_rename_unicode(source):
    pat = re.compile(r'\b([\u3000-\u9fff\u3400-\u4dbf\uf900-\ufaff]{2,})\b')
    names = sorted(set(pat.findall(source)))
    for i, n in enumerate(names):
        source = source.replace(n, f'_v{i}')
    return source

# ── 08  Dummy vars ───────────────────────────────────
def r2_remove_dummy_vars(source):
    lines = source.split('\n')
    pat = re.compile(r'^(\s*)(\w+)\s*=\s*(\d{4,})\s*$')
    out = []
    for line in lines:
        m = pat.match(line)
        if m and '__' not in m.group(2) and not m.group(2).isupper():
            continue
        out.append(line)
    return '\n'.join(out)

# ── 09  Anti-debug time-checks ──────────────────────
def r2_remove_time_checks(source):
    source = re.sub(
        r'\n[ \t]+\w+\s*=\s*(?:__import__\([\'"]time[\'"]\)\.time|time\.time)\s*\(\s*\)[ \t]*(?=\n)', '', source)
    source = re.sub(
        r'\n[ \t]+if\s+(?:__import__\([\'"]time[\'"]\)\.time|time\.time)\s*\(\s*\)\s*-\s*\w+\s*>\s*[\d.]+\s*:\s*\n[ \t]+raise\s+\w+\s*\(\s*\)', '', source)
    return source

# ── 10  Anti-debug imports ───────────────────────────
def r2_remove_antidebug(source):
    for p in [
        r'^[^\n]*IsDebuggerPresent[^\n]*\n',
        r'^[^\n]*gettrace[^\n]*sys\.exit[^\n]*\n',
        r'^import\s+sys\s*,\s*ctypes\s*;[^\n]*\n',
        r'^[^\n]*sys\.exit\s*\(\s*0\s*\)[^\n]*\n',
    ]:
        source = re.sub(p, '', source, flags=re.MULTILINE)
    return source

# ── 11+12  Защитные классы и функции ────────────────
def r2_remove_protection(source):
    source = re.sub(
        r'\nclass\s+__\w+__\s*(?:\([^)]*\))?\s*:\s*\n(?:[ \t]+[^\n]*\n)*', '\n', source)
    for fn in [
        '__tarpit__', '__runtime_protect__', '__validate_signature__',
        '__check_lib__', '__decoder__', '__identity_func__',
        '__check_source__', '__check_imports__', '__check_stack__',
        '__check_file_integrity__', '__check_breakpoints__',
        '__check_modification__', '__protect__', '__check_file__',
        '__wrapper__', '__input_val__',
    ]:
        source = re.sub(
            r'\ndef\s+' + re.escape(fn) + r'\s*\([^)]*\)\s*:\s*\n(?:[ \t]+[^\n]*\n)*',
            '\n', source)
    # Вызовы защитных функций
    source = re.sub(
        r'\ntry:\s*\n[ \t]+(?:__\w+__\.|_v\d+\()(?:__protect__|__check_\w+__)(?:[^)]*\))?\s*\nexcept[^:]*:\s*\n[ \t]+pass\n?',
        '\n', source)
    return source

# ── 13  Boilerplate ──────────────────────────────────
def r2_remove_boilerplate(source):
    prev = None
    while prev != source:
        prev = source
        source = re.sub(
            r'\ntry:\s*\n[ \t]+pass\s*\nexcept[^:]*:\s*\n[ \t]+pass(?:\nelse:\s*\n[ \t]+pass)?(?:\nfinally:\s*\n[ \t]+pass)?',
            '', source)
    for kw in ['else', 'finally']:
        source = re.sub(r'\n' + kw + r'\s*:\s*\n[ \t]+pass(?=\n)', '', source)
    source = re.sub(r'\n[ \t]*__\w+(?:mod|sys|os|hash)__\s*=\s*\w+[ \t]*(?=\n)', '', source)
    return source

# ── 14  State-machine ────────────────────────────────
def r2_remove_state_machine(source):
    source = re.sub(
        r'\n[ \t]*\w+\s*=\s*\d+\s*\n[ \t]*while\s+\w+\s*!=\s*\d+\s*:\s*\n(?:[ \t]+[^\n]*\n)+',
        '\n', source, flags=re.MULTILINE)
    source = re.sub(
        r'\n([ \t]+)if\s+\w+\s*==\s*\d+\s*:\s*\n(?:\1[ \t]+[^\n]*\n)+',
        '\n', source, flags=re.MULTILINE)
    return source

# ── 15  Unreachable code ─────────────────────────────
def r2_remove_unreachable(source):
    lines = source.split('\n')
    result = []; i = 0
    tp = re.compile(r'^(return|raise|continue|break)\b')
    trash = re.compile(r'^\s*(?:\w+\s*=\s*\d+|pass|[\'"][^\'"]*[\'"])\s*$')
    while i < len(lines):
        line = lines[i]
        result.append(line)
        s = line.strip()
        if s and tp.match(s):
            indent = len(line) - len(line.lstrip())
            j = i + 1
            while j < len(lines):
                nl = lines[j]
                if not nl.strip(): j += 1; continue
                ni = len(nl) - len(nl.lstrip())
                if ni < indent: break
                if trash.match(nl.strip()): j += 1; continue
                break
            i = j; continue
        i += 1
    return '\n'.join(result)

# ── 16  Lambda-пустышки ──────────────────────────────
def r2_remove_lambda_noise(source):
    source = re.sub(r'\nlambda\s+\w+\s*:\s*\w+\s*\(\s*lambda\s*:\s*None\s*\)\s*\(\s*\)', '', source)
    source = re.sub(r'\nlambda\s*:\s*lambda\s*:\s*\w+\s*\(\s*\)\s*\(\s*\)', '', source)
    return source

# ── 17  __check_N__ мусор ────────────────────────────
def r2_remove_check_assigns(source):
    source = re.sub(r'\n[ \t]*__(?:check|var|confusion|hash_mod)_\w*__\s*=[^\n]+', '', source)
    return source

# ── 18  Мусорные списки ──────────────────────────────
def r2_remove_noisy_lists(source):
    out = []
    for line in source.split('\n'):
        if re.search(r'=\s*\[', line):
            items = re.findall(r"'[^']*'|\"[^\"]*\"|\d+", line)
            if len(items) > 15 and len(set(items)) <= 3:
                continue
        out.append(line)
    return '\n'.join(out)

# ── 19  Константные выражения ────────────────────────
def r2_fold_constants(source):
    def try_eval(m):
        try: return repr(eval(m.group(0)))
        except: return m.group(0)
    source = re.sub(r'\(\s*\d+\s*\*\s*\d+\s*\+\s*\d+\s*\)\s*%\s*2\s*==\s*\d+', try_eval, source)
    return source

# ── 20  Statement literals ───────────────────────────
def r2_remove_stmt_literals(source):
    source = re.sub(r'\n([ \t]+)(\'(?:[^\'\n])*\'|"(?:[^\"\n])*")[ \t]*(?=\n)', '', source)
    source = re.sub(r'\n[\'"](?:Verify|Detect|Runtime|Check|Protect|Finds subdomains)[^\'"\n]*[\'"][ \t]*(?=\n)', '', source)
    return source

# ── 21  Lambda anti-debug guards ─────────────────────
def r2_remove_lambda_guards(source):
    source = re.sub(r"lambda\s*:\s*\w+\s*\(\s*b['\"][^'\"]*['\"]\s*\)\s*\(\s*\)", '0', source)
    source = re.sub(r'\n[ \t]*if\s+0\s*<\s*0[^\n]*:\s*\n[ \t]+raise\s+Exception\s*\(\s*\)', '', source)
    source = re.sub(r'[ \t]*int\s*\(\s*0\s*-\s*0\s*\)', '', source)
    source = re.sub(r'\nfinally:\s*\n[ \t]*\n', '\n', source)
    return source

# ── 25  Финальная очистка ────────────────────────────
def r2_cleanup(source):
    lines = [l.rstrip() for l in source.split('\n')]
    out = []; blanks = 0
    for line in lines:
        if not line.strip():
            blanks += 1
            if blanks <= 2: out.append('')
        else:
            blanks = 0; out.append(line)
    return '\n'.join(out).strip() + '\n'


# ═══════════════════════════════════════════════════════
#
#   ДЕОБФУСКАТОР v3 — EXE/Binary Unpacker
#
#  Поддерживает:
#   • PyInstaller  (.exe / .pyc extracted)
#   • cx_Freeze    (.exe)
#   • Nuitka       (.exe / .pyd — дизассемблирование)
#   • zipapp       (.pyz / .zip внутри exe)
#   • py2exe       (.exe)
#   • CFF Explorer-style (PE структура, секции)
#   • MBA обфускация (Mixed Boolean Arithmetic)
#   • ROT13 / Caesar / Vigenere
#   • Hex string literals (\x41\x42...)
#   • Unicode escape (\u0041\u0042...)
#   • eval(compile(...)) обёртки
#   • Многослойный exec/eval
#   • String.join обфускация
#   • chr() конкатенация
#   • bytes literal обфускация
#   • Reversed string decode
#
# ═══════════════════════════════════════════════════════

# ── PyInstaller Magic ────────────────────────────────
PYINSTALLER_MAGIC = b'MEI\x0c\x0b\x0a\x0b\x0e'
PYINSTALLER_MAGIC_NEW = b'PYZ\x00'

def v3_detect_format(data: bytes) -> str:
    """Определяет формат бинарного файла."""
    if data[:2] == b'MZ':
        # PE файл
        if PYINSTALLER_MAGIC in data:
            return "pyinstaller"
        if b'cx_Freeze' in data[:4096] or b'cx_freeze' in data[:4096]:
            return "cx_freeze"
        if b'Nuitka' in data[:8192] or b'__nuitka' in data[:8192]:
            return "nuitka"
        if b'py2exe' in data[:4096]:
            return "py2exe"
        if b'PYTHONSCRIPT' in data[:16384]:
            return "brython"
        # Ищем ZIP в конце (PyInstaller, zipapp)
        if b'PK\x03\x04' in data[-65536:]:
            return "pe_with_zip"
        return "pe_unknown"
    if data[:4] == b'PK\x03\x04':
        return "zipapp"
    if data[:4] in (b'\x6f\x0d\x0d\x0a', b'\x61\x0d\x0d\x0a', b'\x33\x0d\x0d\x0a',
                    b'\xee\x0c\x0d\x0a', b'\x55\x0d\x0d\x0a'):
        return "pyc"
    if data[:16] == PYINSTALLER_MAGIC_NEW or b'PYZ-00.pyz' in data[:65536]:
        return "pyinstaller_pyz"
    if data[:2] == b'\x1f\x8b':
        return "gzip_wrapped"
    return "unknown"

def v3_extract_pyinstaller(data: bytes) -> dict:
    """
    Извлекает Python-файлы из PyInstaller EXE.
    Возвращает dict {filename: bytes_content}.
    """
    results = {}

    # Ищем CArchive (новый формат PyInstaller)
    try:
        # Magic для CArchive
        magic_pos = data.rfind(b'MEI\x0c\x0b\x0a\x0b\x0e')
        if magic_pos != -1:
            # TOC находится перед magic
            pkg_start = magic_pos - 8
            if pkg_start > 0:
                toc_pos, toc_size, pkg_len, _, _, pyver = struct.unpack_from('>IIIBBI', data, pkg_start - 24)
                archive_start = len(data) - pkg_len
                toc_start = archive_start + toc_pos
                toc_end   = toc_start + toc_size
                pos = toc_start
                while pos < toc_end:
                    entry_size, compress_size, data_size, compress_flag, typecode = struct.unpack_from('>IIIBB', data, pos)
                    pos += 18
                    name_bytes = data[pos:pos + entry_size - 18]
                    name = name_bytes.rstrip(b'\x00').decode('utf-8', errors='replace')
                    pos += entry_size - 18
                    entry_data = data[archive_start + struct.unpack_from('>I', data, pos - entry_size)[0]:
                                       archive_start + struct.unpack_from('>I', data, pos - entry_size)[0] + compress_size]
                    if compress_flag:
                        try: entry_data = zlib.decompress(entry_data)
                        except: pass
                    if typecode in (b'm', b'M', b's', b'o'):
                        results[name] = entry_data
    except Exception as e:
        results['_carchive_err'] = str(e).encode()

    # Ищем ZIP архив (для нового PyInstaller и zipapp)
    try:
        zip_start = data.rfind(b'PK\x03\x04')
        if zip_start == -1:
            zip_start = data.find(b'PK\x03\x04')
        if zip_start != -1:
            import zipfile
            zdata = io.BytesIO(data[zip_start:])
            try:
                with zipfile.ZipFile(zdata) as zf:
                    for name in zf.namelist():
                        if name.endswith(('.py', '.pyc', '.pyx', '.pyo')):
                            try:
                                results[f'zip_{name}'] = zf.read(name)
                            except: pass
            except: pass
    except Exception as e:
        results['_zip_err'] = str(e).encode()

    return results

def v3_decompile_pyc(data: bytes) -> str:
    """
    Декомпилирует .pyc файл в исходный код.
    Пробует: uncompyle6, decompile3, dis
    """
    # Убираем magic (первые 16 байт в Python 3.8+, 8 в старых)
    header_sizes = [16, 12, 8]
    code_obj = None
    for hsize in header_sizes:
        try:
            code_obj = marshal.loads(data[hsize:])
            break
        except: pass

    if code_obj is None:
        return "# Не удалось прочитать .pyc\n"

    # Пробуем decompyle3 / uncompyle6
    for pkg in ['decompyle3', 'uncompyle6']:
        try:
            mod = __import__(pkg)
            buf = io.StringIO()
            if hasattr(mod, 'decompile_code'):
                mod.decompile_code(code_obj, buf)
            elif hasattr(mod, 'decompile'):
                mod.decompile(code_obj, buf)
            result = buf.getvalue()
            if result and len(result) > 20:
                return result
        except Exception:
            pass

    # Fallback: дизассемблирование
    buf = io.StringIO()
    try:
        dis.dis(code_obj, file=buf)
        return f"# Дизассемблировано (decompyle3/uncompyle6 не найдены)\n{buf.getvalue()}"
    except Exception as e:
        return f"# Ошибка дизассемблирования: {e}\n"

def v3_extract_zipapp(data: bytes) -> dict:
    """Извлекает файлы из .pyz / zipapp архива."""
    import zipfile
    results = {}
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for name in zf.namelist():
                if name.endswith(('.py', '.pyc', '.pyx')):
                    try:
                        results[name] = zf.read(name)
                    except: pass
    except Exception as e:
        results['_err'] = str(e).encode()
    return results

def v3_extract_pe_strings(data: bytes) -> str:
    """Извлекает строки из PE файла — ищет Python-код."""
    results = []
    # Ищем секцию с Python байткодом
    for marker in [b'import ', b'def ', b'class ', b'print(', b'exec(', b'#!']:
        pos = 0
        while True:
            pos = data.find(marker, pos)
            if pos == -1: break
            # Берём контекст 2KB вокруг маркера
            start = max(0, pos - 512)
            end   = min(len(data), pos + 1536)
            chunk = data[start:end]
            try:
                text = chunk.decode('utf-8', errors='ignore')
                # Проверяем что это действительно Python-код
                if 'def ' in text or 'import ' in text or 'class ' in text:
                    results.append(text)
            except: pass
            pos += len(marker)
            if len(results) > 10: break
    return '\n# ─────────────────\n'.join(results[:5]) if results else ''

# ── MBA (Mixed Boolean Arithmetic) ──────────────────
def v3_simplify_mba(source: str) -> str:
    """
    Упрощает MBA (Mixed Boolean Arithmetic) обфускацию.
    MBA заменяет простые операции сложными булевыми выражениями:
        a + b = (a ^ b) + 2*(a & b)
        a - b = (a + ~b) + 1
        x * 2 = (x << 1)
    Восстанавливает читаемые операции.
    """
    # Паттерны MBA → упрощение через eval-подстановку константных выражений
    # (a ^ b) + 2*(a & b)  →  a + b
    source = re.sub(
        r'\(([^()]+)\s*\^\s*([^()]+)\)\s*\+\s*2\s*\*\s*\(([^()]+)\s*&\s*([^()]+)\)',
        lambda m: f'({m.group(1)} + {m.group(2)})' if m.group(1)==m.group(3) and m.group(2)==m.group(4)
                  else m.group(0),
        source)
    # (~a & b) | (a & ~b)  =  a ^ b
    source = re.sub(
        r'\(~([^()]+)\s*&\s*([^()]+)\)\s*\|\s*\(([^()]+)\s*&\s*~([^()]+)\)',
        lambda m: f'{m.group(1)} ^ {m.group(2)}' if m.group(1)==m.group(3) and m.group(2)==m.group(4)
                  else m.group(0),
        source)
    # (a | b) - (a & b)  =  a ^ b
    source = re.sub(
        r'\(([^()]+)\s*\|\s*([^()]+)\)\s*-\s*\(([^()]+)\s*&\s*([^()]+)\)',
        lambda m: f'{m.group(1)} ^ {m.group(2)}' if m.group(1)==m.group(3) and m.group(2)==m.group(4)
                  else m.group(0),
        source)
    # x * 2 → x << 1
    source = re.sub(r'(\w+)\s*\*\s*2(?!\d)', lambda m: f'({m.group(1)} << 1)', source)
    # Упрощаем двойное отрицание ~~x → x
    source = re.sub(r'~~(\w+)', lambda m: m.group(1), source)
    # Константные выражения в скобках
    def try_eval_const(m):
        try:
            v = eval(m.group(1))
            if isinstance(v, int) and -1000000 < v < 1000000:
                return str(v)
        except: pass
        return m.group(0)
    source = re.sub(r'\((\s*-?\d+\s*[\^|&+\-*/%~<>]+\s*-?\d+\s*)\)', try_eval_const, source)
    return source

# ── ROT13 / Caesar ───────────────────────────────────
def v3_decode_rot13_strings(source: str) -> str:
    """Декодирует ROT13 строки: codecs.decode('...', 'rot_13')"""
    def repl(m):
        try:
            import codecs
            return repr(codecs.decode(m.group(1), 'rot_13'))
        except: return m.group(0)
    source = re.sub(r"codecs\.decode\s*\(\s*'([^']+)'\s*,\s*'rot.13'\s*\)", repl, source)
    source = re.sub(r'codecs\.decode\s*\(\s*"([^"]+)"\s*,\s*"rot.13"\s*\)', repl, source)
    return source

def v3_decode_rot13_direct(text: str) -> str:
    """Прямое ROT13 декодирование строки."""
    import codecs
    return codecs.decode(text, 'rot_13')

# ── Hex escape strings ───────────────────────────────
def v3_decode_hex_strings(source: str) -> str:
    """
    Декодирует hex-escape строки:
        "\x70\x72\x69\x6e\x74" → "print"
    """
    def repl(m):
        try:
            raw = bytes.fromhex(m.group(1).replace('\\x', ''))
            return repr(raw.decode('utf-8', errors='replace'))
        except: return m.group(0)
    # '\x41\x42\x43' паттерн
    source = re.sub(
        r"'((?:\\x[0-9a-fA-F]{2})+)'",
        lambda m: repr(bytes(int(x, 16) for x in re.findall(r'\\x([0-9a-fA-F]{2})', m.group(1))).decode('utf-8', errors='replace')),
        source)
    source = re.sub(
        r'"((?:\\x[0-9a-fA-F]{2})+")',
        lambda m: repr(bytes(int(x, 16) for x in re.findall(r'\\x([0-9a-fA-F]{2})', m.group(1))).decode('utf-8', errors='replace')),
        source)
    return source

# ── Unicode escape strings ───────────────────────────
def v3_decode_unicode_escapes(source: str) -> str:
    """Декодирует \u0041\u0042 → AB"""
    def repl(m):
        try:
            return repr(m.group(1).encode('raw_unicode_escape').decode('unicode_escape'))
        except: return m.group(0)
    source = re.sub(r"'((?:\\u[0-9a-fA-F]{4})+)'", repl, source)
    source = re.sub(r'"((?:\\u[0-9a-fA-F]{4})+")', repl, source)
    return source

# ── chr() конкатенация ───────────────────────────────
def v3_decode_chr_concat(source: str) -> str:
    """
    chr(72)+chr(101)+chr(108)+chr(108)+chr(111) → 'Hello'
    """
    def repl(m):
        try:
            nums = re.findall(r'chr\s*\(\s*(\d+)\s*\)', m.group(0))
            if len(nums) >= 2:
                return repr(''.join(chr(int(n)) for n in nums))
        except: pass
        return m.group(0)
    source = re.sub(r'(?:chr\s*\(\s*\d+\s*\)\s*\+\s*){1,}chr\s*\(\s*\d+\s*\)', repl, source)
    return source

# ── String join обфускация ───────────────────────────
def v3_decode_join_obf(source: str) -> str:
    """
    ''.join(['H','e','l','l','o']) → 'Hello'
    ''.join(reversed(['o','l','l','e','H'])) → 'Hello'
    """
    def repl_join(m):
        try:
            sep = m.group(1)
            items = re.findall(r"'([^']*)'|\"([^\"]*)\"", m.group(2))
            chars = [a or b for a, b in items]
            return repr(sep.join(chars))
        except: return m.group(0)
    source = re.sub(
        r"'([^']*)'\s*\.\s*join\s*\(\s*\[([^\]]+)\]\s*\)",
        repl_join, source)
    def repl_reversed(m):
        try:
            items = re.findall(r"'([^']*)'|\"([^\"]*)\"", m.group(1))
            chars = [a or b for a, b in items]
            return repr(''.join(reversed(chars)))
        except: return m.group(0)
    source = re.sub(
        r"''\s*\.\s*join\s*\(\s*reversed\s*\(\s*\[([^\]]+)\]\s*\)\s*\)",
        repl_reversed, source)
    return source

# ── Reversed strings ─────────────────────────────────
def v3_decode_reversed(source: str) -> str:
    """
    'olleH'[::-1] → 'Hello'
    """
    def repl(m):
        try: return repr(m.group(1)[::-1])
        except: return m.group(0)
    source = re.sub(r"'([^']{2,})'\s*\[\s*::\s*-1\s*\]", repl, source)
    source = re.sub(r'"([^"]{2,})"\s*\[\s*::\s*-1\s*\]', repl, source)
    return source

# ── eval(compile(...)) обёртки ───────────────────────
def v3_remove_eval_compile(source: str) -> str:
    """
    eval(compile('code', '<string>', 'exec')) → code
    """
    def repl(m):
        try:
            inner = m.group(1)
            # Пробуем извлечь строку
            str_m = re.match(r"['\"](.+)['\"]", inner, re.DOTALL)
            if str_m:
                code = str_m.group(1)
                # Убираем escape
                code = code.replace('\\n', '\n').replace('\\t', '\t').replace("\\'", "'")
                return code
        except: pass
        return m.group(0)
    source = re.sub(
        r"eval\s*\(\s*compile\s*\(\s*(.+?)\s*,\s*['\"][^'\"]*['\"]\s*,\s*['\"]exec['\"]\s*\)\s*\)",
        repl, source, flags=re.DOTALL)
    return source

# ── Многослойный exec/eval ───────────────────────────
def v3_peel_exec_layers(source: str) -> str:
    """
    Раскрывает exec(base64.b64decode(b'...').decode()) и похожие.
    """
    # exec(base64.b64decode(b'...').decode())
    def repl_b64(m):
        try:
            raw = base64.b64decode(m.group(1))
            return raw.decode('utf-8', errors='replace')
        except: return m.group(0)
    source = re.sub(
        r"exec\s*\(\s*base64\.b64decode\s*\(\s*b['\"]([A-Za-z0-9+/=]+)['\"]\s*\)\s*\.decode\s*\([^)]*\)\s*\)",
        repl_b64, source)
    # exec(zlib.decompress(base64.b64decode(b'...')).decode())
    def repl_zlib(m):
        try:
            raw = zlib.decompress(base64.b64decode(m.group(1)))
            return raw.decode('utf-8', errors='replace')
        except: return m.group(0)
    source = re.sub(
        r"exec\s*\(\s*(?:zlib|__import__\(['\"]zlib['\"]\))\.decompress\s*\(\s*base64\.b64decode\s*\(\s*b['\"]([A-Za-z0-9+/=]+)['\"]\s*\)\s*\)\s*\.decode[^)]*\)\s*\)",
        repl_zlib, source)
    return source

# ── bytes literal обфускация ─────────────────────────
def v3_decode_bytes_literal(source: str) -> str:
    """
    bytes([72,101,108,108,111]).decode() → 'Hello'
    """
    def repl(m):
        try:
            nums = [int(x.strip()) for x in m.group(1).split(',')]
            return repr(bytes(nums).decode('utf-8', errors='replace'))
        except: return m.group(0)
    source = re.sub(
        r"bytes\s*\(\s*\[([0-9,\s]+)\]\s*\)\s*\.decode\s*\([^)]*\)",
        repl, source)
    return source

# ── Главная функция v3 ───────────────────────────────
def v3_deobfuscate_binary(data: bytes, filename: str) -> tuple:
    """
    Распаковывает EXE/binary файл и возвращает извлечённые файлы.
    Возвращает: (list[(name, content_str)], format_name)
    """
    fmt = v3_detect_format(data)
    results = []

    if fmt in ("pyinstaller", "pe_with_zip", "pyinstaller_pyz"):
        files = v3_extract_pyinstaller(data)
        for name, content in files.items():
            if name.endswith('.pyc') or (len(content) > 8 and content[0:4] in
                    [b'\x6f\x0d\x0d\x0a', b'\x61\x0d\x0d\x0a', b'\x33\x0d\x0d\x0a',
                     b'\xee\x0c\x0d\x0a', b'\x55\x0d\x0d\x0a']):
                src = v3_decompile_pyc(content)
                results.append((name.replace('.pyc', '.py'), src))
            elif name.endswith('.py'):
                results.append((name, content.decode('utf-8', errors='replace')))
            elif isinstance(content, str) and content.startswith('#'):
                results.append((name + '.txt', content))

    elif fmt in ("cx_freeze", "py2exe"):
        # cx_Freeze и py2exe хранят .pyc в library.zip
        files = v3_extract_pyinstaller(data)  # ZIP логика та же
        for name, content in files.items():
            if name.endswith('.pyc'):
                src = v3_decompile_pyc(content)
                results.append((name.replace('.pyc', '.py'), src))
            elif name.endswith('.py'):
                results.append((name, content.decode('utf-8', errors='replace')))

    elif fmt == "nuitka":
        # Nuitka компилирует в C, прямой декомпиляции нет — извлекаем строки
        strings = v3_extract_pe_strings(data)
        if strings:
            results.append(('nuitka_strings.py', f"# Извлечённые строки из Nuitka EXE\n\n{strings}"))
        else:
            results.append(('nuitka_info.txt', "# Nuitka EXE — прямая декомпиляция невозможна.\n# Nuitka компилирует Python в C/машинный код.\n# Доступно только извлечение строк."))

    elif fmt == "zipapp":
        files = v3_extract_zipapp(data)
        for name, content in files.items():
            if name.endswith('.pyc'):
                src = v3_decompile_pyc(content)
                results.append((name.replace('.pyc', '.py'), src))
            elif name.endswith('.py'):
                results.append((name, content.decode('utf-8', errors='replace')))

    elif fmt == "pyc":
        src = v3_decompile_pyc(data)
        results.append((filename.replace('.pyc', '_decompiled.py'), src))

    elif fmt == "gzip_wrapped":
        try:
            inner = gzip.decompress(data)
            inner_fmt = v3_detect_format(inner)
            if inner_fmt != "unknown":
                return v3_deobfuscate_binary(inner, filename)
            results.append((filename + '_ungzipped', inner.decode('utf-8', errors='replace')))
        except Exception as e:
            results.append(('err.txt', f"Ошибка распаковки gzip: {e}"))

    elif fmt == "pe_unknown":
        # Неизвестный PE — пробуем извлечь строки и ZIP
        files = v3_extract_pyinstaller(data)
        for name, content in files.items():
            if name.endswith(('.py', '.pyc')):
                if name.endswith('.pyc'):
                    src = v3_decompile_pyc(content)
                    results.append((name.replace('.pyc', '.py'), src))
                else:
                    results.append((name, content.decode('utf-8', errors='replace')))
        if not results:
            strings = v3_extract_pe_strings(data)
            if strings:
                results.append(('extracted_strings.py', strings))
            else:
                results.append(('info.txt', f"PE файл — Python-код не найден.\nФормат: {fmt}\nРазмер: {len(data):,} байт"))

    else:
        results.append(('info.txt', f"Неизвестный формат: {fmt}\nРазмер: {len(data):,} байт"))

    return results, fmt

def v3_deobfuscate_source(source: str) -> str:
    """
    Применяет все v3 source-level техники к Python-коду.
    MBA + строковые декодеры + eval/exec раскрытие.
    """
    source = v3_decode_rot13_strings(source)
    source = v3_decode_chr_concat(source)
    source = v3_decode_join_obf(source)
    source = v3_decode_reversed(source)
    source = v3_decode_hex_strings(source)
    source = v3_decode_unicode_escapes(source)
    source = v3_decode_bytes_literal(source)
    source = v3_peel_exec_layers(source)
    source = v3_remove_eval_compile(source)
    source = v3_simplify_mba(source)
    return source


# ═══════════════════════════════════════════════════════
#   ГЛАВНАЯ ФУНКЦИЯ — АВТО ДЕОБФУСКАТОР
#   Пробует все методы в порядке приоритета
# ═══════════════════════════════════════════════════════

def auto_deobfuscate_source(code: str) -> tuple:
    """
    Пробует все деобфускаторы для .py файла.
    Возвращает (result, method, stats)
    """
    lines_in  = code.count('\n') + 1
    chars_in  = len(code)

    # 1. v1 (lambda+exec)
    method_v1 = detect_obfuscation(code)
    if method_v1:
        result, info = deobfuscate_code(code)
        if result:
            return result, f"v1: {info}", {"lines_in": lines_in, "chars_in": chars_in,
                                           "lines_out": result.count('\n')+1, "chars_out": len(result)}

    # 2. v3 source-level (MBA, chr, hex, ROT13, ...)
    v3_result = v3_deobfuscate_source(code)
    if v3_result != code:
        # Применяем также v2 поверх v3
        v3_then_v2 = rendy2_deobfuscate(v3_result)
        return v3_then_v2, "v3+v2 (MBA/chr/hex + universal cleanup)", {
            "lines_in": lines_in, "chars_in": chars_in,
            "lines_out": v3_then_v2.count('\n')+1, "chars_out": len(v3_then_v2)}

    # 3. v2 (Ренди 2.0)
    v2_result = rendy2_deobfuscate(code)
    method    = "v2 (Ренди 2.0 — universal)"
    if method_v1:
        method = f"v2 fallback (v1 {method_v1} не сработал)"
    return v2_result, method, {
        "lines_in": lines_in, "chars_in": chars_in,
        "lines_out": v2_result.count('\n')+1, "chars_out": len(v2_result)}


def rendy2_deobfuscate(source: str, xor_adj: int = 2) -> str:
    """
    Ренди 2.0 — Universal Python Deobfuscator.
    3 волны, 25+ техник.
    """
    global XOR_ADJ
    XOR_ADJ = xor_adj

    # Волна 1: Трансформации
    source = r2_extract_layer1(source)
    source = r2_decode_xor_strings(source)
    source = r2_simplify_imports(source)
    source = r2_simplify_getattr(source)
    wnames = r2_detect_wrappers(source)
    source = r2_simplify_wrappers(source, wnames)
    source = r2_simplify_identity(source)
    source = r2_simplify_getattr(source)
    source = r2_simplify_imports(source)

    # Волна 2: Удаление мусора
    source = r2_remove_antidebug(source)
    source = r2_remove_time_checks(source)
    source = r2_remove_lambda_guards(source)
    source = r2_remove_protection(source)
    source = r2_remove_boilerplate(source)
    source = r2_remove_stmt_literals(source)
    source = r2_remove_state_machine(source)
    source = r2_remove_dummy_vars(source)
    source = r2_remove_unreachable(source)
    source = r2_remove_lambda_noise(source)
    source = r2_remove_check_assigns(source)
    source = r2_remove_noisy_lists(source)
    source = r2_fold_constants(source)

    # Волна 3: После unicode-rename
    source = r2_rename_unicode(source)
    wnames2 = r2_detect_wrappers(source)
    source = r2_simplify_wrappers(source, wnames2)
    source = r2_expand_vn_wrappers(source)
    source = r2_simplify_getattr(source)
    source = r2_simplify_identity(source)
    source = r2_simplify_imports(source)
    source = r2_remove_dummy_vars(source)
    source = r2_remove_unreachable(source)
    source = r2_remove_boilerplate(source)
    source = r2_remove_stmt_literals(source)
    source = r2_cleanup(source)

    return source


# ═══════════════════════════════════════
#           СОСТОЯНИЕ ПОЛЬЗОВАТЕЛЕЙ
# ═══════════════════════════════════════
_deobf_state: dict = {}


# ═══════════════════════════════════════
#           UI КОМПОНЕНТЫ
# ═══════════════════════════════════════
ASTOLFO_ART = (
    "╔══════════════════════╗\n"
    "║  🔓 DEOBF BOT 🌸    ║\n"
    "║    (\\(\\  ∧＿∧        ║\n"
    "║   (｡•ω•｡)つ━━✿✿✿    ║\n"
    "║  Astolfo Edition 💕  ║\n"
    "╚══════════════════════╝"
)

def _send(chat_id, text, kb=None):
    try:
        bot.send_message(chat_id, text, reply_markup=kb)
    except Exception as e:
        print(f"[send] err: {e}")

def _edit(chat_id, msg_id, text, kb=None):
    try:
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=kb)
    except Exception as e:
        print(f"[edit] err: {e}")

def kb_main():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔓 Деобфускатор (АВТО)")
    kb.row("🔬 Определить метод", "📦 EXE / Binary")
    kb.row("🔓 Только v1", "🔓 Только v2", "🔧 v3 Строки")
    return kb

def kb_deobf():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.row(telebot.types.InlineKeyboardButton("⚡ АВТО (v1→v2→v3)", callback_data="deobf_auto"))
    kb.row(telebot.types.InlineKeyboardButton("🔍 Определить метод", callback_data="deobf_detect"))
    kb.row(
        telebot.types.InlineKeyboardButton("🔓 Только v1", callback_data="deobf_v1"),
        telebot.types.InlineKeyboardButton("🔓 Только v2", callback_data="deobf_v2"))
    kb.row(
        telebot.types.InlineKeyboardButton("🔧 v3 Строки (MBA/chr/hex)", callback_data="deobf_v3src"),
        telebot.types.InlineKeyboardButton("📦 EXE/Binary", callback_data="deobf_v3bin"))
    return kb


# ═══════════════════════════════════════
#             КОМАНДЫ
# ═══════════════════════════════════════
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    try:
        uid  = int(msg.from_user.id)
        name = msg.from_user.first_name or "анон"

        if is_admin(uid):
            key = str(uid)
            if key not in allowed_users:
                allowed_users[key] = {
                    "username":   getattr(msg.from_user, "username", "") or "",
                    "first_name": name,
                    "added":      ts(), "uses": 0
                }
                save_users()

        if not is_allowed(uid):
            bot.send_message(msg.chat.id,
                f"{ASTOLFO_ART}\n\nПривет! Доступ закрыт~\nОбратись к администратору")
            return

        key = str(uid)
        if key in allowed_users:
            allowed_users[key]["uses"] = allowed_users[key].get("uses", 0) + 1
            save_users()

        adm_badge = " [ADMIN]" if is_admin(uid) else ""
        text = (
            f"{ASTOLFO_ART}\n\n"
            f"Привет, {name}!{adm_badge}\n\n"
            "🔓 Python Deobfuscator Bot\n"
            "──────────────────────\n"
            "Поддерживаемые методы:\n\n"
            "v1 (lambda+exec):\n"
            "  base64 / base32 / base16\n"
            "  zlib / gzip / lzma\n"
            "  Комбо base64/32/16 + zlib/gzip/lzma\n"
            "  Rendy (marshal+gzip+lzma+zlib+base64)\n\n"
            "v2 (Ренди 2.0 — Universal):\n"
            "  XOR строки · state-machine\n"
            "  Call-wrappers · dummy vars\n"
            "  getattr chains · unicode names\n"
            "  Anti-debug · защитные классы\n\n"
            "v3 — EXE/Binary:\n"
            "  PyInstaller · cx_Freeze · zipapp\n"
            "  py2exe · Nuitka · .pyc files\n\n"
            "v3 — Строковые методы:\n"
            "  MBA (Mixed Boolean Arithmetic)\n"
            "  ROT13 · chr() concat · hex escape\n"
            "  unicode escape · bytes[] decode\n"
            "  join obf · reversed strings\n"
            "  eval(compile()) · multilayer exec\n\n"
            "──────────────────────\n"
            "Команды:\n"
            "/deobf  — авто деобфускатор\n"
            "/deobf2 — только Ренди 2.0\n"
            "/deobf3 — EXE/Binary распаковка\n"
        )
        if is_admin(uid):
            text += "/admin — панель админа\n"

        if os.path.exists(WELCOME_PHOTO):
            try:
                with open(WELCOME_PHOTO, "rb") as f:
                    bot.send_photo(msg.chat.id, f)
            except: pass

        bot.send_message(msg.chat.id, text, reply_markup=kb_main())

    except Exception as e:
        import traceback
        print(f"[start] ERR: {traceback.format_exc()}")
        try: bot.send_message(msg.chat.id, "Бот работает! Попробуй /start ещё раз")
        except: pass


@bot.message_handler(commands=["deobf"])
@access_required
def cmd_deobf(msg):
    uid = msg.from_user.id
    _deobf_state[uid] = "waiting_auto"
    _send(msg.chat.id,
        "🔓 Авто-деобфускатор 🌸\n\n"
        "АВТО: пробует v1 → v3 строки → v2 (Ренди 2.0)\n\n"
        "📎 Отправь .py файл:",
        kb_deobf())


@bot.message_handler(commands=["deobf2"])
@access_required
def cmd_deobf2(msg):
    uid = msg.from_user.id
    _deobf_state[uid] = "waiting_v2"
    _send(msg.chat.id,
        "🔓 Ренди 2.0 — Universal Python Deobfuscator\n\n"
        "25+ техник деобфускации:\n"
        "  • XOR строки · state-machine · call-wrappers\n"
        "  • dummy vars · getattr() chains\n"
        "  • Anti-debug · защитные классы\n"
        "  • Unicode имена → читаемые\n\n"
        "📎 Отправь .py файл:")


@bot.message_handler(commands=["deobf3"])
@access_required
def cmd_deobf3(msg):
    uid = msg.from_user.id
    _deobf_state[uid] = "waiting_v3bin"
    _send(msg.chat.id,
        "📦 EXE/Binary Unpacker\n\n"
        "Поддерживает:\n"
        "  • PyInstaller (.exe / .pyc)\n"
        "  • cx_Freeze (.exe)\n"
        "  • py2exe (.exe)\n"
        "  • Nuitka (.exe — строки)\n"
        "  • zipapp (.pyz)\n"
        "  • .pyc файлы\n\n"
        "📎 Отправь .exe / .pyc / .pyz файл:")


# ═══════════════════════════════════════
#         Обработка ДОКУМЕНТОВ
# ═══════════════════════════════════════
@bot.message_handler(content_types=["document"])
def handle_document(msg):
    uid = int(msg.from_user.id)

    if not is_allowed(uid):
        bot.send_message(msg.chat.id, "Доступ закрыт~")
        return

    state = _deobf_state.get(uid)
    if state is None:
        bot.send_message(msg.chat.id,
            "Нажми кнопку или используй команду:\n"
            "/deobf — авто деобфускатор\n"
            "/deobf2 — Ренди 2.0\n"
            "/deobf3 — EXE/Binary")
        return

    doc = msg.document
    fname = doc.file_name or "file"
    _deobf_state.pop(uid, None)
    wait = bot.send_message(msg.chat.id, "🔍 Читаю файл...")

    def do():
        try:
            file_info  = bot.get_file(doc.file_id)
            downloaded = bot.download_file(file_info.file_path)

            # ══════════════════════════════════════
            #  EXE / Binary режим (v3 binary)
            # ══════════════════════════════════════
            if state == "waiting_v3bin":
                _edit(msg.chat.id, wait.message_id,
                    f"📦 Анализирую бинарный файл...\n\n"
                    f"📄 Файл: {fname}\n"
                    f"📊 Размер: {len(downloaded):,} байт")

                results, fmt = v3_deobfuscate_binary(downloaded, fname)

                if not results:
                    _edit(msg.chat.id, wait.message_id,
                        f"❌ Не удалось извлечь файлы\n📄 {fname}\nФормат: {fmt}")
                    return

                _edit(msg.chat.id, wait.message_id,
                    f"✅ Распаковано!\n\n"
                    f"📄 Файл: {fname}\n"
                    f"📦 Формат: {fmt}\n"
                    f"📁 Извлечено файлов: {len(results)}")

                for name, content in results[:10]:  # макс 10 файлов
                    if isinstance(content, bytes):
                        content = content.decode('utf-8', errors='replace')
                    out_path = f"/tmp/v3_{name}"
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    with open(out_path, "rb") as f:
                        bot.send_document(msg.chat.id, f, visible_file_name=name,
                            caption=f"📦 {fmt} | {name} | {len(content):,} символов")
                    try: os.remove(out_path)
                    except: pass
                return

            # ══════════════════════════════════════
            #  Python .py файл
            # ══════════════════════════════════════
            if not fname.endswith(".py"):
                # Пробуем как binary даже если не .exe
                _edit(msg.chat.id, wait.message_id,
                    f"📦 Пробую как бинарный файл...\n📄 {fname}")
                results, fmt = v3_deobfuscate_binary(downloaded, fname)
                if results and fmt != "unknown":
                    _edit(msg.chat.id, wait.message_id,
                        f"✅ Распаковано! Формат: {fmt}\n"
                        f"📁 Файлов: {len(results)}")
                    for name, content in results[:5]:
                        if isinstance(content, bytes):
                            content = content.decode('utf-8', errors='replace')
                        out_path = f"/tmp/v3_{name}"
                        with open(out_path, "w", encoding="utf-8") as f:
                            f.write(content)
                        with open(out_path, "rb") as f:
                            bot.send_document(msg.chat.id, f, visible_file_name=name,
                                caption=f"📦 {fmt} | {name}")
                        try: os.remove(out_path)
                        except: pass
                else:
                    _edit(msg.chat.id, wait.message_id,
                        f"❌ Только .py файлы для деобфускатора!\n"
                        f"Для EXE/binary используй /deobf3")
                return

            code = downloaded.decode("utf-8", errors="replace")
            lines_in = code.count('\n') + 1
            chars_in = len(code)

            # ── Режим: определение метода ──
            if state == "waiting_detect":
                _edit(msg.chat.id, wait.message_id, "🔍 Определяю метод обфускации...")
                method_v1 = detect_obfuscation(code)

                has_xor   = bool(re.search(r'bytes\.fromhex', code) and re.search(r'\^\s*\(\d+\s*\^', code))
                has_sm    = bool(re.search(r'while \w+ != \d+:', code))
                has_wrap  = bool(re.search(r'def \w+\s*\(\s*\w+\s*,\s*\w+\s*,\s*\w+\s*\)\s*:', code))
                has_exec  = bool(re.search(r'exec\s*\(', code))
                has_chr   = bool(re.search(r'chr\s*\(\s*\d+\s*\)\s*\+\s*chr', code))
                has_rot13 = bool(re.search(r"codecs\.decode.*rot.13", code))
                has_mba   = bool(re.search(r'\(\w+\s*\^\s*\w+\)\s*\+\s*2\s*\*', code))

                lines = [
                    f"🔬 Анализ: {fname}\n",
                    f"──────────────────────\n",
                    f"📄 Строк: {lines_in}  |  Символов: {chars_in:,}\n",
                    f"──────────────────────\n",
                ]
                if method_v1:
                    lines.append(f"✅ v1 метод: {method_v1}\n→ /deobf\n\n")
                else:
                    lines.append(f"❌ v1: не обнаружен\n\n")

                lines.append("🔎 Признаки:\n")
                lines.append(f"  XOR строки:     {'✅' if has_xor else '❌'}\n")
                lines.append(f"  State-machine:  {'✅' if has_sm else '❌'}\n")
                lines.append(f"  Call-wrappers:  {'✅' if has_wrap else '❌'}\n")
                lines.append(f"  exec() вызовы: {'✅' if has_exec else '❌'}\n")
                lines.append(f"  chr() concat:   {'✅' if has_chr else '❌'}\n")
                lines.append(f"  ROT13:          {'✅' if has_rot13 else '❌'}\n")
                lines.append(f"  MBA выражения:  {'✅' if has_mba else '❌'}\n")

                v2_score = sum([has_xor, has_sm, has_wrap, has_exec])
                v3_score = sum([has_chr, has_rot13, has_mba])
                if v2_score >= 2:
                    lines.append(f"\n🟡 Рекомендую: v2 (Ренди 2.0) → /deobf2\n")
                elif v3_score >= 1:
                    lines.append(f"\n🟡 Рекомендую: v3 строки → /deobf (АВТО)\n")
                elif not method_v1:
                    lines.append(f"\n⚪ Обфускация не распознана\n")

                _edit(msg.chat.id, wait.message_id, "".join(lines))
                return

            # ── Режим: только v3 строки ──
            if state == "waiting_v3src":
                _edit(msg.chat.id, wait.message_id,
                    f"🔧 v3 Строки — обрабатываю...\n📄 {fname}")
                result = v3_deobfuscate_source(code)
                _send_result(msg.chat.id, wait.message_id, result, doc.file_name,
                             "v3 (MBA/chr/hex/ROT13/unicode/bytes/join/reversed/eval)",
                             lines_in, chars_in, prefix="v3src_")
                return

            # ── Режим: только v2 ──
            if state == "waiting_v2":
                _edit(msg.chat.id, wait.message_id,
                    f"🔓 Ренди 2.0 — обрабатываю...\n"
                    f"📄 {fname}\n📊 Строк: {lines_in} | Символов: {chars_in:,}")
                result = rendy2_deobfuscate(code)
                _send_result(msg.chat.id, wait.message_id, result, doc.file_name,
                             "v2 (Ренди 2.0)", lines_in, chars_in, prefix="rendy2_")
                return

            # ── Режим: только v1 ──
            if state == "waiting":
                _edit(msg.chat.id, wait.message_id,
                    f"🔍 v1 — анализирую...\n📄 {fname}")
                result, info = deobfuscate_code(code)
                if result:
                    _send_result(msg.chat.id, wait.message_id, result, doc.file_name,
                                 f"v1: {info}", lines_in, chars_in, prefix="decoded_")
                else:
                    _edit(msg.chat.id, wait.message_id,
                        f"❌ v1 не смог декодировать: {info}\n\n"
                        f"Попробуй /deobf (АВТО) или /deobf2")
                return

            # ── Режим: АВТО ──
            _edit(msg.chat.id, wait.message_id,
                f"🔍 [АВТО] Анализирую {fname}...\n"
                f"📊 Строк: {lines_in} | Символов: {chars_in:,}\n\n"
                "⏳ Пробую методы: v1 → v3 строки → v2...")

            result, method, stats = auto_deobfuscate_source(code)
            _send_result(msg.chat.id, wait.message_id, result, doc.file_name,
                         f"АВТО: {method}", lines_in, chars_in, prefix="auto_")

        except Exception as e:
            import traceback
            print(f"[deobf] ERR: {traceback.format_exc()}")
            try:
                _edit(msg.chat.id, wait.message_id, f"❌ Ошибка обработки: {e}")
            except: pass

    threading.Thread(target=do, daemon=True).start()


def _send_result(chat_id, msg_id, result, orig_name, method, lines_in, chars_in, prefix=""):
    """Отправляет результат деобфускации."""
    lines_out  = result.count('\n') + 1
    chars_out  = len(result)
    red_l = round(100 * (1 - lines_out / max(lines_in, 1)))
    red_c = round(100 * (1 - chars_out / max(chars_in, 1)))

    _edit(chat_id, msg_id,
        f"✅ Готово! 🌸\n\n"
        f"📄 Файл: {orig_name}\n"
        f"──────────────────────\n"
        f"🔑 Метод:    {method}\n"
        f"📊 Строк:    {lines_in:,} → {lines_out:,}  ({red_l}% меньше)\n"
        f"💬 Символов: {chars_in:,} → {chars_out:,}  ({red_c}% меньше)\n"
        f"──────────────────────")

    out_name = f"{prefix}{orig_name}"
    out_path = f"/tmp/{out_name}"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)
    with open(out_path, "rb") as f:
        bot.send_document(chat_id, f, visible_file_name=out_name,
            caption=(
                f"🔓 {method}\n"
                f"Строк: {lines_in}→{lines_out} ({red_l}%↓) | "
                f"Символов: {chars_in:,}→{chars_out:,} ({red_c}%↓)"
            ))
    try: os.remove(out_path)
    except: pass


# ═══════════════════════════════════════
#           CALLBACK КНОПКИ
# ═══════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data.startswith("deobf_"))
def on_deobf_callback(call):
    uid = call.from_user.id
    if not is_allowed(uid):
        bot.answer_callback_query(call.id, "Нет доступа")
        return

    action_map = {
        "deobf_auto":    "waiting_auto",
        "deobf_detect":  "waiting_detect",
        "deobf_v1":      "waiting",
        "deobf_v2":      "waiting_v2",
        "deobf_v3src":   "waiting_v3src",
        "deobf_v3bin":   "waiting_v3bin",
    }
    state = action_map.get(call.data)
    if state:
        _deobf_state[uid] = state
        prompts = {
            "waiting_auto":   "⚡ АВТО активен — отправь .py файл:",
            "waiting_detect": "🔍 Определение метода — отправь .py файл:",
            "waiting":        "🔓 v1 деобфускатор — отправь .py файл:",
            "waiting_v2":     "🔓 Ренди 2.0 — отправь .py файл:",
            "waiting_v3src":  "🔧 v3 Строки — отправь .py файл:",
            "waiting_v3bin":  "📦 EXE/Binary — отправь .exe / .pyc / .pyz:",
        }
        try:
            bot.edit_message_text(prompts[state], call.message.chat.id, call.message.message_id)
        except: pass
    bot.answer_callback_query(call.id)


# ═══════════════════════════════════════
#    Кнопки главного меню (ReplyKeyboard)
# ═══════════════════════════════════════
@bot.message_handler(func=lambda m: m.text in [
    "🔓 Деобфускатор (АВТО)", "🔬 Определить метод", "📦 EXE / Binary",
    "🔓 Только v1", "🔓 Только v2", "🔧 v3 Строки"
])
@access_required
def handle_menu_button(msg):
    uid = msg.from_user.id
    state_map = {
        "🔓 Деобфускатор (АВТО)": "waiting_auto",
        "🔬 Определить метод":    "waiting_detect",
        "📦 EXE / Binary":        "waiting_v3bin",
        "🔓 Только v1":           "waiting",
        "🔓 Только v2":           "waiting_v2",
        "🔧 v3 Строки":           "waiting_v3src",
    }
    state = state_map.get(msg.text)
    if state:
        _deobf_state[uid] = state
        prompts = {
            "waiting_auto":  "⚡ АВТО активен — отправь .py файл:",
            "waiting_detect":"🔍 Определение метода — отправь .py файл:",
            "waiting_v3bin": "📦 EXE/Binary — отправь .exe / .pyc / .pyz:",
            "waiting":       "🔓 v1 — отправь .py файл:",
            "waiting_v2":    "🔓 Ренди 2.0 — отправь .py файл:",
            "waiting_v3src": "🔧 v3 Строки — отправь .py файл:",
        }
        bot.send_message(msg.chat.id, prompts[state], reply_markup=kb_deobf())


# ═══════════════════════════════════════
#       ADMIN КОМАНДЫ
# ═══════════════════════════════════════
@bot.message_handler(commands=["admin"])
def cmd_admin(msg):
    if not is_admin(msg.from_user.id):
        return
    total = len(allowed_users)
    banned = len(banned_users)
    bot.send_message(msg.chat.id,
        f"👑 Панель администратора\n\n"
        f"Пользователей: {total}\n"
        f"Заблокировано: {banned}\n\n"
        f"Команды:\n"
        f"/add ID — выдать доступ\n"
        f"/remove ID — забрать доступ\n"
        f"/ban ID — заблокировать\n"
        f"/unban ID — разблокировать\n"
        f"/users — список пользователей")

@bot.message_handler(commands=["add"])
def cmd_add(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 2:
        bot.send_message(msg.chat.id, "Использование: /add ID [имя]"); return
    try:
        target_id = int(parts[1])
        name = " ".join(parts[2:]) if len(parts) > 2 else f"user_{target_id}"
        allowed_users[str(target_id)] = {
            "username": "", "first_name": name,
            "added": ts(), "uses": 0
        }
        save_users()
        bot.send_message(msg.chat.id, f"✅ Доступ выдан: {target_id} ({name})")
        try:
            bot.send_message(target_id,
                "✅ Тебе выдан доступ к боту!\n"
                "Используй /start")
        except: pass
    except ValueError:
        bot.send_message(msg.chat.id, "❌ Неверный ID")

@bot.message_handler(commands=["remove"])
def cmd_remove(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 2:
        bot.send_message(msg.chat.id, "Использование: /remove ID"); return
    try:
        target_id = str(int(parts[1]))
        if target_id in allowed_users:
            del allowed_users[target_id]
            save_users()
            bot.send_message(msg.chat.id, f"✅ Доступ забран: {target_id}")
        else:
            bot.send_message(msg.chat.id, f"❌ Пользователь {target_id} не найден")
    except ValueError:
        bot.send_message(msg.chat.id, "❌ Неверный ID")

@bot.message_handler(commands=["ban"])
def cmd_ban(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 2:
        bot.send_message(msg.chat.id, "Использование: /ban ID"); return
    try:
        target_id = str(int(parts[1]))
        banned_users[target_id] = {"banned": ts()}
        save_users()
        bot.send_message(msg.chat.id, f"🚫 Заблокирован: {target_id}")
    except ValueError:
        bot.send_message(msg.chat.id, "❌ Неверный ID")

@bot.message_handler(commands=["unban"])
def cmd_unban(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 2:
        bot.send_message(msg.chat.id, "Использование: /unban ID"); return
    try:
        target_id = str(int(parts[1]))
        if target_id in banned_users:
            del banned_users[target_id]
            save_users()
            bot.send_message(msg.chat.id, f"✅ Разблокирован: {target_id}")
        else:
            bot.send_message(msg.chat.id, f"❌ {target_id} не заблокирован")
    except ValueError:
        bot.send_message(msg.chat.id, "❌ Неверный ID")

@bot.message_handler(commands=["users"])
def cmd_users(msg):
    if not is_admin(msg.from_user.id): return
    if not allowed_users:
        bot.send_message(msg.chat.id, "Список пользователей пуст"); return
    lines = [f"👥 Пользователи ({len(allowed_users)}):\n"]
    for uid, info in list(allowed_users.items())[:50]:
        banned_mark = "🚫" if uid in banned_users else "✅"
        name = info.get('first_name', '') or info.get('username', '') or uid
        uses = info.get('uses', 0)
        lines.append(f"{banned_mark} {uid} — {name} (uses: {uses})\n")
    bot.send_message(msg.chat.id, "".join(lines))


# ═══════════════════════════════════════
#              ЗАПУСК
# ═══════════════════════════════════════
if __name__ == "__main__":
    print("=" * 55)
    print("  🔓 Python Deobfuscator Bot · Astolfo Edition 🌸")
    print(f"  Admins: {ADMIN_IDS}")
    print(f"  Users:  {len(allowed_users)}")
    print(f"  Фото:   {'✓ ' + WELCOME_PHOTO if os.path.exists(WELCOME_PHOTO) else '✗ нет файла'}")
    print("=" * 55)
    bot.infinity_polling(timeout=30, long_polling_timeout=20)
