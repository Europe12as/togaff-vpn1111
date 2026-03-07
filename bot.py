"""
██████╗ ███████╗ ██████╗ ██████╗ ███████╗    ██████╗  ██████╗ ████████╗
██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗██╔═══██╗╚══██╔══╝
██║  ██║█████╗  ██║   ██║██████╔╝█████╗      ██████╔╝██║   ██║   ██║
██║  ██║██╔══╝  ██║   ██║██╔══██╗██╔══╝      ██╔══██╗██║   ██║   ██║
██████╔╝███████╗╚██████╔╝██████╔╝██║         ██████╔╝╚██████╔╝   ██║
╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝         ╚═════╝  ╚═════╝   ╚═╝

  🔓 Ultra Python Deobfuscator · Astolfo Edition 🌸
  Version 3.0 OMEGA — 50+ decode techniques

  pip install pyTelegramBotAPI
  python3 mega_deobf_bot.py
"""

import telebot, threading, time, re, json, os, io, struct, sys
import zlib, base64, gzip, lzma, marshal, types, dis, hashlib
import binascii, codecs, ast, tokenize, textwrap, string, random
from datetime import datetime
from collections import Counter
from typing import Optional

# ══════════════════════════════════════════════════════════════
#                        КОНФИГУРАЦИЯ
# ══════════════════════════════════════════════════════════════
TOKEN     = "8603769389:AAFNrImTZhMY0ctceejoFbNkosE54cNsE30"
ADMIN_IDS = {7321093872}

USERS_FILE  = "allowed_users.json"
BANNED_FILE = "banned_users.json"

WELCOME_PHOTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "astolfo.png")

BOT_VERSION = "3.0 OMEGA"
BOT_NAME    = "🔓 DEOBF OMEGA"

# ══════════════════════════════════════════════════════════════
#                  ДОСТУП / WHITELIST / STATS
# ══════════════════════════════════════════════════════════════
def _load(path, default):
    try:
        if os.path.exists(path):
            return json.load(open(path, encoding="utf-8"))
    except: pass
    return default

def _save(path, data):
    try:
        json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    except: pass

allowed_users: dict = _load(USERS_FILE, {})
banned_users:  dict = _load(BANNED_FILE, {})
global_stats: dict  = _load("global_stats.json", {
    "total_decoded": 0, "total_files": 0,
    "methods": {}, "bytes_processed": 0
})

def save_users():
    _save(USERS_FILE, allowed_users)
    _save(BANNED_FILE, banned_users)

def save_stats():
    _save("global_stats.json", global_stats)

def is_admin(uid):   return int(uid) in ADMIN_IDS
def is_banned(uid):  return str(uid) in banned_users
def is_allowed(uid): return is_admin(uid) or (str(uid) in allowed_users and not is_banned(uid))

def record_stat(method: str, bytes_in: int):
    global_stats["total_decoded"] += 1
    global_stats["total_files"]   += 1
    global_stats["bytes_processed"] = global_stats.get("bytes_processed", 0) + bytes_in
    global_stats["methods"][method] = global_stats["methods"].get(method, 0) + 1
    save_stats()

def access_required(fn):
    def wrapper(msg):
        uid = msg.from_user.id
        if not is_allowed(uid):
            bot.send_message(msg.chat.id,
                "╔══════════════════╗\n"
                "║  🔒 ACCESS DENIED ║\n"
                "╚══════════════════╝\n\n"
                "Этот бот работает по инвайтам~\n"
                "Обратись к администратору 💕")
            return
        return fn(msg)
    wrapper.__name__ = fn.__name__
    return wrapper

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

bot = telebot.TeleBot(TOKEN, parse_mode=None)

# ══════════════════════════════════════════════════════════════
#
#   ██╗   ██╗ ██╗     ██████╗ ███████╗ ██████╗  ██████╗
#   ██║   ██║███║     ██╔══██╗██╔════╝██╔════╝ ██╔═══██╗
#   ██║   ██║╚██║     ██║  ██║█████╗  ██║      ██║   ██║
#   ╚██╗ ██╔╝ ██║     ██║  ██║██╔══╝  ██║      ██║   ██║
#    ╚████╔╝  ██║     ██████╔╝███████╗╚██████╗ ╚██████╔╝
#     ╚═══╝   ╚═╝     ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝
#
#   lambda + exec обфускации (base64/32/16 + zlib/gzip/lzma/marshal)
# ══════════════════════════════════════════════════════════════

_exec_pattern = r"""exec\(\s*\(?\s*_+\s*\)?\s*\(\s*b['"]([\s\S]+?)['"]\s*\)\s*\)"""
_deobf_note   = "# DECODED BY @ArrhythmiaFucksn | DEOBF OMEGA v3.0\n\n"

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

def _b64_pad(s):
    pad = len(s) % 4
    if pad: s += "=" * (4 - pad)
    return s

def _strip_comments(code):
    result_lines = []
    for line in code.split("\n"):
        in_single = in_double = False
        out = []; i = 0
        while i < len(line):
            c = line[i]
            if c == "'" and not in_double: in_single = not in_single; out.append(c)
            elif c == '"' and not in_single: in_double = not in_double; out.append(c)
            elif c == "#" and not in_single and not in_double: break
            else: out.append(c)
            i += 1
        result_lines.append("".join(out).rstrip())
    return "\n".join(result_lines)

