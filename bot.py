"""
██████╗ ███████╗ ██████╗ ██████╗ ███████╗    ██████╗  ██████╗ ████████╗
██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗██╔═══██╗╚══██╔══╝
██║  ██║█████╗  ██║   ██║██████╔╝█████╗      ██████╔╝██║   ██║   ██║
██║  ██║██╔══╝  ██║   ██║██╔══██╗██╔══╝      ██╔══██╗██║   ██║   ██║
██████╔╝███████╗╚██████╔╝██████╔╝██║         ██████╔╝╚██████╔╝   ██║
╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝         ╚═════╝  ╚═════╝   ╚═╝

  Python Deobfuscator - sicksilent edition
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
ADMIN_IDS = {8683323127}
ADMIN_USERNAME = "@godmidainte"

CHANNEL_LINK = ""  # Channel removed
CHANNEL_ID   = None

USERS_FILE  = "allowed_users.json"
BANNED_FILE = "banned_users.json"

WELCOME_PHOTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sicksilent.png")
WELCOME_GIF   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sicksilent.gif")
# If sicksilent.png doesn't exist bot still works fine

BOT_VERSION = "3.0 OMEGA"
BOT_NAME    = "[!] SICKSILENT DEOBF"

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
    """Декоратор — проверяет whitelist перед выполнением команды."""
    def wrapper(msg):
        uid   = int(msg.from_user.id)
        name  = msg.from_user.first_name or "user"
        uname = getattr(msg.from_user, "username", "") or ""
        if is_allowed(uid):
            return fn(msg)
        _send_locked_screen(msg.chat.id, name, uid, uname)
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
_deobf_note   = "# DECODED BY @ArrhythmiaFucks | sicksilent deobf OMEGA v3.0\n\n"

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

def v4_decode_utf8_calls(source: str) -> str:
    """
    Decodes the obfuscation pattern: 'string'('utf-8') -> 'string'
    This appears after some obfuscators wrap string literals:
      __import__('sys'('utf-8'))  ->  __import__('sys')
      for x in ['requests'('utf-8'), 'os'('utf-8')]:  -> ['requests', 'os']
      getattr(obj, '__method__'('utf-8'))()  ->  getattr(obj, '__method__')()
    Also handles: b'bytes'('utf-8') -> b'bytes'
    """
    prev = None
    passes = 0
    while prev != source and passes < 15:
        prev = source
        passes += 1
        # 'string'('encoding') -> 'string'
        source = re.sub(
            r"'([^'\\]*)'\s*\(\s*'(?:utf-8|utf8|ascii|latin-1|cp1251|utf_8)'\s*\)",
            lambda m: f"'{m.group(1)}'",
            source
        )
        source = re.sub(
            r'"([^"\\]*)"\s*\(\s*"(?:utf-8|utf8|ascii|latin-1|cp1251|utf_8)"\s*\)',
            lambda m: f'"{m.group(1)}"',
            source
        )
        # b'bytes'('encoding') -> b'bytes'
        source = re.sub(
            r"(b'[^']*')\s*\(\s*'[^']*'\s*\)",
            lambda m: m.group(1),
            source
        )
        source = re.sub(
            r'(b"[^"]*")\s*\(\s*"[^"]*"\s*\)',
            lambda m: m.group(1),
            source
        )
    return source


def v4_deobfuscate_source(source: str) -> str:
    """Применяет все эксклюзивные v4 техники."""
    source = v4_decode_utf8_calls(source)  # FIX: 'str'('utf-8') pattern
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
#   ██╗   ██╗███████╗    ██╗   ██╗██╗  ████████╗██████╗  █████╗
#   ██║   ██║██╔════╝    ██║   ██║██║  ╚══██╔══╝██╔══██╗██╔══██╗
#   ██║   ██║███████╗    ██║   ██║██║     ██║   ██████╔╝███████║
#   ╚██╗ ██╔╝╚════██║    ██║   ██║██║     ██║   ██╔══██╗██╔══██║
#    ╚████╔╝ ███████║    ╚██████╔╝███████╗██║   ██║  ██║██║  ██║
#     ╚═══╝  ╚══════╝     ╚═════╝ ╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝
#
#   v5 ULTRA — 20+ НОВЫХ ЭКСКЛЮЗИВНЫХ МЕТОДОВ ДЕКОДИРОВАНИЯ
# ══════════════════════════════════════════════════════════════

# ── v5-1: AES-like string table decode ──────────────────────────
def v5_decode_string_table(source: str) -> str:
    """
    Decodes obfuscation where strings are stored in a list/dict
    and referenced by index. Pattern:
      _s = ["string1","string2",...]; x = _s[0]
      __strings__ = {...}; x = __strings__[key]
    """
    import ast as _ast
    changed = True
    passes = 0
    while changed and passes < 8:
        changed = False; passes += 1
        # Pattern: _varname = ["str1", "str2", ...]
        pat = re.compile(
            r'([A-Za-z_]\w*)\s*=\s*\[([^\]]{10,})\]'
        )
        for m in pat.finditer(source):
            varname = m.group(1)
            try:
                vals = _ast.literal_eval('[' + m.group(2) + ']')
                if not all(isinstance(v, str) for v in vals): continue
                # Replace all _varname[N] with the actual string
                def replace_idx(mo):
                    try:
                        idx = int(mo.group(1))
                        if 0 <= idx < len(vals):
                            changed = True
                            return repr(vals[idx])
                    except: pass
                    return mo.group(0)
                new = re.sub(
                    re.escape(varname) + r'\[(\d+)\]',
                    replace_idx, source
                )
                if new != source: source = new; changed = True
            except: pass
    return source


# ── v5-2: Lambda chain decode ────────────────────────────────────
def v5_decode_lambda_chains(source: str) -> str:
    """
    Decodes: (lambda x: x)("string") -> "string"
    And:     (lambda: "string")() -> "string"
    """
    changed = True
    while changed:
        changed = False
        # (lambda x: x)(val) -> val
        p2 = re.compile(r'\(lambda\s+(\w+)\s*:\s*\1\)\(([^)]+)\)')
        new = p2.sub(lambda m: m.group(2), source)
        if new != source: source = new; changed = True
        # (lambda: 'literal')() -> 'literal'
        p1 = re.compile(r"\(lambda\s*:\s*('[^']*')\)\(\)")
        new = p1.sub(lambda m: m.group(1), source)
        if new != source: source = new; changed = True
        p1b = re.compile(r'\(lambda\s*:\s*("[^"]*")\)\(\)')
        new = p1b.sub(lambda m: m.group(1), source)
        if new != source: source = new; changed = True
    return source


# ── v5-3: Nested exec/eval unwrapper ────────────────────────────
def v5_unwrap_nested_exec(source: str) -> str:
    """
    Decodes: exec("literal string") -> the literal string
    """
    changed = True; depth = 0
    while changed and depth < 5:
        changed = False; depth += 1
        # exec('...') with single quotes
        p1 = re.compile(r"exec\s*\(\s*'((?:[^'\\]|\\.)*)'\s*\)")
        def unwrap1(m):
            cs = m.group(1).replace("\\n", "\n").replace("\\t", "\t").replace("\\'", "'")
            return cs if len(cs) > 10 else m.group(0)
        new = p1.sub(unwrap1, source)
        if new != source: source = new; changed = True
        # exec("...") with double quotes
        p2 = re.compile(r'exec\s*\(\s*"((?:[^"\\]|\\.)*)"\s*\)')
        def unwrap2(m):
            cs = m.group(1).replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
            return cs if len(cs) > 10 else m.group(0)
        new = p2.sub(unwrap2, source)
        if new != source: source = new; changed = True
    return source



def v5_decode_compile_exec(source: str) -> str:
    """
    Decodes: exec(compile(base64.b64decode(b'...'), '<str>', 'exec'))
    """
    import re as _re
    # Match: exec(compile(base64.b64decode(b'DATA'), 'name', 'exec'))
    p = _re.compile(
        r"exec\s*\(\s*compile\s*\(\s*"
        r"(?:__import__\s*\(['\"]base64['\"]\)\.b64decode|base64\.b64decode)\s*\("
        r"\s*(b?['\"][A-Za-z0-9+/=\s]+['\"])\s*\)"
        r"\s*,\s*['\"][^'\"]*['\"]\s*,\s*['\"]exec['\"]\s*\)\s*\)"
    )
    def decode_compile(m):
        try:
            raw = m.group(1).strip()
            raw = raw.lstrip('bB').strip("'\"")
            decoded = base64.b64decode(raw.replace(' ','').replace('\n',''))
            return decoded.decode('utf-8', errors='replace')
        except: return m.group(0)
    return p.sub(decode_compile, source)





def v5_decode_marshal_strings(source: str) -> str:
    """Removes marshal/base64 obfuscation boilerplate."""
    # Remove entire marshal.loads(...) calls
    source = re.sub(
        r"marshal\.loads\s*\([^)]{10,}\)",
        "# [v5: marshal payload removed]",
        source
    )
    return source




def v5_remove_dead_code(source: str) -> str:
    """Removes obvious dead code: if False, while False, assert True, etc."""
    # Multiple consecutive pass
    source = re.sub(r"(\bpass\b\s*\n){3,}", "pass\n", source)
    # assert True
    source = re.sub(r"\bassert\s+True(?:\s*,\s*[^\n]+)?\n", "", source)
    # Fake __all__ = []
    source = re.sub(r"__all__\s*=\s*\[\s*\]\s*\n", "", source)
    # Remove obf markers
    source = re.sub(r"#\s*(?:PROTECTED|OBFUSCATED|ENCRYPTED)\s+(?:BY|WITH)\s+\S+[^\n]*\n", "", source, flags=re.I)
    source = re.sub(r"#\s*DO NOT MODIFY[^\n]*\n", "", source, flags=re.I)
    # Excess blank lines
    source = re.sub(r"\n{4,}", "\n\n\n", source)
    return source




def v5_decode_exotic_b91(source: str) -> str:
    """Decodes base91 encoded string literals in code."""
    _SQUOTE = "'"
    _DQUOTE = '"'
    p = re.compile(r"base91\.decode\s*\(\s*b?[" + _SQUOTE + _DQUOTE + r"]([^" + _SQUOTE + _DQUOTE + r"]{20,})[" + _SQUOTE + _DQUOTE + r"]\s*\)")
    def try_b91(m):
        try:
            result = v5_base91_decode(m.group(1)).decode("utf-8", errors="replace")
            if result.isprintable(): return repr(result)
        except: pass
        return m.group(0)
    return p.sub(try_b91, source)




def v5_decode_utf8_fix(source: str) -> str:
    """Re-run utf-8 call fix for v5 pipeline."""
    prev = None; p = 0
    while prev != source and p < 15:
        prev = source; p += 1
        source = re.sub(
            r"'([^'\\]*)'\s*\(\s*'(?:utf-8|utf8|ascii|latin-1|cp1251)'\s*\)",
            lambda m: f"'{m.group(1)}'", source)
        source = re.sub(
            r'"([^"\\]*)"\s*\(\s*"(?:utf-8|utf8|ascii)"\s*\)',
            lambda m: f'"{m.group(1)}"', source)
    return source


# ══════════════════════════════════════════════════════════════
#   MULTI-LAYER DECODER — keeps decoding until stable
# ══════════════════════════════════════════════════════════════


# ── v5-6: Hex-encoded string literals ────────────────────────────



def v5_decode_hex_literals(source):
    """Decodes b'\\xNN...' hex byte string literals."""
    import re as _r
    def hd(m):
        try:
            raw = bytes.fromhex(m.group(1).replace('\\x',''))
            return repr(raw.decode('utf-8', errors='replace'))
        except: return m.group(0)
    return _r.sub(rb"b'((?:\\x[0-9a-fA-F]{2})+)'\.decode\([^)]+\)".decode(), hd, source)


def v5_decode_encoded_literals(source):
    """Decodes bytes([N,N,...]).decode('utf-8') patterns."""
    import re as _r
    def bd(m):
        try:
            nums = [int(x.strip()) for x in m.group(1).split(',') if x.strip()]
            return repr(bytes(nums).decode('utf-8', errors='replace'))
        except: return m.group(0)
    return _r.sub(r"bytes\s*\(\s*\[([\d,\s]+)\]\s*\)\.decode\s*\([^)]+\)", bd, source)


def v5_decode_reduce_patterns(source):
    """Decodes reduce(lambda a,b: a+chr(b), [N,...], '') patterns."""
    import re as _r
    def rd(m):
        try:
            nums = [int(x.strip()) for x in m.group(1).split(',') if x.strip()]
            return repr(''.join(chr(n) for n in nums))
        except: return m.group(0)
    return _r.sub(
        r"(?:functools\.)?reduce\s*\(\s*lambda\s+\w+\s*,\s*\w+\s*:\s*\w+\s*\+\s*chr\s*\(\s*\w+\s*\)\s*,"
        r"\s*\[([\d,\s]+)\]\s*,\s*''\s*\)",
        rd, source
    )


def v5_decode_string_ops(source):
    """Decodes string repetition: 'a'*5 -> 'aaaaa'"""
    import re as _r
    source = _r.sub(r"'([^'\\])'\s*\*\s*(\d+)", lambda m: repr(m.group(1)*int(m.group(2))), source)
    source = _r.sub(r'"([^"\\])"\s*\*\s*(\d+)', lambda m: repr(m.group(1)*int(m.group(2))), source)
    return source


def v5_decode_pyarmor_bootstrap(source):
    """Removes PyArmor bootstrap code."""
    import re as _r
    source = _r.sub(r'from\s+pytransform\s+import[^\n]*\n', '', source, flags=_r.I)
    source = _r.sub(r'pyarmor_runtime\s*\([^)]*\)\s*\n', '', source, flags=_r.I)
    source = _r.sub(r'__pyarmor__\s*\([^)]*\)\s*\n', '', source, flags=_r.I)
    source = _r.sub(r'from\s+pytransform3\s+import[^\n]*\n', '', source, flags=_r.I)
    source = _r.sub(r'\n{3,}', '\n\n', source)
    return source.strip() + '\n' if source.strip() else source


def v5_decode_fstring_obf(source):
    """Decodes: f\"{'hello'}\" -> 'hello'"""
    import re as _r
    source = _r.sub(r'''f'\{('(?:[^'\\]|\\.)*')\}' '''.strip(), lambda m: m.group(1), source)
    source = _r.sub(r'''f"\{("(?:[^"\\]|\\.)*")\}"'''.strip(), lambda m: m.group(1), source)
    return source