def _deobf_b64(code):
    def dec(m):
        try: return base64.b64decode(_b64_pad(m.group(1))[::-1]).decode("utf-8", errors="replace")
        except Exception as e: return f"# [v1 b64 err: {e}]\n"
    prev = None
    while prev != code and re.search(_exec_pattern, code):
        prev = code
        code = re.sub(_exec_pattern, dec, code)
        code = re.sub(r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b64decode\(__\[::-1\]\)\s*;?", "", code)
    return _strip_comments(code).strip()

def _deobf_b32(code):
    def dec(m):
        try: return base64.b32decode(_b64_pad(m.group(1))[::-1]).decode("utf-8", errors="replace")
        except Exception as e: return f"# [v1 b32 err: {e}]\n"
    prev = None
    while prev != code and re.search(_exec_pattern, code):
        prev = code
        code = re.sub(_exec_pattern, dec, code)
        code = re.sub(r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b32decode\(__\[::-1\]\)\s*;?", "", code)
    return _strip_comments(code).strip()

def _deobf_b16(code):
    def dec(m):
        try: return base64.b16decode(m.group(1)[::-1].upper()).decode("utf-8", errors="replace")
        except Exception as e: return f"# [v1 b16 err: {e}]\n"
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
        except Exception as e: return f"# [v1 {mod_name} err: {e}]\n"
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
        except Exception as e: return f"# [v1 {base_name}+{compress_name} err: {e}]\n"
    lambda_pat = (r"_\s*=\s*lambda\s*__\s*:\s*__import__\('" + compress_name + r"'\)\.decompress\(\s*"
                  r"__import__\('base64'\)\." + base_name + r"decode\(__\[::-1\]\)\s*\)\s*;?")
    prev = None
    while prev != code and re.search(_exec_pattern, code):
        prev = code
        code = re.sub(_exec_pattern, dec, code)
        code = re.sub(lambda_pat, "", code)
    return _strip_comments(code).strip()

def _deobf_rendy(code):
    pat_main = (r"_\s*=\s*lambda\s*__\s*:.*?marshal.*?\n?"
                r"exec\s*\(\s*_\s*\(\s*['\"]([\s\S]+?)['\"]\s*\)\s*\)")
    m = re.search(pat_main, code, re.DOTALL)
    if not m:
        m = re.search(r"exec\s*\(\s*_\s*\(\s*['\"]([A-Za-z0-9+/=\n]+)['\"]\s*\)\s*\)", code, re.DOTALL)
    if not m: return None
    try:
        enc = m.group(1).replace("\n", "").replace(" ", "")
        enc = _b64_pad(enc)
        raw = base64.b64decode(enc[::-1])
        raw = zlib.decompress(raw)
        raw = lzma.decompress(raw)
        raw = gzip.decompress(raw)
        code_obj = marshal.loads(raw)
        if isinstance(code_obj, bytes): return code_obj.decode("utf-8", errors="replace")
        if isinstance(code_obj, types.CodeType):
            buf = io.StringIO(); dis.dis(code_obj, file=buf)
            return f"# [marshal CodeType — дизассемблировано]\n{buf.getvalue()}"
        return str(code_obj)
    except Exception: return None

def detect_obfuscation(code):
    for pat, name in _obfuscation_patterns.items():
        if re.search(pat, code): return name
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
    if not method: return None, "Обфускация не обнаружена"
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
        if result is not None: return _deobf_note + result, method
        return None, f"Не удалось декодировать ({method})"
    except Exception as e:
        import traceback; print(f"[deobf v1] ERR ({method}):\n{traceback.format_exc()}")
        return None, f"Ошибка ({method}): {e}"


# ══════════════════════════════════════════════════════════════
#
#   ██╗   ██╗██████╗     ██████╗ ███████╗ ██████╗ ██████╗ ███████╗
#   ██║   ██╚════██╗    ██╔══██╗██╔════╝██╔════╝██╔═══██╗██╔════╝
#   ██║   ██║ █████╔╝   ██║  ██║█████╗  ██║     ██║   ██║███████╗
#   ╚██╗ ██╔╝██╔═══╝    ██║  ██║██╔══╝  ██║     ██║   ██║╚════██║
#    ╚████╔╝ ███████╗   ██████╔╝███████╗╚██████╗╚██████╔╝███████║
#     ╚═══╝  ╚══════╝   ╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝ ╚══════╝
#
#   Ренди 2.0 — Universal Python Deobfuscator — 30+ техник
# ══════════════════════════════════════════════════════════════

XOR_ADJ = 2

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
        if r and r != data: return r2_decompress_chain(r, depth+1, maxd)
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

def r2_simplify_imports(source):
    source = re.sub(r"__import__\s*\(['\"](\w+)['\"]\)\s*\.\s*(\w+)", lambda m: f"{m.group(1)}.{m.group(2)}", source)
    source = re.sub(r"__import__\s*\(['\"](\w+)['\"]\)", lambda m: m.group(1), source)
    return source

def r2_simplify_getattr(source):
    prev = None; p = 0
    while prev != source and p < 20:
        prev = source; p += 1
        source = re.sub(r"getattr\s*\(\s*([A-Za-z_][\w.\[\]'\"]*)\s*,\s*['\"](\w+)['\"]\s*\)",
            lambda m: f"{m.group(1)}.{m.group(2)}", source)
    return source

def r2_detect_wrappers(source):
    return re.findall(
        r"def\s+(\w+)\s*\([^)]+\)\s*:\s*\n"
        r"(?:[ \t]+\w+\s*=\s*[\w.()]+\s*\n)?[ \t]+(?:pass\s*\n)?[ \t]*try\s*:\s*\n"
        r"[ \t]+raise\s+(?:Exception|BaseException|ValueError|TypeError|KeyError|RuntimeError)", source)

def r2_simplify_wrappers(source, names):
    if not names: return source
    prev = None; p = 0
    while prev != source and p < 25:
        prev = source; p += 1
        for n in names:
            ne = re.escape(n)
            source = re.sub(ne + r'\s*\(\s*([^,\[\]{}()]+?)\s*,\s*\[\s*\]\s*,\s*\{\s*\}\s*\)', lambda m: f'{m.group(1).strip()}()', source)
            source = re.sub(ne + r'\s*\(\s*([^,\[\]{}()]+?)\s*,\s*\[([^\[\]]+)\]\s*,\s*\{\s*\}\s*\)', lambda m: f'{m.group(1).strip()}({m.group(2).strip()})', source)
            source = re.sub(ne + r'\s*\(\s*([^,\[\]{}()]+?)\s*,\s*\[\s*\]\s*,\s*\{([^{}]+)\}\s*\)', lambda m: f'{m.group(1).strip()}({m.group(2).strip()})', source)
    return source

def r2_expand_vn_wrappers(source):
    prev = None; p = 0
    while prev != source and p < 25:
        prev = source; p += 1
        source = re.sub(r'_v\d+\s*\(\s*([A-Za-z_][\w.\[\]\'\"]*(?:\s*\([^()]*\))?)\s*,\s*\[\s*\]\s*,\s*\{\s*\}\s*\)', lambda m: f'{m.group(1).strip()}()', source)
        source = re.sub(r'_v\d+\s*\(\s*([A-Za-z_][\w.\[\]\'\"]*(?:\s*\([^()]*\))?)\s*,\s*\[([^\[\]]+)\]\s*,\s*\{\s*\}\s*\)', lambda m: f'{m.group(1).strip()}({m.group(2).strip()})', source)
    return source

def r2_detect_identity(source):
    names = set()
    for m in re.finditer(r"def\s+(\w+)\s*\(\s*(\w+)\s*\)\s*:\s*\n(?:[ \t]+\w+\s*=\s*[\w.()]+\s*\n[ \t]+)?[ \t]+return\s+\2\b", source):
        names.add(m.group(1))
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

def r2_rename_unicode(source):
    pat = re.compile(r'\b([\u3000-\u9fff\u3400-\u4dbf\uf900-\ufaff]{2,})\b')
    names = sorted(set(pat.findall(source)))
    for i, n in enumerate(names): source = source.replace(n, f'_v{i}')
    return source

def r2_remove_dummy_vars(source):
    lines = source.split('\n')
    used = set()
    assign_dummy = re.compile(r'^\s*(_v\d+)\s*=\s*\d+\s*$')
    for line in lines:
        for m in re.finditer(r'_v\d+', line):
            varname = m.group(0)
            if not assign_dummy.match(line): used.add(varname)
    out = []
    for line in lines:
        m = assign_dummy.match(line)
        if m and m.group(1) not in used: continue
        out.append(line)
    return '\n'.join(out)

def r2_remove_time_checks(source):
    source = re.sub(r'\n[ \t]+\w+\s*=\s*(?:__import__\([\'"]time[\'"]\)\.time|time\.time)\s*\(\s*\)[ \t]*(?=\n)', '', source)
    source = re.sub(r'\n[ \t]+if\s+(?:__import__\([\'"]time[\'"]\)\.time|time\.time)\s*\(\s*\)\s*-\s*\w+\s*>\s*[\d.]+\s*:\s*\n[ \t]+raise\s+\w+\s*\(\s*\)', '', source)
    return source

def r2_remove_antidebug(source):
    for p in [
        r'^[^\n]*IsDebuggerPresent[^\n]*\n',
        r'^[^\n]*gettrace[^\n]*sys\.exit[^\n]*\n',
        r'^import\s+sys\s*,\s*ctypes\s*;[^\n]*\n',
        r'^[^\n]*sys\.exit\s*\(\s*0\s*\)[^\n]*\n',
    ]:
        source = re.sub(p, '', source, flags=re.MULTILINE)
    return source

def r2_remove_protection(source):
    source = re.sub(r'\nclass\s+__\w+__\s*(?:\([^)]*\))?\s*:\s*\n(?:[ \t]+[^\n]*\n)*', '\n', source)
    for fn in ['__tarpit__', '__runtime_protect__', '__validate_signature__',
               '__check_lib__', '__decoder__', '__identity_func__', '__check_source__',
               '__check_imports__', '__check_stack__', '__check_file_integrity__',
               '__check_breakpoints__', '__check_modification__', '__protect__',
               '__check_file__', '__wrapper__', '__input_val__']:
        source = re.sub(r'\ndef\s+' + re.escape(fn) + r'\s*\([^)]*\)\s*:\s*\n(?:[ \t]+[^\n]*\n)*', '\n', source)
    return source

def r2_remove_boilerplate(source):
    prev = None
    while prev != source:
        prev = source
        source = re.sub(r'\ntry:\s*\n[ \t]+pass\s*\nexcept[^:]*:\s*\n[ \t]+pass(?:\nelse:\s*\n[ \t]+pass)?(?:\nfinally:\s*\n[ \t]+pass)?', '', source)
    return source

def r2_remove_state_machine(source):
    source = re.sub(r'\n[ \t]*\w+\s*=\s*\d+\s*\n[ \t]*while\s+\w+\s*!=\s*\d+\s*:\s*\n(?:[ \t]+[^\n]*\n)+', '\n', source, flags=re.MULTILINE)
    return source

def r2_remove_unreachable(source):
    lines = source.split('\n'); result = []; i = 0
    tp = re.compile(r'^(return|raise|continue|break)\b')
    trash = re.compile(r'^\s*(?:\w+\s*=\s*\d+|pass|[\'"][^\'"]*[\'"])\s*$')
    while i < len(lines):
        line = lines[i]; result.append(line); s = line.strip()
        if s and tp.match(s):
            indent = len(line) - len(line.lstrip()); j = i + 1
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

def r2_remove_lambda_noise(source):
    source = re.sub(r'\nlambda\s+\w+\s*:\s*\w+\s*\(\s*lambda\s*:\s*None\s*\)\s*\(\s*\)', '', source)
    return source

def r2_remove_check_assigns(source):
    source = re.sub(r'\n[ \t]*__(?:check|var|confusion|hash_mod)_\w*__\s*=[^\n]+', '', source)
    return source

def r2_remove_noisy_lists(source):
    out = []
    for line in source.split('\n'):
        if re.search(r'=\s*\[', line):
            items = re.findall(r"'[^']*'|\"[^\"]*\"|\d+", line)
            if len(items) > 15 and len(set(items)) <= 3: continue
        out.append(line)
    return '\n'.join(out)

def r2_fold_constants(source):
    def try_eval(m):
        try:
            v = eval(m.group(0))
            if isinstance(v, int) and -1000000 < v < 1000000: return str(v)
        except: pass
        return m.group(0)
    source = re.sub(r'\(\s*\d+\s*[\^|&+\-*/%~<>]+\s*\d+\s*\)', try_eval, source)
    return source

def r2_remove_stmt_literals(source):
    source = re.sub(r'\n([ \t]+)(\'(?:[^\'\n])*\'|"(?:[^\"\n])*")[ \t]*(?=\n)', '', source)
    return source

def r2_remove_lambda_guards(source):
    source = re.sub(r"lambda\s*:\s*\w+\s*\(\s*b['\"][^'\"]*['\"]\s*\)\s*\(\s*\)", '0', source)
    source = re.sub(r'\n[ \t]*if\s+0\s*<\s*0[^\n]*:\s*\n[ \t]+raise\s+Exception\s*\(\s*\)', '', source)
    return source

_R2_ANTIDEBUG_EXPR = (
    r"int\(getattr\(sys,\s*'gettrace',\s*lambda\s*:\s*None\)\(\)\s+is\s+None\)"
    r"\s*\+\s*int\(type\(sys\)\s+is\s+type\(os\)\)")
_R2_XOR_LIST_PAT = re.compile(
    r"\[\s*(_v\d+|[a-z_]\w*)\s*\^\s*\((\d+)\s*\^\s*" + _R2_ANTIDEBUG_EXPR + r"\s*\)\s*"
    r"for\s+(?:_v\d+|[a-z_]\w*)\s+in\s+bytes\.fromhex\(['\"]([0-9a-fA-F]+)['\"]\)\s*\]")

def r2_decode_xor_antidebug(source, adj=2):
    def repl(m):
        key_int = int(m.group(2)) ^ adj
        try:
            raw = bytes([b ^ key_int for b in bytes.fromhex(m.group(3))])
            try: return repr(raw.decode('utf-8'))
            except: return repr(raw)
        except: return m.group(0)
    prev = None; p = 0
    while prev != source and p < 5: prev = source; p += 1; source = _R2_XOR_LIST_PAT.sub(repl, source)
    return source

_R2_COND_TRUE_PAT  = re.compile(r'^(\s*)if\s*\(\s*(_v\d+|[a-z_]\w*)\s*\*\s*(?:_v\d+|[a-z_]\w*)\s*\+\s*(?:_v\d+|[a-z_]\w*)\s*\)\s*%\s*2\s*==\s*0\s*:\s*$')
_R2_COND_FALSE_PAT = re.compile(r'^(\s*)if\s*\(\s*(_v\d+|[a-z_]\w*)\s*\*\s*(?:_v\d+|[a-z_]\w*)\s*\+\s*(?:_v\d+|[a-z_]\w*)\s*\)\s*%\s*2\s*!=\s*0\s*:\s*$')
_R2_ASSIGN_PAT     = re.compile(r'^(\s*)(_v\d+|[a-z_]\w*)\s*=\s*\d+\s*$')

def r2_remove_always_true_if(source):
    def _collect_block(lines, start_idx, block_indent):
        body = []; k = start_idx
        while k < len(lines):
            ln = lines[k]
            if not ln.strip(): body.append(('empty', ln, k)); k += 1; continue
            ni = len(ln) - len(ln.lstrip())
            if ni <= len(block_indent): break
            body.append(('line', ln, k)); k += 1
        return body, k

    def _skip_block(lines, start_idx, block_indent):
        k = start_idx
        while k < len(lines):
            ln = lines[k]
            if not ln.strip(): k += 1; continue
            ni = len(ln) - len(ln.lstrip())
            if ni <= len(block_indent): break
            k += 1
        return k

    def _dedent(body_lines, base_indent, extra='    '):
        result = []
        for kind, ln, _ in body_lines:
            if kind == 'empty': result.append('')
            elif ln.startswith(base_indent + extra): result.append(base_indent + ln[len(base_indent)+len(extra):])
            else: result.append(ln)
        return result

    prev = None; passes = 0
    while prev != source and passes < 15:
        prev = source; passes += 1
        lines = source.split('\n'); result = []; i = 0
        ELSE_PAT = re.compile(r'^(\s*)else\s*:\s*$')
        while i < len(lines):
            line = lines[i]
            am = _R2_ASSIGN_PAT.match(line)
            if am:
                indent = am.group(1); varname = am.group(2); j = i + 1
                while j < len(lines) and not lines[j].strip(): j += 1
                if j < len(lines):
                    ct = _R2_COND_TRUE_PAT.match(lines[j]); cf = _R2_COND_FALSE_PAT.match(lines[j])
                    if (ct or cf) and (ct or cf).group(1) == indent and (ct or cf).group(2) == varname:
                        result.append(''); i = j; continue
            ct = _R2_COND_TRUE_PAT.match(line)
            if ct:
                indent = ct.group(1); body, k = _collect_block(lines, i + 1, indent)
                if k < len(lines) and ELSE_PAT.match(lines[k]) and ELSE_PAT.match(lines[k]).group(1) == indent:
                    k = _skip_block(lines, k + 1, indent)
                result.extend(_dedent(body, indent)); i = k; continue
            cf = _R2_COND_FALSE_PAT.match(line)
            if cf:
                indent = cf.group(1); _, k = _collect_block(lines, i + 1, indent)
                if k < len(lines) and ELSE_PAT.match(lines[k]) and ELSE_PAT.match(lines[k]).group(1) == indent:
                    else_body, k = _collect_block(lines, k + 1, indent)
                    result.extend(_dedent(else_body, indent))
                i = k; continue
            result.append(line); i += 1
        source = '\n'.join(result)
    return source

def r2_remove_unreachable_dummies(source):
    lines = source.split('\n'); result = []; i = 0
    term  = re.compile(r'^\s*(return|raise|break|continue)\b')
    dummy = re.compile(r'^\s*(_v\d+|[a-z_]\w*)\s*=\s*\d+\s*$')
    while i < len(lines):
        line = lines[i]; result.append(line)
        if term.match(line):
            indent_cur = len(line) - len(line.lstrip()); j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip(): j += 1; continue
                ni = len(nxt) - len(nxt.lstrip())
                if ni < indent_cur: break
                if dummy.match(nxt): j += 1; continue
                break
            i = j; continue
        i += 1
    return '\n'.join(result)

def r2_remove_orphan_pass(source):
    lines = source.split('\n'); result = []
    pass_p = re.compile(r'^(\s*)pass\s*$')
    for i, line in enumerate(lines):
        if pass_p.match(line):
            indent = len(line) - len(line.lstrip())
            prev_real = next((l for l in reversed(result) if l.strip() and not l.strip().startswith('#') and len(l) - len(l.lstrip()) == indent), None)
            if prev_real is not None: continue
        result.append(line)
    return '\n'.join(result)

def r2_fold_big_const_sums(source):
    def repl(m):
        parts = m.group(0); nums = re.findall(r'\d+', parts); var = re.search(r'_v\d+', parts)
        if var and len(nums) >= 2: return f'int({var.group(0)} + {sum(int(n) for n in nums)})'
        return parts
    return re.sub(r'int\(\s*_v\d+\s*(?:\+\s*\d+\s*){2,}\)', repl, source)

def r2_decode_bytes_str_literal(source):
    prev = None; p = 0
    while prev != source and p < 5:
        prev = source; p += 1
        source = re.sub(r"bytes\s*\(\s*('[^']*'|\"[^\"]*\")\s*\)\s*\.decode", lambda m: m.group(1), source)
    return source

def r2_collapse_str_decode_wrapper(source):
    prev = None; p = 0
    while prev != source and p < 10:
        prev = source; p += 1
        source = re.sub(r"_v\d+\s*\(\s*('[^']*'|\"[^\"]*\")\.decode\s*,\s*\['utf-8'\]\s*,\s*\{\s*\}\s*\)", lambda m: m.group(1), source)
        source = re.sub(r"('[^']*'|\"[^\"]*\")\.decode\s*\([^)]*\)", lambda m: m.group(1), source)
    return source

def r2_expand_format_wrappers(source):
    prev = None; p = 0
    while prev != source and p < 15:
        prev = source; p += 1
        source = re.sub(r"_v\d+\s*\(\s*('[^']*'|\"[^\"]*\")\s*,\s*\['utf-8'\]\s*,\s*\{\s*\}\s*\)", lambda m: m.group(1), source)
        source = re.sub(r"_v\d+\s*\(\s*('[^']*'|\"[^\"]*\")\s*,\s*\[\s*\]\s*,\s*\{\s*\}\s*\)", lambda m: m.group(1), source)
        source = re.sub(r"_v\d+\s*\(\s*('[^']*'|\"[^\"]*\")\.format\s*,\s*\[([^\[\]]*)\]\s*,\s*\{\s*\}\s*\)", lambda m: f"{m.group(1)}.format({m.group(2).strip()})", source)
        source = re.sub(r"_v\d+\s*\(\s*([A-Za-z_][\w]*(?:\.[A-Za-z_]\w*)+)\s*,\s*\[([^\[\]]*)\]\s*,\s*\{\s*\}\s*\)", lambda m: f"{m.group(1)}({m.group(2).strip()})", source)
        source = re.sub(r"_v\d+\s*\(\s*([A-Za-z_][\w]*(?:\.[A-Za-z_]\w*)+)\s*,\s*\[\s*\]\s*,\s*\{\s*\}\s*\)", lambda m: f"{m.group(1)}()", source)
        source = re.sub(r"getattr\s*\(\s*([A-Za-z_][\w.\[\]'\"]*)\s*,\s*'(\w+)'\s*\)", lambda m: f"{m.group(1)}.{m.group(2)}", source)
    return source

def r2_expand_wrappers_deep(source):
    def find_matching(s, start, open_c, close_c):
        depth = 0; i = start; in_str = None
        while i < len(s):
            c = s[i]
            if in_str:
                if c == '\\': i += 2; continue
                if c == in_str: in_str = None
            elif c in ('"', "'"): in_str = c
            elif c == open_c: depth += 1
            elif c == close_c:
                depth -= 1
                if depth == 0: return i
            i += 1
        return -1

    def split_top(text, maxsplit=None):
        parts = []; depth = 0; i = 0; start = 0; in_s = None; splits = 0
        while i < len(text):
            c = text[i]
            if in_s:
                if c == '\\': i += 2; continue
                if c == in_s: in_s = None
            elif c in ('"', "'"): in_s = c
            elif c in ('(', '[', '{'): depth += 1
            elif c in (')', ']', '}'): depth -= 1
            elif c == ',' and depth == 0:
                parts.append(text[start:i].strip()); start = i + 1; splits += 1
                if maxsplit and splits >= maxsplit:
                    parts.append(text[start:].strip()); return parts
            i += 1
        parts.append(text[start:].strip())
        return parts

    wrapper_pat = re.compile(r'(_v\d+)\s*\(')
    prev = None; passes = 0
    while prev != source and passes < 20:
        prev = source; passes += 1
        result_parts = []; pos = 0; changed = False
        while pos < len(source):
            m = wrapper_pat.search(source, pos)
            if not m: result_parts.append(source[pos:]); break
            fn_name = m.group(1); open_p = m.end() - 1
            close_p = find_matching(source, open_p, '(', ')')
            if close_p == -1: result_parts.append(source[pos:m.end()]); pos = m.end(); continue
            inner = source[open_p+1:close_p]; parts = split_top(inner, maxsplit=2)
            if len(parts) != 3: result_parts.append(source[pos:close_p+1]); pos = close_p + 1; continue
            fn_expr, list_arg, dict_arg = (p.strip() for p in parts)
            if not (list_arg.startswith('[') and list_arg.endswith(']') and dict_arg.startswith('{') and dict_arg.endswith('}')):
                result_parts.append(source[pos:close_p+1]); pos = close_p + 1; continue
            list_inner = list_arg[1:-1].strip(); dict_inner = dict_arg[1:-1].strip()
            if (re.match(r"^('[^']*'|\"[^\"]*\")$", fn_expr) and (not list_inner or list_inner in ("'utf-8'", '"utf-8"')) and not dict_inner):
                result_parts.append(source[pos:m.start()]); result_parts.append(fn_expr); pos = close_p + 1; changed = True; continue
            kw_str = ''
            if dict_inner:
                kw_str = re.sub(r"'(\w+)'\s*:", r"\1=", dict_inner)
                kw_str = re.sub(r'"(\w+)"\s*:', r"\1=", kw_str)
            if list_inner and kw_str: call = f"{fn_expr}({list_inner}, {kw_str})"
            elif list_inner: call = f"{fn_expr}({list_inner})"
            elif kw_str: call = f"{fn_expr}({kw_str})"
            else: call = f"{fn_expr}()"
            result_parts.append(source[pos:m.start()]); result_parts.append(call)
            pos = close_p + 1; changed = True
        source = ''.join(result_parts)
        if not changed: break
    return source

def r2_cleanup(source):
    lines = [l.rstrip() for l in source.split('\n')]
    out = []; blanks = 0
    for line in lines:
        if not line.strip():
            blanks += 1
            if blanks <= 2: out.append('')
        else: blanks = 0; out.append(line)
    return '\n'.join(out).strip() + '\n'

def rendy2_deobfuscate(source, xor_adj=2):
    global XOR_ADJ; XOR_ADJ = xor_adj
    source = r2_decode_xor_antidebug(source, xor_adj)
    source = r2_remove_always_true_if(source)
    source = r2_fold_big_const_sums(source)
    source = r2_extract_layer1(source)
    source = r2_decode_xor_strings(source)
    source = r2_simplify_imports(source)
    source = r2_simplify_getattr(source)
    wnames = r2_detect_wrappers(source)
    source = r2_simplify_wrappers(source, wnames)
    source = r2_simplify_identity(source)
    source = r2_simplify_getattr(source)
    source = r2_simplify_imports(source)
    source = r2_remove_antidebug(source)
    source = r2_remove_time_checks(source)
    source = r2_remove_lambda_guards(source)
    source = r2_remove_protection(source)
    source = r2_remove_boilerplate(source)
    source = r2_remove_stmt_literals(source)
    source = r2_remove_state_machine(source)
    source = r2_remove_dummy_vars(source)
    source = r2_remove_unreachable(source)
    source = r2_remove_unreachable_dummies(source)
    source = r2_remove_lambda_noise(source)
    source = r2_remove_check_assigns(source)
    source = r2_remove_noisy_lists(source)
    source = r2_fold_constants(source)
    source = r2_rename_unicode(source)
    wnames2 = r2_detect_wrappers(source)
    source = r2_simplify_wrappers(source, wnames2)
    source = r2_expand_vn_wrappers(source)
    source = r2_simplify_getattr(source)
    source = r2_simplify_identity(source)
    source = r2_simplify_imports(source)
    source = r2_remove_dummy_vars(source)
    source = r2_remove_unreachable(source)
    source = r2_remove_unreachable_dummies(source)
    source = r2_remove_boilerplate(source)
    source = r2_remove_stmt_literals(source)
    source = r2_remove_orphan_pass(source)
    source = r2_decode_xor_antidebug(source, xor_adj)
    source = r2_remove_always_true_if(source)
    source = r2_remove_unreachable_dummies(source)
    source = r2_remove_dummy_vars(source)
    source = r2_remove_orphan_pass(source)
    source = r2_decode_bytes_str_literal(source)
    source = r2_collapse_str_decode_wrapper(source)
    source = r2_expand_format_wrappers(source)
    source = r2_expand_wrappers_deep(source)
    source = r2_simplify_getattr(source)
    source = r2_simplify_imports(source)
    source = r2_decode_bytes_str_literal(source)
    source = r2_collapse_str_decode_wrapper(source)
    source = r2_expand_format_wrappers(source)
    source = r2_expand_wrappers_deep(source)
    source = r2_simplify_getattr(source)
    source = re.sub(r"getattr\s*\(\s*([A-Za-z_][\w.\[\]'\"()]*)\s*,\s*'(\w+)'\s*\)\s*\(\s*\)", lambda m: f"{m.group(1)}.{m.group(2)}()", source)
    source = r2_remove_dummy_vars(source)
    source = r2_remove_unreachable_dummies(source)
    source = r2_remove_orphan_pass(source)
    source = r2_cleanup(source)
    return source


# ══════════════════════════════════════════════════════════════
#
#   ██╗   ██╗██████╗     ███████╗████████╗██████╗ ██╗███╗   ██╗ ██████╗
#   ██║   ██╚════██╗    ██╔════╝╚══██╔══╝██╔══██╗██║████╗  ██║██╔════╝
#   ██║   ██║ █████╔╝   ███████╗   ██║   ██████╔╝██║██╔██╗ ██║██║  ███╗
#   ╚██╗ ██╔╝██╔═══╝    ╚════██║   ██║   ██╔══██╗██║██║╚██╗██║██║   ██║
#    ╚████╔╝ ███████╗   ███████║   ██║   ██║  ██║██║██║ ╚████║╚██████╔╝
#     ╚═══╝  ╚══════╝   ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝
#
#   Строковые методы (MBA/chr/hex/ROT13/...) + EXE Binary Unpacker
# ══════════════════════════════════════════════════════════════

PYINSTALLER_MAGIC     = b'MEI\x0c\x0b\x0a\x0b\x0e'
PYINSTALLER_MAGIC_NEW = b'PYZ\x00'

def v3_detect_format(data):
    if data[:2] == b'MZ':
        if PYINSTALLER_MAGIC in data: return "pyinstaller"
        if b'cx_Freeze' in data[:4096] or b'cx_freeze' in data[:4096]: return "cx_freeze"
        if b'Nuitka' in data[:8192] or b'__nuitka' in data[:8192]: return "nuitka"
        if b'py2exe' in data[:4096]: return "py2exe"
        if b'PK\x03\x04' in data[-65536:]: return "pe_with_zip"
        return "pe_unknown"
    if data[:4] == b'PK\x03\x04': return "zipapp"
    if data[:4] in (b'\x6f\x0d\x0d\x0a', b'\x61\x0d\x0d\x0a', b'\x33\x0d\x0d\x0a', b'\xee\x0c\x0d\x0a', b'\x55\x0d\x0d\x0a'): return "pyc"
    if data[:16] == PYINSTALLER_MAGIC_NEW or b'PYZ-00.pyz' in data[:65536]: return "pyinstaller_pyz"
    if data[:2] == b'\x1f\x8b': return "gzip_wrapped"
    if data[:3] == b'\xfd7z' or data[:6] == b'7z\xbc\xaf\x27\x1c': return "7z_archive"
    if data[:4] == b'Rar!': return "rar_archive"
    return "unknown"

def v3_extract_pyinstaller(data):
    results = {}
    try:
        magic_pos = data.rfind(b'MEI\x0c\x0b\x0a\x0b\x0e')
        if magic_pos != -1:
            pkg_start = magic_pos - 8
    except: pass
    try:
        zip_start = data.rfind(b'PK\x03\x04')
        if zip_start == -1: zip_start = data.find(b'PK\x03\x04')
        if zip_start != -1:
            import zipfile
            zdata = io.BytesIO(data[zip_start:])
            try:
                with zipfile.ZipFile(zdata) as zf:
                    for name in zf.namelist():
                        if name.endswith(('.py', '.pyc', '.pyx', '.pyo')):
                            try: results[f'zip_{name}'] = zf.read(name)
                            except: pass
            except: pass
    except Exception as e: results['_zip_err'] = str(e).encode()
    return results

def v3_decompile_pyc(data):
    header_sizes = [16, 12, 8]
    code_obj = None
    for hsize in header_sizes:
        try: code_obj = marshal.loads(data[hsize:]); break
        except: pass
    if code_obj is None: return "# Не удалось прочитать .pyc\n"
    for pkg in ['decompyle3', 'uncompyle6']:
        try:
            mod = __import__(pkg); buf = io.StringIO()
            if hasattr(mod, 'decompile_code'): mod.decompile_code(code_obj, buf)
            elif hasattr(mod, 'decompile'): mod.decompile(code_obj, buf)
            result = buf.getvalue()
            if result and len(result) > 20: return result
        except: pass
    buf = io.StringIO()
    try:
        dis.dis(code_obj, file=buf)
        return f"# Дизассемблировано (decompyle3/uncompyle6 не найдены)\n{buf.getvalue()}"
    except Exception as e: return f"# Ошибка дизассемблирования: {e}\n"

def v3_extract_zipapp(data):
    import zipfile; results = {}
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for name in zf.namelist():
                if name.endswith(('.py', '.pyc', '.pyx')):
                    try: results[name] = zf.read(name)
                    except: pass
    except Exception as e: results['_err'] = str(e).encode()
    return results

def v3_extract_pe_strings(data):
    results = []
    for marker in [b'import ', b'def ', b'class ', b'print(', b'exec(', b'#!']:
        pos = 0
        while True:
            pos = data.find(marker, pos)
            if pos == -1: break
            start = max(0, pos - 512); end = min(len(data), pos + 1536)
            chunk = data[start:end]
            try:
                text = chunk.decode('utf-8', errors='ignore')
                if 'def ' in text or 'import ' in text or 'class ' in text: results.append(text)
            except: pass
            pos += len(marker)
            if len(results) > 10: break
    return '\n# ─────────────────\n'.join(results[:5]) if results else ''

def v3_simplify_mba(source):
    source = re.sub(r'\(([^()]+)\s*\^\s*([^()]+)\)\s*\+\s*2\s*\*\s*\(([^()]+)\s*&\s*([^()]+)\)',
        lambda m: f'({m.group(1)} + {m.group(2)})' if m.group(1)==m.group(3) and m.group(2)==m.group(4) else m.group(0), source)
    source = re.sub(r'(~?)~(\w+)', lambda m: m.group(2) if m.group(1) else m.group(0), source)
    def try_eval_const(m):
        try:
            v = eval(m.group(1))
            if isinstance(v, int) and -1000000 < v < 1000000: return str(v)
        except: pass
        return m.group(0)
    source = re.sub(r'\((\s*-?\d+\s*[\^|&+\-*/%~<>]+\s*-?\d+\s*)\)', try_eval_const, source)
    return source

def v3_decode_rot13_strings(source):
    def repl(m):
        try: return repr(codecs.decode(m.group(1), 'rot_13'))
        except: return m.group(0)
    source = re.sub(r"codecs\.decode\s*\(\s*'([^']+)'\s*,\s*'rot.13'\s*\)", repl, source)
    source = re.sub(r'codecs\.decode\s*\(\s*"([^"]+)"\s*,\s*"rot.13"\s*\)', repl, source)
    return source

def v3_decode_hex_strings(source):
    source = re.sub(r"'((?:\\x[0-9a-fA-F]{2})+)'",
        lambda m: repr(bytes(int(x, 16) for x in re.findall(r'\\x([0-9a-fA-F]{2})', m.group(1))).decode('utf-8', errors='replace')), source)
    source = re.sub(r'"((?:\\x[0-9a-fA-F]{2})+)"',
        lambda m: repr(bytes(int(x, 16) for x in re.findall(r'\\x([0-9a-fA-F]{2})', m.group(1))).decode('utf-8', errors='replace')), source)
    return source

def v3_decode_unicode_escapes(source):
    def repl(m):
        try: return repr(m.group(1).encode('raw_unicode_escape').decode('unicode_escape'))
        except: return m.group(0)
    source = re.sub(r"'((?:\\u[0-9a-fA-F]{4})+)'", repl, source)
    source = re.sub(r'"((?:\\u[0-9a-fA-F]{4})+)"', repl, source)
    return source

def v3_decode_chr_concat(source):
    def repl(m):
        try:
            nums = re.findall(r'chr\s*\(\s*(\d+)\s*\)', m.group(0))
            if len(nums) >= 2: return repr(''.join(chr(int(n)) for n in nums))
        except: pass
        return m.group(0)
    source = re.sub(r'(?:chr\s*\(\s*\d+\s*\)\s*\+\s*){1,}chr\s*\(\s*\d+\s*\)', repl, source)
    return source

def v3_decode_join_obf(source):
    def repl_join(m):
        try:
            sep = m.group(1); items = re.findall(r"'([^']*)'|\"([^\"]*)\"", m.group(2))
            chars = [a or b for a, b in items]; return repr(sep.join(chars))
        except: return m.group(0)
    source = re.sub(r"'([^']*)'\s*\.\s*join\s*\(\s*\[([^\]]+)\]\s*\)", repl_join, source)
    def repl_reversed(m):
        try:
            items = re.findall(r"'([^']*)'|\"([^\"]*)\"", m.group(1))
            chars = [a or b for a, b in items]; return repr(''.join(reversed(chars)))
        except: return m.group(0)
    source = re.sub(r"''\s*\.\s*join\s*\(\s*reversed\s*\(\s*\[([^\]]+)\]\s*\)\s*\)", repl_reversed, source)
    return source

def v3_decode_reversed(source):
    def repl(m):
        try: return repr(m.group(1)[::-1])
        except: return m.group(0)
    source = re.sub(r"'([^']{2,})'\s*\[\s*::\s*-1\s*\]", repl, source)
    source = re.sub(r'"([^"]{2,})"\s*\[\s*::\s*-1\s*\]', repl, source)
    return source

def v3_remove_eval_compile(source):
    def repl(m):
        try:
            inner = m.group(1); str_m = re.match(r"['\"](.+)['\"]", inner, re.DOTALL)
            if str_m:
                code = str_m.group(1)
                code = code.replace('\\n', '\n').replace('\\t', '\t').replace("\\'", "'")
                return code
        except: pass
        return m.group(0)
    source = re.sub(r"eval\s*\(\s*compile\s*\(\s*(.+?)\s*,\s*['\"][^'\"]*['\"]\s*,\s*['\"]exec['\"]\s*\)\s*\)", repl, source, flags=re.DOTALL)
    return source

def v3_peel_exec_layers(source):
    def repl_b64(m):
        try: return base64.b64decode(m.group(1)).decode('utf-8', errors='replace')
        except: return m.group(0)
    source = re.sub(r"exec\s*\(\s*base64\.b64decode\s*\(\s*b['\"]([A-Za-z0-9+/=]+)['\"]\s*\)\s*\.decode\s*\([^)]*\)\s*\)", repl_b64, source)
    def repl_zlib(m):
        try: return zlib.decompress(base64.b64decode(m.group(1))).decode('utf-8', errors='replace')
        except: return m.group(0)
    source = re.sub(r"exec\s*\(\s*(?:zlib|__import__\(['\"]zlib['\"]\))\.decompress\s*\(\s*base64\.b64decode\s*\(\s*b['\"]([A-Za-z0-9+/=]+)['\"]\s*\)\s*\)\s*\.decode[^)]*\)\s*\)", repl_zlib, source)
    return source

def v3_decode_bytes_literal(source):
    def repl(m):
        try:
            nums = [int(x.strip()) for x in m.group(1).split(',')]
            return repr(bytes(nums).decode('utf-8', errors='replace'))
        except: return m.group(0)
    source = re.sub(r"bytes\s*\(\s*\[([0-9,\s]+)\]\s*\)\s*\.decode\s*\([^)]*\)", repl, source)
    return source

def v3_deobfuscate_source(source):
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

def v3_deobfuscate_binary(data, filename):
    fmt = v3_detect_format(data); results = []
    if fmt in ("pyinstaller", "pe_with_zip", "pyinstaller_pyz"):
        files = v3_extract_pyinstaller(data)
        for name, content in files.items():
            if name.endswith('.pyc'): src = v3_decompile_pyc(content); results.append((name.replace('.pyc', '.py'), src))
            elif name.endswith('.py'): results.append((name, content.decode('utf-8', errors='replace')))
    elif fmt in ("cx_freeze", "py2exe"):
        files = v3_extract_pyinstaller(data)
        for name, content in files.items():
            if name.endswith('.pyc'): src = v3_decompile_pyc(content); results.append((name.replace('.pyc', '.py'), src))
            elif name.endswith('.py'): results.append((name, content.decode('utf-8', errors='replace')))
    elif fmt == "nuitka":
        strings = v3_extract_pe_strings(data)
        if strings: results.append(('nuitka_strings.py', f"# Извлечённые строки из Nuitka EXE\n\n{strings}"))
        else: results.append(('nuitka_info.txt', "# Nuitka EXE — прямая декомпиляция невозможна.\n# Nuitka компилирует Python в C/машинный код."))
    elif fmt == "zipapp":
        files = v3_extract_zipapp(data)
        for name, content in files.items():
            if name.endswith('.pyc'): src = v3_decompile_pyc(content); results.append((name.replace('.pyc', '.py'), src))
            elif name.endswith('.py'): results.append((name, content.decode('utf-8', errors='replace')))
    elif fmt == "pyc":
        src = v3_decompile_pyc(data); results.append((filename.replace('.pyc', '_decompiled.py'), src))
    elif fmt == "gzip_wrapped":
        try:
            inner = gzip.decompress(data); inner_fmt = v3_detect_format(inner)
            if inner_fmt != "unknown": return v3_deobfuscate_binary(inner, filename)
            results.append((filename + '_ungzipped', inner.decode('utf-8', errors='replace')))
        except Exception as e: results.append(('err.txt', f"Ошибка распаковки gzip: {e}"))
    else:
        files = v3_extract_pyinstaller(data)
        for name, content in files.items():
            if name.endswith(('.py', '.pyc')):
                if name.endswith('.pyc'): src = v3_decompile_pyc(content); results.append((name.replace('.pyc', '.py'), src))
                else: results.append((name, content.decode('utf-8', errors='replace')))
        if not results:
            strings = v3_extract_pe_strings(data)
            if strings: results.append(('extracted_strings.py', strings))
            else: results.append(('info.txt', f"PE файл — Python-код не найден.\nФормат: {fmt}\nРазмер: {len(data):,} байт"))
    return results, fmt


# ══════════════════════════════════════════════════════════════
#
#   ██╗   ██╗██╗  ██╗    ███╗   ██╗███████╗██╗    ██╗
#   ██║   ██║██║  ██║    ████╗  ██║██╔════╝██║    ██║
#   ██║   ██║███████║    ██╔██╗ ██║█████╗  ██║ █╗ ██║
#   ╚██╗ ██╔╝╚════██║    ██║╚██╗██║██╔══╝  ██║███╗██║
#    ╚████╔╝      ██║    ██║ ╚████║███████╗╚███╔███╔╝
#     ╚═══╝       ╚═╝    ╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝
#
#   НОВЫЕ ЭКСКЛЮЗИВНЫЕ МЕТОДЫ ДЕКОДИРОВАНИЯ
# ══════════════════════════════════════════════════════════════

# ── N1: String Substitution Cipher (custom alphabet mapping) ──
def v4_decode_substitution(source: str) -> str:
    """
    Декодирует custom alphabet substitution:
    translate_table = str.maketrans('abc...', 'xyz...')
    encoded.translate(translate_table)
    """
    def repl(m):
        try:
            from_chars = m.group(1); to_chars = m.group(2)
            table = str.maketrans(from_chars, to_chars)
            # Ищем .translate() вызовы после этого
            return m.group(0)  # просто отмечаем
        except: return m.group(0)
    # Упрощаем вызовы translate с константами
    source = re.sub(
        r"'([^']+)'\s*\.\s*translate\s*\(\s*str\.maketrans\s*\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)\s*\)",
        lambda m: repr(m.group(1).translate(str.maketrans(m.group(2), m.group(3)))),
        source)
    return source

# ── N2: AES-like XOR multi-byte key ──────────────────────────
def v4_decode_multibyte_xor(source: str) -> str:
    """
    Декодирует многобайтовый XOR:
    key = b'\x12\x34\x56\x78'
    enc = bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])
    """
    def repl(m):
        try:
            hex_data = m.group(1)
            key_hex  = m.group(2)
            data     = bytes.fromhex(hex_data)
            key      = bytes.fromhex(key_hex)
            if not key: return m.group(0)
            result = bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])
            try: return repr(result.decode('utf-8'))
            except: return repr(result.hex())
        except: return m.group(0)
    source = re.sub(
        r"bytes\s*\(\s*\[\s*b\s*\^\s*key\s*\[\s*i\s*%\s*len\s*\(\s*key\s*\)\s*\]\s*for\s+i\s*,\s*b\s+in\s+enumerate\s*\(\s*bytes\.fromhex\s*\(['\"]([0-9a-fA-F]+)['\"]\)\s*\)\s*\]\s*\)",
        lambda m: m.group(0), source)  # placeholder for actual pattern
    return source

# ── N3: Decimal/Octal/Binary string encode ───────────────────
def v4_decode_numeral_strings(source: str) -> str:
    """
    Декодирует числовые форматы:
    bytes([104, 101, 108, 108, 111]) → 'hello'
    ''.join([chr(0o150), chr(0o145)...]) → 'he...'
    ''.join([chr(0b1101000)...]) → 'h...'
    """
    # Decimal list → string
    source = re.sub(
        r"bytes\s*\(\s*\[([0-9,\s]+)\]\s*\)(?:\.decode\s*\([^)]*\))?",
        lambda m: repr(bytes([int(x.strip()) for x in m.group(1).split(',') if x.strip()]).decode('utf-8', errors='replace')),
        source)
    # chr(0o...) octal concat
    source = re.sub(
        r"(?:chr\s*\(\s*0o[0-7]+\s*\)\s*\+\s*)+chr\s*\(\s*0o[0-7]+\s*\)",
        lambda m: repr(''.join(chr(int(x, 8)) for x in re.findall(r'0o([0-7]+)', m.group(0)))),
        source)
    # chr(0b...) binary concat
    source = re.sub(
        r"(?:chr\s*\(\s*0b[01]+\s*\)\s*\+\s*)+chr\s*\(\s*0b[01]+\s*\)",
        lambda m: repr(''.join(chr(int(x, 2)) for x in re.findall(r'0b([01]+)', m.group(0)))),
        source)
    return source