def v5_decode_obf_imports(source):
    """Decodes __import__('os').path -> os.path"""
    import re as _r
    source = _r.sub(r"__import__\s*\(\s*'(\w+)'\s*\)\s*\.\s*(\w+)", lambda m: f"{m.group(1)}.{m.group(2)}", source)
    source = _r.sub(r'__import__\s*\(\s*"(\w+)"\s*\)\s*\.\s*(\w+)', lambda m: f"{m.group(1)}.{m.group(2)}", source)
    source = _r.sub(r"__import__\s*\(\s*'(\w+)'\s*\)", lambda m: m.group(1), source)
    source = _r.sub(r'__import__\s*\(\s*"(\w+)"\s*\)', lambda m: m.group(1), source)
    return source


def v5_decode_aes_like_strings(source):
    """Decodes chr(ord(c)^KEY) for c in 'string' patterns."""
    import re as _r
    def xd(m):
        try:
            key = int(m.group(1))
            return repr(''.join(chr(ord(c)^key) for c in m.group(2)))
        except: return m.group(0)
    return _r.sub(r"''\s*\.join\s*\(\s*chr\s*\(\s*ord\s*\(\s*\w+\s*\)\s*\^\s*(\d+)\s*\)\s*for\s+\w+\s+in\s+'([^']*)'\s*\)", xd, source)


def v5_decode_tuple_string(source):
    """Decodes ''.join(['h','e','l','l','o']) -> 'hello'"""
    import re as _r
    def jd(m):
        try:
            items = _r.findall(r"'([^']*)'", m.group(1))
            if len(items) > 1: return repr(''.join(items))
        except: pass
        return m.group(0)
    source = _r.sub(r"''\s*\.join\s*\(\s*\[\s*((?:'[^']*'\s*,?\s*)+)\s*\]\s*\)", jd, source)
    source = _r.sub(r"''\s*\.join\s*\(\s*\(\s*((?:'[^']*'\s*,?\s*)+)\s*\)\s*\)", jd, source)
    return source


def v5_remove_stacked_decorators(source):
    """Removes common obfuscation decorators."""
    import re as _r
    for name in ['protect','_protect','verify','_verify','antidebug','anti_debug','no_debug']:
        source = _r.sub(rf'@{_r.escape(name)}\s*\n', '', source)
        source = _r.sub(rf'@{_r.escape(name)}\s*\([^)]*\)\s*\n', '', source)
    return source


def v5_comprehensive_cleanup(source):
    """Final cleanup: remove obf markers, excess blank lines."""
    import re as _r
    source = _r.sub(r'#\s*(?:PROTECTED|OBFUSCATED|ENCRYPTED)\s+(?:BY|WITH)\s+\S+[^\n]*\n', '', source, flags=_r.I)
    source = _r.sub(r'#\s*DO NOT MODIFY[^\n]*\n', '', source, flags=_r.I)
    source = _r.sub(r'\n{4,}', '\n\n\n', source)
    return source.rstrip() + '\n'


def v5_deobfuscate_source(source: str) -> str:
    """v5 ULTRA — applies all exclusive v5 techniques."""
    source = v5_decode_utf8_fix(source)
    source = v5_decode_string_table(source)
    source = v5_decode_lambda_chains(source)
    source = v5_decode_hex_literals(source)
    source = v5_decode_encoded_literals(source)
    source = v5_decode_bytearray_xor(source)
    source = v5_decode_reduce_patterns(source)
    source = v5_decode_compile_exec(source)
    source = v5_decode_exotic_b91(source)
    source = v5_decode_obf_imports(source)
    source = v5_decode_tuple_string(source)
    source = v5_decode_fstring_obf(source)
    source = v5_decode_aes_like_strings(source)
    source = v5_unwrap_nested_exec(source)
    source = v5_decode_pyarmor_bootstrap(source)
    source = v5_decode_string_ops(source)
    source = v5_remove_stacked_decorators(source)
    source = v5_remove_dead_code(source)
    source = v5_rename_obf_vars(source)
    source = v5_comprehensive_cleanup(source)
    return source




def multilayer_deobfuscate(code: str, max_rounds: int = 10, progress_cb=None) -> tuple:
    """
    OMEGA MULTILAYER DECODER.
    Runs the full deobfuscation pipeline repeatedly until:
    - Code stops changing (stable)
    - No more obfuscation detected
    - Max rounds reached
    
    Returns: (final_code, rounds_done, methods_used, layers_info)
    """
    original = code
    current  = code
    methods_used = []
    layers_info  = []
    
    for round_num in range(1, max_rounds + 1):
        if progress_cb:
            progress_cb(round_num, max_rounds, current)
        
        # Check if still obfuscated
        detected = full_detect_obfuscation(current)
        analysis = analyze_code_complexity(current)
        
        if not detected and analysis['obf_score'] < 15:
            layers_info.append({
                'round': round_num,
                'status': 'CLEAN',
                'score': analysis['obf_score'],
                'method': 'none'
            })
            break
        
        prev = current
        method_this_round = []
        
        # Try all engines in sequence
        # v1
        try:
            r1, m1 = deobfuscate_code(current)
            if r1 and r1 != current:
                current = r1; method_this_round.append(f'v1:{m1}')
        except: pass
        
        # v5 (new)
        try:
            r5 = v5_deobfuscate_source(current)
            if r5 != current:
                method_this_round.append('v5')
                current = r5
        except: pass
        
        # v4
        try:
            r4 = v4_deobfuscate_source(current)
            if r4 != current:
                method_this_round.append('v4')
                current = r4
        except: pass
        
        # v3
        try:
            r3 = v3_deobfuscate_source(current)
            if r3 != current:
                method_this_round.append('v3')
                current = r3
        except: pass
        
        # v2
        try:
            r2 = rendy2_deobfuscate(current)
            if r2 != current:
                method_this_round.append('v2')
                current = r2
        except: pass
        
        if not method_this_round:
            method_this_round = ['no_change']
        
        method_str = '+'.join(method_this_round)
        reduction  = 1 - len(current) / max(len(prev), 1)
        
        layers_info.append({
            'round':     round_num,
            'status':    'DECODED' if current != prev else 'NO_CHANGE',
            'score':     analysis['obf_score'],
            'method':    method_str,
            'reduction': f'{reduction*100:.1f}%',
            'chars':     len(current),
        })
        
        methods_used.extend(method_this_round)
        
        # If nothing changed, stop
        if current == prev:
            break
    
    return current, len(layers_info), list(dict.fromkeys(methods_used)), layers_info


# ══════════════════════════════════════════════════════════════
#   ENHANCED EXE EXTRACTION — v6 BINARY ENGINE
# ══════════════════════════════════════════════════════════════

def exe_v6_extract_pyinstaller_full(data: bytes) -> dict:
    """
    Full PyInstaller extractor with TOC parsing.
    Handles PyInstaller 2.x, 3.x, 4.x, 5.x, 6.x
    """
    results = {}
    MAGIC_PATTERNS = [
        b'MEI\014\013\012\013\016',   # PyInstaller 2.x
        b'PYZ-00.pyz',                    # PYZ archive
        b'PKG\x0b\x0a',                 # PKG archive
    ]
    
    # Find the CArchive at end of file
    for end_offset in range(len(data) - 24, max(len(data) - 65536, 0), -1):
        chunk = data[end_offset:end_offset+4]
        if chunk == b'MEI':
            try:
                import struct
                toc_offset, toc_size, pkg_len, py_ver, flags = struct.unpack(
                    '>IIIII', data[end_offset-20:end_offset])
                # Extract TOC entries
                toc_data = data[end_offset - 20 - toc_size : end_offset - 20]
                pos = 0
                while pos < len(toc_data):
                    try:
                        entry_size = struct.unpack('>I', toc_data[pos:pos+4])[0]
                        if entry_size < 16: break
                        dpos, dlen, ulen, compress, typecode = struct.unpack(
                            '>IIIB1s', toc_data[pos+4:pos+18])
                        name = toc_data[pos+18:pos+entry_size].rstrip(b'\x00').decode('utf-8', errors='replace')
                        raw = data[dpos:dpos+dlen]
                        if compress:
                            try: raw = zlib.decompress(raw)
                            except: pass
                        results[name] = raw
                        pos += entry_size
                    except: break
            except: pass
            break
    
    # Fallback: search for embedded PYZ
    pyz_magic = b'PYZ-00.pyz'
    pos = data.find(pyz_magic)
    if pos != -1:
        try:
            pyz_data = data[pos:]
            with zipfile.ZipFile(io.BytesIO(pyz_data)) as zf:
                for name in zf.namelist():
                    content = zf.read(name)
                    results[f'pyz_{name}'] = content
        except: pass
    
    return results