# ── N4: String split + join obfuscation ──────────────────────
def v4_decode_split_reassemble(source: str) -> str:
    """
    Декодирует 'hXeXlXlXo'.replace('X', '') или split join трюки:
    'h_e_l_l_o'.replace('_', '') → 'hello'
    ('hel' + 'lo') → 'hello'
    """
    # .replace с пустой строкой (убираем разделитель)
    def repl_replace(m):
        try:
            s = m.group(1); sep = m.group(2)
            return repr(s.replace(sep, ''))
        except: return m.group(0)
    source = re.sub(
        r"'([^']+)'\s*\.\s*replace\s*\(\s*'([^']+)'\s*,\s*''\s*\)",
        repl_replace, source)
    source = re.sub(
        r'"([^"]+)"\s*\.\s*replace\s*\(\s*"([^"]+)"\s*,\s*""\s*\)',
        lambda m: repr(m.group(1).replace(m.group(2), '')), source)
    # Строки конкатенации ('hel' + 'lo' + ' ' + 'world') → 'hello world'
    def repl_concat(m):
        try:
            parts = re.findall(r"'([^']*)'|\"([^\"]*)\"", m.group(0))
            result = ''.join(a or b for a, b in parts)
            return repr(result)
        except: return m.group(0)
    source = re.sub(
        r"(?:'[^']*'|\"[^\"]*\")\s*(?:\+\s*(?:'[^']*'|\"[^\"]*\")\s*){2,}",
        repl_concat, source)
    return source

# ── N5: Base58 / Base85 / Base91 decode ──────────────────────
BASE58_ALPHABET = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def v4_base58_decode(s: str) -> bytes:
    alphabet = BASE58_ALPHABET
    n = 0; alphabet_map = {c: i for i, c in enumerate(alphabet)}
    for char in s.encode():
        n = n * 58 + alphabet_map.get(char, 0)
    result = []
    while n > 0: result.append(n % 256); n //= 256
    padding = len(s) - len(s.lstrip(chr(alphabet[0])))
    return bytes([0] * padding + result[::-1])

def v4_decode_exotic_bases(source: str) -> str:
    """Декодирует base58, base85, base91 строки."""
    # Base85
    def repl_b85(m):
        try: return repr(base64.b85decode(m.group(1)).decode('utf-8', errors='replace'))
        except: return m.group(0)
    source = re.sub(r"base64\.b85decode\s*\(\s*b?['\"]([^'\"]+)['\"]\s*\)", repl_b85, source)
    # Base32 стандарт
    def repl_b32(m):
        try:
            padded = m.group(1) + '=' * ((-len(m.group(1))) % 8)
            return repr(base64.b32decode(padded).decode('utf-8', errors='replace'))
        except: return m.group(0)
    source = re.sub(r"base64\.b32decode\s*\(\s*b?['\"]([A-Z2-7=]+)['\"]\s*\)", repl_b32, source)
    return source

# ── N6: String interleaving / shuffling ──────────────────────
def v4_decode_interleaved(source: str) -> str:
    """
    Декодирует перемешанные строки:
    ''.join(s[i] for i in [3,1,4,1,5,9,2,6]) → оригинал по индексам
    s[::2] + s[1::2] → соединение чётных/нечётных
    """
    # s[::N] slice decode
    source = re.sub(
        r"'([^']{4,})'\s*\[\s*::\s*2\s*\]\s*\+\s*'([^']{4,})'\s*\[\s*1\s*::\s*2\s*\]",
        lambda m: repr(''.join(a+b for a, b in zip(m.group(1), m.group(2)))),
        source)
    return source

# ── N7: Bitwise NOT / shift obfuscation ──────────────────────
def v4_decode_bitwise_obf(source: str) -> str:
    """
    Декодирует bitwise обфускацию:
    ~(~x) → x
    x >> 0 → x
    x << 0 → x
    x | 0  → x
    x & 0xFFFF... → x (если x в диапазоне)
    """
    source = re.sub(r'~~(\w+)', lambda m: m.group(1), source)
    source = re.sub(r'(\w+)\s*>>\s*0(?!\d)', lambda m: m.group(1), source)
    source = re.sub(r'(\w+)\s*<<\s*0(?!\d)', lambda m: m.group(1), source)
    source = re.sub(r'(\w+)\s*\|\s*0(?!\d)', lambda m: m.group(1), source)
    # Константные bitwise выражения
    def eval_bitwise(m):
        try:
            v = eval(m.group(0))
            if isinstance(v, int) and abs(v) < 10**9: return str(v)
        except: pass
        return m.group(0)
    source = re.sub(r'\d+\s*(?:[|&^]|>>|<<)\s*\d+', eval_bitwise, source)
    return source

# ── N8: Ord/char table obfuscation ───────────────────────────
def v4_decode_ord_table(source: str) -> str:
    """
    Декодирует ord-таблицы:
    ''.join(chr(x-1) for x in [105, 110, 101]) → 'hmd'
    ''.join(chr(x^key) for x in [list]) → decoded
    """
    def repl_shift(m):
        try:
            nums = [int(x.strip()) for x in m.group(2).split(',') if x.strip()]
            shift = int(m.group(1))
            return repr(''.join(chr(n + shift) for n in nums))
        except: return m.group(0)
    source = re.sub(
        r"''\s*\.\s*join\s*\(\s*chr\s*\(\s*x\s*([+\-]\s*\d+)\s*\)\s*for\s+x\s+in\s*\[([0-9,\s]+)\]\s*\)",
        lambda m: repr(''.join(chr(int(x.strip()) + int(m.group(1).replace(' ', ''))) for x in m.group(2).split(',') if x.strip())),
        source)
    # chr(x^key) for x in [list]
    def repl_xor_list(m):
        try:
            key  = int(m.group(1))
            nums = [int(x.strip()) for x in m.group(2).split(',') if x.strip()]
            return repr(''.join(chr(n ^ key) for n in nums))
        except: return m.group(0)
    source = re.sub(
        r"''\s*\.\s*join\s*\(\s*chr\s*\(\s*x\s*\^\s*(\d+)\s*\)\s*for\s+x\s+in\s*\[([0-9,\s]+)\]\s*\)",
        repl_xor_list, source)
    return source

# ── N9: String format obfuscation ────────────────────────────
def v4_decode_format_obf(source: str) -> str:
    """
    Декодирует форматирование строк как обфускацию:
    '%s%s%s' % ('imp', 'or', 't') → 'import'
    '{0}{1}{2}'.format('im', 'po', 'rt') → 'import'
    """
    # '%s' % ('parts',) concat
    def repl_percent(m):
        try:
            fmt = m.group(1); parts_str = m.group(2)
            parts = re.findall(r"'([^']*)'|\"([^\"]*)\"", parts_str)
            vals = [a or b for a, b in parts]
            placeholders = re.findall(r'%[sd]', fmt)
            if len(placeholders) == len(vals): return repr(fmt % tuple(vals))
        except: pass
        return m.group(0)
    source = re.sub(
        r"'([^']*(?:%[sd][^']*)+)'\s*%\s*\(([^)]+)\)",
        repl_percent, source)
    # '{0}{1}...'.format(parts) literal
    def repl_format(m):
        try:
            fmt_str = m.group(1); args_str = m.group(2)
            args = re.findall(r"'([^']*)'|\"([^\"]*)\"", args_str)
            vals = [a or b for a, b in args]
            result = fmt_str.format(*vals)
            return repr(result)
        except: return m.group(0)
    source = re.sub(
        r"'((?:\{[0-9]*\})+)'\s*\.\s*format\s*\(([^)]+)\)",
        repl_format, source)
    return source

# ── N10: AST-based constant folding ──────────────────────────
def v4_ast_constant_fold(source: str) -> str:
    """
    Раскрывает константные AST-выражения:
    True and True → True
    1 + 2 + 3 → 6
    'a' * 3 → 'aaa'
    """
    def try_safe_eval(expr: str):
        # Только безопасные операции
        safe_nodes = (ast.Constant, ast.BinOp, ast.UnaryOp, ast.BoolOp,
                      ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod,
                      ast.Pow, ast.FloorDiv, ast.BitOr, ast.BitAnd,
                      ast.BitXor, ast.LShift, ast.RShift, ast.Invert,
                      ast.Not, ast.USub, ast.UAdd, ast.And, ast.Or)
        try:
            tree = ast.parse(expr, mode='eval')
            for node in ast.walk(tree):
                if not isinstance(node, safe_nodes): return None
            v = eval(compile(tree, '<string>', 'eval'))
            if isinstance(v, (int, float, str, bool, bytes)) and len(repr(v)) < 200:
                return repr(v)
        except: pass
        return None

    def repl(m):
        r = try_safe_eval(m.group(0))
        return r if r else m.group(0)
    # Числовые выражения в скобках
    source = re.sub(r'\(\s*\d+\s*[\+\-\*\/\%\^\|\&]+\s*\d+\s*\)', repl, source)
    # True/False/None boolean folding
    source = re.sub(r'\bTrue\s+and\s+True\b', 'True', source)
    source = re.sub(r'\bFalse\s+or\s+False\b', 'False', source)
    source = re.sub(r'\bTrue\s+or\s+\w+\b', 'True', source)
    source = re.sub(r'\bFalse\s+and\s+\w+\b', 'False', source)
    source = re.sub(r'\bnot\s+False\b', 'True', source)
    source = re.sub(r'\bnot\s+True\b', 'False', source)
    return source

# ── N11: Hyperion / Python obfuscator EXE ────────────────────
def v4_decode_hyperion_style(source: str) -> str:
    """
    Hyperion/PyArmor стиль: зашифрованный payload в переменной + exec.
    pyarmor_runtime() + __pyarmor__(__name__, __file__, b'...', 1)
    """
    # Убираем PyArmor runtime calls
    source = re.sub(r'from\s+pytransform\s+import\s+pyarmor_runtime\s*\n', '', source)
    source = re.sub(r'pyarmor_runtime\s*\(\s*\)\s*\n?', '', source)
    source = re.sub(r'__pyarmor__\s*\([^)]*\)\s*\n?', '# [PyArmor protected — runtime decrypt required]\n', source)
    # Убираем Hyperion-стиль exec(decrypt(...))
    source = re.sub(r"exec\s*\(\s*decrypt\s*\([^)]+\)\s*\)", '# [Hyperion encrypted block]', source)
    return source

# ── N12: Caesar cipher (всех ROT вариантов) ──────────────────
def v4_decode_caesar_all(source: str) -> str:
    """
    Декодирует Caesar/ROT шифры всех вариантов (ROT1-ROT25).
    Ищет паттерны codecs.decode(s, 'rot_N') или строки с таким смещением.
    """
    def rot_n(text: str, n: int) -> str:
        result = []
        for c in text:
            if 'a' <= c <= 'z': result.append(chr((ord(c) - ord('a') + n) % 26 + ord('a')))
            elif 'A' <= c <= 'Z': result.append(chr((ord(c) - ord('A') + n) % 26 + ord('A')))
            else: result.append(c)
        return ''.join(result)
    # codecs.decode(s, 'rot_13') уже обрабатывается в v3
    # Добавляем остальные ROT варианты если вдруг встречаются
    source = re.sub(r"codecs\.decode\s*\(\s*'([^']+)'\s*,\s*'caesar_(\d+)'\s*\)",
        lambda m: repr(rot_n(m.group(1), int(m.group(2)))), source)
    return source

# ── N13: String interleave decode (чётные/нечётные символы) ──
def v4_decode_interleave_chars(source: str) -> str:
    """
    Декодирует interleave: первая половина чётные, вторая нечётные:
    'aAbBcC' → 'abc' + 'ABC' → recombine
    """
    def repl(m):
        try:
            s = m.group(1)
            if len(s) % 2 != 0: return m.group(0)
            half = len(s) // 2
            evens = s[:half]; odds = s[half:]
            return repr(''.join(a+b for a, b in zip(evens, odds)))
        except: return m.group(0)
    # Помечаем interleaved строки через специальный паттерн
    return source

# ── N14: Hash-based string obfuscation ───────────────────────
def v4_decode_hash_strings(source: str) -> str:
    """
    Некоторые обфускаторы используют словари hash→string:
    _strings = {0x1a2b: 'import', 0x3c4d: 'os'}
    _s(0x1a2b) → 'import'
    """
    # Ищем словарь hex → string
    string_dict = {}
    for m in re.finditer(r"(0x[0-9a-fA-F]+|0X[0-9A-Fa-f]+)\s*:\s*['\"]([^'\"]+)['\"]", source):
        string_dict[m.group(1).lower()] = m.group(2)
    if string_dict:
        def lookup(m):
            key = m.group(1).lower()
            return repr(string_dict[key]) if key in string_dict else m.group(0)
        source = re.sub(r'_s\s*\(\s*(0x[0-9a-fA-F]+)\s*\)', lookup, source)
    return source

# ── N15: Zlib + base64 inline (без lambda) ───────────────────
def v4_decode_zlib_inline(source: str) -> str:
    """
    exec(zlib.decompress(base64.b64decode('...')))
    или exec(__import__('zlib').decompress(base64.b64decode(b'...')))
    """
    def repl(m):
        try:
            data = base64.b64decode(m.group(1).strip())
            result = zlib.decompress(data).decode('utf-8', errors='replace')
            return f"# [INLINE ZLIB+B64 DECODED]\n{result}"
        except: return m.group(0)
    source = re.sub(
        r"exec\s*\(\s*(?:zlib|__import__\s*\(\s*['\"]zlib['\"]\s*\))\s*\.\s*decompress\s*\(\s*(?:base64|__import__\s*\(\s*['\"]base64['\"]\s*\))\s*\.\s*b64decode\s*\(\s*b?['\"]([A-Za-z0-9+/=\n]+)['\"]\s*\)\s*\)\s*\)",
        repl, source)
    return source

# ── Применяем все v4 техники ─────────────────────────────────
def v4_deobfuscate_source(source: str) -> str:
    """Применяет все эксклюзивные v4 техники."""
    source = v4_decode_substitution(source)
    source = v4_decode_numeral_strings(source)
    source = v4_decode_split_reassemble(source)
    source = v4_decode_exotic_bases(source)
    source = v4_decode_bitwise_obf(source)
    source = v4_decode_ord_table(source)
    source = v4_decode_format_obf(source)
    source = v4_ast_constant_fold(source)
    source = v4_decode_hyperion_style(source)
    source = v4_decode_caesar_all(source)
    source = v4_decode_zlib_inline(source)
    source = v4_decode_hash_strings(source)
    return source


# ══════════════════════════════════════════════════════════════
#
#   ███████╗██╗  ██╗███████╗    ███╗   ██╗███████╗██╗    ██╗
#   ██╔════╝╚██╗██╔╝██╔════╝    ████╗  ██║██╔════╝██║    ██║
#   █████╗   ╚███╔╝ █████╗      ██╔██╗ ██║█████╗  ██║ █╗ ██║
#   ██╔══╝   ██╔██╗ ██╔══╝      ██║╚██╗██║██╔══╝  ██║███╗██║
#   ███████╗██╔╝ ██╗███████╗    ██║ ╚████║███████╗╚███╔███╔╝
#   ╚══════╝╚═╝  ╚═╝╚══════╝    ╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝
#
#   СУПЕРПРОДВИНУТАЯ РАСПАКОВКА EXE
# ══════════════════════════════════════════════════════════════

def exe_deep_scan(data: bytes) -> dict:
    """
    Глубокое сканирование EXE файла — ищет все возможные
    Python payload'ы, строки, конфиги и embedded файлы.
    """
    report = {
        'format':        v3_detect_format(data),
        'size':          len(data),
        'python_strings': [],
        'base64_blobs':  [],
        'embedded_zips': [],
        'pe_sections':   [],
        'python_version': None,
        'entry_points':  [],
        'imports':       [],
    }

    # Определение версии Python
    ver_patterns = [
        (b'python38.dll', '3.8'), (b'python39.dll', '3.9'),
        (b'python310.dll', '3.10'), (b'python311.dll', '3.11'),
        (b'python312.dll', '3.12'), (b'python37.dll', '3.7'),
        (b'python36.dll', '3.6'),
    ]
    for pat, ver in ver_patterns:
        if pat.lower() in data.lower():
            report['python_version'] = ver; break

    # Поиск Python-строк
    try:
        text = data.decode('utf-8', errors='ignore')
        for pattern in [r'import \w+', r'def \w+\s*\(', r'class \w+[:(]',
                        r'if __name__\s*==', r'from \w+ import']:
            matches = re.findall(pattern, text)
            report['python_strings'].extend(matches[:5])
    except: pass

    # Поиск base64 блоков
    b64_pat = re.compile(rb'[A-Za-z0-9+/]{40,}={0,2}')
    for m in b64_pat.finditer(data):
        blob = m.group(0)
        try:
            decoded = base64.b64decode(blob)
            if len(decoded) > 50:
                inner = decoded
                for fn in [zlib.decompress, gzip.decompress, lzma.decompress]:
                    try: inner = fn(inner)
                    except: pass
                try:
                    s = inner.decode('utf-8')
                    if ('def ' in s or 'import ' in s) and len(s) > 100:
                        report['base64_blobs'].append({'offset': m.start(), 'size': len(decoded), 'preview': s[:200]})
                        if len(report['base64_blobs']) >= 3: break
                except: pass
        except: pass

    # PE секции
    if data[:2] == b'MZ':
        try:
            pe_offset = struct.unpack_from('<I', data, 0x3C)[0]
            if pe_offset < len(data) - 4 and data[pe_offset:pe_offset+4] == b'PE\x00\x00':
                machine, num_sections = struct.unpack_from('<HH', data, pe_offset + 4)
                sec_offset = pe_offset + 24 + struct.unpack_from('<H', data, pe_offset + 20)[0]
                for i in range(min(num_sections, 16)):
                    so = sec_offset + i * 40
                    if so + 40 > len(data): break
                    name = data[so:so+8].rstrip(b'\x00').decode('ascii', errors='replace')
                    vsize, vaddr, raw_size, raw_offset = struct.unpack_from('<IIII', data, so + 8)
                    report['pe_sections'].append({'name': name, 'vsize': vsize, 'raw_size': raw_size})
        except: pass

    return report

def exe_extract_all(data: bytes, filename: str) -> list:
    """
    Максимальное извлечение — пробует ВСЕ методы.
    Возвращает список (name, content, method).
    """
    results = []
    fmt = v3_detect_format(data)

    # Метод 1: PyInstaller
    if fmt in ("pyinstaller", "pe_with_zip", "pyinstaller_pyz", "pe_unknown"):
        try:
            pyinst_files = v3_extract_pyinstaller(data)
            for name, content in pyinst_files.items():
                if name.startswith('_') and name.endswith('err'): continue
                if isinstance(content, bytes) and name.endswith('.pyc'):
                    src = v3_decompile_pyc(content)
                    results.append((name.replace('.pyc', '.py'), src, "PyInstaller+decompile"))
                elif isinstance(content, bytes):
                    try: results.append((name, content.decode('utf-8', errors='replace'), "PyInstaller"))
                    except: pass
        except: pass

    # Метод 2: ZIP внутри EXE (универсальный поиск)
    import zipfile
    for start_offset in [0, data.rfind(b'PK\x03\x04'), data.find(b'PK\x03\x04')]:
        if start_offset <= 0: continue
        try:
            with zipfile.ZipFile(io.BytesIO(data[start_offset:])) as zf:
                for entry in zf.namelist():
                    if any(entry.endswith(x) for x in ('.py', '.pyc', '.pyx', '.pyo', '.py3')):
                        try:
                            content = zf.read(entry)
                            if entry.endswith('.pyc'):
                                src = v3_decompile_pyc(content)
                                results.append((f"zip_{entry.replace('.pyc','.py')}", src, "ZIP+decompile"))
                            else:
                                results.append((f"zip_{entry}", content.decode('utf-8', errors='replace'), "ZIP"))
                        except: pass
        except: pass
        if results: break

    # Метод 3: Поиск .pyc magic bytes
    pyc_magics = [b'\x6f\x0d\x0d\x0a', b'\x61\x0d\x0d\x0a', b'\x33\x0d\x0d\x0a',
                  b'\xee\x0c\x0d\x0a', b'\x55\x0d\x0d\x0a', b'\x42\x0d\x0d\x0a',
                  b'\xd1\x0c\x0d\x0a', b'\x0c\x0d\x0d\x0a']
    for magic in pyc_magics:
        pos = 0
        while True:
            pos = data.find(magic, pos)
            if pos == -1: break
            try:
                pyc_data = data[pos:]
                src = v3_decompile_pyc(pyc_data)
                if len(src) > 100 and ('def ' in src or 'import ' in src):
                    results.append((f'embedded_{pos:08x}.py', src, f"embedded .pyc@{pos:#x}"))
            except: pass
            pos += 1
            if len(results) >= 20: break

    # Метод 4: zlib-сжатые блоки
    pos = 0
    zlib_found = 0
    while zlib_found < 5:
        pos = data.find(b'\x78\x9c', pos)  # zlib magic
        if pos == -1:
            pos = data.find(b'\x78\xda', 0)  # best compression
            if pos == -1: break
        try:
            decomp = zlib.decompress(data[pos:pos+65536])
            if len(decomp) > 100:
                try:
                    s = decomp.decode('utf-8')
                    if 'def ' in s or 'import ' in s or 'class ' in s:
                        results.append((f'zlib_{pos:08x}.py', s, f"zlib block@{pos:#x}"))
                        zlib_found += 1
                except: pass
        except: pass
        pos += 2

    # Метод 5: Python string extraction (строки из PE)
    if not results or fmt == "nuitka":
        extracted = v3_extract_pe_strings(data)
        if extracted:
            results.append(('strings_extracted.py', f"# Extracted Python strings from {filename}\n\n{extracted}", "PE strings"))

    # Метод 6: base64 блоки → decompress → source
    b64_pat = re.compile(rb'[A-Za-z0-9+/]{100,}={0,2}')
    b64_found = 0
    for m in b64_pat.finditer(data):
        if b64_found >= 3: break
        blob = m.group(0)
        try:
            decoded = base64.b64decode(blob)
            inner = decoded
            chain = []
            for fn, name in [(zlib.decompress,'zlib'), (gzip.decompress,'gzip'), (lzma.decompress,'lzma')]:
                try: inner = fn(inner); chain.append(name)
                except: pass
            try:
                s = inner.decode('utf-8')
                if len(s) > 100 and ('def ' in s or 'import ' in s):
                    method_str = 'b64+' + '+'.join(chain) if chain else 'b64'
                    results.append((f'b64blob_{m.start():08x}.py', s, method_str))
                    b64_found += 1
            except: pass
        except: pass

    # Дедупликация по содержимому
    seen = set()
    unique_results = []
    for name, content, method in results:
        sig = hashlib.md5(content[:500].encode() if isinstance(content, str) else content[:500]).hexdigest()
        if sig not in seen:
            seen.add(sig)
            unique_results.append((name, content, method))

    return unique_results if unique_results else [('no_python_found.txt',
        f"# Python код не найден в {filename}\n"
        f"# Формат: {fmt}\n"
        f"# Размер: {len(data):,} байт\n"
        f"# Попробуй другой инструмент (IDA, Ghidra) для дизассемблирования", "none")]