def exe_v6_extract_nuitka(data: bytes) -> list:
    """
    Extract from Nuitka compiled executables.
    Nuitka doesn't have Python source directly, but we can:
    1. Extract embedded module names and string constants
    2. Look for __main__ wrapper code
    3. Extract any bundled Python files
    """
    results = []
    
    # Search for Python string constants (typical in Nuitka output)
    # These often contain function names, module names, etc.
    strings = []
    pos = 0
    while pos < len(data) - 2:
        # Windows-style null-terminated ASCII strings
        if 32 <= data[pos] < 127:
            end = pos
            while end < len(data) and 32 <= data[end] < 127:
                end += 1
            if end - pos >= 4:
                try:
                    s = data[pos:end].decode('ascii')
                    if (('def ' in s or 'import ' in s or 'class ' in s) and
                            len(s) > 20):
                        strings.append(s)
                except: pass
            pos = end
        else:
            pos += 1
    
    if strings:
        code_strings = [s for s in strings if
                        any(kw in s for kw in ['def ', 'import ', 'class ', 'return ', 'print('])]
        if code_strings:
            fragment_text = "# Extracted code fragments from Nuitka EXE\n"
            fragment_text += "# NOTE: Nuitka compiles to native code, these are partial\n\n"
            fragment_text += "\n".join(f"# Fragment: {frag[:200]}" for frag in code_strings[:50])
            results.append((
                'nuitka_code_fragments.py',
                fragment_text,
                'Nuitka fragments'
            ))
    
    return results


def exe_v6_extract_cxfreeze(data: bytes) -> list:
    """
    Extract from cx_Freeze executables.
    cx_Freeze uses a ZIP archive embedded in the EXE.
    Library.zip is the main container.
    """
    results = []
    import zipfile
    
    # cx_Freeze embeds a ZIP at the end
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for name in zf.namelist():
                content = zf.read(name)
                if name.endswith('.pyc'):
                    src = v3_decompile_pyc(content)
                    results.append((name.replace('.pyc', '_cx.py'), src, 'cx_Freeze+decompile'))
                elif name.endswith('.py'):
                    results.append((name + '_cx', content.decode('utf-8', errors='replace'), 'cx_Freeze'))
    except: pass
    
    # Also try finding Library.zip by scanning
    lib_marker = b'Library.zip'
    pos = data.find(lib_marker)
    if pos != -1:
        # Scan backwards for ZIP start (PK magic)
        for back in range(pos, max(0, pos-1024), -1):
            if data[back:back+2] == b'PK':
                try:
                    with zipfile.ZipFile(io.BytesIO(data[back:])) as zf:
                        for name in zf.namelist()[:30]:
                            try:
                                content = zf.read(name)
                                if name.endswith('.pyc'):
                                    src = v3_decompile_pyc(content)
                                    results.append((f'lib_{name.replace(".pyc",".py")}', src, 'cx_Freeze/Library.zip'))
                            except: pass
                except: pass
                break
    
    return results


def exe_v6_extract_py2exe(data: bytes) -> list:
    """
    Extract from py2exe executables.
    py2exe bundles a library.zip and looks for scripts in it.
    """
    results = []
    import zipfile
    
    # py2exe often has a ZIPFILE section
    MAGIC = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    
    # Search for embedded ZIP
    for start in range(len(data) - 4, -1, -1):
        if data[start:start+2] == b'PK' and data[start+2:start+4] in [b'\x03\x04', b'\x05\x06']:
            try:
                with zipfile.ZipFile(io.BytesIO(data[start:])) as zf:
                    py_files = [n for n in zf.namelist() if n.endswith(('.py', '.pyc', '.pyo'))]
                    if py_files:
                        for name in py_files[:20]:
                            content = zf.read(name)
                            if name.endswith('.pyc'):
                                src = v3_decompile_pyc(content)
                                results.append((name.replace('.pyc', '_py2.py'), src, 'py2exe'))
                            else:
                                results.append((name + '_py2', content.decode('utf-8', errors='replace'), 'py2exe'))
                        break
            except: pass
    
    return results


def exe_v6_extract_embedded_archive(data: bytes) -> list:
    """
    Generic embedded archive extractor.
    Tries: ZIP, tar.gz, tar.bz2, RAR (partial), 7z (partial)
    """
    results = []
    import zipfile
    
    # ZIP - scan from multiple offsets
    for magic_pos in [m.start() for m in re.finditer(b'PK\x03\x04', data)][:5]:
        try:
            with zipfile.ZipFile(io.BytesIO(data[magic_pos:])) as zf:
                for name in zf.namelist()[:10]:
                    if name.endswith(('.py', '.pyc')):
                        content = zf.read(name)
                        if name.endswith('.pyc'):
                            src = v3_decompile_pyc(content)
                            results.append((f'arch_{name.replace(".pyc",".py")}', src, 'embedded ZIP'))
                        else:
                            results.append((f'arch_{name}', content.decode('utf-8', errors='replace'), 'embedded ZIP'))
        except: pass
    
    # tar.gz: find 
    pos = data.find(b'\x1f\x8b')
    if pos != -1:
        try:
            import tarfile
            buf = io.BytesIO(data[pos:])
            with tarfile.open(fileobj=buf, mode='r:gz') as tf:
                for member in tf.getmembers()[:10]:
                    if member.name.endswith('.py'):
                        f = tf.extractfile(member)
                        if f:
                            results.append((f'tar_{member.name}', f.read().decode('utf-8', errors='replace'), 'tar.gz'))
        except: pass
    
    return results


def exe_v6_extract_elf(data: bytes) -> list:
    """
    Extract from ELF binaries (Linux compiled Python).
    Searches for Python bytecode sections.
    """
    results = []
    if not data.startswith(b'\x7fELF'):
        return results
    
    # Search for .pydata section or embedded pyc
    pyc_offsets = []
    pos = 0
    for magic in [b'\x6f\x0d\x0d\x0a', b'\x61\x0d\x0d\x0a', b'\xd1\x0c\x0d\x0a']:
        pos = 0
        while True:
            pos = data.find(magic, pos)
            if pos == -1: break
            pyc_offsets.append(pos)
            pos += 1
    
    for offset in pyc_offsets[:5]:
        try:
            src = v3_decompile_pyc(data[offset:])
            if len(src) > 100 and 'def ' in src:
                results.append((f'elf_pyc_{offset:x}.py', src, f'ELF embedded pyc @{offset:#x}'))
        except: pass
    
    return results


def exe_v6_extract_all_enhanced(data: bytes, filename: str) -> list:
    """
    ENHANCED v6 extraction — tries all 8+ methods.
    """
    results = []
    seen = set()
    fmt = v3_detect_format(data)
    
    def add(name, content, method):
        if isinstance(content, bytes):
            try: content = content.decode('utf-8', errors='replace')
            except: return
        sig = hashlib.md5(content[:1000].encode('utf-8', errors='replace')).hexdigest()
        if sig not in seen and len(content) > 10:
            seen.add(sig)
            results.append((name, content, method))
    
    # Method 1: PyInstaller TOC parser
    try:
        files = exe_v6_extract_pyinstaller_full(data)
        for name, content in files.items():
            if name.endswith('.pyc'):
                src = v3_decompile_pyc(content)
                add(name.replace('.pyc', '.py'), src, 'PyInstaller v6/TOC')
            else:
                add(name, content, 'PyInstaller v6')
    except: pass
    
    # Method 2: cx_Freeze
    for name, content, method in exe_v6_extract_cxfreeze(data):
        add(name, content, method)
    
    # Method 3: py2exe
    for name, content, method in exe_v6_extract_py2exe(data):
        add(name, content, method)
    
    # Method 4: Standard PyInstaller fallback
    try:
        files = v3_extract_pyinstaller(data)
        for name, content in files.items():
            if name.endswith('.pyc'):
                src = v3_decompile_pyc(content)
                add(name.replace('.pyc', '.py'), src, 'PyInstaller classic')
            elif isinstance(content, bytes):
                add(name, content, 'PyInstaller classic')
    except: pass
    
    # Method 5: zipapp / generic zip
    for name, content, method in exe_v6_extract_embedded_archive(data):
        add(name, content, method)
    
    # Method 6: Nuitka
    for name, content, method in exe_v6_extract_nuitka(data):
        add(name, content, method)
    
    # Method 7: ELF binary (Linux)
    for name, content, method in exe_v6_extract_elf(data):
        add(name, content, method)
    
    # Method 8: .pyc magic byte scanner
    pyc_magics = [b'\x6f\x0d\x0d\x0a', b'\x61\x0d\x0d\x0a',
                  b'\x33\x0d\x0d\x0a', b'\xee\x0c\x0d\x0a',
                  b'\x55\x0d\x0d\x0a', b'\x42\x0d\x0d\x0a',
                  b'\xd1\x0c\x0d\x0a', b'\x0c\x0d\x0d\x0a',
                  b'\xf3\x0d\x0d\x0a', b'\x99\x0d\x0d\x0a']
    found_pyc = 0
    for magic in pyc_magics:
        pos = 0
        while found_pyc < 8:
            pos = data.find(magic, pos)
            if pos == -1: break
            try:
                src = v3_decompile_pyc(data[pos:])
                if len(src) > 100 and ('def ' in src or 'import ' in src):
                    add(f'pyc_{pos:08x}.py', src, f'embedded .pyc@{pos:#x}')
                    found_pyc += 1
            except: pass
            pos += 1
    
    # Method 9: zlib compressed blocks
    zlib_found = 0
    for start_magic in [b'\x78\x9c', b'\x78\xda', b'\x78\x01']:
        pos = 0
        while zlib_found < 5:
            pos = data.find(start_magic, pos)
            if pos == -1: break
            for size in [65536, 32768, 16384]:
                try:
                    decomp = zlib.decompress(data[pos:pos+size])
                    if len(decomp) > 100:
                        s = decomp.decode('utf-8', errors='ignore')
                        if 'def ' in s or 'import ' in s or 'class ' in s:
                            add(f'zlib_{pos:08x}.py', s, f'zlib@{pos:#x}')
                            zlib_found += 1
                            break
                except: pass
            pos += 2
    
    # Method 10: base64 payload scan
    b64_pat = re.compile(rb'[A-Za-z0-9+/]{80,}={0,2}')
    b64_found = 0
    for m in b64_pat.finditer(data):
        if b64_found >= 5: break
        blob = m.group(0)
        try:
            decoded = base64.b64decode(blob)
            inner = decoded
            chain = []
            for fn, name in [(zlib.decompress,'zlib'), (gzip.decompress,'gzip'), (lzma.decompress,'lzma')]:
                try: inner = fn(inner); chain.append(name)
                except: pass
            s = inner.decode('utf-8', errors='ignore')
            if len(s) > 100 and ('def ' in s or 'import ' in s):
                mname = 'b64+' + '+'.join(chain) if chain else 'b64'
                add(f'b64_{m.start():08x}.py', s, mname)
                b64_found += 1
        except: pass
    
    # Method 11: PE string extraction with Python detection
    if not results or fmt == 'nuitka':
        pe_strings = v3_extract_pe_strings(data)
        if pe_strings:
            add('strings_python.py', pe_strings, 'PE string extraction')
    
    # Fallback
    if not results:
        results.append((
            'no_python_found.txt',
            f'# Python code not found in {filename}\n'
            f'# Format: {fmt}\n'
            f'# Size: {len(data):,} bytes\n'
            f'# Methods tried: PyInstaller/cx_Freeze/py2exe/pyc/zlib/b64/ELF\n'
            f'# Try specialized tools (IDA Pro, Ghidra) for native binaries',
            'none'
        ))
    
    return results

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
    import math
    freq = Counter(data)
    length = len(data)
    # Правильная формула — float не имеет bit_length, используем math.log2
    return -sum((c / length) * math.log2(c / length) for c in freq.values() if c > 0)

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

    # 2. v5+v4+v3+v2 full pipeline
    v5_result = v5_deobfuscate_source(code)
    v4_result = v4_deobfuscate_source(v5_result)
    v3_result = v3_deobfuscate_source(v4_result)
    if v3_result != code:
        final = rendy2_deobfuscate(v3_result)
        return final, "v5+v4+v3+v2 (ULTRA full pipeline)", analysis

    # 3. v4+v3+v2
    v4_result = v4_deobfuscate_source(code)
    v3_result = v3_deobfuscate_source(v4_result)
    if v3_result != code:
        final = rendy2_deobfuscate(v3_result)
        return final, "v4+v3+v2 (OMEGA full pipeline)", analysis

    # 4. v3 source-level
    v3_only = v3_deobfuscate_source(code)
    if v3_only != code:
        final = rendy2_deobfuscate(v3_only)
        return final, "v3+v2 (MBA/chr/hex + universal cleanup)", analysis

    # 5. v5 alone
    v5_only = v5_deobfuscate_source(code)
    if v5_only != code:
        final = rendy2_deobfuscate(v5_only)
        return final, "v5+v2 (ULTRA+Rendy)", analysis

    # 6. v2 (Ренди 2.0)
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

# ══════════════════════════════════════════════════════════════
#   ASCII БАННЕРЫ — SICKSILENT EDITION
#   Все рамки выровнены ровно, ничего не торчит
# ══════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────
# BANNER SYSTEM — Telegram Monospace Edition
# All banners wrapped in ``` for guaranteed alignment on any device
# ──────────────────────────────────────────────────────────────

def _hbox(lines: list, w: int = 42) -> str:
    """Fixed-width ASCII box. Use inside ``` for guaranteed alignment."""
    sep = "+" + "-" * (w + 2) + "+"
    rows = [sep]
    for line in lines:
        line = str(line)
        if len(line) > w:
            line = line[:w-1] + ">"
        rows.append("| " + line + " " * (w - len(line)) + " |")
    rows.append(sep)
    return "\n".join(rows)

def _mono(text: str) -> str:
    """Wrap in Telegram monospace block."""
    return "```\n" + text.replace("`", "'") + "\n```"

# ── MAIN BANNER ──────────────────────────────────────────────
_SICK_ASCII = (
    " ___ ___ ___ _  __ ___ ___ _   ___ _  _ _____\n"
    "/ __|_ _/ __| |/ // __/ __| | | __| \\| |_   _|\n"
    "\\__ \\| | (__ | ' <\\__ \\ __ \\ | | _|| .` | | |\n"
    "|___/|_|\\___||_|\\_|___/___/_| |___|_|\\_| |_|"
)

def BANNER_MAIN() -> str:
    box = _hbox([
        " PYTHON DEOBFUSCATOR  v3.0 OMEGA ",
        " 50+ DECODE TECHNIQUES           ",
        " @ArrhythmiaFucks  [sicksilent]  ",
        " v1 / v2 / v3 / v4 + EXE UNPACK ",
    ], 42)
    return _mono(_SICK_ASCII + "\n" + box)

def BANNER_SUCCESS(method="", lines_r="", chars_r="") -> str:
    m = (method[:38] + ">") if len(method) > 38 else method
    return _mono(_hbox([
        " >>> DECODE COMPLETE <<<          ",
        "",
        f" METHOD : {m}",
        f" LINES  : {lines_r}",
        f" CHARS  : {chars_r}",
        "",
        " sicksilent deobf | @ArrhythmiaFucks ",
    ], 42))

def BANNER_FAIL() -> str:
    return _mono(_hbox([
        " >>> DECODE FAILED <<<            ",
        "",
        " No obfuscation found or          ",
        " method not supported.            ",
        " Try /deobf  [OMEGA AUTO]         ",
    ], 42))

def BANNER_BINARY() -> str:
    return _mono(_hbox([
        " >>> EXE UNPACKER OMEGA <<<       ",
        "",
        " [+] PyInstaller                  ",
        " [+] cx_Freeze                    ",
        " [+] py2exe                       ",
        " [+] zipapp / .pyz                ",
        " [+] .pyc decompile               ",
        " [+] Deep Scan  (6 methods)       ",
        "",
        " sicksilent deobf | @ArrhythmiaFucks ",
    ], 42))

def BANNER_LOCKED() -> str:
    return _mono(_hbox([
        " >>> ACCESS DENIED <<<            ",
        "",
        " [sicksilent deobf]               ",
        "",
        " Step 1: Subscribe to channel     ",
        " Step 2: Press [I subscribed]     ",
        " Step 3: Wait for admin confirm   ",
        "",
        " Admin: @ArrhythmiaFucks          ",
    ], 42))

def BANNER_ADMIN() -> str:
    return _mono(_hbox([
        " >>> ADMIN PANEL <<<              ",
        " sicksilent deobf | OMEGA v3.0   ",
    ], 42))

def BANNER_STATS() -> str:
    return _mono(_hbox([
        " >>> STATISTICS <<<               ",
        " sicksilent deobf | OMEGA v3.0   ",
    ], 42))

def BANNER_ANALYZE() -> str:
    return _mono(_hbox([
        " >>> CODE ANALYSIS <<<            ",
        " sicksilent deobf | OMEGA v3.0   ",
    ], 42))

# Прогресс-бар
def pbar(pct: int, width: int = 20) -> str:
    filled = int(width * pct / 100)
    empty  = width - filled
    return "[" + "#" * filled + "-" * empty + "] " + str(pct) + "%"

# Декоративный разделитель
DIV  = "=" * 34
DIV2 = "-" * 34


# ══════════════════════════════════════════════════════════════
#   СИСТЕМА ПОДПИСКИ НА КАНАЛ
# ══════════════════════════════════════════════════════════════

# Словарь ожидающих подтверждения: {user_id: {"name": ..., "username": ..., "ts": ...}}
pending_subscribe: dict = {}

_deobf_state: dict = {}


def _send(chat_id, text, kb=None, md=False):
    try:
        pm = "Markdown" if md else None
        bot.send_message(chat_id, text, reply_markup=kb, parse_mode=pm)
    except Exception as e:
        try: bot.send_message(chat_id, text, reply_markup=kb)
        except: print(f"[send] err: {e}")

def _edit(chat_id, msg_id, text, kb=None, md=False):
    try:
        pm = "Markdown" if md else None
        bot.edit_message_text(text, chat_id, msg_id, reply_markup=kb, parse_mode=pm)
    except Exception as e:
        try: bot.edit_message_text(text, chat_id, msg_id, reply_markup=kb)
        except: print(f"[edit] err: {e}")


# ================================================================
#   KEYBOARD SYSTEM  —  SICKSILENT PREMIUM EDITION
#   All button texts are defined as constants to avoid mismatch
# ================================================================

# ── Button text constants (MUST match handler checks exactly) ──
BTN_AUTO    = "⚡ OMEGA AUTO"
BTN_ANALYZE = "🔬 ANALYZE"
BTN_EXE     = "📦 EXE/Binary"
BTN_DEEP    = "🧬 DEEP SCAN"
BTN_V1      = "🔓 v1 Lambda"
BTN_V2      = "🧠 v2 Rendy"
BTN_V3      = "🔧 v3 Strings"
BTN_V4      = "🆕 v4 OMEGA"
BTN_V5      = "🔮 v5 ULTRA"
BTN_MULTI   = "♾️ MULTI-LAYER"
BTN_STATS   = "📊 Stats"
BTN_MENU    = "🏠 Menu"

# ── Main ReplyKeyboard ─────────────────────────────────────────
def kb_main():
    kb = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, row_width=2, one_time_keyboard=False)
    kb.row(BTN_AUTO, BTN_ANALYZE)
    kb.row(BTN_EXE, BTN_DEEP)
    kb.row(BTN_V1, BTN_V2)
    kb.row(BTN_V3, BTN_V4)
    kb.row(BTN_V5, BTN_MULTI)
    kb.row(BTN_STATS)
    return kb

# ── Inline: main decode selector ──────────────────────────────
def kb_deobf():
    IB = telebot.types.InlineKeyboardButton
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        IB("⚡ OMEGA AUTO  v1→v4→v3→v2", callback_data="deobf_auto"),
    )
    kb.add(
        IB("🔬 Analyze file",       callback_data="deobf_detect"),
    )
    kb.add(
        IB("🔓 v1 Lambda",  callback_data="deobf_v1"),
        IB("🧠 v2 Rendy",   callback_data="deobf_v2"),
    )
    kb.add(
        IB("🔧 v3 Strings", callback_data="deobf_v3src"),
        IB("🆕 v4 OMEGA",   callback_data="deobf_v4"),
    )
    kb.add(
        IB("📦 EXE/Binary", callback_data="deobf_v3bin"),
        IB("🧬 Deep Scan",  callback_data="deobf_deep"),
    )
    kb.add(
        IB("🔮 v5 ULTRA",    callback_data="deobf_v5"),
        IB("♾️ MULTI-LAYER", callback_data="deobf_multi"),
    )
    kb.add(
        IB("🏠 Back to menu", callback_data="menu_back"),
    )
    return kb

# ── Inline: subscribe prompt ───────────────────────────────────
def kb_subscribe():
    """Inline keyboard for unregistered users (no channel)."""
    kb = telebot.types.InlineKeyboardMarkup()
    IB = telebot.types.InlineKeyboardButton
    kb.add(IB("📨 Request Access", callback_data="request_access"))
    return kb

# ── Inline: after successful register ─────────────────────────
def kb_after_register():
    IB = telebot.types.InlineKeyboardButton
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(IB("🔓  Start decoding  →", callback_data="open_menu"))
    return kb

# ── Inline: admin approve single request ──────────────────────
def kb_approve(uid: int, name: str):
    IB = telebot.types.InlineKeyboardButton
    safe = name[:15]
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        IB(f"✅ Grant access", callback_data=f"approve_{uid}_{safe}"),
        IB(f"❌ Deny",         callback_data=f"deny_{uid}"),
    )
    return kb

# ── Inline: admin panel ───────────────────────────────────────
def kb_admin_panel():
    IB = telebot.types.InlineKeyboardButton
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        IB("👥 Users",     callback_data="adm_users"),
        IB("📨 Requests",  callback_data="adm_pending"),
    )
    kb.add(
        IB("📢 Broadcast", callback_data="adm_broadcast"),
        IB("📊 Stats",     callback_data="adm_stats"),
    )
    kb.add(
        IB("⚙️ Settings",  callback_data="adm_settings"),
    )
    return kb



# ================================================================
#   UI HELPERS  —  ANIMATED MENU SYSTEM
# ================================================================

def _send_welcome_media(chat_id: int):
    """Send welcome GIF or photo for sicksilent branding."""
    # Try GIF first (animated), fallback to photo
    if os.path.exists(WELCOME_GIF):
        try:
            with open(WELCOME_GIF, "rb") as f:
                bot.send_animation(chat_id, f)
            return
        except: pass
    if os.path.exists(WELCOME_PHOTO):
        try:
            with open(WELCOME_PHOTO, "rb") as f:
                bot.send_photo(chat_id, f)
            return
        except: pass
    # Fallback: ASCII art "photo" as text
    bot.send_message(chat_id, _mono(
        "  _____ ___ ___ _  __ ___ ___ _   ___ _  _ _____  \n"
        " / __|_ _/ __| |/ // __/ __| | | __| \\| |_   _| \n"
        " \\__ \\| | (__ | \'<\\__ \\ __ \\ | | _|| .\'| | |   \n"
        " |___/|_|\\___||_|\\_|___/___/_| |___|_|\\_| |_|   \n"
        "                                                   \n"
        "         D  E  O  B  F  U  S  C  A  T  O  R       \n"
        "              v3.0 OMEGA  |  50+ tech             "
    ), parse_mode="Markdown")


def _anim_typing(chat_id: int, delay: float = 0.6):
    """Send typing action for realistic feel."""
    try:
        bot.send_chat_action(chat_id, "typing")
        time.sleep(delay)
    except: pass


def _send_main_menu(chat_id: int, name: str = "user", is_adm: bool = False):
    """Send the main menu with beautiful formatting."""
    adm_line = "\n🔑 *Admin panel:* /admin\n" if is_adm else ""
    text = (
        f"*[sicksilent deobf]* — v3.0 OMEGA\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Welcome back, *{name}*! 👋\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Choose a decode method below 👇"
        f"{adm_line}"
    )
    bot.send_message(chat_id, text, reply_markup=kb_main(), parse_mode="Markdown")