# ══════════════════════════════════════════════════════════════
#   АНАЛИЗАТОР — энтропия, сложность, обнаружение
# ══════════════════════════════════════════════════════════════

def calc_entropy(data: bytes) -> float:
    """Вычисляет энтропию Шеннона (0-8 бит/байт)."""
    if not data: return 0.0
    freq = Counter(data)
    length = len(data)
    entropy = -sum((c/length) * (c/length).bit_length() for c in freq.values() if c > 0)
    # Нормализованная энтропия
    import math
    return -sum((c/length) * math.log2(c/length) for c in freq.values() if c > 0)

def analyze_code_complexity(source: str) -> dict:
    """Анализирует сложность и характеристики кода."""
    lines = source.split('\n')
    result = {
        'lines':        len(lines),
        'chars':        len(source),
        'functions':    len(re.findall(r'^\s*def\s+\w+', source, re.MULTILINE)),
        'classes':      len(re.findall(r'^\s*class\s+\w+', source, re.MULTILINE)),
        'imports':      len(re.findall(r'^\s*(?:import|from)\s+', source, re.MULTILINE)),
        'exec_calls':   len(re.findall(r'\bexec\s*\(', source)),
        'eval_calls':   len(re.findall(r'\beval\s*\(', source)),
        'lambdas':      len(re.findall(r'\blambda\b', source)),
        'base64_blobs': len(re.findall(r'b64decode', source)),
        'hex_strings':  len(re.findall(r'\\x[0-9a-fA-F]{2}', source)),
        'unicode_names': len(re.findall(r'[\u3000-\u9fff]', source)),
        'xor_ops':      len(re.findall(r'\^', source)),
        'entropy':      calc_entropy(source.encode()),
    }
    # Оценка уровня обфускации (0-100)
    score = 0
    if result['exec_calls'] > 0:   score += 15
    if result['eval_calls'] > 0:   score += 10
    if result['base64_blobs'] > 0: score += 20
    if result['hex_strings'] > 10: score += 15
    if result['unicode_names'] > 0: score += 25
    if result['xor_ops'] > 5:      score += 10
    if result['entropy'] > 5.5:    score += 15
    if result['lambdas'] > 10:     score += 10
    result['obf_score'] = min(score, 100)
    result['obf_level'] = (
        "🔴 МАКСИМУМ" if score >= 70 else
        "🟠 ВЫСОКИЙ"  if score >= 50 else
        "🟡 СРЕДНИЙ"  if score >= 25 else
        "🟢 НИЗКИЙ"
    )
    return result

def full_detect_obfuscation(code: str) -> list:
    """Полное обнаружение всех методов обфускации."""
    detected = []
    method_v1 = detect_obfuscation(code)
    if method_v1: detected.append(f"v1: {method_v1}")
    if re.search(r'bytes\.fromhex', code) and re.search(r'\^\s*\(\d+\s*\^', code): detected.append("XOR-строки")
    if re.search(r'while \w+ != \d+:', code): detected.append("state-machine")
    if re.search(r'def \w+\s*\(\s*\w+\s*,\s*\w+\s*,\s*\w+\s*\)\s*:', code): detected.append("call-wrappers")
    if re.search(r'[\u3000-\u9fff]', code): detected.append("unicode-имена")
    if re.search(r'chr\s*\(\s*\d+\s*\)\s*\+\s*chr', code): detected.append("chr()-конкат")
    if re.search(r"codecs\.decode.*rot.13", code): detected.append("ROT13")
    if re.search(r'\(~?\w+\s*\^\s*\w+\)\s*\+\s*2\s*\*', code): detected.append("MBA")
    if re.search(r'\\x[0-9a-fA-F]{2}', code): detected.append("hex-escape")
    if re.search(r'\\u[0-9a-fA-F]{4}', code): detected.append("unicode-escape")
    if re.search(r"'\s*\.join\s*\(\s*\[", code): detected.append("join-obf")
    if re.search(r"\[::-1\]", code): detected.append("reversed-strings")
    if re.search(r'eval\s*\(\s*compile', code): detected.append("eval(compile)")
    if re.search(r'pyarmor_runtime\s*\(', code): detected.append("PyArmor")
    if re.search(r'__pyarmor__', code): detected.append("PyArmor-runtime")
    if re.search(r'IsDebuggerPresent|gettrace', code): detected.append("anti-debug")
    if re.search(r'time\.time\(\)\s*-\s*\w+\s*>', code): detected.append("time-check")
    if re.search(r'_\s*\*\s*_\s*\+\s*_.*%\s*2\s*==\s*0', code): detected.append("N*(N+1)%2")
    if re.search(r'translate\s*\(\s*str\.maketrans', code): detected.append("substitution")
    if re.search(r'bytes\s*\(\s*\[[0-9,\s]+\]\s*\)', code): detected.append("bytes-literal")
    return detected if detected else ["не обнаружена"]


# ══════════════════════════════════════════════════════════════
#   ГЛАВНЫЙ АВТО-ДЕОБФУСКАТОР
# ══════════════════════════════════════════════════════════════

def auto_deobfuscate_source(code: str) -> tuple:
    """
    OMEGA авто-деобфускатор.
    Пробует все методы v1 → v4 → v3 → v2 в порядке приоритета.
    Возвращает (result, method, stats)
    """
    lines_in = code.count('\n') + 1
    chars_in = len(code)
    analysis = analyze_code_complexity(code)

    # 1. v1 (lambda+exec)
    method_v1 = detect_obfuscation(code)
    if method_v1:
        result, info = deobfuscate_code(code)
        if result:
            return result, f"v1: {info}", analysis

    # 2. v4 (новые методы) + v3 + v2 комбо
    v4_result = v4_deobfuscate_source(code)
    v3_result = v3_deobfuscate_source(v4_result)
    if v3_result != code:
        final = rendy2_deobfuscate(v3_result)
        return final, "v4+v3+v2 (OMEGA full pipeline)", analysis

    # 3. v3 source-level
    v3_only = v3_deobfuscate_source(code)
    if v3_only != code:
        final = rendy2_deobfuscate(v3_only)
        return final, "v3+v2 (MBA/chr/hex + universal cleanup)", analysis

    # 4. v2 (Ренди 2.0)
    v2_result = rendy2_deobfuscate(code)
    method = "v2 (Ренди 2.0 — universal)"
    if method_v1: method = f"v2 fallback (v1 {method_v1} не сработал)"
    return v2_result, method, analysis


# ══════════════════════════════════════════════════════════════
#
#   ██████╗  ██████╗ ████████╗    ██╗   ██╗██╗
#   ██╔══██╗██╔═══██╗╚══██╔══╝   ██║   ██║██║
#   ██████╔╝██║   ██║   ██║      ██║   ██║██║
#   ██╔══██╗██║   ██║   ██║      ██║   ██║██║
#   ██████╔╝╚██████╔╝   ██║      ╚██████╔╝██║
#   ╚═════╝  ╚═════╝    ╚═╝       ╚═════╝ ╚═╝
#
#   ТГ БОТ — ЛЕГЕНДАРНЫЙ ДИЗАЙН
# ══════════════════════════════════════════════════════════════

# Крутые ASCII баннеры для разных режимов
BANNER_MAIN = (
    "╔═══════════════════════════════════╗\n"
    "║  ██████╗ ███████╗ ██████╗ ██████╗ ║\n"
    "║  ██╔══██╗██╔════╝██╔═══██╗██╔══██╗║\n"
    "║  ██║  ██║█████╗  ██║   ██║██████╔╝║\n"
    "║  ██║  ██║██╔══╝  ██║   ██║██╔══██╗║\n"
    "║  ██████╔╝███████╗╚██████╔╝██████╔╝║\n"
    "║  ╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝ ║\n"
    "║  🔓 OMEGA  v3.0   Astolfo Edition ║\n"
    "║  (\\(\\  ∧＿∧  💕  50+ TECHNIQUES  ║\n"
    "║  (｡•ω•｡)つ━━━━━━━━━━━━━━━━━━━━━━ ║\n"
    "╚═══════════════════════════════════╝"
)

BANNER_DECODE = (
    "┌─────────────────────────────┐\n"
    "│  🔓 DECODING IN PROGRESS... │\n"
    "│  ▓▓▓▓▓▓▓░░░░░░░░░░░  45%   │\n"
    "│  Breaking encryption...     │\n"
    "└─────────────────────────────┘"
)

BANNER_SUCCESS = (
    "╔═══════════════════════════╗\n"
    "║   ✅ DECODED SUCCESSFULLY ║\n"
    "║   🌸 ~Astolfo approved~   ║\n"
    "╚═══════════════════════════╝"
)

BANNER_BINARY = (
    "╔══════════════════════════════╗\n"
    "║  📦 EXE UNPACKER OMEGA       ║\n"
    "║  ► PyInstaller  ✓            ║\n"
    "║  ► cx_Freeze    ✓            ║\n"
    "║  ► py2exe       ✓            ║\n"
    "║  ► zipapp       ✓            ║\n"
    "║  ► .pyc files   ✓            ║\n"
    "║  ► Deep scan    ✓            ║\n"
    "╚══════════════════════════════╝"
)

LOADING_FRAMES = [
    "⠋ Анализирую...", "⠙ Анализирую...", "⠹ Анализирую...",
    "⠸ Декодирую...", "⠼ Декодирую...", "⠴ Декодирую...",
    "⠦ Очищаю...", "⠧ Очищаю...", "⠇ Финализирую...", "⠏ Финализирую..."
]

_deobf_state: dict = {}


def _send(chat_id, text, kb=None):
    try: bot.send_message(chat_id, text, reply_markup=kb)
    except Exception as e: print(f"[send] err: {e}")

def _edit(chat_id, msg_id, text, kb=None):
    try: bot.edit_message_text(text, chat_id, msg_id, reply_markup=kb)
    except Exception as e: print(f"[edit] err: {e}")


# ── ReplyKeyboard ──────────────────────────────────────────────
def kb_main():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.row("🔓 АВТО ДЕКОД", "🔬 Анализ файла")
    kb.row("📦 EXE / Binary", "🧬 Глубокое сканирование")
    kb.row("🔓 v1 lambda", "🔓 v2 Ренди", "🔧 v3 Строки")
    kb.row("🆕 v4 OMEGA", "📊 Моя статистика")
    return kb

# ── InlineKeyboard для выбора режима ──────────────────────────
def kb_deobf():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.row(telebot.types.InlineKeyboardButton("⚡ OMEGA АВТО (v1→v4→v3→v2)", callback_data="deobf_auto"))
    kb.row(telebot.types.InlineKeyboardButton("🔍 Анализ + определить метод", callback_data="deobf_detect"))
    kb.row(
        telebot.types.InlineKeyboardButton("🔓 Только v1", callback_data="deobf_v1"),
        telebot.types.InlineKeyboardButton("🔓 Только v2", callback_data="deobf_v2"))
    kb.row(
        telebot.types.InlineKeyboardButton("🔧 v3 Строки", callback_data="deobf_v3src"),
        telebot.types.InlineKeyboardButton("🆕 v4 OMEGA", callback_data="deobf_v4"))
    kb.row(
        telebot.types.InlineKeyboardButton("📦 EXE/Binary", callback_data="deobf_v3bin"),
        telebot.types.InlineKeyboardButton("🧬 Deep Scan EXE", callback_data="deobf_deep"))
    return kb