def _send_registration_flow(chat_id: int, name: str, uname: str, uid: int):
    """Shows locked access screen and notifies admin."""
    intro = (
        f"🔒 *ACCESS REQUIRED*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Hey *{name}*, this bot is private.\n\n"
        f"📨 Press the button below to request access.\n"
        f"Admin {ADMIN_USERNAME} will review your request.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_sicksilent deobf — {BOT_VERSION}_"
    )
    bot.send_message(chat_id, intro, reply_markup=kb_subscribe(), parse_mode="Markdown")
    # Notify admin
    for admin_id in ADMIN_IDS:
        _send_admin_request_notification(admin_id, uid, name, uname)



def _send_access_granted(chat_id: int, name: str):
    """Beautiful access granted notification."""
    _anim_typing(chat_id, 0.5)
    text = (
        f"✅ *ACCESS GRANTED*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Welcome to *sicksilent deobf*, {name}! 🎉\n\n"
        f"You now have access to:\n"
        f"  ⚡ OMEGA AUTO  —  50+ techniques\n"
        f"  🔓 v1 · v2 · v3 · v4 decoders\n"
        f"  📦 EXE/Binary unpacker\n"
        f"  🧬 Deep scan (6 methods)\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Press the button below to start 👇"
    )
    bot.send_message(chat_id, text, reply_markup=kb_after_register(), parse_mode="Markdown")


def _send_request_pending(chat_id: int, name: str):
    """Beautiful pending request notification."""
    text = (
        f"📨 *REQUEST SENT*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Hey *{name}*, your request has been sent\n"
        f"to the administrator {ADMIN_USERNAME}\n\n"
        f"⏳ *Waiting for confirmation...*\n\n"
        f"You will be notified as soon as\n"
        f"your access is granted.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_Average response time: a few minutes_"
    )
    bot.send_message(chat_id, text, parse_mode="Markdown")


def _send_admin_request_notification(admin_id: int, uid: int, name: str, uname: str):
    """Beautiful admin notification for new access request."""
    uname_str = f"@{uname}" if uname else f"ID: `{uid}`"
    text = (
        f"📨 *NEW ACCESS REQUEST*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 *Name:*      {name}\n"
        f"🔗 *Username:*  {uname_str}\n"
        f"🆔 *User ID:*   `{uid}`\n"
        f"🕐 *Time:*      {ts()}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Grant or deny access below 👇"
    )
    try:
        bot.send_message(admin_id, text, reply_markup=kb_approve(uid, name), parse_mode="Markdown")
    except Exception as e:
        print(f"[admin notify] err: {e}")


# ══════════════════════════════════════════════════════════════
#   КОМАНДЫ
# ══════════════════════════════════════════════════════════════
# ================================================================
#   REPLY KEYBOARD HANDLER  —  uses BTN_* constants
# ================================================================

def _send_locked_screen(chat_id: int, name: str, uid: int, uname: str = ""):
    """Shows locked screen and sends admin notification."""
    _send_registration_flow(chat_id, name, uname, uid)


@bot.message_handler(func=lambda m: m.text in [
    BTN_AUTO, BTN_ANALYZE, BTN_EXE, BTN_DEEP,
    BTN_V1, BTN_V2, BTN_V3, BTN_V4, BTN_V5, BTN_MULTI,
    BTN_STATS, BTN_MENU
])
@access_required
def handle_menu_button(msg):
    uid  = msg.from_user.id
    text = msg.text

    if text == BTN_STATS:
        cmd_stats(msg); return

    if text == BTN_MENU:
        _send_main_menu(msg.chat.id, msg.from_user.first_name or "user"); return

    state_map = {
        BTN_AUTO:    "waiting_auto",
        BTN_ANALYZE: "waiting_detect",
        BTN_EXE:     "waiting_v3bin",
        BTN_DEEP:    "waiting_deep",
        BTN_V1:      "waiting",
        BTN_V2:      "waiting_v2",
        BTN_V3:      "waiting_v3src",
        BTN_V4:      "waiting_v4",
        BTN_V5:      "waiting_v5",
        BTN_MULTI:   "waiting_multi",
    }
    state = state_map.get(text)
    if not state:
        return

    _deobf_state[uid] = state

    prompts = {
        "waiting_auto": (
            "⚡ *OMEGA AUTO*\n\n"
            "All methods in sequence: `v1 → v4 → v3 → v2`\n\n"
            "📎 Send a `.py` file:"
        ),
        "waiting_detect": (
            "🔬 *CODE ANALYSIS*\n\n"
            "Detects obfuscation type, entropy, complexity.\n\n"
            "📎 Send a `.py` file:"
        ),
        "waiting_v3bin": (
            "📦 *EXE / BINARY UNPACKER*\n\n"
            "PyInstaller · cx Freeze / py2exe\n"
            "zipapp · .pyc · .pyz\n\n"
            "📎 Send `.exe` / `.pyc` / `.pyz` file:"
        ),
        "waiting_deep": (
            "🧬 *DEEP SCAN*\n\n"
            "6-method scan: PyInstaller · ZIP · .pyc magic\n"
            "zlib blocks · base64 payloads · PE strings\n\n"
            "📎 Send `.exe` / `.pyc` file:"
        ),
        "waiting": (
            "🔓 *v1 — Lambda + Exec*\n\n"
            "base64/32/16 · zlib/gzip/lzma\n"
            "Rendy marshal-chain\n\n"
            "📎 Send a `.py` file:"
        ),
        "waiting_v2": (
            "🧠 *v2 — Rendy 2.0 Universal*\n\n"
            "XOR strings · state-machine · call-wrappers\n"
            "dummy vars · N\\*(N+1)%2 blocks\n\n"
            "📎 Send a `.py` file:"
        ),
        "waiting_v3src": (
            "🔧 *v3 — String Decoders*\n\n"
            "MBA · ROT13 · chr() concat · hex escape\n"
            "reversed · eval(compile) · join obf\n\n"
            "📎 Send a `.py` file:"
        ),
        "waiting_v4": (
            "🆕 *v4 — OMEGA Exclusive*\n\n"
            "Substitution · Base58/85 · Format obf\n"
            "Bitwise · AST folding · PyArmor · utf-8 fix\n\n"
            "📎 Send a `.py` file:"
        ),
        "waiting_v5": (
            "🔮 *v5 — ULTRA Engine*\n\n"
            "String tables · Lambda chains · Hex literals\n"
            "Bytearrays · Reduce · Compile/exec unwrap\n"
            "Base91 · Obf imports · Tuple join decode\n"
            "AES-like · Dead code removal · 20 techniques\n\n"
            "📎 Send a `.py` file:"
        ),
        "waiting_multi": (
            "♾️ *MULTI-LAYER DECODER*\n\n"
            "Analyzes code → detects layers → decodes\n"
            "Repeats until code is fully clean.\n"
            "Uses all engines: v1+v2+v3+v4+v5\n\n"
            "⚠️ May take longer for deeply nested code.\n\n"
            "📎 Send a `.py` file:"
        ),
    }

    prompt_text = prompts.get(state, "📎 Send file:")
    bot.send_message(msg.chat.id, prompt_text, reply_markup=kb_deobf(), parse_mode="Markdown")


# ================================================================
#   INLINE CALLBACKS  —  open_menu, menu_back, adm_*
# ================================================================

# ================================================================
#   SUBSCRIPTION & APPROVAL CALLBACKS
# ================================================================

@bot.callback_query_handler(func=lambda c: c.data == "request_access")
def on_request_access(call):
    """User pressed 'Request Access' button."""
    uid   = call.from_user.id
    name  = call.from_user.first_name or "user"
    uname = getattr(call.from_user, "username", "") or ""

    if is_allowed(uid):
        bot.answer_callback_query(call.id, "✅ You already have access!")
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        _send_main_menu(call.message.chat.id, name, is_admin(uid))
        return

    # Send request to all admins
    bot.answer_callback_query(call.id, "📨 Request sent to admin!")
    for admin_id in ADMIN_IDS:
        _send_admin_request_notification(admin_id, uid, name, uname)

    try:
        bot.edit_message_text(
            f"📨 *REQUEST SENT*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Hey *{name}*, your request has been sent\n"
            f"to {ADMIN_USERNAME}.\n\n"
            f"⏳ *Waiting for approval...*\n\n"
            f"_You will be notified once access is granted._",
            call.message.chat.id, call.message.message_id,
            parse_mode="Markdown"
        )
    except: pass



@bot.callback_query_handler(func=lambda c: c.data.startswith("approve_") or c.data.startswith("deny_"))
def on_admin_approve(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "No admin rights!"); return

    parts  = call.data.split("_", 2)
    action = parts[0]

    if action == "approve":
        target_id   = int(parts[1])
        target_name = parts[2] if len(parts) > 2 else f"user_{target_id}"
        uname_save  = ""
        if target_id in pending_subscribe:
            info        = pending_subscribe[target_id]
            target_name = info.get("name", target_name)
            uname_save  = info.get("username", "")

        allowed_users[str(target_id)] = {
            "username": uname_save, "first_name": target_name,
            "added": ts(), "uses": 0, "source": "admin_approve"
        }
        save_users()
        pending_subscribe.pop(target_id, None)

        bot.answer_callback_query(call.id, f"✅ Granted: {target_name}")

        # Update the admin's message
        try:
            bot.edit_message_text(
                f"✅ *ACCESS GRANTED*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 *{target_name}*  (`{target_id}`)\n"
                f"🕐 Time: _{ts()}_\n\n"
                f"_User has been notified._",
                call.message.chat.id, call.message.message_id,
                parse_mode="Markdown"
            )
        except: pass

        # Notify the user with beautiful access screen
        try:
            _anim_typing(target_id, 0.5)
            _send_welcome_media(target_id)
            _anim_typing(target_id, 0.5)
            _send_access_granted(target_id, target_name)
        except: pass

    elif action == "deny":
        target_id   = int(parts[1])
        target_name = pending_subscribe.get(target_id, {}).get("name", f"user_{target_id}")
        pending_subscribe.pop(target_id, None)

        bot.answer_callback_query(call.id, "❌ Request denied")

        try:
            bot.edit_message_text(
                f"❌ *REQUEST DENIED*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 *{target_name}*  (`{target_id}`)\n"
                f"🕐 Time: _{ts()}_",
                call.message.chat.id, call.message.message_id,
                parse_mode="Markdown"
            )
        except: pass

        try:
            bot.send_message(
                target_id,
                f"❌ *ACCESS DENIED*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Your request has been denied.\n\n"
                f"For questions contact {ADMIN_USERNAME}",
                parse_mode="Markdown"
            )
        except: pass


@bot.callback_query_handler(func=lambda c: c.data == "open_menu")
def on_open_menu(call):
    uid  = call.from_user.id
    name = call.from_user.first_name or "user"
    bot.answer_callback_query(call.id)
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    _send_main_menu(call.message.chat.id, name, is_adm=is_admin(uid))


@bot.callback_query_handler(func=lambda c: c.data == "menu_back")
def on_menu_back(call):
    uid  = call.from_user.id
    name = call.from_user.first_name or "user"
    bot.answer_callback_query(call.id)
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    _send_main_menu(call.message.chat.id, name, is_adm=is_admin(uid))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_"))
def on_admin_panel_cb(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "No rights!"); return
    action = call.data
    bot.answer_callback_query(call.id)

    if action == "adm_users":
        cmd_users_inline(call.message)
    elif action == "adm_pending":
        cmd_pending_inline(call.message)
    elif action == "adm_stats":
        total   = len(allowed_users)
        banned  = len(banned_users)
        decoded = global_stats.get("total_decoded", 0)
        xbytes  = global_stats.get("bytes_processed", 0)
        pend    = len(pending_subscribe)
        bot.send_message(
            call.message.chat.id,
            f"📊 *GLOBAL STATS*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"  Users:            *{total}*\n"
            f"  Banned:           *{banned}*\n"
            f"  Pending:          *{pend}*\n"
            f"  Total decoded:    *{decoded}*\n"
            f"  Bytes processed:  *{xbytes:,}*",
            parse_mode="Markdown"
        )
    elif action == "adm_broadcast":
        bot.send_message(
            call.message.chat.id,
            "📢 *BROADCAST*\n\nSend: `/broadcast <message>`",
            parse_mode="Markdown"
        )
    elif action == "adm_settings":
        bot.answer_callback_query(call.id, "Settings coming soon!")