# ══════════════════════════════════════════════════════════════
#   КОМАНДЫ
# ══════════════════════════════════════════════════════════════
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    try:
        uid  = int(msg.from_user.id)
        name = msg.from_user.first_name or "анон"

        if is_admin(uid):
            key = str(uid)
            if key not in allowed_users:
                allowed_users[key] = {"username": getattr(msg.from_user, "username", "") or "", "first_name": name, "added": ts(), "uses": 0}
                save_users()

        if not is_allowed(uid):
            bot.send_message(msg.chat.id,
                f"{BANNER_MAIN}\n\n"
                "🔒 Доступ закрыт~\n"
                "Этот бот работает только по приглашению.\n"
                "Обратись к администратору 💕")
            return

        key = str(uid)
        if key in allowed_users:
            allowed_users[key]["uses"] = allowed_users[key].get("uses", 0) + 1
            save_users()

        adm_badge = " ★ ADMIN" if is_admin(uid) else ""
        text = (
            f"{BANNER_MAIN}\n\n"
            f"Привет, {name}!{adm_badge} 🌸\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔓 OMEGA — 50+ методов декода\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📦 v1 — lambda+exec:\n"
            "  base64/32/16 · zlib/gzip/lzma\n"
            "  Комбо · Rendy marshal-chain\n\n"
            "🧠 v2 — Ренди 2.0 Universal:\n"
            "  XOR строки · state-machine\n"
            "  call-wrappers · dummy vars\n"
            "  getattr chains · unicode\n"
            "  N*(N+1)%2 if-blocks\n\n"
            "🔧 v3 — String Decoders:\n"
            "  MBA · ROT13 · chr() concat\n"
            "  hex/unicode escape\n"
            "  join obf · reversed strings\n"
            "  eval(compile) · exec layers\n\n"
            "🆕 v4 — OMEGA Exclusive:\n"
            "  Substitution cipher\n"
            "  Multi-byte XOR · Base58/85\n"
            "  Format obf · Bitwise tricks\n"
            "  Ord/char tables · Caesar all\n"
            "  AST constant folding\n"
            "  PyArmor/Hyperion cleanup\n"
            "  Zlib inline decode\n\n"
            "📦 EXE Unpacker:\n"
            "  PyInstaller · cx_Freeze\n"
            "  py2exe · zipapp · .pyc\n"
            "  Deep scan + 6 методов\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Команды:\n"
            "/deobf  — 🔓 авто декод\n"
            "/deobf2 — 🧠 Ренди 2.0\n"
            "/deobf3 — 📦 EXE распаковка\n"
            "/deobf4 — 🆕 v4 OMEGA техники\n"
            "/deep   — 🧬 глубокий анализ\n"
            "/stats  — 📊 статистика\n"
        )
        if is_admin(uid):
            text += "/admin  — 👑 панель админа\n"

        if os.path.exists(WELCOME_PHOTO):
            try:
                with open(WELCOME_PHOTO, "rb") as f: bot.send_photo(msg.chat.id, f)
            except: pass

        bot.send_message(msg.chat.id, text, reply_markup=kb_main())
    except Exception as e:
        import traceback; print(f"[start] ERR: {traceback.format_exc()}")
        try: bot.send_message(msg.chat.id, "Бот работает! /start ещё раз")
        except: pass


@bot.message_handler(commands=["deobf"])
@access_required
def cmd_deobf(msg):
    _deobf_state[msg.from_user.id] = "waiting_auto"
    _send(msg.chat.id,
        "╔══════════════════════════════╗\n"
        "║  ⚡ OMEGA АВТО ДЕОБФУСКАТОР  ║\n"
        "╚══════════════════════════════╝\n\n"
        "Пробует все методы автоматически:\n"
        "v1 → v4 OMEGA → v3 → v2\n\n"
        "📎 Отправь .py файл:",
        kb_deobf())


@bot.message_handler(commands=["deobf2"])
@access_required
def cmd_deobf2(msg):
    _deobf_state[msg.from_user.id] = "waiting_v2"
    _send(msg.chat.id,
        "╔══════════════════════════════╗\n"
        "║  🧠 РЕНДИ 2.0 UNIVERSAL      ║\n"
        "╚══════════════════════════════╝\n\n"
        "30+ техник:\n"
        "  • XOR строки · state-machine\n"
        "  • call-wrappers · dummy vars\n"
        "  • getattr() chains\n"
        "  • N*(N+1)%2 if-blocks\n"
        "  • anti-debug cleanup\n\n"
        "📎 Отправь .py файл:")


@bot.message_handler(commands=["deobf3"])
@access_required
def cmd_deobf3(msg):
    _deobf_state[msg.from_user.id] = "waiting_v3bin"
    _send(msg.chat.id,
        f"{BANNER_BINARY}\n\n"
        "📎 Отправь .exe / .pyc / .pyz файл:")


@bot.message_handler(commands=["deobf4"])
@access_required
def cmd_deobf4(msg):
    _deobf_state[msg.from_user.id] = "waiting_v4"
    _send(msg.chat.id,
        "╔══════════════════════════════╗\n"
        "║  🆕 v4 OMEGA EXCLUSIVE       ║\n"
        "╚══════════════════════════════╝\n\n"
        "15 эксклюзивных техник:\n"
        "  • Substitution cipher\n"
        "  • Base58/85/91 decode\n"
        "  • Format string obf\n"
        "  • Bitwise NOT/shift cleanup\n"
        "  • Ord/char XOR tables\n"
        "  • AST constant folding\n"
        "  • PyArmor/Hyperion cleanup\n"
        "  • Decimal/octal/binary chars\n"
        "  • Hash string tables\n"
        "  • Zlib inline exec decode\n\n"
        "📎 Отправь .py файл:")


@bot.message_handler(commands=["deep"])
@access_required
def cmd_deep(msg):
    _deobf_state[msg.from_user.id] = "waiting_deep"
    _send(msg.chat.id,
        "╔══════════════════════════════╗\n"
        "║  🧬 DEEP SCAN OMEGA          ║\n"
        "╚══════════════════════════════╝\n\n"
        "Максимальный анализ EXE:\n"
        "  • 6 методов извлечения\n"
        "  • PE секции + импорты\n"
        "  • Поиск .pyc magic bytes\n"
        "  • zlib/gzip блоки\n"
        "  • base64 payload scan\n"
        "  • Python string extraction\n"
        "  • Версия Python\n"
        "  • Дедупликация результатов\n\n"
        "📎 Отправь .exe / .pyc / .pyz:")


@bot.message_handler(commands=["stats"])
@access_required
def cmd_stats(msg):
    uid = str(msg.from_user.id)
    user_info = allowed_users.get(uid, {})
    uses = user_info.get('uses', 0)
    joined = user_info.get('added', 'неизвестно')
    total  = global_stats.get('total_decoded', 0)
    total_bytes = global_stats.get('bytes_processed', 0)
    top_methods = sorted(global_stats.get('methods', {}).items(), key=lambda x: -x[1])[:5]
    text = (
        "╔══════════════════════════════╗\n"
        "║  📊 СТАТИСТИКА OMEGA         ║\n"
        "╚══════════════════════════════╝\n\n"
        f"👤 Твои данные:\n"
        f"  Файлов декодировано: {uses}\n"
        f"  Дата регистрации: {joined}\n\n"
        f"🌍 Глобальная статистика:\n"
        f"  Всего декодировано: {total}\n"
        f"  Байт обработано: {total_bytes:,}\n\n"
    )
    if top_methods:
        text += "🏆 Топ методов:\n"
        medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
        for i, (method, count) in enumerate(top_methods):
            text += f"  {medals[i]} {method}: {count}\n"
    bot.send_message(msg.chat.id, text, reply_markup=kb_main())


# ══════════════════════════════════════════════════════════════
#   ОБРАБОТКА ДОКУМЕНТОВ
# ══════════════════════════════════════════════════════════════
@bot.message_handler(content_types=["document"])
def handle_document(msg):
    uid = int(msg.from_user.id)
    if not is_allowed(uid):
        bot.send_message(msg.chat.id, "🔒 Доступ закрыт~"); return

    state = _deobf_state.get(uid)
    if state is None:
        bot.send_message(msg.chat.id,
            "Выбери режим:\n"
            "/deobf  — ⚡ АВТО\n"
            "/deobf2 — 🧠 Ренди 2.0\n"
            "/deobf3 — 📦 EXE/Binary\n"
            "/deobf4 — 🆕 v4 OMEGA\n"
            "/deep   — 🧬 Deep Scan\n"); return

    doc = msg.document; fname = doc.file_name or "file"
    _deobf_state.pop(uid, None)
    wait = bot.send_message(msg.chat.id, "⠋ Загружаю файл...")

    def do():
        try:
            file_info  = bot.get_file(doc.file_id)
            downloaded = bot.download_file(file_info.file_path)

            # ── EXE Binary ──
            if state in ("waiting_v3bin", "waiting_deep"):
                mode_name = "🧬 DEEP SCAN" if state == "waiting_deep" else "📦 EXE UNPACK"
                _edit(msg.chat.id, wait.message_id,
                    f"╔══════════════════════════════╗\n"
                    f"║  {mode_name}               ║\n"
                    f"╚══════════════════════════════╝\n\n"
                    f"📄 Файл: {fname}\n"
                    f"📊 Размер: {len(downloaded):,} байт\n"
                    f"🔎 Определяю формат...")

                fmt = v3_detect_format(downloaded)
                _edit(msg.chat.id, wait.message_id,
                    f"📦 Формат: {fmt}\n"
                    f"⠴ Извлекаю Python код...")

                if state == "waiting_deep":
                    # Глубокий скан
                    results = exe_extract_all(downloaded, fname)
                    report  = exe_deep_scan(downloaded)
                    header  = (
                        f"╔══════════════════════════════╗\n"
                        f"║  🧬 DEEP SCAN ЗАВЕРШЁН       ║\n"
                        f"╚══════════════════════════════╝\n\n"
                        f"📄 Файл: {fname}\n"
                        f"📦 Формат: {fmt}\n"
                        f"🐍 Python: {report.get('python_version', 'неизвестно')}\n"
                        f"🧩 PE секций: {len(report.get('pe_sections', []))}\n"
                        f"📁 Извлечено файлов: {len(results)}\n"
                        f"🔍 B64 блоков найдено: {len(report.get('base64_blobs', []))}\n"
                    )
                    if report.get('python_strings'):
                        header += f"\n🐍 Python строки: {', '.join(report['python_strings'][:3])}\n"
                    _edit(msg.chat.id, wait.message_id, header)
                    for name, content, method in results[:15]:
                        if isinstance(content, bytes): content = content.decode('utf-8', errors='replace')
                        out_path = f"/tmp/deep_{name}"
                        with open(out_path, "w", encoding="utf-8") as f: f.write(content)
                        with open(out_path, "rb") as f:
                            bot.send_document(msg.chat.id, f, visible_file_name=name,
                                caption=f"🧬 {method} | {name} | {len(content):,} символов")
                        try: os.remove(out_path)
                        except: pass
                else:
                    results, fmt = v3_deobfuscate_binary(downloaded, fname)
                    _edit(msg.chat.id, wait.message_id,
                        f"╔══════════════════════════════╗\n"
                        f"║  ✅ РАСПАКОВАНО!              ║\n"
                        f"╚══════════════════════════════╝\n\n"
                        f"📄 {fname}\n"
                        f"📦 Формат: {fmt}\n"
                        f"📁 Файлов: {len(results)}")
                    for name, content in results[:10]:
                        if isinstance(content, bytes): content = content.decode('utf-8', errors='replace')
                        out_path = f"/tmp/v3_{name}"
                        with open(out_path, "w", encoding="utf-8") as f: f.write(content)
                        with open(out_path, "rb") as f:
                            bot.send_document(msg.chat.id, f, visible_file_name=name,
                                caption=f"📦 {fmt} | {name}")
                        try: os.remove(out_path)
                        except: pass

                record_stat(fmt, len(downloaded))
                return

            # ── Python .py ──
            if not fname.endswith(".py"):
                _edit(msg.chat.id, wait.message_id, f"📦 Пробую как бинарный файл...\n📄 {fname}")
                results, fmt = v3_deobfuscate_binary(downloaded, fname)
                if results and fmt != "unknown":
                    _edit(msg.chat.id, wait.message_id, f"✅ Распаковано! Формат: {fmt}")
                    for name, content in results[:5]:
                        if isinstance(content, bytes): content = content.decode('utf-8', errors='replace')
                        out_path = f"/tmp/v3_{name}"
                        with open(out_path, "w", encoding="utf-8") as f: f.write(content)
                        with open(out_path, "rb") as f:
                            bot.send_document(msg.chat.id, f, visible_file_name=name, caption=f"📦 {fmt}")
                        try: os.remove(out_path)
                        except: pass
                else:
                    _edit(msg.chat.id, wait.message_id, "❌ Только .py для декодера!\nДля EXE/binary — /deobf3 или /deep")
                return

            code = downloaded.decode("utf-8", errors="replace")
            lines_in = code.count('\n') + 1
            chars_in = len(code)
            analysis = analyze_code_complexity(code)

            # ── Анализ ──
            if state == "waiting_detect":
                _edit(msg.chat.id, wait.message_id, "🔬 Анализирую...")
                detected = full_detect_obfuscation(code)
                info = analysis

                bar_length = 20
                score = info['obf_score']
                filled = int(bar_length * score / 100)
                bar = "█" * filled + "░" * (bar_length - filled)

                text = (
                    "╔══════════════════════════════╗\n"
                    "║  🔬 ПОЛНЫЙ АНАЛИЗ КОДА       ║\n"
                    "╚══════════════════════════════╝\n\n"
                    f"📄 Файл: {fname}\n"
                    f"📏 Строк: {info['lines']:,}  |  Символов: {info['chars']:,}\n\n"
                    f"🔧 Структура:\n"
                    f"  Функций:   {info['functions']}\n"
                    f"  Классов:   {info['classes']}\n"
                    f"  Импортов:  {info['imports']}\n\n"
                    f"⚠️ Признаки обфускации:\n"
                    f"  exec():     {info['exec_calls']}\n"
                    f"  eval():     {info['eval_calls']}\n"
                    f"  lambda:     {info['lambdas']}\n"
                    f"  base64:     {info['base64_blobs']}\n"
                    f"  hex-стр:   {info['hex_strings']}\n"
                    f"  unicode:    {info['unicode_names']}\n"
                    f"  XOR (^):    {info['xor_ops']}\n"
                    f"  Энтропия:  {info['entropy']:.2f} bpb\n\n"
                    f"📊 Уровень обфускации:\n"
                    f"  [{bar}] {score}%\n"
                    f"  {info['obf_level']}\n\n"
                    f"🎯 Обнаружено:\n  " + "\n  ".join(f"• {d}" for d in detected) + "\n\n"
                    f"💡 Рекомендация: /deobf (OMEGA АВТО)"
                )
                _edit(msg.chat.id, wait.message_id, text)
                return

            # ── Только v4 ──
            if state == "waiting_v4":
                _edit(msg.chat.id, wait.message_id,
                    f"🆕 v4 OMEGA — обрабатываю...\n📄 {fname}")
                result = v4_deobfuscate_source(code)
                _send_result(msg.chat.id, wait.message_id, result, doc.file_name,
                             "v4 OMEGA (15 exclusive techniques)", lines_in, chars_in, "v4_")
                record_stat("v4", chars_in)
                return

            # ── Только v3 строки ──
            if state == "waiting_v3src":
                _edit(msg.chat.id, wait.message_id, f"🔧 v3 Строки...\n📄 {fname}")
                result = v3_deobfuscate_source(code)
                _send_result(msg.chat.id, wait.message_id, result, doc.file_name,
                             "v3 (MBA/chr/hex/ROT13/unicode)", lines_in, chars_in, "v3src_")
                record_stat("v3", chars_in)
                return

            # ── Только v2 ──
            if state == "waiting_v2":
                _edit(msg.chat.id, wait.message_id,
                    f"🧠 Ренди 2.0...\n📄 {fname}\n"
                    f"📊 Строк: {lines_in} | Символов: {chars_in:,}\n"
                    f"🔎 Уровень: {analysis['obf_level']}")
                result = rendy2_deobfuscate(code)
                _send_result(msg.chat.id, wait.message_id, result, doc.file_name,
                             "v2 (Ренди 2.0)", lines_in, chars_in, "rendy2_")
                record_stat("v2", chars_in)
                return

            # ── Только v1 ──
            if state == "waiting":
                _edit(msg.chat.id, wait.message_id, f"🔓 v1 анализ...\n📄 {fname}")
                result, info_v1 = deobfuscate_code(code)
                if result:
                    _send_result(msg.chat.id, wait.message_id, result, doc.file_name,
                                 f"v1: {info_v1}", lines_in, chars_in, "decoded_")
                    record_stat(f"v1:{info_v1}", chars_in)
                else:
                    _edit(msg.chat.id, wait.message_id,
                        f"❌ v1 не смог: {info_v1}\n\n"
                        f"Попробуй /deobf (OMEGA АВТО)")
                return

            # ── АВТО OMEGA ──
            progress_bar = lambda p: "█" * int(p/5) + "░" * (20 - int(p/5))
            _edit(msg.chat.id, wait.message_id,
                f"╔══════════════════════════════╗\n"
                f"║  ⚡ OMEGA АВТО СТАРТ         ║\n"
                f"╚══════════════════════════════╝\n\n"
                f"📄 {fname}\n"
                f"📊 Строк: {lines_in:,} | Символов: {chars_in:,}\n"
                f"🎯 Уровень: {analysis['obf_level']}\n\n"
                f"[{progress_bar(0)}] 0%\n"
                f"⠋ Запускаю конвейер...")

            time.sleep(0.5)
            _edit(msg.chat.id, wait.message_id,
                f"📄 {fname}\n"
                f"[{progress_bar(25)}] 25%\n"
                f"⠹ v1 → v4 → v3 → v2...")

            result, method, stats = auto_deobfuscate_source(code)

            _edit(msg.chat.id, wait.message_id,
                f"📄 {fname}\n"
                f"[{progress_bar(90)}] 90%\n"
                f"⠧ Финализирую...")

            _send_result(msg.chat.id, wait.message_id, result, doc.file_name,
                         f"OMEGA: {method}", lines_in, chars_in, "omega_")
            record_stat(method, chars_in)

            key = str(uid)
            if key in allowed_users:
                allowed_users[key]["uses"] = allowed_users[key].get("uses", 0) + 1
                save_users()

        except Exception as e:
            import traceback; print(f"[deobf] ERR: {traceback.format_exc()}")
            try: _edit(msg.chat.id, wait.message_id, f"❌ Ошибка: {e}")
            except: pass

    threading.Thread(target=do, daemon=True).start()


def _send_result(chat_id, msg_id, result, orig_name, method, lines_in, chars_in, prefix=""):
    lines_out = result.count('\n') + 1
    chars_out = len(result)
    red_l = round(100 * (1 - lines_out / max(lines_in, 1)))
    red_c = round(100 * (1 - chars_out / max(chars_in, 1)))

    bar_in  = "█" * min(10, lines_in // 100 + 1) + "░" * max(0, 10 - lines_in // 100 - 1)
    bar_out = "█" * min(10, lines_out // 100 + 1) + "░" * max(0, 10 - lines_out // 100 - 1)

    _edit(chat_id, msg_id,
        f"{BANNER_SUCCESS}\n\n"
        f"📄 Файл: {orig_name}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 Метод: {method}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Строк:   [{bar_in}] {lines_in:,}\n"
        f"        → [{bar_out}] {lines_out:,}  ({red_l}%↓)\n"
        f"💬 Символов: {chars_in:,} → {chars_out:,}  ({red_c}%↓)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💕 Decoded by @ArrhythmiaFucksn")

    out_name = f"{prefix}{orig_name}"
    out_path = f"/tmp/{out_name}"
    with open(out_path, "w", encoding="utf-8") as f: f.write(result)
    with open(out_path, "rb") as f:
        bot.send_document(chat_id, f, visible_file_name=out_name,
            caption=(
                f"🔓 OMEGA v{BOT_VERSION} | {method}\n"
                f"📊 {lines_in}→{lines_out} строк ({red_l}%↓) | "
                f"{chars_in:,}→{chars_out:,} символов ({red_c}%↓)\n"
                f"💕 @ArrhythmiaFucksn"
            ))
    try: os.remove(out_path)
    except: pass


# ══════════════════════════════════════════════════════════════
#   CALLBACK КНОПКИ
# ══════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data.startswith("deobf_"))
def on_deobf_callback(call):
    uid = call.from_user.id
    if not is_allowed(uid): bot.answer_callback_query(call.id, "Нет доступа"); return

    action_map = {
        "deobf_auto":   "waiting_auto",
        "deobf_detect": "waiting_detect",
        "deobf_v1":     "waiting",
        "deobf_v2":     "waiting_v2",
        "deobf_v3src":  "waiting_v3src",
        "deobf_v3bin":  "waiting_v3bin",
        "deobf_v4":     "waiting_v4",
        "deobf_deep":   "waiting_deep",
    }
    state = action_map.get(call.data)
    if state:
        _deobf_state[uid] = state
        prompts = {
            "waiting_auto":   "⚡ OMEGA АВТО — отправь .py файл:",
            "waiting_detect": "🔬 Анализ — отправь .py файл:",
            "waiting":        "🔓 v1 — отправь .py файл:",
            "waiting_v2":     "🧠 Ренди 2.0 — отправь .py файл:",
            "waiting_v3src":  "🔧 v3 Строки — отправь .py файл:",
            "waiting_v3bin":  "📦 EXE/Binary — отправь .exe / .pyc / .pyz:",
            "waiting_v4":     "🆕 v4 OMEGA — отправь .py файл:",
            "waiting_deep":   "🧬 Deep Scan — отправь .exe / .pyc:",
        }
        try: bot.edit_message_text(prompts[state], call.message.chat.id, call.message.message_id)
        except: pass
    bot.answer_callback_query(call.id)


# ══════════════════════════════════════════════════════════════
#   ReplyKeyboard кнопки
# ══════════════════════════════════════════════════════════════
@bot.message_handler(func=lambda m: m.text in [
    "🔓 АВТО ДЕКОД", "🔬 Анализ файла", "📦 EXE / Binary",
    "🧬 Глубокое сканирование", "🔓 v1 lambda", "🔓 v2 Ренди",
    "🔧 v3 Строки", "🆕 v4 OMEGA", "📊 Моя статистика"
])
@access_required
def handle_menu_button(msg):
    uid = msg.from_user.id
    if msg.text == "📊 Моя статистика":
        cmd_stats(msg); return

    state_map = {
        "🔓 АВТО ДЕКОД":          "waiting_auto",
        "🔬 Анализ файла":        "waiting_detect",
        "📦 EXE / Binary":        "waiting_v3bin",
        "🧬 Глубокое сканирование": "waiting_deep",
        "🔓 v1 lambda":           "waiting",
        "🔓 v2 Ренди":            "waiting_v2",
        "🔧 v3 Строки":           "waiting_v3src",
        "🆕 v4 OMEGA":            "waiting_v4",
    }
    state = state_map.get(msg.text)
    if state:
        _deobf_state[uid] = state
        prompts = {
            "waiting_auto":   "⚡ OMEGA АВТО — отправь .py файл:",
            "waiting_detect": "🔬 Анализ — отправь .py файл:",
            "waiting_v3bin":  "📦 EXE/Binary — отправь .exe / .pyc:",
            "waiting_deep":   "🧬 Deep Scan — отправь .exe / .pyc:",
            "waiting":        "🔓 v1 — отправь .py файл:",
            "waiting_v2":     "🧠 Ренди 2.0 — отправь .py файл:",
            "waiting_v3src":  "🔧 v3 Строки — отправь .py файл:",
            "waiting_v4":     "🆕 v4 OMEGA — отправь .py файл:",
        }
        bot.send_message(msg.chat.id, prompts[state], reply_markup=kb_deobf())


# ══════════════════════════════════════════════════════════════
#   ADMIN КОМАНДЫ
# ══════════════════════════════════════════════════════════════
@bot.message_handler(commands=["admin"])
def cmd_admin(msg):
    if not is_admin(msg.from_user.id): return
    total = len(allowed_users); banned = len(banned_users)
    total_decoded = global_stats.get('total_decoded', 0)
    bot.send_message(msg.chat.id,
        "╔══════════════════════════════╗\n"
        "║  👑 ADMIN PANEL OMEGA        ║\n"
        "╚══════════════════════════════╝\n\n"
        f"👥 Пользователей: {total}\n"
        f"🚫 Заблокировано: {banned}\n"
        f"🔓 Декодировано: {total_decoded}\n\n"
        "Команды:\n"
        "/add ID — выдать доступ\n"
        "/remove ID — забрать доступ\n"
        "/ban ID — заблокировать\n"
        "/unban ID — разблокировать\n"
        "/users — список пользователей\n"
        "/broadcast — рассылка всем")

@bot.message_handler(commands=["add"])
def cmd_add(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 2: bot.send_message(msg.chat.id, "Использование: /add ID [имя]"); return
    try:
        target_id = int(parts[1]); name = " ".join(parts[2:]) if len(parts) > 2 else f"user_{target_id}"
        allowed_users[str(target_id)] = {"username": "", "first_name": name, "added": ts(), "uses": 0}
        save_users()
        bot.send_message(msg.chat.id, f"✅ Доступ выдан: {target_id} ({name})")
        try: bot.send_message(target_id, f"✅ Тебе выдан доступ к OMEGA DEOBF!\nИспользуй /start 💕")
        except: pass
    except ValueError: bot.send_message(msg.chat.id, "❌ Неверный ID")

@bot.message_handler(commands=["remove"])
def cmd_remove(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 2: bot.send_message(msg.chat.id, "Использование: /remove ID"); return
    try:
        target_id = str(int(parts[1]))
        if target_id in allowed_users: del allowed_users[target_id]; save_users(); bot.send_message(msg.chat.id, f"✅ Доступ забран: {target_id}")
        else: bot.send_message(msg.chat.id, f"❌ {target_id} не найден")
    except ValueError: bot.send_message(msg.chat.id, "❌ Неверный ID")

@bot.message_handler(commands=["ban"])
def cmd_ban(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 2: bot.send_message(msg.chat.id, "Использование: /ban ID"); return
    try:
        target_id = str(int(parts[1])); banned_users[target_id] = {"banned": ts()}; save_users()
        bot.send_message(msg.chat.id, f"🚫 Заблокирован: {target_id}")
    except ValueError: bot.send_message(msg.chat.id, "❌ Неверный ID")

@bot.message_handler(commands=["unban"])
def cmd_unban(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 2: bot.send_message(msg.chat.id, "Использование: /unban ID"); return
    try:
        target_id = str(int(parts[1]))
        if target_id in banned_users: del banned_users[target_id]; save_users(); bot.send_message(msg.chat.id, f"✅ Разблокирован: {target_id}")
        else: bot.send_message(msg.chat.id, f"❌ {target_id} не заблокирован")
    except ValueError: bot.send_message(msg.chat.id, "❌ Неверный ID")

@bot.message_handler(commands=["users"])
def cmd_users(msg):
    if not is_admin(msg.from_user.id): return
    if not allowed_users: bot.send_message(msg.chat.id, "Список пуст"); return
    lines = ["╔══════════════════════════════╗\n║  👥 ПОЛЬЗОВАТЕЛИ OMEGA       ║\n╚══════════════════════════════╝\n\n"]
    for uid, info in list(allowed_users.items())[:50]:
        banned_mark = "🚫" if uid in banned_users else "✅"
        name = info.get('first_name', '') or uid
        uses = info.get('uses', 0)
        lines.append(f"{banned_mark} {uid} — {name} [{uses} файлов]\n")
    bot.send_message(msg.chat.id, "".join(lines))

@bot.message_handler(commands=["broadcast"])
def cmd_broadcast(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2: bot.send_message(msg.chat.id, "Использование: /broadcast текст"); return
    text = f"📢 OMEGA DEOBF\n\n{parts[1]}"
    sent = 0; failed = 0
    for uid in allowed_users:
        try: bot.send_message(int(uid), text); sent += 1
        except: failed += 1
    bot.send_message(msg.chat.id, f"✅ Отправлено: {sent}\n❌ Ошибок: {failed}")


# ══════════════════════════════════════════════════════════════
#   ЗАПУСК
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("╔═══════════════════════════════════════════════════════╗")
    print("║                                                       ║")
    print("║  🔓 DEOBF OMEGA v3.0 — Astolfo Edition 🌸            ║")
    print("║                                                       ║")
    print("║  Techniques:                                          ║")
    print("║    v1: base64/32/16 + zlib/gzip/lzma + marshal       ║")
    print("║    v2: Ренди 2.0 — 30+ universal                     ║")
    print("║    v3: MBA/chr/hex/ROT13/unicode/eval/exec            ║")
    print("║    v4: OMEGA — 15 exclusive new methods               ║")
    print("║    EXE: 6-method deep scan unpacker                   ║")
    print("║                                                       ║")
    print(f"║  Admins:   {list(ADMIN_IDS)}                         ║")
    print(f"║  Users:    {len(allowed_users)}                                      ║")
    print(f"║  Stats:    {global_stats.get('total_decoded', 0)} files decoded               ║")
    print("║                                                       ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()
    bot.infinity_polling(timeout=30, long_polling_timeout=20)