def cmd_users_inline(msg):
    if not allowed_users:
        bot.send_message(msg.chat.id,
            "👥 *USERS*\n\nList is empty.", parse_mode="Markdown"); return
    lines = [f"👥 *USERS* — total: *{len(allowed_users)}*\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for uid, info in list(allowed_users.items())[:30]:
        banned_mark = "🚫" if uid in banned_users else "✅"
        name  = info.get("first_name", "") or uid
        uname = info.get("username", "")
        uses  = info.get("uses", 0)
        src   = info.get("source", "")
        src_ic = "📢" if "channel" in src else "👑" if "admin" in src else "➕"
        ustr  = f" @{uname}" if uname else ""
        lines.append(f"{banned_mark}{src_ic} `{uid}`{ustr} — *{name}* [{uses} files]\n")
    bot.send_message(msg.chat.id, "".join(lines), parse_mode="Markdown")


def cmd_pending_inline(msg):
    if not pending_subscribe:
        bot.send_message(
            msg.chat.id,
            "📨 *PENDING REQUESTS*\n\nNo pending requests ✅",
            parse_mode="Markdown"); return
    text = f"📨 *PENDING REQUESTS* — {len(pending_subscribe)}\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    kb   = telebot.types.InlineKeyboardMarkup()
    for uid, info in list(pending_subscribe.items())[:10]:
        uname = info.get("username", "")
        name  = info.get("name", f"user_{uid}")
        t     = info.get("ts", "")
        ustr  = f"@{uname}" if uname else str(uid)
        text += f"👤 *{name}*  |  {ustr}  |  _{t}_\n"
        kb.row(
            telebot.types.InlineKeyboardButton(f"✅ {name[:12]}", callback_data=f"approve_{uid}_{name[:15]}"),
            telebot.types.InlineKeyboardButton(f"❌ Deny",        callback_data=f"deny_{uid}")
        )
    bot.send_message(msg.chat.id, text, reply_markup=kb, parse_mode="Markdown")


@bot.message_handler(commands=["start"])
def cmd_start(msg):
    try:
        uid   = int(msg.from_user.id)
        name  = msg.from_user.first_name or "user"
        uname = getattr(msg.from_user, "username", "") or ""

        if is_banned(uid):
            bot.send_message(msg.chat.id,
                f"🚫 *You are banned.*\nContact: {ADMIN_USERNAME}", parse_mode="Markdown")
            return

        if is_admin(uid):
            key = str(uid)
            if key not in allowed_users:
                allowed_users[key] = {
                    "username": uname, "first_name": name,
                    "added": ts(), "uses": 0
                }
                save_users()

        if not is_allowed(uid):
            _send_welcome_media(msg.chat.id)
            _anim_typing(msg.chat.id, 0.4)
            _send_locked_screen(msg.chat.id, name, uid, uname)
            return

        key = str(uid)
        if key in allowed_users:
            allowed_users[key]["uses"] = allowed_users[key].get("uses", 0) + 1
            save_users()

        # Send welcome media (GIF or photo)
        _send_welcome_media(msg.chat.id)
        _anim_typing(msg.chat.id, 0.7)

        adm_badge = "  🔑 *ADMIN*" if is_admin(uid) else ""
        # Beautiful welcome message
        text = (
            f"⚡ *SICKSILENT DEOBF* — v3.0 OMEGA\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Welcome, *{name}*!{adm_badge}\n\n"
            f"*50+ Python deobfuscation techniques*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ `OMEGA AUTO`  —  full pipeline\n"
            f"🔓 `v1`  lambda / exec / base64\n"
            f"🧠 `v2`  Rendy 2.0 · 30+ methods\n"
            f"🔧 `v3`  string decoders\n"
            f"🆕 `v4`  OMEGA exclusive · utf-8 fix\n"
            f"🔮 `v5`  ULTRA · 20 exclusive techniques\n"
            f"♾️  `MULTI` multi-layer auto decoder\n"
            f"📦 `EXE` PyInstaller / cxFreeze / py2exe\n"
            f"🧬 `DEEP` 6-method binary scan\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Use the menu below 👇"
        )
        bot.send_message(msg.chat.id, text, reply_markup=kb_main(), parse_mode="Markdown")
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        print(f"[start] ERR: {err}")
        try:
            bot.send_message(msg.chat.id,
                "⚡ sicksilent deobf\n\nSomething went wrong, restarting...\n\nError: " + str(e)[:100])
        except: pass


@bot.message_handler(commands=["deobf"])
@access_required
def cmd_deobf(msg):
    _deobf_state[msg.from_user.id] = "waiting_auto"
    _send(msg.chat.id,
        "╔══════════════════════════════╗\n"
        "║  [*] OMEGA АВТО ДЕОБФУСКАТОР  ║\n"
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
        BANNER_BINARY() + "\n\n"
        "[*] Send .exe / .pyc / .pyz file:",
        md=True)


@bot.message_handler(commands=["deobf4"])
@access_required
def cmd_deobf4(msg):
    _deobf_state[msg.from_user.id] = "waiting_v4"

@bot.message_handler(commands=["deobf5"])
@access_required
def cmd_deobf5(msg):
    _deobf_state[msg.from_user.id] = "waiting_v5"
    bot.send_message(msg.chat.id,
        "🔮 *v5 ULTRA* — 20 exclusive techniques\n\n"
        "String tables · Lambda chains · Hex literals\n"
        "Bytearrays · Reduce · AES-like · Base91\n"
        "PyArmor cleanup · Dead code removal\n\n"
        "📎 Send `.py` file:",
        reply_markup=kb_deobf(), parse_mode="Markdown")


@bot.message_handler(commands=["multi", "multilayer"])
@access_required
def cmd_multi(msg):
    _deobf_state[msg.from_user.id] = "waiting_multi"
    bot.send_message(msg.chat.id,
        "♾️ *MULTI-LAYER DECODER*\n\n"
        "Analyzes code layer by layer.\n"
        "Repeats until fully clean or stable.\n"
        "Uses: v1 + v2 + v3 + v4 + v5\n\n"
        "⚠️ May take 10-30s for complex files\n\n"
        "📎 Send `.py` file:",
        reply_markup=kb_deobf(), parse_mode="Markdown")
    _send(msg.chat.id,
        "╔══════════════════════════════╗\n"
        "║  [NEW] v4 OMEGA EXCLUSIVE       ║\n"
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
        "║  [DEEP] DEEP SCAN OMEGA          ║\n"
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



# ================================================================
#   INLINE DEOBF MODE SELECTOR CALLBACK
# ================================================================

@bot.callback_query_handler(func=lambda c: c.data.startswith("deobf_"))
def on_deobf_callback(call):
    uid  = call.from_user.id
    name = call.from_user.first_name or "user"
    bot.answer_callback_query(call.id)

    if not is_allowed(uid):
        bot.send_message(call.message.chat.id,
            "🔒 No access. Use /start",
            parse_mode="Markdown"); return

    state_map = {
        "deobf_auto":   "waiting_auto",
        "deobf_detect": "waiting_detect",
        "deobf_v1":     "waiting",
        "deobf_v2":     "waiting_v2",
        "deobf_v3src":  "waiting_v3src",
        "deobf_v4":     "waiting_v4",
        "deobf_v5":     "waiting_v5",
        "deobf_multi":  "waiting_multi",
        "deobf_v3bin":  "waiting_v3bin",
        "deobf_deep":   "waiting_deep",
    }
    state = state_map.get(call.data)
    if not state:
        return

    _deobf_state[uid] = state

    prompts = {
        "waiting_auto": (
            "⚡ *OMEGA AUTO*\n\n"
            "Pipeline: `v1 → v4 → v3 → v2`\n\n"
            "📎 Send `.py` file:"
        ),
        "waiting_detect": (
            "🔬 *CODE ANALYSIS*\n\n"
            "Detects obfuscation type and entropy.\n\n"
            "📎 Send `.py` file:"
        ),
        "waiting": (
            "🔓 *v1 — Lambda + Exec*\n\n"
            "base64/32/16 · zlib/gzip/lzma\n\n"
            "📎 Send `.py` file:"
        ),
        "waiting_v2": (
            "🧠 *v2 — Rendy 2.0 Universal*\n\n"
            "XOR · state-machine · 30+ methods\n\n"
            "📎 Send `.py` file:"
        ),
        "waiting_v3src": (
            "🔧 *v3 — String Decoders*\n\n"
            "MBA · ROT13 · chr() · hex · join\n\n"
            "📎 Send `.py` file:"
        ),
        "waiting_v4": (
            "🆕 *v4 — OMEGA Exclusive*\n\n"
            "Base58/85 · AST · PyArmor · utf-8 fix\n\n"
            "📎 Send `.py` file:"
        ),
        "waiting_v3bin": (
            "📦 *EXE / BINARY UNPACKER*\n\n"
            "PyInstaller · cxFreeze / py2exe · .pyc\n\n"
            "📎 Send `.exe` / `.pyc` / `.pyz` file:"
        ),
        "waiting_deep": (
            "🧬 *DEEP SCAN*\n\n"
            "6-method simultaneous scan\n\n"
            "📎 Send `.exe` / `.pyc` file:"
        ),
    }
    prompt = prompts.get(state, "📎 Send file:")

    try:
        bot.edit_message_text(
            prompt,
            call.message.chat.id, call.message.message_id,
            reply_markup=kb_deobf(), parse_mode="Markdown"
        )
    except:
        bot.send_message(
            call.message.chat.id, prompt,
            reply_markup=kb_deobf(), parse_mode="Markdown"
        )


# ══════════════════════════════════════════════════════════════
#   ОБРАБОТКА ДОКУМЕНТОВ
# ══════════════════════════════════════════════════════════════
@bot.message_handler(content_types=["document"])
def handle_document(msg):
    uid = int(msg.from_user.id)
    if not is_allowed(uid):
        bot.send_message(msg.chat.id,
            "🔒 *Access denied.*\nUse /start to register.",
            parse_mode="Markdown"); return

    state = _deobf_state.get(uid)
    if state is None:
        bot.send_message(msg.chat.id,
            "📎 Choose a decode mode first:\n"
            "Use the menu buttons or /deobf",
            reply_markup=kb_deobf(), parse_mode="Markdown"); return

    # Skip already-decoded files
    pass  # check done after code is read

    doc = msg.document; fname = doc.file_name or "file"
    _deobf_state.pop(uid, None)
    _anim_typing(msg.chat.id, 0.3)
    wait = bot.send_message(msg.chat.id,
        f"⏳ *Processing* `{fname}`...",
        parse_mode="Markdown")

    def do():
        try:
            file_info  = bot.get_file(doc.file_id)
            downloaded = bot.download_file(file_info.file_path)

            # ── EXE Binary ──
            if state in ("waiting_v3bin", "waiting_deep"):
                mode_name = "[DEEP] DEEP SCAN" if state == "waiting_deep" else "[EXE] EXE UNPACK"
                _edit(msg.chat.id, wait.message_id,
                    f"╔══════════════════════════════╗\n"
                    f"║  {mode_name}               ║\n"
                    f"╚══════════════════════════════╝\n\n"
                    f"[FILE] Файл: {fname}\n"
                    f"[STAT] Размер: {len(downloaded):,} байт\n"
                    f"🔎 Определяю формат...")

                fmt = v3_detect_format(downloaded)
                _edit(msg.chat.id, wait.message_id,
                    f"[EXE] Формат: {fmt}\n"
                    f"⠴ Извлекаю Python код...")

                if state == "waiting_deep":
                    # Глубокий скан
                    results = exe_v6_extract_all_enhanced(downloaded, fname)
                    report  = exe_deep_scan(downloaded)
                    header  = (
                        f"╔══════════════════════════════╗\n"
                        f"║  [DEEP] DEEP SCAN ЗАВЕРШЁН       ║\n"
                        f"╚══════════════════════════════╝\n\n"
                        f"[FILE] Файл: {fname}\n"
                        f"[EXE] Формат: {fmt}\n"
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
                                caption=f"[DEEP] {method} | {name} | {len(content):,} символов")
                        try: os.remove(out_path)
                        except: pass
                else:
                    results, fmt = v3_deobfuscate_binary(downloaded, fname)
                    _edit(msg.chat.id, wait.message_id,
                        f"╔══════════════════════════════╗\n"
                        f"║  [+] РАСПАКОВАНО!              ║\n"
                        f"╚══════════════════════════════╝\n\n"
                        f"[FILE] {fname}\n"
                        f"[EXE] Формат: {fmt}\n"
                        f"📁 Файлов: {len(results)}")
                    for name, content in results[:10]:
                        if isinstance(content, bytes): content = content.decode('utf-8', errors='replace')
                        out_path = f"/tmp/v3_{name}"
                        with open(out_path, "w", encoding="utf-8") as f: f.write(content)
                        with open(out_path, "rb") as f:
                            bot.send_document(msg.chat.id, f, visible_file_name=name,
                                caption=f"[EXE] {fmt} | {name}")
                        try: os.remove(out_path)
                        except: pass

                record_stat(fmt, len(downloaded))
                return

            # ── Python .py ──
            if not fname.endswith(".py"):
                _edit(msg.chat.id, wait.message_id, f"[EXE] Пробую как бинарный файл...\n[FILE] {fname}")
                results, fmt = v3_deobfuscate_binary(downloaded, fname)
                if results and fmt != "unknown":
                    _edit(msg.chat.id, wait.message_id, f"[+] Распаковано! Формат: {fmt}")
                    for name, content in results[:5]:
                        if isinstance(content, bytes): content = content.decode('utf-8', errors='replace')
                        out_path = f"/tmp/v3_{name}"
                        with open(out_path, "w", encoding="utf-8") as f: f.write(content)
                        with open(out_path, "rb") as f:
                            bot.send_document(msg.chat.id, f, visible_file_name=name, caption=f"[EXE] {fmt}")
                        try: os.remove(out_path)
                        except: pass
                else:
                    _edit(msg.chat.id, wait.message_id, "[-] Только .py для декодера!\nДля EXE/binary — /deobf3 или /deep")
                return

            code = downloaded.decode("utf-8", errors="replace")

            # Skip files that are already decoded or are junk stub files
            already_decoded = [
                "# DECODED BY @ArrhythmiaFucks",
                "# 🔓 DECODED BY",
                "TOGAFF DEOBFUSCATOR",
                "# DECODED BY @ArrhythmiaFucksn",
            ]
            if any(m in code[:300] for m in already_decoded):
                _edit(msg.chat.id, wait.message_id,
                    "⚠️ *File already decoded*\n\n"
                    "This file already contains a decoder header.\n"
                    "It was previously processed by another tool.\n\n"
                    "_Send the original obfuscated file._",
                    md=True
                )
                return

            lines_in = code.count('\n') + 1
            chars_in = len(code)
            analysis = analyze_code_complexity(code)

            # ── Анализ ──
            if state == "waiting_detect":
                _edit(msg.chat.id, wait.message_id, "[SCAN] Анализирую...")
                detected = full_detect_obfuscation(code)
                info = analysis

                bar_length = 20
                score = info['obf_score']
                filled = int(bar_length * score / 100)
                bar = "█" * filled + "░" * (bar_length - filled)

                text = (
                    "🔬 *CODE ANALYSIS*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"[FILE] Файл: {fname}\n"
                    f"📏 Строк: {info['lines']:,}  |  Символов: {info['chars']:,}\n\n"
                    f"[FIX] Структура:\n"
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
                    f"[STAT] Уровень обфускации:\n"
                    f"  [{bar}] {score}%\n"
                    f"  {info['obf_level']}\n\n"
                    f"🎯 Обнаружено:\n  " + "\n  ".join(f"• {d}" for d in detected) + "\n\n"
                    f"💡 Рекомендация: /deobf (OMEGA АВТО)"
                )
                _edit(msg.chat.id, wait.message_id, text, md=True)
                return

            # ── Только v4 ──
            if state == "waiting_v4":
                _edit(msg.chat.id, wait.message_id,
                    f"🆕 *v4 OMEGA* — processing...\n`{fname}`",
                    md=True)
                result = v4_deobfuscate_source(code)
                _send_result(msg.chat.id, wait.message_id, result, doc.file_name,
                             "v4 OMEGA (15 exclusive techniques)", lines_in, chars_in, "v4_")
                record_stat("v4", chars_in)
                return

            # ── v5 ULTRA ──
            if state == "waiting_v5":
                _edit(msg.chat.id, wait.message_id,
                    f"🔮 *v5 ULTRA* — processing...\n`{fname}`",
                    md=True)
                result = v5_deobfuscate_source(code)
                _send_result(msg.chat.id, wait.message_id, result, doc.file_name,
                             "v5 ULTRA (20 exclusive techniques)", lines_in, chars_in, "v5_")
                record_stat("v5", chars_in)
                return

            # ── MULTI-LAYER ──
            if state == "waiting_multi":
                _edit(msg.chat.id, wait.message_id,
                    f"♾️ *MULTI-LAYER DECODER*\n\n"
                    f"File: `{fname}`\n"
                    f"Lines: {lines_in:,} | Score: {analysis['obf_score']}%\n\n"
                    f"Starting layer analysis...",
                    md=True)

                def ml_progress(rnd, max_r, current):
                    pct = int(rnd / max_r * 80)
                    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                    try:
                        _edit(msg.chat.id, wait.message_id,
                            f"♾️ *MULTI-LAYER DECODER*\n\n"
                            f"Round: *{rnd}/{max_r}*\n"
                            f"`[{bar}]` {pct}%\n\n"
                            f"Score: {analyze_code_complexity(current)['obf_score']}% obfuscated\n"
                            f"Size: {len(current):,} chars",
                            md=True)
                    except: pass

                result, rounds_done, methods_used, layers_info = multilayer_deobfuscate(
                    code, max_rounds=10, progress_cb=ml_progress)

                # Build detailed layer report
                layer_report = "\n".join(
                    f"Round {l['round']}: {l['status']} | {l['method']} | "
                    f"score={l['score']}% | {l.get('reduction','0%')} smaller"
                    for l in layers_info
                )

                method_str = f"MULTILAYER ({rounds_done} rounds, methods: {'+'.join(methods_used[:5])})"
                _send_result(msg.chat.id, wait.message_id, result, doc.file_name,
                             method_str, lines_in, chars_in, "multi_")

                # Send layer report
                try:
                    report_text = (
                        f"♾️ *MULTI-LAYER REPORT*\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"File: `{fname}`\n"
                        f"Rounds: *{rounds_done}*\n"
                        f"Methods: `{', '.join(methods_used)}`\n\n"
                        f"*Layer details:*\n"
                    )
                    for l in layers_info:
                        status_emoji = "✅" if l['status'] == 'CLEAN' else "🔓" if l['status'] == 'DECODED' else "➡️"
                        report_text += (
                            f"{status_emoji} *Round {l['round']}*: "
                            f"{l['method']} | score={l['score']}%"
                        )
                        if 'reduction' in l:
                            report_text += f" | {l['reduction']} smaller"
                        report_text += "\n"
                    bot.send_message(msg.chat.id, report_text, parse_mode="Markdown")
                except: pass

                record_stat("multilayer", chars_in)
                return

            # ── Только v3 строки ──
            if state == "waiting_v3src":
                _edit(msg.chat.id, wait.message_id, f"[FIX] v3 Строки...\n[FILE] {fname}")
                result = v3_deobfuscate_source(code)
                _send_result(msg.chat.id, wait.message_id, result, doc.file_name,
                             "v3 (MBA/chr/hex/ROT13/unicode)", lines_in, chars_in, "v3src_")
                record_stat("v3", chars_in)
                return

            # ── Только v2 ──
            if state == "waiting_v2":
                _edit(msg.chat.id, wait.message_id,
                    f"🧠 Ренди 2.0...\n[FILE] {fname}\n"
                    f"[STAT] Строк: {lines_in} | Символов: {chars_in:,}\n"
                    f"🔎 Уровень: {analysis['obf_level']}")
                result = rendy2_deobfuscate(code)
                _send_result(msg.chat.id, wait.message_id, result, doc.file_name,
                             "v2 (Ренди 2.0)", lines_in, chars_in, "rendy2_")
                record_stat("v2", chars_in)
                return

            # ── Только v1 ──
            if state == "waiting":
                _edit(msg.chat.id, wait.message_id, f"🔓 v1 анализ...\n[FILE] {fname}")
                result, info_v1 = deobfuscate_code(code)
                if result:
                    _send_result(msg.chat.id, wait.message_id, result, doc.file_name,
                                 f"v1: {info_v1}", lines_in, chars_in, "decoded_")
                    record_stat(f"v1:{info_v1}", chars_in)
                else:
                    _edit(msg.chat.id, wait.message_id,
                        f"[-] v1 не смог: {info_v1}\n\n"
                        f"Попробуй /deobf (OMEGA АВТО)")
                return

            # ── АВТО OMEGA ──
            progress_bar = lambda p: "█" * int(p/5) + "░" * (20 - int(p/5))
            _edit(msg.chat.id, wait.message_id,
                f"╔══════════════════════════════╗\n"
                f"║  [*] OMEGA АВТО СТАРТ         ║\n"
                f"╚══════════════════════════════╝\n\n"
                f"[FILE] {fname}\n"
                f"[STAT] Строк: {lines_in:,} | Символов: {chars_in:,}\n"
                f"🎯 Уровень: {analysis['obf_level']}\n\n"
                f"[{progress_bar(0)}] 0%\n"
                f"⠋ Запускаю конвейер...")

            time.sleep(0.5)
            _edit(msg.chat.id, wait.message_id,
                f"[FILE] {fname}\n"
                f"[{progress_bar(25)}] 25%\n"
                f"⠹ v1 → v4 → v3 → v2...")

            result, method, stats = auto_deobfuscate_source(code)

            _edit(msg.chat.id, wait.message_id,
                f"[FILE] {fname}\n"
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
            try: _edit(msg.chat.id, wait.message_id, f"[-] Ошибка: {e}")
            except: pass

    threading.Thread(target=do, daemon=True).start()


def _send_result(chat_id, msg_id, result, orig_name, method, lines_in, chars_in, prefix=""):
    lines_out = result.count("\n") + 1
    chars_out = len(result)
    red_l = round(100 * (1 - lines_out / max(lines_in, 1)))
    red_c = round(100 * (1 - chars_out / max(chars_in, 1)))

    lines_r = f"{lines_in:,} -> {lines_out:,}  ({red_l}% smaller)"
    chars_r = f"{chars_in:,} -> {chars_out:,}  ({red_c}% smaller)"

    success_text = (
        f"✅ *DECODE COMPLETE*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📄 *File:*   `{orig_name}`\n"
        f"🔑 *Method:* `{method}`\n\n"
        f"📊 *Lines:*  {lines_r}\n"
        f"💬 *Chars:*  {chars_r}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_sicksilent deobf | @ArrhythmiaFucks_"
    )
    _edit(chat_id, msg_id, success_text, md=True)

    out_name = f"{prefix}{orig_name}"
    out_path = f"/tmp/{out_name}"
    with open(out_path, "w", encoding="utf-8") as f: f.write(result)
    with open(out_path, "rb") as f:
        bot.send_document(chat_id, f, visible_file_name=out_name,
            caption=(
                f"[sicksilent deobf] v{BOT_VERSION}\n"
                f"[METHOD] {method}\n"
                f"[LINES]  {lines_in} -> {lines_out} ({red_l}% smaller)\n"
                f"[CHARS]  {chars_in:,} -> {chars_out:,} ({red_c}% smaller)\n"
                f"@ArrhythmiaFucks"
            ))
    try: os.remove(out_path)
    except: pass


# ══════════════════════════════════════════════════════════════
#   CALLBACK — ПРОВЕРКА ПОДПИСКИ НА КАНАЛ
# ══════════════════════════════════════════════════════════════


@bot.callback_query_handler(func=lambda c: c.data.startswith("approve_") or c.data.startswith("deny_"))
def on_admin_approve(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "No admin rights!"); return

    parts = call.data.split("_", 2)
    action = parts[0]

    if action == "approve":
        target_id  = int(parts[1])
        target_name = parts[2] if len(parts) > 2 else f"user_{target_id}"
        uname_save  = ""
        if target_id in pending_subscribe:
            info = pending_subscribe[target_id]
            target_name = info.get("name", target_name)
            uname_save  = info.get("username", "")

        allowed_users[str(target_id)] = {
            "username": uname_save, "first_name": target_name,
            "added": ts(), "uses": 0, "source": "admin_approve"
        }
        save_users()
        pending_subscribe.pop(target_id, None)
        bot.answer_callback_query(call.id, f"[+] Доступ выдан {target_name}!")
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.send_message(call.message.chat.id, f"[+] [+] Access granted: {target_id} ({target_name})")
        except: pass
        try:
            bot.send_message(target_id,
                f"╔══════════════════════════════╗\n"
                f"║  [+]  ДОСТУП ОТКРЫТ!  [+]      ║\n"
                f"╚══════════════════════════════╝\n\n"
                f"[!] Добро пожаловать в sicksilent deobf!\n\n"
                f"Используй /start 🔓")
        except: pass

    elif action == "deny":
        target_id = int(parts[1])
        pending_subscribe.pop(target_id, None)
        bot.answer_callback_query(call.id, "[-] Заявка отклонена")
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.send_message(call.message.chat.id, f"[-] [-] Denied: {target_id}")
        except: pass
        try:
            bot.send_message(target_id,
                f"[-] Твоя заявка отклонена.\n"
                f"По вопросам: {ADMIN_USERNAME}")
        except: pass


# ══════════════════════════════════════════════════════════════
#   CALLBACK КНОПКИ
# ══════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data.startswith("deobf_"))
def on_deobf_callback(call):
    uid = call.from_user.id
    if not is_allowed(uid): bot.answer_callback_query(call.id, "No access"); return

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
            "waiting_auto":   "[*] OMEGA АВТО — отправь .py файл:",
            "waiting_detect": "[SCAN] Анализ — отправь .py файл:",
            "waiting":        "🔓 v1 — отправь .py файл:",
            "waiting_v2":     "🧠 Ренди 2.0 — отправь .py файл:",
            "waiting_v3src":  "[FIX] v3 Строки — отправь .py файл:",
            "waiting_v3bin":  "[EXE] EXE/Binary — отправь .exe / .pyc / .pyz:",
            "waiting_v4":     "[NEW] v4 OMEGA — отправь .py файл:",
            "waiting_deep":   "[DEEP] Deep Scan — отправь .exe / .pyc:",
        }
        try: bot.edit_message_text(prompts[state], call.message.chat.id, call.message.message_id)
        except: pass
    bot.answer_callback_query(call.id)


# ══════════════════════════════════════════════════════════════
#   ReplyKeyboard кнопки
# ══════════════════════════════════════════════════════════════
@bot.message_handler(func=lambda m: m.text in [
    "🔓 АВТО ДЕКОД", "[SCAN] Анализ файла", "[EXE] EXE / Binary",
    "[DEEP] Глубокое сканирование", "🔓 v1 lambda", "🔓 v2 Ренди",
    "[FIX] v3 Строки", "[NEW] v4 OMEGA", "[STAT] Моя статистика"
])
@access_required
def handle_menu_button(msg):
    uid = msg.from_user.id
    if msg.text == "[STAT] Моя статистика":
        cmd_stats(msg); return

    state_map = {
        "🔓 АВТО ДЕКОД":          "waiting_auto",
        "[SCAN] Анализ файла":        "waiting_detect",
        "[EXE] EXE / Binary":        "waiting_v3bin",
        "[DEEP] Глубокое сканирование": "waiting_deep",
        "🔓 v1 lambda":           "waiting",
        "🔓 v2 Ренди":            "waiting_v2",
        "[FIX] v3 Строки":           "waiting_v3src",
        "[NEW] v4 OMEGA":            "waiting_v4",
    }
    state = state_map.get(msg.text)
    if state:
        _deobf_state[uid] = state
        prompts = {
            "waiting_auto":   "[*] OMEGA АВТО — отправь .py файл:",
            "waiting_detect": "[SCAN] Анализ — отправь .py файл:",
            "waiting_v3bin":  "[EXE] EXE/Binary — отправь .exe / .pyc:",
            "waiting_deep":   "[DEEP] Deep Scan — отправь .exe / .pyc:",
            "waiting":        "🔓 v1 — отправь .py файл:",
            "waiting_v2":     "🧠 Ренди 2.0 — отправь .py файл:",
            "waiting_v3src":  "[FIX] v3 Строки — отправь .py файл:",
            "waiting_v4":     "[NEW] v4 OMEGA — отправь .py файл:",
        }
        bot.send_message(msg.chat.id, prompts[state], reply_markup=kb_deobf())



@bot.message_handler(commands=["stats"])
@access_required
def cmd_stats(msg):
    uid = str(msg.from_user.id)
    user_info   = allowed_users.get(uid, {})
    uses        = user_info.get("uses", 0)
    joined      = user_info.get("added", "unknown")
    total       = global_stats.get("total_decoded", 0)
    total_bytes = global_stats.get("bytes_processed", 0)
    top_methods = sorted(global_stats.get("methods", {}).items(), key=lambda x: -x[1])[:5]

    lvl      = min(uses // 5 + 1, 100)
    xp_bar   = "▓" * min(lvl // 5, 20) + "░" * (20 - min(lvl // 5, 20))
    lvl_name = (
        "👑 ELITE"   if lvl >= 50 else
        "💎 EXPERT"  if lvl >= 25 else
        "⚡ SKILLED" if lvl >= 10 else
        "🔰 ROOKIE"
    )

    text = (
        f"📊 *STATISTICS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 *Your profile:*\n"
        f"  Files decoded:  *{uses}*\n"
        f"  Level:          *{lvl_name}* (lv.{lvl})\n"
        f"  `[{xp_bar}]`\n"
        f"  Member since:   _{joined}_\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌍 *Global stats:*\n"
        f"  Total decoded:  *{total}*\n"
        f"  Bytes processed: *{total_bytes:,}*\n"
    )
    if top_methods:
        text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n🏆 *Top methods:*\n"
        medals = ["🥇", "🥈", "🥉", "4.", "5."]
        for i, (method, count) in enumerate(top_methods):
            short = method[:28] + ("…" if len(method) > 28 else "")
            text += f"  {medals[i]} `{short}` — {count}\n"
    text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n_sicksilent deobf | @ArrhythmiaFucks_"
    bot.send_message(msg.chat.id, text, reply_markup=kb_main(), parse_mode="Markdown")




@bot.message_handler(commands=["pending"])
def cmd_pending(msg):
    if not is_admin(msg.from_user.id): return
    cmd_pending_inline(msg)

@bot.message_handler(commands=["add"])
def cmd_add(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 2: bot.send_message(msg.chat.id, "Использование: /add ID [имя]"); return
    try:
        target_id = int(parts[1]); name = " ".join(parts[2:]) if len(parts) > 2 else f"user_{target_id}"
        allowed_users[str(target_id)] = {"username": "", "first_name": name, "added": ts(), "uses": 0}
        save_users()
        bot.send_message(msg.chat.id, f"✅ *Granted:* `{target_id}` ({name})", parse_mode="Markdown")
        try: _send_access_granted(target_id, name)
        except: pass
    except ValueError: bot.send_message(msg.chat.id, "❌ Invalid ID")

@bot.message_handler(commands=["remove"])
def cmd_remove(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 2: bot.send_message(msg.chat.id, "Использование: /remove ID"); return
    try:
        target_id = str(int(parts[1]))
        if target_id in allowed_users: del allowed_users[target_id]; save_users(); bot.send_message(msg.chat.id, f"✅ *Removed:* `{target_id}`", parse_mode="Markdown")
        else: bot.send_message(msg.chat.id, f"❌ `{target_id}` not found", parse_mode="Markdown")
    except ValueError: bot.send_message(msg.chat.id, "❌ Invalid ID")

@bot.message_handler(commands=["ban"])
def cmd_ban(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 2: bot.send_message(msg.chat.id, "Использование: /ban ID"); return
    try:
        target_id = str(int(parts[1])); banned_users[target_id] = {"banned": ts()}; save_users()
        bot.send_message(msg.chat.id, f"[BAN] Заблокирован: {target_id}")
    except ValueError: bot.send_message(msg.chat.id, "❌ Invalid ID")

@bot.message_handler(commands=["unban"])
def cmd_unban(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 2: bot.send_message(msg.chat.id, "Использование: /unban ID"); return
    try:
        target_id = str(int(parts[1]))
        if target_id in banned_users: del banned_users[target_id]; save_users(); bot.send_message(msg.chat.id, f"[+] Разблокирован: {target_id}")
        else: bot.send_message(msg.chat.id, f"[-] {target_id} не заблокирован")
    except ValueError: bot.send_message(msg.chat.id, "❌ Invalid ID")

@bot.message_handler(commands=["users"])
def cmd_users(msg):
    if not is_admin(msg.from_user.id): return
    cmd_users_inline(msg)


@bot.message_handler(commands=["broadcast"])
def cmd_broadcast(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(msg.chat.id,
            "📢 *BROADCAST*\n\nUsage: `/broadcast <your message>`",
            parse_mode="Markdown"); return
    text = (
        f"📢 *Message from sicksilent deobf*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{parts[1]}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_@ArrhythmiaFucks_"
    )
    sent = 0; failed = 0
    for uid in allowed_users:
        try:
            bot.send_message(int(uid), text, parse_mode="Markdown")
            sent += 1; time.sleep(0.04)
        except: failed += 1
    bot.send_message(msg.chat.id,
        f"✅ *Broadcast done*\n  Sent: *{sent}*  |  Failed: *{failed}*",
        parse_mode="Markdown")




# ══════════════════════════════════════════════════════════════
#   ЗАПУСК
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print()
    print(" ___ ___ ___ _  __ ___ ___ _   ___ _  _ _____ ")
    print("/ __|_ _/ __| |/ // __/ __| | | __| \\| |_   _|")
    print("\\__ \\| | (__ | ' <\\__ \\ __ \\ | | _|| .` | | |  ")
    print("|___/|_|\\___||_|\\_|___/___/_| |___|_|\\_| |_|")
    print()
    print(f"  Admin:   {ADMIN_USERNAME}")
    print(f"  Users:   {len(allowed_users)}")
    print(f"  Decoded: {global_stats.get('total_decoded', 0)}")
    print("+------------------------------------------------+")
    print()
    bot.infinity_polling(timeout=30, long_polling_timeout=20)


e
