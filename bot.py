"""
╔══════════════════════════════════════════════════════════════════════╗
║        🔓 TOGAFF DEOBFUSCATOR BOT v5.0  —  ALL-IN-ONE 🌸           ║
║        by @ArrhythmiaFucksn                                         ║
╠══════════════════════════════════════════════════════════════════════╣
║  pip install pyTelegramBotAPI uncompyle6                            ║
║  python3 togaff_deobf.py                                            ║
╚══════════════════════════════════════════════════════════════════════╝
"""

# ════════════════════════════════════════════════════════════════════
#  IMPORTS
# ════════════════════════════════════════════════════════════════════
import re, base64, zlib, gzip, lzma, bz2, marshal, types, dis, io
import struct, os, sys, codecs, ast, binascii, hashlib, hmac
import threading, subprocess, tempfile, shutil, zipfile, time, json
import itertools, string, random, traceback
from typing import Optional, Tuple, List, Dict, Any
import telebot
from telebot import types as types

# ════════════════════════════════════════════════════════════════════
#  CONFIG
# ════════════════════════════════════════════════════════════════════
TOKEN      = "8603769389:AAFNrImTZhMY0ctceejoFbNkosE54cNsE30"
ADMIN_IDS  = {7321093872}
BOT_NAME   = "Togaff Deobfuscator"
BOT_TAG    = "@ArrhythmiaFucksn"
VERSION    = "5.0"
OPEN_ACCESS = True   # ← True = все могут пользоваться без вайтлиста

USERS_FILE  = "users.json"
BANNED_FILE = "banned.json"
STATS_FILE  = "stats.json"
LOG_FILE    = "activity.log"

ALLOWED_EXT  = {'.py', '.pyc', '.pyw', '.exe', '.pyd', '.so', '.pyz', '.zip'}
MAX_FILE_MB  = 30

# ════════════════════════════════════════════════════════════════════
#  STORAGE
# ════════════════════════════════════════════════════════════════════
def _load(path, default):
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except: pass
    return default

def _save(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass

_lock   = threading.Lock()
users:  dict = _load(USERS_FILE,  {})
banned: set  = set(_load(BANNED_FILE, []))
stats:  dict = _load(STATS_FILE,  {"total_files": 0, "methods": {}, "daily": {}})

def save_all():
    with _lock:
        _save(USERS_FILE,  users)
        _save(BANNED_FILE, list(banned))
        _save(STATS_FILE,  stats)

def log_action(msg: str):
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {msg}\n")
    except: pass

def ts():   return time.strftime("%d.%m %H:%M")
def today(): return time.strftime("%Y-%m-%d")

def is_admin(uid):  return int(uid) in ADMIN_IDS
def is_banned(uid): return int(uid) in {int(b) for b in banned}

def is_allowed(uid):
    if OPEN_ACCESS: return not is_banned(int(uid))
    uid = int(uid)
    if is_admin(uid): return True
    if is_banned(uid): return False
    return str(uid) in users or uid in users

def ensure_user(uid, name, uname):
    key = str(uid)
    if key not in users:
        users[key] = {"name": name, "username": uname, "added": ts(),
                      "files": 0, "role": "admin" if is_admin(uid) else "user", "methods": {}}
        stats["total_files"] = stats.get("total_files", 0)
        save_all()

def update_stats(method: str):
    stats["total_files"] = stats.get("total_files", 0) + 1
    stats.setdefault("methods", {})[method] = stats["methods"].get(method, 0) + 1
    d = stats.setdefault("daily", {})
    d[today()] = d.get(today(), 0) + 1

# ════════════════════════════════════════════════════════════════════
#  ENGINE UTILS
# ════════════════════════════════════════════════════════════════════
DEOBF_TAG = "# 🔓 DECODED BY @ArrhythmiaFucksn | TOGAFF DEOBFUSCATOR v5.0\n\n"

def _b64_pad(s: str) -> str:
    pad = len(s) % 4
    return s + "=" * (4 - pad) if pad else s

def _safe_decode(data: bytes) -> str:
    for enc in ("utf-8", "utf-16-le", "utf-16-be", "latin-1", "cp1251", "cp1252"):
        try: return data.decode(enc)
        except: pass
    return data.decode("utf-8", errors="replace")

def _is_python(text: str, min_len: int = 30) -> bool:
    if len(text) < min_len: return False
    kws = ["def ", "class ", "import ", "print(", "return ", "if ", "for ", "while ",
           "__name__", "self.", "lambda ", "= "]
    return sum(1 for k in kws if k in text) >= 2

def _clean(code: str) -> str:
    code = re.sub(r'\n{4,}', '\n\n\n', code)
    code = re.sub(r'[ \t]+\n', '\n', code)
    return code.strip()

def _strip_comments(code: str) -> str:
    result = []
    for line in code.split("\n"):
        in_s = in_d = False
        out = []; i = 0
        while i < len(line):
            c = line[i]
            if c == "\\" and i + 1 < len(line):
                out.append(c); out.append(line[i+1]); i += 2; continue
            if c == "'" and not in_d: in_s = not in_s
            elif c == '"' and not in_s: in_d = not in_d
            elif c == "#" and not in_s and not in_d: break
            out.append(c); i += 1
        result.append("".join(out).rstrip())
    return "\n".join(result)

def _marshal_loads_safe(data: bytes):
    for offset in (0, 4, 8, 12, 16, 20):
        try: return marshal.loads(data[offset:])
        except: pass
    return None

def _try_marshal_to_source(code_obj) -> Optional[str]:
    for lib in ("uncompyle6", "decompile3"):
        try:
            m = __import__(lib)
            buf = io.StringIO()
            if hasattr(m, 'decompile_code'): m.decompile_code(code_obj, buf)
            elif hasattr(m, 'decompile'): m.decompile(sys.version_info[:2], code_obj, buf)
            r = buf.getvalue()
            if r and len(r) > 5: return r
        except: pass
    try:
        buf = io.StringIO()
        dis.dis(code_obj, file=buf)
        return f"# [bytecode disassembly — install uncompyle6 for source]\n{buf.getvalue()}"
    except: pass
    return None

# ════════════════════════════════════════════════════════════════════
#  V1 — BASE ENCODINGS + COMPRESSION  (из оригинального CLI)
# ════════════════════════════════════════════════════════════════════

# Точные паттерны из оригинального деобфускатора
_EXEC_PAT     = re.compile(r"exec\(\(_\)\(b'(.+?)'\)\)")
_EXEC_PAT2    = re.compile(r"exec\s*\(\s*\(?\s*_+\s*\)?\s*\(\s*b['\"](.+?)['\"]\s*\)\s*\)", re.DOTALL)
_EXEC_PAT3    = re.compile(r"exec\s*\(\s*_+\s*\(\s*b?['\"](.+?)['\"]", re.DOTALL)
_COMMENTS_PAT = re.compile(r"#[^\n]*\n")

_V1_LAMBDA_PATTERNS = {
    "base64":     r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b64decode\(__\[::-1\]\);?",
    "base32":     r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b32decode\(__\[::-1\]\);?",
    "base16":     r"_\s*=\s*lambda\s*__\s*:\s*__import__\('base64'\)\.b16decode\(__\[::-1\]\);?",
    "zlib":       r"_\s*=\s*lambda\s*__\s*:\s*__import__\('zlib'\)\.decompress\(__\[::-1\]\);?",
    "gzip":       r"_\s*=\s*lambda\s*__\s*:\s*__import__\('gzip'\)\.decompress\(__\[::-1\]\);?",
    "lzma":       r"_\s*=\s*lambda\s*__\s*:\s*__import__\('lzma'\)\.decompress\(__\[::-1\]\);?",
    "bz2":        r"_\s*=\s*lambda\s*__\s*:\s*__import__\('bz2'\)\.decompress\(__\[::-1\]\);?",
    "base64+zlib":r"_\s*=\s*lambda\s*__\s*:\s*__import__\('zlib'\)\.decompress\(s*__import__\('base64'\)\.b64decode\(__\[::-1\]\)\);?",
    "base64+gzip":r"_\s*=\s*lambda\s*__\s*:\s*__import__\('gzip'\)\.decompress\(s*__import__\('base64'\)\.b64decode\(__\[::-1\]\)\);?",
    "base64+lzma":r"_\s*=\s*lambda\s*__\s*:\s*__import__\('lzma'\)\.decompress\(s*__import__\('base64'\)\.b64decode\(__\[::-1\]\)\);?",
    "base32+zlib":r"_\s*=\s*lambda\s*__\s*:\s*__import__\('zlib'\)\.decompress\(s*__import__\('base64'\)\.b32decode\(__\[::-1\]\)\);?",
    "base32+gzip":r"_\s*=\s*lambda\s*__\s*:\s*__import__\('gzip'\)\.decompress\(s*__import__\('base64'\)\.b32decode\(__\[::-1\]\)\);?",
    "base32+lzma":r"_\s*=\s*lambda\s*__\s*:\s*__import__\('lzma'\)\.decompress\(s*__import__\('base64'\)\.b32decode\(__\[::-1\]\)\);?",
    "base16+zlib":r"_\s*=\s*lambda\s*__\s*:\s*__import__\('zlib'\)\.decompress\(s*__import__\('base64'\)\.b16decode\(__\[::-1\]\)\);?",
    "base16+gzip":r"_\s*=\s*lambda\s*__\s*:\s*__import__\('gzip'\)\.decompress\(s*__import__\('base64'\)\.b16decode\(__\[::-1\]\)\);?",
    "base16+lzma":r"_\s*=\s*lambda\s*__\s*:\s*__import__\('lzma'\)\.decompress\(s*__import__\('base64'\)\.b16decode\(__\[::-1\]\)\);?",
    "base64+bz2": r"_\s*=\s*lambda\s*__\s*:\s*__import__\('bz2'\)\.decompress\(s*__import__\('base64'\)\.b64decode\(__\[::-1\]\)\);?",
    "rendy":      r"_=lambda __:__import__\('marshal'\)\.loads\(__import__\('gzip'\)\.decompress\(__import__\('lzma'\)\.decompress\(__import__\('zlib'\)\.decompress\(__import__\('base64'\)\.b64decode\(__\[::-1\]\)\)\)\)\);",
}

_V1_DECODE_MAP = {
    "base64":     lambda s: _safe_decode(base64.b64decode(_b64_pad(s[::-1]))),
    "base32":     lambda s: _safe_decode(base64.b32decode(_b64_pad(s[::-1]).upper())),
    "base16":     lambda s: _safe_decode(base64.b16decode(s[::-1].upper())),
    "zlib":       lambda s: _safe_decode(zlib.decompress(s.encode("latin-1")[::-1])),
    "gzip":       lambda s: _safe_decode(gzip.decompress(s.encode("latin-1")[::-1])),
    "lzma":       lambda s: _safe_decode(lzma.decompress(s.encode("latin-1")[::-1])),
    "bz2":        lambda s: _safe_decode(bz2.decompress(s.encode("latin-1")[::-1])),
    "base64+zlib":lambda s: _safe_decode(zlib.decompress(base64.b64decode(_b64_pad(s[::-1])))),
    "base64+gzip":lambda s: _safe_decode(gzip.decompress(base64.b64decode(_b64_pad(s[::-1])))),
    "base64+lzma":lambda s: _safe_decode(lzma.decompress(base64.b64decode(_b64_pad(s[::-1])))),
    "base64+bz2": lambda s: _safe_decode(bz2.decompress(base64.b64decode(_b64_pad(s[::-1])))),
    "base32+zlib":lambda s: _safe_decode(zlib.decompress(base64.b32decode(_b64_pad(s[::-1]).upper()))),
    "base32+gzip":lambda s: _safe_decode(gzip.decompress(base64.b32decode(_b64_pad(s[::-1]).upper()))),
    "base32+lzma":lambda s: _safe_decode(lzma.decompress(base64.b32decode(_b64_pad(s[::-1]).upper()))),
    "base16+zlib":lambda s: _safe_decode(zlib.decompress(base64.b16decode(s[::-1].upper()))),
    "base16+gzip":lambda s: _safe_decode(gzip.decompress(base64.b16decode(s[::-1].upper()))),
    "base16+lzma":lambda s: _safe_decode(lzma.decompress(base64.b16decode(s[::-1].upper()))),
}

def _v1_detect(code: str) -> Optional[str]:
    for name, pat in _V1_LAMBDA_PATTERNS.items():
        if re.search(pat, code, re.DOTALL): return name
    return None

def _v1_rendy(code: str) -> Optional[str]:
    rendy_exec = re.compile(
        r"_=lambda __:__import__\('marshal'\)\.loads\(__import__\('gzip'\)\.decompress\("
        r"__import__\('lzma'\)\.decompress\(__import__\('zlib'\)\.decompress\("
        r"__import__\('base64'\)\.b64decode\(__\[::-1\]\)\)\)\)\);"
        r"exec\(_\('(.*?)'\)\)"
    )
    m = rendy_exec.search(code)
    if not m: return None
    encoded = m.group(1)
    combos = [
        lambda d: marshal.loads(gzip.decompress(lzma.decompress(zlib.decompress(base64.b64decode(_b64_pad(d[::-1])))))),
        lambda d: marshal.loads(zlib.decompress(lzma.decompress(gzip.decompress(base64.b64decode(_b64_pad(d[::-1])))))),
        lambda d: marshal.loads(lzma.decompress(gzip.decompress(zlib.decompress(base64.b64decode(_b64_pad(d[::-1])))))),
        lambda d: marshal.loads(zlib.decompress(base64.b64decode(_b64_pad(d[::-1])))),
        lambda d: marshal.loads(gzip.decompress(base64.b64decode(_b64_pad(d[::-1])))),
    ]
    for fn in combos:
        try:
            obj = fn(encoded)
            if isinstance(obj, bytes): return _safe_decode(obj)
            if isinstance(obj, types.CodeType):
                src = _try_marshal_to_source(obj)
                if src: return src
        except: pass
    return None

def _v1_apply(code: str, method: str) -> str:
    decode_fn = _V1_DECODE_MAP.get(method)
    if not decode_fn: return code
    changed = True
    passes = 0
    while changed and passes < 30:
        changed = False; passes += 1
        for pat in [_EXEC_PAT, _EXEC_PAT2, _EXEC_PAT3]:
            def make_rep(fn):
                def rep(m):
                    try: return fn(m.group(1))
                    except Exception as e: return f"# [decode_err: {e}]\n"
                return rep
            new = pat.sub(make_rep(decode_fn), code)
            if new != code: code = new; changed = True
    # Remove lambda definition
    for pat in _V1_LAMBDA_PATTERNS.values():
        code = re.sub(pat, "", code, flags=re.DOTALL)
    # Remove comments
    code = _COMMENTS_PAT.sub("", code)
    return _clean(code)

def deobfuscate_v1(code: str) -> Tuple[Optional[str], str]:
    method = _v1_detect(code)
    if not method: return None, "v1: паттерн не обнаружен"
    if method == "rendy":
        result = _v1_rendy(code)
        if result: return DEOBF_TAG + result, "rendy"
        return None, "rendy: не удалось декодировать"
    try:
        result = _v1_apply(code, method)
        if result and result.strip() != code.strip():
            return DEOBF_TAG + result, method
        return None, f"v1({method}): не изменилось"
    except Exception as e:
        return None, f"v1 error: {e}"

# ════════════════════════════════════════════════════════════════════
#  V2 — РЕНДИ 2.0 UNIVERSAL
# ════════════════════════════════════════════════════════════════════

def _r2_decompress_chain(data: bytes, depth=0, max_depth=16) -> bytes:
    if depth >= max_depth: return data
    for fn in [
        lambda d: base64.b64decode(d + b"=="),
        lambda d: base64.b64decode(d[::-1] + b"=="),
        zlib.decompress, gzip.decompress, lzma.decompress, bz2.decompress,
    ]:
        try:
            r = fn(data)
            if r and r != data and len(r) > 5:
                deeper = _r2_decompress_chain(r, depth+1, max_depth)
                return deeper if deeper != r else r
        except: pass
    obj = _marshal_loads_safe(data)
    if obj:
        if isinstance(obj, bytes): return _r2_decompress_chain(obj, depth+1, max_depth)
        if isinstance(obj, types.CodeType):
            src = _try_marshal_to_source(obj)
            if src: return src.encode()
    return data

def _r2_extract_blobs(source: str) -> List[str]:
    results = []
    for pat in [r"b['\"]([A-Za-z0-9+/=\r\n]{80,})['\"]", r"['\"]([A-Za-z0-9+/=\r\n]{200,})['\"]"]:
        for m in re.finditer(pat, source, re.DOTALL):
            candidate = re.sub(r'[\r\n\s]', '', m.group(1))
            for variant in [candidate, candidate[::-1], _b64_pad(candidate), _b64_pad(candidate[::-1])]:
                try:
                    result = _r2_decompress_chain(variant.encode())
                    text = _safe_decode(result)
                    if _is_python(text, 80): results.append(text)
                except: pass
    return results

def _r2_decode_xor(source: str) -> str:
    # bytes([b ^ KEY for b in bytes.fromhex('...')])
    for pat in [
        re.compile(r'bytes\(\[b\s*\^\s*\((\d+)\s*\^\s*\d+\)\s+for\s+b\s+in\s+bytes\.fromhex\([\'"]([0-9a-fA-F]+)[\'"]\)\]\)(?:\.decode\([^)]*\))?'),
        re.compile(r'bytes\(\[b\s*\^\s*(\d+)\s+for\s+b\s+in\s+bytes\.fromhex\([\'"]([0-9a-fA-F]+)[\'"]\)\]\)(?:\.decode\([^)]*\))?'),
        re.compile(r'bytes\(\[i\s*\^\s*(\d+)\s+for\s+i\s+in\s+bytes\.fromhex\([\'"]([0-9a-fA-F]+)[\'"]\)\]\)(?:\.decode\([^)]*\))?'),
    ]:
        def rep(m):
            try:
                key = int(m.group(1))
                return repr(bytes([b ^ key for b in bytes.fromhex(m.group(2))]).decode("utf-8", errors="replace"))
            except: return m.group(0)
        source = pat.sub(rep, source)
    # bytes([x ^ KEY for x in [N, N, N, ...]])
    arr_pat = re.compile(r'bytes\(\[(?:x|b|i|c)\s*\^\s*(\d+)\s+for\s+(?:x|b|i|c)\s+in\s+\[([0-9,\s]+)\]\]\)')
    def arr_rep(m):
        try:
            key = int(m.group(1))
            nums = [int(x.strip()) for x in m.group(2).split(",") if x.strip()]
            return repr(bytes([n ^ key for n in nums]).decode("utf-8", errors="replace"))
        except: return m.group(0)
    source = arr_pat.sub(arr_rep, source)
    return source

def _r2_decode_hex_escapes(source: str) -> str:
    for pat in [
        re.compile(r"b'((?:\\x[0-9a-fA-F]{2}){4,})'"),
        re.compile(r'b"((?:\\x[0-9a-fA-F]{2}){4,})"'),
    ]:
        def rep(m):
            try: return repr(_safe_decode(bytes.fromhex(re.sub(r'\\x','', m.group(1)))))
            except: return m.group(0)
        source = pat.sub(rep, source)
    return source

def _r2_decode_unicode_escapes(source: str) -> str:
    def rep(m):
        try: return repr(m.group(1).encode().decode("unicode_escape"))
        except: return m.group(0)
    return re.compile(r"'((?:\\u[0-9a-fA-F]{4}){3,})'").sub(rep, source)

def _r2_decode_b64_arrays(source: str) -> str:
    pat = re.compile(r'(\w+)\s*=\s*\[([\'"][A-Za-z0-9+/=]+[\'"](?:\s*,\s*[\'"][A-Za-z0-9+/=]+[\'"])+)\s*\]')
    for m in pat.finditer(source):
        var = m.group(1)
        items = re.findall(r'[\'"]([A-Za-z0-9+/=]+)[\'"]', m.group(2))
        decoded = []
        ok = True
        for item in items:
            try: decoded.append(base64.b64decode(_b64_pad(item)).decode("utf-8"))
            except: ok = False; break
        if ok and decoded:
            for idx, val in enumerate(decoded):
                source = re.sub(re.escape(var) + r'\s*\[\s*' + str(idx) + r'\s*\]', repr(val), source)
    return source

def _r2_decode_chr_arrays(source: str) -> str:
    # chr(72)+chr(101)+... chains
    chr_plus = re.compile(r'(chr\s*\(\s*\d+\s*\)(?:\s*\+\s*chr\s*\(\s*\d+\s*\)){2,})')
    def rep(m):
        nums = re.findall(r'chr\s*\(\s*(\d+)\s*\)', m.group(1))
        try: return repr("".join(chr(int(n)) for n in nums))
        except: return m.group(0)
    source = chr_plus.sub(rep, source)
    # ''.join([chr(x) for x in [...]])
    join_pat = re.compile(r"['\"]?\s*['\"]?\s*\.join\s*\(\s*\[?((?:chr\s*\(\s*\d+\s*\)\s*(?:,\s*)?){3,})\]?\s*\)")
    def rep2(m):
        nums = re.findall(r'chr\s*\(\s*(\d+)\s*\)', m.group(1))
        try: return repr("".join(chr(int(n)) for n in nums))
        except: return m.group(0)
    return join_pat.sub(rep2, source)

def _r2_simplify_wrappers(source: str) -> str:
    names = list(set(re.findall(r'def\s+(\w+)\s*\(\s*\w+\s*,\s*\w+\s*,\s*\w+\s*\)', source)))
    for wname in names:
        if len(wname) < 3: continue
        for _ in range(8):
            new = re.sub(
                re.escape(wname) + r'\s*\(\s*([^,\n]+?)\s*,\s*\[([^\[\]\n]*?)\]\s*,\s*\{\s*\}\s*\)',
                lambda m: f'{m.group(1).strip()}({m.group(2).strip()})',
                source
            )
            if new == source: break
            source = new
    return source

def _r2_remove_state_machine(source: str) -> str:
    lines = source.split('\n'); result = []; i = 0
    while i < len(lines):
        s = lines[i].strip()
        if re.match(r'^while\s+\w+\s*!=\s*\d+\s*:\s*$', s): i += 1; continue
        if re.match(r'^(?:if|elif)\s+\w+\s*==\s*\d{4,}\s*:\s*$', s): i += 1; continue
        if re.match(r'^\w+\s*=\s*\d{5,}\s*$', s): i += 1; continue
        result.append(lines[i]); i += 1
    return '\n'.join(result)

def _r2_remove_dummies(source: str) -> str:
    result = []
    for line in source.split('\n'):
        s = line.strip()
        m = re.match(r'^(\w+)\s*=\s*(?:\d+|None|True|False|["\'][^"\']{0,20}["\'])\s*$', s)
        if m:
            vname = m.group(1)
            if (vname.startswith('_') and vname.count('_') >= 2) or re.match(r'^[a-z]{1,3}[0-9]+$', vname):
                if len(re.findall(r'\b' + re.escape(vname) + r'\b', source)) <= 2: continue
        result.append(line)
    return '\n'.join(result)

def _r2_decode_octal(source: str) -> str:
    pat = re.compile(r"b'((?:\\[0-7]{1,3}){4,})'")
    def rep(m):
        try:
            raw = bytes([int(x, 8) for x in re.findall(r'\\([0-7]{1,3})', m.group(1))])
            return repr(_safe_decode(raw))
        except: return m.group(0)
    return pat.sub(rep, source)

def _r2_simplify_getattr(source: str) -> str:
    source = re.sub(r"getattr\((\w+),\s*['\"]([a-zA-Z_]\w*)['\"](?:,\s*None)?\)", r"\1.\2", source)
    return source

def deobfuscate_v2(source: str) -> str:
    original = source
    blobs = _r2_extract_blobs(source)
    if blobs:
        best = max(blobs, key=len)
        if len(best) > max(len(source) * 0.25, 100): source = best
    source = _r2_decode_xor(source)
    source = _r2_decode_hex_escapes(source)
    source = _r2_decode_unicode_escapes(source)
    source = _r2_decode_b64_arrays(source)
    source = _r2_decode_chr_arrays(source)
    source = _r2_decode_octal(source)
    source = _r2_simplify_wrappers(source)
    source = _r2_remove_state_machine(source)
    source = _r2_remove_dummies(source)
    source = _r2_simplify_getattr(source)
    source = _clean(source)
    return DEOBF_TAG + source

# ════════════════════════════════════════════════════════════════════
#  V3 — POPULAR ADVANCED METHODS
# ════════════════════════════════════════════════════════════════════

def _v3_rot13(code: str) -> Tuple[Optional[str], str]:
    for pat in [
        re.compile(r"exec\s*\(\s*codecs\.decode\s*\(['\"](.+?)['\"]\s*,\s*['\"]rot[_-]?13['\"]\s*\)\s*\)", re.DOTALL),
        re.compile(r"exec\s*\(\s*['\"](.+?)['\"]\s*\.encode\(\)\s*\.decode\s*\(['\"]rot[_-]?13['\"]\s*\)\s*\)", re.DOTALL),
    ]:
        m = pat.search(code)
        if m:
            try: return DEOBF_TAG + codecs.decode(m.group(1), 'rot_13'), "rot13"
            except: pass
    return None, ""

def _v3_xor_fixed(code: str) -> Tuple[Optional[str], str]:
    pats = [
        re.compile(r"exec\s*\(\s*bytes\s*\(\s*\[\s*b\s*\^\s*(\d+)\s+for\s+b\s+in\s+bytes\.fromhex\s*\(\s*['\"]([0-9a-fA-F]+)['\"]\s*\)\s*\]\s*\)\s*\)"),
        re.compile(r"exec\s*\(\s*bytes\s*\(\s*\[\s*b\s*\^\s*(\d+)\s+for\s+b\s+in\s+b['\"](.+?)['\"]\s*\]\s*\)\s*\)"),
    ]
    for pat in pats:
        m = pat.search(code)
        if m:
            try:
                key = int(m.group(1))
                raw = bytes.fromhex(m.group(2)) if re.match(r'^[0-9a-fA-F]+$', m.group(2)) else m.group(2).encode("latin-1").decode("unicode_escape").encode("latin-1")
                dec = _safe_decode(bytes([b ^ key for b in raw]))
                if _is_python(dec): return DEOBF_TAG + dec, "xor-fixed-key"
            except: pass
    return None, ""

def _v3_plain_b64(code: str) -> Tuple[Optional[str], str]:
    for pat in [
        re.compile(r"exec\s*\(\s*base64\.b64decode\s*\(\s*b?['\"]([A-Za-z0-9+/=]{20,})['\"]", re.DOTALL),
        re.compile(r"exec\s*\(\s*__import__\(['\"]base64['\"]\)\.b64decode\s*\(\s*b?['\"]([A-Za-z0-9+/=]{20,})['\"]", re.DOTALL),
    ]:
        for m in pat.finditer(code):
            enc = m.group(1).replace("\n","").replace(" ","")
            try:
                result = base64.b64decode(_b64_pad(enc)).decode("utf-8")
                # Multi-layer
                for _ in range(20):
                    m2 = re.search(r"exec\s*\(\s*base64\.b64decode\s*\(\s*b?['\"]([A-Za-z0-9+/=]{20,})['\"]", result)
                    if not m2: break
                    try: result = base64.b64decode(_b64_pad(m2.group(1))).decode("utf-8")
                    except: break
                if len(result) > 5: return DEOBF_TAG + result, "plain-base64"
            except: pass
    return None, ""

def _v3_hex_exec(code: str) -> Tuple[Optional[str], str]:
    m = re.search(r"exec\s*\(\s*['\"]([\\x0-9a-fA-F\\u0-9a-fA-F]{20,})['\"]", code)
    if m:
        try:
            raw = m.group(1).encode("latin-1").decode("unicode_escape")
            if _is_python(raw): return DEOBF_TAG + raw, "hex-exec"
        except: pass
    return None, ""

def _v3_compile_marshal(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"marshal\.loads\s*\(\s*(?:(?:zlib|gzip|lzma)\.decompress\s*\()?(?:base64\.b64decode\s*\()?\s*b?['\"]([A-Za-z0-9+/=\n]+)['\"]\)?(?:\))?\s*\)")
    for m in pat.finditer(code, re.DOTALL):
        enc = re.sub(r'\s','', m.group(1))
        for transform in [
            lambda x: base64.b64decode(_b64_pad(x)),
            lambda x: zlib.decompress(base64.b64decode(_b64_pad(x))),
            lambda x: gzip.decompress(base64.b64decode(_b64_pad(x))),
            lambda x: lzma.decompress(base64.b64decode(_b64_pad(x))),
            lambda x: base64.b64decode(_b64_pad(x[::-1])),
        ]:
            try:
                raw = transform(enc)
                obj = _marshal_loads_safe(raw)
                if obj and isinstance(obj, types.CodeType):
                    src = _try_marshal_to_source(obj)
                    if src: return DEOBF_TAG + src, "compile+marshal"
            except: pass
    return None, ""

def _v3_chr_obfuscate(code: str) -> Tuple[Optional[str], str]:
    count = len(re.findall(r'\bchr\s*\(\s*\d+\s*\)', code))
    if count < 5: return None, ""
    result = re.sub(r'chr\s*\(\s*(\d+)\s*\)', lambda m: repr(chr(int(m.group(1)))), code)
    for _ in range(10):
        new = re.sub(r"'([^'\\]*)'\s*\+\s*'([^'\\]*)'", lambda m: repr(m.group(1)+m.group(2)), result)
        if new == result: break
        result = new
    if result != code:
        return DEOBF_TAG + f"# chr() unrolled: {count} calls\n\n" + result, f"chr-obfuscate ({count})"
    return None, ""

def _v3_pyarmor(code: str) -> Tuple[Optional[str], str]:
    if "__pyarmor__" not in code and "pyarmor_runtime" not in code: return None, ""
    result = re.sub(r"from\s+pyarmor_runtime\s+import.*?\n", "", code)
    result = re.sub(r"import\s+pyarmor_runtime.*?\n", "", result)
    result = re.sub(r"__pyarmor__\s*\([^)]+\)", "# [PyArmor call removed]", result)
    return DEOBF_TAG + "# ⚠️ PyArmor — partial decode (no runtime key)\n\n" + result, "pyarmor (partial)"

def _v3_reverse_string(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"exec\s*\(\s*['\"](.{30,})['\"](?:\s*\.\s*encode\(\))?\s*\[\s*::-1\s*\]\s*(?:\.decode\([^)]*\))?\s*\)")
    m = pat.search(code)
    if m:
        dec = m.group(1)[::-1]
        if _is_python(dec): return DEOBF_TAG + dec, "reverse-string"
    return None, ""

def _v3_decimal_array(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"exec\s*\(\s*['\"]?\s*['\"]?\s*\.join\s*\(\s*map\s*\(\s*chr\s*,\s*\[([0-9,\s]+)\]\s*\)\s*\)")
    m = pat.search(code)
    if m:
        try:
            nums = [int(x.strip()) for x in m.group(1).split(",") if x.strip()]
            dec = "".join(chr(n) for n in nums)
            if _is_python(dec): return DEOBF_TAG + dec, "map-chr"
        except: pass
    return None, ""

def _v3_lambda_chain(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"\(lambda\s+\w+\s*:.*?exec.*?\)\s*\(\s*['\"]([A-Za-z0-9+/=]{30,})['\"]", re.DOTALL)
    m = pat.search(code)
    if m:
        enc = m.group(1).replace("\n","")
        for fn in [
            lambda x: base64.b64decode(_b64_pad(x)).decode(),
            lambda x: zlib.decompress(base64.b64decode(_b64_pad(x))).decode(),
        ]:
            try:
                dec = fn(enc)
                if _is_python(dec): return DEOBF_TAG + dec, "lambda-chain"
            except: pass
    return None, ""

def _v3_base85(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"exec\s*\(\s*(?:base64\.b85decode|__import__\(['\"]base64['\"]\)\.b85decode)\s*\(\s*b?['\"](.{20,})['\"]")
    m = pat.search(code)
    if m:
        try:
            dec = base64.b85decode(m.group(1)).decode("utf-8")
            if _is_python(dec): return DEOBF_TAG + dec, "base85"
        except: pass
    return None, ""

def _v3_integer_encoded(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"exec\s*\(\s*\((\d{10,})\)\.to_bytes\s*\(\s*(\d+)\s*,\s*['\"](?:big|little)['\"]\s*\)(?:\.decode\([^)]*\))?\s*\)")
    m = pat.search(code)
    if m:
        try:
            dec = int(m.group(1)).to_bytes(int(m.group(2)), 'big').decode("utf-8")
            if _is_python(dec): return DEOBF_TAG + dec, "integer-encoded"
        except: pass
    return None, ""

def _v3_eval_b64(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"eval\s*\(\s*base64\.b64decode\s*\(\s*b?['\"]([A-Za-z0-9+/=]{20,})['\"]")
    m = pat.search(code)
    if m:
        try:
            dec = base64.b64decode(_b64_pad(m.group(1))).decode("utf-8")
            if len(dec) > 5: return DEOBF_TAG + dec, "eval-base64"
        except: pass
    return None, ""

def _v3_hex_fromhex(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"exec\s*\(\s*bytes\.fromhex\s*\(\s*['\"]([0-9a-fA-F]{20,})['\"]\s*\)(?:\.decode\([^)]*\))?\s*\)")
    m = pat.search(code)
    if m:
        try:
            dec = _safe_decode(bytes.fromhex(m.group(1)))
            if _is_python(dec): return DEOBF_TAG + dec, "hex-fromhex"
        except: pass
    return None, ""

def _v3_bz2_plain(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"exec\s*\(\s*bz2\.decompress\s*\(\s*base64\.b64decode\s*\(\s*b?['\"]([A-Za-z0-9+/=]{20,})['\"]")
    m = pat.search(code)
    if m:
        try:
            dec = _safe_decode(bz2.decompress(base64.b64decode(_b64_pad(m.group(1)))))
            if _is_python(dec): return DEOBF_TAG + dec, "bz2"
        except: pass
    return None, ""

def _v3_pyc_decompile(pyc_data: bytes) -> Tuple[Optional[str], str]:
    for lib in ("uncompyle6",):
        try:
            mod = __import__(lib)
            with tempfile.NamedTemporaryFile(suffix=".pyc", delete=False) as f:
                f.write(pyc_data); fname = f.name
            buf = io.StringIO()
            mod.decompile_file(fname, buf)
            os.unlink(fname)
            r = buf.getvalue()
            if r and len(r) > 10: return DEOBF_TAG + r, "pyc-uncompyle6"
        except: pass
    for offset in (8, 12, 16):
        try:
            obj = marshal.loads(pyc_data[offset:])
            if isinstance(obj, types.CodeType):
                src = _try_marshal_to_source(obj)
                if src: return DEOBF_TAG + src, "pyc-marshal"
        except: pass
    return None, "pyc: установи uncompyle6"

def _v3_pyz_extract(pyz_data: bytes) -> Tuple[Optional[str], str]:
    try:
        with tempfile.NamedTemporaryFile(suffix=".pyz", delete=False) as f:
            f.write(pyz_data); fname = f.name
        with zipfile.ZipFile(fname) as zf:
            results = []
            for fn in zf.namelist():
                if fn.endswith(('.py', '.pyc')):
                    data = zf.read(fn)
                    if fn.endswith('.pyc'):
                        src, _ = _v3_pyc_decompile(data)
                        if src: results.append((fn, src))
                    else:
                        results.append((fn, DEOBF_TAG + _safe_decode(data)))
            os.unlink(fname)
            if results:
                combined = "\n\n".join(f"# === {fn} ===\n{src}" for fn, src in results)
                return DEOBF_TAG + combined, f"pyz-zip ({len(results)} files)"
    except: pass
    return None, "pyz: не удалось извлечь"

def deobfuscate_v3(code: str) -> Tuple[Optional[str], str]:
    for fn in [
        _v3_plain_b64, _v3_rot13, _v3_xor_fixed, _v3_hex_exec,
        _v3_compile_marshal, _v3_chr_obfuscate, _v3_decimal_array,
        _v3_reverse_string, _v3_lambda_chain, _v3_eval_b64, _v3_base85,
        _v3_hex_fromhex, _v3_bz2_plain, _v3_integer_encoded,
        _v3_pyarmor, _v3_lambda_chain,
    ]:
        try:
            r, m = fn(code)
            if r: return r, m
        except: pass
    return None, "v3: метод не обнаружен"

# ════════════════════════════════════════════════════════════════════
#  V4 — CFF + MBA + НОВЫЕ МЕТОДЫ
# ════════════════════════════════════════════════════════════════════

def _v4_cff_reconstruct(code: str) -> Tuple[Optional[str], str]:
    """
    CFF (Control Flow Flattening) деобфускация.
    Паттерн: dispatcher (switch/while) с state-переменной.
    Восстанавливает оригинальный поток выполнения.
    """
    # Детект CFF: while + state-var + if/elif цепочка с числами
    dispatcher_pat = re.compile(
        r'(\w+)\s*=\s*(\d+)\s*\n'
        r'.*?while\s+True\s*:.*?'
        r'(?:if|elif)\s+\1\s*==\s*\d+\s*:',
        re.DOTALL
    )
    if not dispatcher_pat.search(code):
        # Второй паттерн: switch через dict
        if not re.search(r'\w+\s*=\s*\{.*?\d+\s*:\s*(?:lambda|def)', code, re.DOTALL):
            return None, ""

    lines = code.split('\n')
    # Парсим блоки dispatcher
    state_var = None
    blocks: Dict[int, List[str]] = {}
    current_state = None
    current_block: List[str] = []
    initial_state = None

    state_assign = re.compile(r'^(\s*)(\w+)\s*=\s*(\d+)\s*$')
    if_state = re.compile(r'^(\s*)(?:if|elif)\s+(\w+)\s*==\s*(\d+)\s*:\s*$')

    # Находим имя state-переменной и начальное значение
    for line in lines[:50]:
        m = state_assign.match(line)
        if m:
            var_name = m.group(2)
            val = int(m.group(3))
            # Проверяем что эта переменная используется в if == N паттерне
            if any(f"{var_name} ==" in l or f"== {var_name}" in l for l in lines[:200]):
                state_var = var_name
                initial_state = val
                break

    if not state_var:
        return None, ""

    # Собираем блоки
    for line in lines:
        m = if_state.match(line)
        if m and m.group(2) == state_var:
            if current_state is not None:
                blocks[current_state] = current_block
            current_state = int(m.group(3))
            current_block = []
        elif current_state is not None:
            # Ищем state_var = N (переход)
            sm = state_assign.match(line)
            if sm and sm.group(2) == state_var:
                current_block.append(f"    # → state {sm.group(3)}")
            else:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    current_block.append(line)

    if current_state is not None:
        blocks[current_state] = current_block

    if not blocks:
        return None, ""

    # Восстанавливаем порядок: начинаем с initial_state
    result_lines = [
        "# CFF (Control Flow Flattening) — деобфусцировано Togaff\n",
        "# Блоки восстановлены в порядке выполнения\n\n",
    ]
    visited = set()
    queue = [initial_state]
    while queue:
        st = queue.pop(0)
        if st in visited or st not in blocks: continue
        visited.add(st)
        result_lines.append(f"\n# === Block {st} ===\n")
        block_code = blocks[st]
        result_lines.extend(block_code)
        # Ищем следующие состояния в блоке
        for bl in block_code:
            m2 = re.search(r'# → state (\d+)', bl)
            if m2:
                next_s = int(m2.group(1))
                if next_s not in visited:
                    queue.append(next_s)
    # Добавляем непосещённые блоки
    for st, blk in blocks.items():
        if st not in visited:
            result_lines.append(f"\n# === Block {st} (unreachable?) ===\n")
            result_lines.extend(blk)

    result = "\n".join(result_lines)
    if len(result) > 50:
        return DEOBF_TAG + f"# CFF: {len(blocks)} блоков восстановлено\n\n" + result, f"cff ({len(blocks)} blocks)"
    return None, ""

def _v4_mba_simplify(code: str) -> Tuple[Optional[str], str]:
    """
    MBA (Mixed Boolean Arithmetic) simplification.
    Упрощает типичные MBA-выражения в арифметические.
    
    MBA tautologies (всегда верны):
      (x & y) + (x | y)  ==  x + y
      (x ^ y) + 2*(x & y) == x + y
      x + y  ==  (x ^ y) + 2*(x & y)
      x - y  ==  (x ^ ~y) + 1 + ... (вариации)
      x * 2  ==  x + x  ==  x << 1
    """
    if not re.search(r'\bx\s*[&|^~]\s*y\b|\bx\s*[&|^]\s*0x[0-9a-fA-F]+', code):
        # Ищем числовые MBA паттерны
        if not re.search(r'\(\s*\w+\s*[&|^]\s*\w+\s*\)\s*[+\-\*]\s*\(', code):
            return None, ""

    changes = 0
    original = code

    # MBA tautology patterns → simplified form
    mba_rules = [
        # (x & y) + (x | y) → x + y
        (re.compile(r'\(\s*(\w+)\s*&\s*(\w+)\s*\)\s*\+\s*\(\s*\1\s*\|\s*\2\s*\)'),
         lambda m: f"({m.group(1)} + {m.group(2)})"),
        # (x ^ y) + 2*(x & y) → x + y
        (re.compile(r'\(\s*(\w+)\s*\^\s*(\w+)\s*\)\s*\+\s*2\s*\*\s*\(\s*\1\s*&\s*\2\s*\)'),
         lambda m: f"({m.group(1)} + {m.group(2)})"),
        # x + (-1 ^ x) → -1  (MBA constant)
        (re.compile(r'(\w+)\s*\+\s*\(\s*-1\s*\^\s*\1\s*\)'),
         lambda m: "-1"),
        # (x | ~y) - (x ^ ~y) → y  
        (re.compile(r'\(\s*(\w+)\s*\|\s*~(\w+)\s*\)\s*-\s*\(\s*\1\s*\^\s*~\2\s*\)'),
         lambda m: m.group(2)),
        # x ^ 0 → x
        (re.compile(r'(\w+)\s*\^\s*0\b'),
         lambda m: m.group(1)),
        # x & x → x
        (re.compile(r'(\w+)\s*&\s*\1'),
         lambda m: m.group(1)),
        # x | x → x
        (re.compile(r'(\w+)\s*\|\s*\1'),
         lambda m: m.group(1)),
        # x ^ x → 0
        (re.compile(r'(\w+)\s*\^\s*\1'),
         lambda m: "0"),
        # x | 0 → x
        (re.compile(r'(\w+)\s*\|\s*0\b'),
         lambda m: m.group(1)),
        # x & -1 (0xFFFFFFFF) → x
        (re.compile(r'(\w+)\s*&\s*(?:-1|0xFFFFFFFF|0xffffffff)\b'),
         lambda m: m.group(1)),
        # ~~x → x  (double NOT)
        (re.compile(r'~~(\w+)'),
         lambda m: m.group(1)),
        # x * 1 → x
        (re.compile(r'(\w+)\s*\*\s*1\b'),
         lambda m: m.group(1)),
        # x * 0 → 0
        (re.compile(r'(\w+)\s*\*\s*0\b'),
         lambda m: "0"),
        # (x + y) - y → x
        (re.compile(r'\(\s*(\w+)\s*\+\s*(\w+)\s*\)\s*-\s*\2'),
         lambda m: m.group(1)),
        # (x - y) + y → x
        (re.compile(r'\(\s*(\w+)\s*-\s*(\w+)\s*\)\s*\+\s*\2'),
         lambda m: m.group(1)),
        # x << 1 → x * 2  (читаемее)
        (re.compile(r'(\w+)\s*<<\s*1\b'),
         lambda m: f"{m.group(1)} * 2"),
        # x >> 1 → x // 2
        (re.compile(r'(\w+)\s*>>\s*1\b'),
         lambda m: f"{m.group(1)} // 2"),
        # (x & 1) * ... — чётность
        # Числовые константы: 0xFF & x → x % 256
        (re.compile(r'0xFF\s*&\s*(\w+)'),
         lambda m: f"{m.group(1)} % 256"),
        (re.compile(r'(\w+)\s*&\s*0xFF\b'),
         lambda m: f"{m.group(1)} % 256"),
        # 0xFFFFFFFF ^ x → ~x & 0xFFFFFFFF
        (re.compile(r'0xFFFFFFFF\s*\^\s*(\w+)'),
         lambda m: f"~{m.group(1)} & 0xFFFFFFFF"),
    ]

    for _ in range(15):  # Multi-pass
        prev = code
        for pat, repl in mba_rules:
            try:
                new = pat.sub(repl, code)
                if new != code: changes += 1
                code = new
            except: pass
        if code == prev: break

    if changes > 0 and code != original:
        return DEOBF_TAG + f"# MBA simplified: {changes} transformations\n\n" + code, f"mba-simplify ({changes})"
    return None, ""

def _v4_cff_and_mba(code: str) -> Tuple[Optional[str], str]:
    """Применяет CFF + MBA вместе."""
    result = code
    methods_applied = []

    # Сначала MBA
    r, m = _v4_mba_simplify(result)
    if r:
        result = r.replace(DEOBF_TAG, "")
        methods_applied.append(m)

    # Потом CFF
    r2, m2 = _v4_cff_reconstruct(result)
    if r2:
        result = r2.replace(DEOBF_TAG, "")
        methods_applied.append(m2)

    if methods_applied:
        return DEOBF_TAG + result, " + ".join(methods_applied)
    return None, ""

def _v4_bitwise_not(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"exec\s*\(\s*bytes\s*\(\s*\[\s*~b\s*&\s*0xFF\s+for\s+b\s+in\s+b['\"](.+?)['\"]\s*\]\s*\)")
    m = pat.search(code)
    if m:
        try:
            raw = bytes([~b & 0xFF for b in m.group(1).encode("latin-1").decode("unicode_escape").encode("latin-1")])
            dec = _safe_decode(raw)
            if _is_python(dec): return DEOBF_TAG + dec, "bitwise-NOT"
        except: pass
    return None, ""

def _v4_multi_xor(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"exec\s*\(\s*bytes\s*\(\s*\[b\s*\^\s*(\d+)\s*\^\s*(\d+)(?:\s*\^\s*(\d+))?\s+for\s+b\s+in\s+bytes\.fromhex\(['\"]([0-9a-fA-F]+)['\"]\)\]\)")
    m = pat.search(code)
    if m:
        try:
            keys = [int(x) for x in [m.group(1), m.group(2), m.group(3)] if x]
            key = 0
            for k in keys: key ^= k
            raw = bytes([b ^ key for b in bytes.fromhex(m.group(4))])
            dec = _safe_decode(raw)
            if _is_python(dec): return DEOBF_TAG + dec, f"multi-xor"
        except: pass
    return None, ""

def _v4_rol_ror(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"exec\s*\(\s*bytes\s*\(\s*\[\s*\(b\s*>>\s*(\d+)\s*\|\s*b\s*<<\s*(\d+)\)\s*&\s*0xFF\s+for\s+b\s+in\s+b['\"](.+?)['\"]\s*\]\s*\)")
    m = pat.search(code)
    if m:
        try:
            n = int(m.group(1))
            raw = m.group(3).encode("latin-1").decode("unicode_escape").encode("latin-1")
            dec = _safe_decode(bytes([(b >> n | b << (8-n)) & 0xFF for b in raw]))
            if _is_python(dec): return DEOBF_TAG + dec, f"ROR (n={n})"
        except: pass
    return None, ""

def _v4_add_sub(code: str) -> Tuple[Optional[str], str]:
    for op_name, pat in [
        ("add", re.compile(r"exec\s*\(\s*bytes\s*\(\s*\[\s*b\s*\+\s*(\d+)\s+for\s+b\s+in\s+b['\"](.+?)['\"]\s*\]\s*\)")),
        ("sub", re.compile(r"exec\s*\(\s*bytes\s*\(\s*\[\s*b\s*-\s*(\d+)\s+for\s+b\s+in\s+b['\"](.+?)['\"]\s*\]\s*\)")),
    ]:
        m = pat.search(code)
        if m:
            try:
                n = int(m.group(1))
                raw = m.group(2).encode("latin-1").decode("unicode_escape").encode("latin-1")
                if op_name == "add": dec = _safe_decode(bytes([(b + n) % 256 for b in raw]))
                else:                dec = _safe_decode(bytes([(b - n) % 256 for b in raw]))
                if _is_python(dec): return DEOBF_TAG + dec, f"{op_name}-cipher (n={n})"
            except: pass
    return None, ""

def _v4_string_split_join(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"exec\s*\(\s*['\"]['\"]\.join\s*\(\s*\[([^\]]{20,})\]\s*\)\s*\)")
    m = pat.search(code)
    if m:
        parts = re.findall(r"['\"]([^'\"]*)['\"]", m.group(1))
        joined = "".join(parts)
        if _is_python(joined): return DEOBF_TAG + joined, "string-split-join"
    return None, ""

def _v4_base62(code: str) -> Tuple[Optional[str], str]:
    CHARS = string.digits + string.ascii_letters
    def decode(s: str) -> bytes:
        n = 0
        for c in s:
            if c not in CHARS: raise ValueError(c)
            n = n * 62 + CHARS.index(c)
        return n.to_bytes((n.bit_length() + 7) // 8, 'big')
    pat = re.compile(r"exec\s*\(\s*['\"]([0-9a-zA-Z]{30,})['\"]")
    for m in pat.finditer(code):
        try:
            dec = decode(m.group(1)).decode("utf-8")
            if _is_python(dec): return DEOBF_TAG + dec, "base62"
        except: pass
    return None, ""

def _v4_string_encrypt_table(code: str) -> Tuple[Optional[str], str]:
    """
    Деобфускация таблицы строк: _TABLE = {0: 'abc', 1: 'def', ...}
    или _T[N], где значения — b64/hex/xor закодированные строки.
    """
    # Паттерн: словарь с числовыми ключами и строковыми значениями
    table_pat = re.compile(
        r'(\w+)\s*=\s*\{(\s*\d+\s*:\s*[\'"][^\'"]{4,}[\'"](?:\s*,\s*\d+\s*:\s*[\'"][^\'"]{4,}[\'"])*\s*)\}'
    )
    m = table_pat.search(code)
    if not m: return None, ""
    var_name = m.group(1)
    entries_raw = m.group(2)
    # Парсим записи
    entry_pat = re.compile(r'(\d+)\s*:\s*[\'"]([^\'"]+)[\'"]')
    entries = {int(k): v for k, v in entry_pat.findall(entries_raw)}
    if len(entries) < 3: return None, ""
    # Пробуем декодировать каждое значение
    decoded_entries = {}
    for k, v in entries.items():
        for fn in [
            lambda x: base64.b64decode(_b64_pad(x)).decode("utf-8"),
            lambda x: bytes.fromhex(x).decode("utf-8"),
            lambda x: x,
        ]:
            try:
                d = fn(v)
                if d and d.isprintable(): decoded_entries[k] = d; break
            except: pass
    if not decoded_entries: return None, ""
    # Заменяем вхождения var_name[N] → 'decoded_value'
    result = code
    for k, v in decoded_entries.items():
        result = re.sub(
            re.escape(var_name) + r'\s*\[\s*' + str(k) + r'\s*\]',
            repr(v), result
        )
    if result != code:
        return DEOBF_TAG + f"# String table decoded: {len(decoded_entries)} entries\n\n" + result, "string-table"
    return None, ""

def _v4_opaque_predicates(code: str) -> Tuple[Optional[str], str]:
    """
    Удаляет opaque predicates — условия которые всегда True или False.
    Например: if (2 * x + 1) % 2 == 1: → всегда True
              if x * x >= 0: → всегда True для реальных чисел
              if 1 == 0: → всегда False (мёртвый код)
    """
    changes = 0
    lines = code.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        # Всегда False: if 1 == 0: / if False: / if 0:
        if re.match(r'^if\s+(?:1\s*==\s*0|0\s*==\s*1|False|0)\s*:', s):
            indent = len(line) - len(line.lstrip())
            i += 1
            while i < len(lines):
                bl = lines[i]
                if bl.strip() and (len(bl) - len(bl.lstrip())) <= indent:
                    break
                i += 1
            result.append(f"{'    ' * (indent // 4)}# [opaque predicate False — dead code removed]")
            changes += 1
            continue
        # Всегда True: if True: / if 1: / if 1 == 1:
        if re.match(r'^if\s+(?:True|1\s*==\s*1|0\s*==\s*0)\s*:', s):
            indent = len(line) - len(line.lstrip())
            i += 1
            while i < len(lines):
                bl = lines[i]
                bs = bl.strip()
                if bs and (len(bl) - len(bl.lstrip())) <= indent:
                    break
                if bs:
                    # Убираем один уровень отступа
                    result.append(bl[4:] if bl.startswith('    ') else bl)
                i += 1
            changes += 1
            continue
        result.append(line)
        i += 1
    if changes > 0:
        return DEOBF_TAG + f"# Opaque predicates removed: {changes}\n\n" + '\n'.join(result), f"opaque-predicates ({changes})"
    return None, ""

def _v4_zlib_b64(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"exec\s*\(\s*zlib\.decompress\s*\(\s*base64\.b64decode\s*\(\s*b?['\"]([A-Za-z0-9+/=]{20,})['\"]")
    m = pat.search(code)
    if m:
        try:
            dec = _safe_decode(zlib.decompress(base64.b64decode(_b64_pad(m.group(1)))))
            if _is_python(dec): return DEOBF_TAG + dec, "zlib+base64"
        except: pass
    return None, ""

def _v4_variable_rename_analysis(code: str) -> Tuple[Optional[str], str]:
    """
    Анализ обфускации переименованием переменных (l1lI, 0OO0, Il1I и т.п.)
    Находит паттерны и добавляет аналитические комментарии.
    """
    # Обнаруживаем обфусцированные имена
    obf_names = re.findall(r'\b([lI1O0]{4,})\b', code)
    obf_names += re.findall(r'\b(_[0-9a-f]{6,})\b', code)
    unique_obf = list(set(obf_names))
    if len(unique_obf) < 5: return None, ""
    # Добавляем предупреждение
    note = (
        f"# ⚠️ Variable name obfuscation detected\n"
        f"# {len(unique_obf)} obfuscated names found: "
        + ", ".join(unique_obf[:10])
        + ("\n# Use v2 (Ренди 2.0) for deeper cleaning\n\n")
    )
    return DEOBF_TAG + note + code, f"var-rename ({len(unique_obf)} names)"

def deobfuscate_v4(code: str) -> Tuple[Optional[str], str]:
    for fn in [
        _v4_cff_and_mba, _v4_cff_reconstruct, _v4_mba_simplify,
        _v4_zlib_b64, _v4_hex_fromhex_plain := _v3_hex_fromhex,
        _v4_bitwise_not, _v4_multi_xor, _v4_rol_ror, _v4_add_sub,
        _v4_string_split_join, _v4_base62, _v4_string_encrypt_table,
        _v4_opaque_predicates, _v4_variable_rename_analysis,
    ]:
        try:
            r, m = fn(code)
            if r: return r, m
        except: pass
    return None, "v4: метод не обнаружен"

# ════════════════════════════════════════════════════════════════════
#  EXE EXTRACTOR
# ════════════════════════════════════════════════════════════════════

def detect_exe_type(data: bytes) -> str:
    if b'MEI\x0c\x0b\x0a\x0b\x0e' in data or b'MEIPASS' in data or b'PYZ\x00' in data: return "pyinstaller"
    if b'__nuitka__' in data or b'NUITKA_PACKAGE' in data or b'nuitka' in data[:8192].lower(): return "nuitka"
    if b'__pyx_' in data or b'cython' in data[:4096].lower(): return "cython"
    if b'cx_Freeze' in data[:8192]: return "cx_freeze"
    if b'py2exe' in data[:8192].lower(): return "py2exe"
    if data[:2] == b'PK': return "zipapp"
    if data[:2] == b'MZ': return "pe-unknown"
    if data[:4] == b'\x7fELF': return "elf"
    return "unknown"

def _extract_pyinstaller(data: bytes, out_dir: str) -> Tuple[bool, str, List[str]]:
    files = []
    # pyinstxtractor
    try:
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False, dir=out_dir) as f:
            f.write(data); exe_path = f.name
        script = os.path.join(out_dir, "_pix.py")
        with open(script, "w") as f:
            f.write("""
import sys, os
sys.argv = ['pyinstxtractor', sys.argv[1]]
try:
    import pyinstxtractor
    a = pyinstxtractor.PyInstArchive(sys.argv[1])
    if a.open() and a.checkFile() and a.getCArchiveInfo():
        a.parseTOC(); a.extractFiles(); a.close()
        print("OK:" + sys.argv[1] + "_extracted")
    else: print("FAIL")
except Exception as e: print("ERR:" + str(e))
""")
        r = subprocess.run([sys.executable, script, exe_path], cwd=out_dir,
                           capture_output=True, text=True, timeout=120)
        for line in r.stdout.split("\n"):
            if line.startswith("OK:"):
                extracted = line[3:].strip()
                if os.path.exists(extracted):
                    for root, _, fnames in os.walk(extracted):
                        for fn in fnames:
                            if fn.endswith(('.py', '.pyc', '.pyz')):
                                files.append(os.path.join(root, fn))
        if files:
            decompiled = []
            for fp in files:
                if fp.endswith('.pyc'):
                    with open(fp, 'rb') as f2: pyc = f2.read()
                    src, _ = _v3_pyc_decompile(pyc)
                    if src:
                        out = fp.replace('.pyc', '_dec.py')
                        with open(out, 'w') as f2: f2.write(src)
                        decompiled.append(out)
                else:
                    decompiled.append(fp)
            if decompiled: return True, f"PyInstaller: {len(decompiled)} файлов", decompiled
    except Exception as e:
        print(f"[pyinstxtractor] {e}")
    # Manual scan
    return _pyinst_manual(data, out_dir)

def _pyinst_manual(data: bytes, out_dir: str) -> Tuple[bool, str, List[str]]:
    files = []; count = 0
    pos = 0
    while pos < len(data) - 4 and count < 50:
        if data[pos:pos+2] in (b'\x78\x9c', b'\x78\xda', b'\x78\x01'):
            for size in range(64, min(len(data)-pos, 5_000_000), 1024):
                try:
                    raw = zlib.decompress(data[pos:pos+size])
                    if len(raw) > 100:
                        text = None
                        for off in (8, 12, 16):
                            try:
                                obj = marshal.loads(raw[off:])
                                if isinstance(obj, types.CodeType):
                                    src = _try_marshal_to_source(obj)
                                    if src: text = DEOBF_TAG + src; break
                            except: pass
                        if not text:
                            t2 = _safe_decode(raw)
                            if _is_python(t2, 80): text = DEOBF_TAG + t2
                        if text:
                            fn = os.path.join(out_dir, f"block_{count:04d}.py")
                            with open(fn, 'w') as f: f.write(text)
                            files.append(fn); count += 1
                        break
                except: pass
        pos += 1
    if files: return True, f"PyInstaller manual: {len(files)} блоков", files
    return False, "PyInstaller: не удалось извлечь", []

def _extract_nuitka(data: bytes, out_dir: str) -> Tuple[bool, str, List[str]]:
    strings = []
    cur = []; i = 0
    while i < min(len(data), 20_000_000):
        b = data[i]
        if 32 <= b < 127: cur.append(chr(b))
        else:
            if len(cur) >= 12:
                s = "".join(cur)
                if any(kw in s for kw in ["import ", "def ", "class ", ".py", "print("]):
                    strings.append(s)
            cur = []
        i += 1
    fname = os.path.join(out_dir, "nuitka_analysis.py")
    with open(fname, 'w') as f:
        f.write(DEOBF_TAG + "# Nuitka — compiled to C, full reversal not possible\n# Extracted strings:\n\n")
        for s in strings[:300]: f.write(f"# {s}\n")
    guide = os.path.join(out_dir, "REVERSE_GUIDE.txt")
    with open(guide, 'w') as f:
        f.write("NUITKA REVERSE:\n1. strings <exe> | grep 'def \\|import '\n2. IDA Pro + FLIRT\n3. Ghidra + Python plugin\n4. frida hooking\n")
    return bool(strings), f"Nuitka: {len(strings)} строк", [fname, guide]

def _extract_zipapp(data: bytes, out_dir: str) -> Tuple[bool, str, List[str]]:
    files = []
    try:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False, dir=out_dir) as f:
            f.write(data); zpath = f.name
        with zipfile.ZipFile(zpath) as zf:
            for name in zf.namelist():
                content = zf.read(name)
                if name.endswith('.pyc'):
                    src, _ = _v3_pyc_decompile(content)
                    if src:
                        out = os.path.join(out_dir, name.replace('/', '_').replace('.pyc', '.py'))
                        with open(out, 'w') as f: f.write(src)
                        files.append(out)
                elif name.endswith('.py'):
                    out = os.path.join(out_dir, name.replace('/', '_'))
                    with open(out, 'wb') as f: f.write(content)
                    files.append(out)
        os.unlink(zpath)
    except: pass
    if files: return True, f"ZIP: {len(files)} файлов", files
    return False, "ZIP: не удалось извлечь", []

def extract_from_exe(data: bytes, out_dir: str, filename: str = "") -> Tuple[bool, str, List[str]]:
    os.makedirs(out_dir, exist_ok=True)
    t = detect_exe_type(data)
    if t == "pyinstaller": return _extract_pyinstaller(data, out_dir)
    if t == "nuitka":      return _extract_nuitka(data, out_dir)
    if t in ("cython","elf","pe-unknown"):
        ok, msg, files = _extract_pyinstaller(data, out_dir)
        if ok: return ok, msg, files
        return _extract_nuitka(data, out_dir)
    if t in ("cx_freeze","py2exe","zipapp"):
        return _extract_zipapp(data, out_dir)
    # Unknown — try all
    for fn in [_extract_pyinstaller, _extract_zipapp, lambda d,o: _extract_nuitka(d,o)]:
        try:
            ok, msg, files = fn(data, out_dir)
            if ok: return ok, msg, files
        except: pass
    return False, "Неизвестный формат", []

# ════════════════════════════════════════════════════════════════════
#  DETECT + AUTO
# ════════════════════════════════════════════════════════════════════

def detect_all_methods(code: str) -> dict:
    return {
        "v1":               _v1_detect(code),
        "has_exec":         bool(re.search(r'exec\s*\(', code)),
        "has_base64":       bool(re.search(r'[A-Za-z0-9+/=]{50,}', code)),
        "has_xor":          bool(re.search(r'bytes\.fromhex|b\s*\^\s*\d+', code)),
        "has_state_machine":bool(re.search(r'while\s+\w+\s*!=\s*\d+', code)),
        "has_wrappers":     bool(re.search(r'def\s+\w+\s*\(\s*\w+\s*,\s*\w+\s*,\s*\w+\s*\)', code)),
        "has_chr":          len(re.findall(r'\bchr\s*\(\s*\d+\s*\)', code)),
        "has_marshal":      "marshal" in code,
        "has_pyarmor":      "__pyarmor__" in code or "pyarmor_runtime" in code,
        "has_hyperion":     bool(re.search(r"range\s*\(\s*256\s*\)", code)),
        "has_rot13":        "rot_13" in code or "rot-13" in code.lower(),
        "has_cff":          bool(re.search(r'while\s+True\s*:', code) and re.search(r'if\s+\w+\s*==\s*\d{2,}', code)),
        "has_mba":          bool(re.search(r'\w+\s*[&|^]\s*\w+\s*[+\-\*]', code)),
        "has_bz2":          "bz2" in code,
        "has_lzma":         "lzma" in code,
        "has_reverse":      "[::-1]" in code,
        "has_opaque":       bool(re.search(r'if\s+(?:True|False|1\s*==\s*[01]|0\s*==\s*[01])\s*:', code)),
        "lines":            code.count('\n') + 1,
        "chars":            len(code),
    }

def auto_deobfuscate(code: str) -> Tuple[Optional[str], str]:
    """v1 → v3 → v4(CFF+MBA) → v2"""
    r, m = deobfuscate_v1(code)
    if r: return r, f"v1: {m}"
    r, m = deobfuscate_v3(code)
    if r: return r, f"v3: {m}"
    r, m = deobfuscate_v4(code)
    if r: return r, f"v4: {m}"
    result = deobfuscate_v2(code)
    return result, "v2: Ренди 2.0"

# ════════════════════════════════════════════════════════════════════
#  BOT — CONFIG
# ════════════════════════════════════════════════════════════════════
ASTOLFO_FACES = [
    "(\\(\\  ∧＿∧\n(｡•ω•｡)つ━━✿✿✿",
    "(\\(\\  ˘ω˘ )\n(っ･∀･)っ━━★",
    "( ˘ω˘ )つ━━✿",
    "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧",
    "(◕‿◕✿) ⋆⭐",
    "≧◡≦ ✨",
    "( •̀ ω •́ )✧",
    "(。◕‿‿◕。)♡",
]

DONE_MSGS = [
    "Готово~ ✅ файл декодирован! 🌸",
    "Ура~ всё распаковано! ✨",
    "Готово! Код больше не скрывает секретов~ 💕",
    "Расшифровано~ держи файлик! 🎀",
    "Вуаля~ обфускация снята! ⭐",
]

FAIL_MSGS = [
    "Не удалось декодировать~ попробуй другой режим",
    "Хмм~ метод не подошёл, пробуй АВТО",
    "Файл сопротивляется~ попробуй АВТО или другой режим",
]

DECODE_STEPS = [
    "Анализирую паттерны", "Снимаю слои шифрования",
    "Дешифрую payload", "Разворачиваю обфускацию",
    "Декодирую строки", "Финальная очистка",
]

DIVIDER      = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
DIVIDER_THIN = "──────────────────────────────"
LOGO = (
    "╔══════════════════════════════════╗\n"
    "║  🔓 TOGAFF DEOBFUSCATOR v5.0   ║\n"
    "║  (\\(\\  ∧＿∧                    ║\n"
    "║  (｡•ω•｡)つ━━✿✿✿               ║\n"
    "║     Astolfo Edition 💕          ║\n"
    "╚══════════════════════════════════╝"
)

METHODS_TEXT = (
    "🔓 v1   base64/32/16 + zlib/gzip/lzma/bz2\n"
    "         все комбо · Rendy marshal-chain\n\n"
    "🔩 v2   Ренди 2.0 Universal\n"
    "         XOR · state-machine · wrappers\n"
    "         hex/unicode escapes · chr-arrays\n"
    "         octal · getattr-chains · dummies\n\n"
    "🧬 v3   rot13 · xor-key · plain-b64\n"
    "         multilayer-b64 · hex-exec\n"
    "         chr() · marshal · PyArmor\n"
    "         reverse · lambda-chain · base85\n"
    "         hex-fromhex · bz2 · eval-b64\n\n"
    "🆕 v4   CFF · MBA · opaque predicates\n"
    "         bitwise-NOT · ROL/ROR · multi-XOR\n"
    "         add/sub cipher · string-table\n"
    "         base62 · zlib+b64 · var-rename\n\n"
    "📦 EXE  PyInstaller · Nuitka · Cython\n"
    "         cx_Freeze · py2exe · zipapp\n"
    "📟 PYC  uncompyle6 / marshal+dis\n"
    "🗜️  PYZ  ZIP archiver extractor"
)

MODE_INFO = {
    "auto":   ("⚡", "АВТО",       "Умный перебор: v1 → v3 → v4 → v2"),
    "detect": ("🔬", "Анализ",     "Полный анализ без декодирования"),
    "v1":     ("🔓", "v1",         "base64/32/16 · zlib/gzip/lzma/bz2 · Rendy"),
    "v2":     ("🔩", "v2",         "Ренди 2.0 — XOR · state-machine · wrappers"),
    "v3":     ("🧬", "v3",         "rot13 · xor · chr() · PyArmor · marshal"),
    "v4":     ("🆕", "v4 CFF+MBA", "CFF · MBA · opaque predicates · bitwise"),
    "exe":    ("📦", "EXE",        "PyInstaller · Nuitka · cx_Freeze · zipapp"),
    "pyc":    ("📟", "PYC",        "Декомпиляция .pyc байткода"),
    "pyz":    ("🗜️", "PYZ/ZIP",    "Извлечение из ZIP/PYZ архива"),
}

# ════════════════════════════════════════════════════════════════════
#  BOT INIT
# ════════════════════════════════════════════════════════════════════
bot = telebot.TeleBot(TOKEN, parse_mode=None)

def _send(cid, text, kb=None):
    try: return bot.send_message(cid, text, reply_markup=kb)
    except Exception as e: print(f"[send] {e}")

def _edit(cid, mid, text, kb=None):
    try: return bot.edit_message_text(text, cid, mid, reply_markup=kb)
    except Exception as e: print(f"[edit] {e}")

def _answer(call, text=""):
    try: bot.answer_callback_query(call.id, text)
    except: pass

def _typing(cid):
    try: bot.send_chat_action(cid, 'upload_document')
    except: pass

# ════════════════════════════════════════════════════════════════════
#  BOT KEYBOARDS
# ════════════════════════════════════════════════════════════════════
def kb_main(adm=False):
    k = types.InlineKeyboardMarkup(row_width=1)
    k.add(types.InlineKeyboardButton("⚡  АВТО  — рекомендуется",       callback_data="mode_auto"))
    k.add(types.InlineKeyboardButton("🔬  Анализ  — без декода",        callback_data="mode_detect"))
    k.add(types.InlineKeyboardButton("─" * 30,                          callback_data="noop"))
    k.row(
        types.InlineKeyboardButton("🔓 v1", callback_data="mode_v1"),
        types.InlineKeyboardButton("🔩 v2", callback_data="mode_v2"),
    )
    k.row(
        types.InlineKeyboardButton("🧬 v3", callback_data="mode_v3"),
        types.InlineKeyboardButton("🆕 v4 CFF+MBA", callback_data="mode_v4"),
    )
    k.add(types.InlineKeyboardButton("─" * 30,                          callback_data="noop"))
    k.add(types.InlineKeyboardButton("📦  EXE/PYD Extractor",           callback_data="mode_exe"))
    k.add(types.InlineKeyboardButton("📟  .pyc Decompiler",             callback_data="mode_pyc"))
    k.add(types.InlineKeyboardButton("🗜️   .pyz / ZIP Extractor",       callback_data="mode_pyz"))
    k.add(types.InlineKeyboardButton("─" * 30,                          callback_data="noop"))
    k.row(
        types.InlineKeyboardButton("📊 Статы",    callback_data="show_stats"),
        types.InlineKeyboardButton("📖 Методы",   callback_data="show_methods"),
    )
    if adm:
        k.add(types.InlineKeyboardButton("👑 Admin Panel",              callback_data="admin_panel"))
    return k

def kb_back():
    k = types.InlineKeyboardMarkup()
    k.add(types.InlineKeyboardButton("◀  Назад в меню", callback_data="back_main"))
    return k

def kb_after(mode):
    k = types.InlineKeyboardMarkup(row_width=2)
    k.row(
        types.InlineKeyboardButton("🔄 Ещё файл",  callback_data=f"mode_{mode}"),
        types.InlineKeyboardButton("🏠 Меню",       callback_data="back_main"),
    )
    return k

def kb_admin():
    k = types.InlineKeyboardMarkup(row_width=2)
    k.row(
        types.InlineKeyboardButton("👥 Юзеры",     callback_data="adm_users"),
        types.InlineKeyboardButton("🚫 Баны",       callback_data="adm_bans"),
    )
    k.row(
        types.InlineKeyboardButton("📊 Статы",      callback_data="adm_stats"),
        types.InlineKeyboardButton("📝 Логи",        callback_data="adm_logs"),
    )
    k.row(
        types.InlineKeyboardButton("📢 Рассылка",   callback_data="adm_broadcast"),
        types.InlineKeyboardButton("🗑️ Очистить логи", callback_data="adm_clearlogs"),
    )
    k.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_main"))
    return k

# ════════════════════════════════════════════════════════════════════
#  BOT STATE
# ════════════════════════════════════════════════════════════════════
_state: dict = {}   # uid → {"mode": str}
_bcast: dict = {}   # uid → True

def get_mode(uid): return _state.get(uid, {}).get("mode")
def set_mode(uid, mode): _state.setdefault(uid, {})["mode"] = mode

# ════════════════════════════════════════════════════════════════════
#  BOT ANIMATIONS
# ════════════════════════════════════════════════════════════════════
def _animate_decode(cid, mid, filename, mode_name):
    face = random.choice(ASTOLFO_FACES)
    total = len(DECODE_STEPS)
    for step, msg in enumerate(random.sample(DECODE_STEPS, min(5, total)), 1):
        bar = "█" * step + "░" * (total - step)
        pct = int(step / total * 100)
        try:
            bot.edit_message_text(
                f"🔓 {mode_name}\n{DIVIDER}\n📄 {filename}\n\n"
                f"{face}\n\n[{bar}] {pct}%\n⏳ {msg}...",
                cid, mid
            )
        except: pass
        time.sleep(0.5)

def _animate_auto(cid, mid, filename, chars_in, step_num, total_steps, face, prev_failed=""):
    steps_names = ["v1 base64/zlib/rendy", "v3 rot13/xor/chr/marshal", "v4 CFF+MBA/bitwise", "v2 Ренди 2.0 (universal)"]
    name = steps_names[min(step_num-1, len(steps_names)-1)]
    bar = "█" * step_num + "░" * (total_steps - step_num)
    pct = int(step_num / total_steps * 100)
    fail_line = f"✗ {prev_failed}\n" if prev_failed else ""
    try:
        bot.edit_message_text(
            f"⚡ АВТО-деобфускация\n{DIVIDER}\n📄 {filename}\n📊 {chars_in:,} символов\n\n"
            f"{face}\n\n{fail_line}[{bar}] {pct}%\n⏳ {name}...",
            cid, mid
        )
    except: pass
    time.sleep(0.5)

# ════════════════════════════════════════════════════════════════════
#  BOT COMMANDS
# ════════════════════════════════════════════════════════════════════
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    uid   = int(msg.from_user.id)
    name  = msg.from_user.first_name or "анон"
    uname = getattr(msg.from_user, "username", "") or ""

    if is_banned(uid):
        _send(msg.chat.id, f"{LOGO}\n\n🚫 Ты в бан-листе.\nОбратись к {BOT_TAG}~")
        return

    ensure_user(uid, name, uname)
    u = users.get(str(uid), {})
    file_count = u.get("files", 0)
    adm = "  👑 ADMIN" if is_admin(uid) else ""
    face = random.choice(ASTOLFO_FACES)
    access_note = "" if OPEN_ACCESS else "\n🔓 Доступ открытый — все могут пользоваться!"

    text = (
        f"{LOGO}\n\n"
        f"Привет, {name}!{adm} 🌸\n"
        f"{DIVIDER}\n"
        f"{face}\n"
        f"{DIVIDER}\n\n"
        f"📁 Файлов декодировано: {file_count}{access_note}\n\n"
        f"Выбери режим и отправь файл~ 💕\n\n"
        f"/help — помощь  |  /methods — все методы"
    )
    if is_admin(uid): text += "  |  /admin — панель"
    _send(msg.chat.id, text, kb_main(is_admin(uid)))

@bot.message_handler(commands=["help"])
def cmd_help(msg):
    if is_banned(msg.from_user.id): return
    access = "🌐 Открытый доступ — бот доступен всем!" if OPEN_ACCESS else "🔒 Доступ по приглашению"
    _send(msg.chat.id,
        f"❓ Помощь — {BOT_NAME} v{VERSION}\n{DIVIDER}\n\n"
        f"{access}\n\n"
        f"КАК ИСПОЛЬЗОВАТЬ:\n"
        f"1️⃣ Нажми кнопку с нужным режимом\n"
        f"2️⃣ Отправь .py / .pyc / .exe / .pyz файл\n"
        f"3️⃣ Получи декодированный файл\n\n"
        f"КОМАНДЫ:\n"
        f"/start — главное меню\n"
        f"/methods — список всех методов\n"
        f"/stats — твоя статистика\n"
        f"/cancel — отменить режим\n\n"
        f"ФОРМАТЫ:\n"
        f".py .pyc .pyw .exe .pyd .so .pyz .zip\n\n"
        f"by {BOT_TAG}",
        kb_back()
    )

@bot.message_handler(commands=["methods"])
def cmd_methods(msg):
    if is_banned(msg.from_user.id): return
    _send(msg.chat.id,
        f"🧬 Все методы деобфускации\n{DIVIDER}\n\n{METHODS_TEXT}",
        kb_back()
    )

@bot.message_handler(commands=["stats"])
def cmd_stats(msg):
    if is_banned(msg.from_user.id): return
    uid = str(msg.from_user.id)
    u = users.get(uid, {})
    methods_used = sorted(u.get("methods", {}).items(), key=lambda x: -x[1])[:5]
    top = "\n".join(f"  {i+1}. {m}: {n}×" for i,(m,n) in enumerate(methods_used)) or "  нет данных"
    _send(msg.chat.id,
        f"📊 Твоя статистика\n{DIVIDER}\n\n"
        f"👤 {u.get('name','?')} (@{u.get('username','?')})\n"
        f"📁 Файлов: {u.get('files',0)}\n"
        f"📅 С: {u.get('added','?')}\n\n"
        f"Топ методов:\n{top}",
        kb_back()
    )

@bot.message_handler(commands=["cancel"])
def cmd_cancel(msg):
    uid = msg.from_user.id
    set_mode(uid, None)
    _bcast.pop(uid, None)
    _send(msg.chat.id, "❌ Отменено~", kb_main(is_admin(uid)))

@bot.message_handler(commands=["admin"])
def cmd_admin(msg):
    if not is_admin(msg.from_user.id): _send(msg.chat.id, "🚫 Нет доступа~"); return
    _send(msg.chat.id, _admin_text(), kb_admin())

def _admin_text():
    total_files = sum(u.get("files",0) for u in users.values())
    top_m = sorted(stats.get("methods",{}).items(), key=lambda x:-x[1])[:5]
    top_str = "  " + " | ".join(f"{m}:{n}" for m,n in top_m) if top_m else "  нет"
    return (
        f"👑 Admin Panel\n{DIVIDER}\n\n"
        f"👥 Юзеры:   {len(users)}\n"
        f"🚫 Баны:    {len(banned)}\n"
        f"📁 Файлов:  {total_files}\n"
        f"📅 Сегодня: {stats.get('daily',{}).get(today(),0)}\n"
        f"🌐 Доступ: {'открытый' if OPEN_ACCESS else 'закрытый'}\n\n"
        f"Топ методов:\n{top_str}"
    )

@bot.message_handler(commands=["add"])
def cmd_add(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.strip().split(None, 2)
    if len(parts) < 2: _send(msg.chat.id, "/add <id> [имя]"); return
    try: target = int(parts[1])
    except: _send(msg.chat.id, "❌ Неверный ID"); return
    banned.discard(target); banned.discard(str(target))
    name = parts[2] if len(parts) > 2 else f"User {target}"
    users[str(target)] = {"name": name, "username": "", "added": ts(), "files": 0, "role": "user", "methods": {}}
    save_all(); log_action(f"ADD {target} by {msg.from_user.id}")
    _send(msg.chat.id, f"✅ Добавлен {name} ({target}) 🌸")
    try: bot.send_message(target, f"{LOGO}\n\n🌸 Тебе открыт доступ к {BOT_NAME}!\n\n/start чтобы начать~ 💕")
    except: pass

@bot.message_handler(commands=["remove"])
def cmd_remove(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.strip().split()
    if len(parts) < 2: return
    try: target = str(int(parts[1]))
    except: return
    if target in users:
        del users[target]; save_all()
        _send(msg.chat.id, f"✅ Удалён {target}")

@bot.message_handler(commands=["ban"])
def cmd_ban(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.strip().split()
    if len(parts) < 2: return
    try: target = int(parts[1])
    except: return
    if is_admin(target): _send(msg.chat.id, "❌ Нельзя банить админа"); return
    banned.add(target); banned.add(str(target))
    if str(target) in users: del users[str(target)]
    save_all(); log_action(f"BAN {target}")
    _send(msg.chat.id, f"🚫 Забанен {target}")
    try: bot.send_message(target, "🚫 Твой доступ заблокирован.")
    except: pass

@bot.message_handler(commands=["unban"])
def cmd_unban(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.strip().split()
    if len(parts) < 2: return
    try: target = int(parts[1])
    except: return
    banned.discard(target); banned.discard(str(target)); save_all()
    _send(msg.chat.id, f"✅ Разбанен {target} 🌸")

@bot.message_handler(commands=["broadcast"])
def cmd_broadcast(msg):
    if not is_admin(msg.from_user.id): return
    _bcast[msg.from_user.id] = True
    _send(msg.chat.id, "📢 Отправь текст рассылки~ (/cancel отмена)")

@bot.message_handler(commands=["users"])
def cmd_users(msg):
    if not is_admin(msg.from_user.id): return
    lines = [f"👥 Пользователи ({len(users)})\n{DIVIDER}\n\n"]
    for i, (uid_s, u) in enumerate(list(users.items())[:40], 1):
        un = f"@{u['username']}" if u.get('username') else f"ID:{uid_s}"
        adm_mark = " 👑" if u.get("role") == "admin" else ""
        lines.append(f"{i}. {u.get('name','?')}{adm_mark} {un} — {u.get('files',0)} файлов\n")
    if len(users) > 40: lines.append(f"...ещё {len(users)-40}")
    _send(msg.chat.id, "".join(lines))

# ════════════════════════════════════════════════════════════════════
#  BROADCAST HANDLER
# ════════════════════════════════════════════════════════════════════
@bot.message_handler(func=lambda m: int(m.from_user.id) in _bcast and _bcast.get(int(m.from_user.id)))
def handle_broadcast(msg):
    if not is_admin(msg.from_user.id): return
    _bcast.pop(int(msg.from_user.id), None)
    ok = fail = 0
    all_uids = list(users.keys())
    wait = _send(msg.chat.id, f"📢 Рассылка {len(all_uids)} пользователям...")
    for uid_str in all_uids:
        try:
            bot.send_message(int(uid_str), f"📢 {BOT_NAME} 🌸\n{DIVIDER}\n\n{msg.text}\n\nby {BOT_TAG}")
            ok += 1; time.sleep(0.05)
        except: fail += 1
    if wait: _edit(msg.chat.id, wait.message_id, f"✅ Рассылка: {ok} доставлено, {fail} ошибок")

# ════════════════════════════════════════════════════════════════════
#  CALLBACKS
# ════════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: True)
def on_callback(call):
    uid = int(call.from_user.id)
    d   = call.data
    cid = call.message.chat.id
    mid = call.message.message_id

    if d == "noop": _answer(call); return

    if d == "back_main":
        _answer(call)
        set_mode(uid, None)
        face = random.choice(ASTOLFO_FACES)
        try:
            bot.edit_message_text(
                f"{LOGO}\n\n{face}\n\nВыбери режим и отправь файл~ 💕",
                cid, mid, reply_markup=kb_main(is_admin(uid))
            )
        except: _send(cid, "Главное меню~", kb_main(is_admin(uid)))
        return

    if d == "show_stats":
        _answer(call)
        total_files = sum(u.get("files",0) for u in users.values())
        today_f = stats.get("daily",{}).get(today(), 0)
        top_m = sorted(stats.get("methods",{}).items(), key=lambda x:-x[1])[:7]
        top_str = "\n".join(f"  {i+1}. {m}: {n}×" for i,(m,n) in enumerate(top_m)) or "  нет данных"
        try:
            bot.edit_message_text(
                f"📊 Статистика\n{DIVIDER}\n\n"
                f"👥 Пользователей: {len(users)}\n"
                f"📁 Файлов всего:  {total_files}\n"
                f"📅 Сегодня:       {today_f}\n\n"
                f"Топ методов:\n{top_str}",
                cid, mid, reply_markup=kb_back()
            )
        except: pass
        return

    if d == "show_methods":
        _answer(call)
        try:
            bot.edit_message_text(
                f"🧬 Методы деобфускации\n{DIVIDER}\n\n{METHODS_TEXT}",
                cid, mid, reply_markup=kb_back()
            )
        except: pass
        return

    if d == "admin_panel":
        if not is_admin(uid): _answer(call, "🚫"); return
        _answer(call)
        try: bot.edit_message_text(_admin_text(), cid, mid, reply_markup=kb_admin())
        except: _send(cid, _admin_text(), kb_admin())
        return

    # Admin callbacks
    if d.startswith("adm_"):
        if not is_admin(uid): _answer(call, "🚫"); return
        _answer(call)
        if d == "adm_users":
            lines = [f"👥 Пользователи ({len(users)})\n{DIVIDER}\n\n"]
            for i, (uid_s, u) in enumerate(list(users.items())[:25], 1):
                un = f"@{u['username']}" if u.get('username') else f"ID:{uid_s}"
                lines.append(f"{i}. {u.get('name','?')} {un} — {u.get('files',0)} файлов\n")
            if len(users) > 25: lines.append(f"...ещё {len(users)-25}")
            try: bot.edit_message_text("".join(lines), cid, mid, reply_markup=kb_back())
            except: _send(cid, "".join(lines), kb_back())
        elif d == "adm_bans":
            text = (f"🚫 Бан-лист ({len(banned)})\n\n" + "\n".join(f"• {b}" for b in list(banned)[:40])) if banned else "🚫 Бан-лист пуст~"
            try: bot.edit_message_text(text, cid, mid, reply_markup=kb_back())
            except: _send(cid, text, kb_back())
        elif d == "adm_stats":
            total_files = sum(u.get("files",0) for u in users.values())
            top_m = sorted(stats.get("methods",{}).items(), key=lambda x:-x[1])[:10]
            top_str = "\n".join(f"  {i+1}. {m}: {n}×" for i,(m,n) in enumerate(top_m)) or "  нет"
            week = sorted(stats.get("daily",{}).items())[-7:]
            week_str = "\n".join(f"  {d_}: {n}" for d_,n in week)
            text = (f"📊 Детальная статистика\n{DIVIDER}\n\n"
                    f"👥 Юзеры: {len(users)}\n🚫 Баны: {len(banned)}\n"
                    f"📁 Файлов: {total_files}\n📅 Сегодня: {stats.get('daily',{}).get(today(),0)}\n\n"
                    f"Топ методов:\n{top_str}\n\nПо дням (7д):\n{week_str}")
            try: bot.edit_message_text(text, cid, mid, reply_markup=kb_back())
            except: _send(cid, text, kb_back())
        elif d == "adm_logs":
            try:
                if os.path.exists(LOG_FILE):
                    with open(LOG_FILE, 'r') as f: lines = f.readlines()
                    text = "📝 Лог (последние 30)\n\n" + "".join(lines[-30:])
                    if len(text) > 4000: text = text[-4000:]
                else: text = "Лог пустой~"
                try: bot.edit_message_text(text, cid, mid, reply_markup=kb_back())
                except: _send(cid, text, kb_back())
            except Exception as e: _send(cid, f"Ошибка: {e}")
        elif d == "adm_broadcast":
            _bcast[uid] = True
            try: bot.edit_message_text("📢 Отправь текст рассылки~", cid, mid, reply_markup=kb_back())
            except: _send(cid, "📢 Текст рассылки:")
        elif d == "adm_clearlogs":
            try: open(LOG_FILE, 'w').close(); _send(cid, "✅ Логи очищены~")
            except: pass
        return

    # Mode selection
    mode_map = {
        "mode_auto": "auto", "mode_detect": "detect",
        "mode_v1": "v1",     "mode_v2": "v2",
        "mode_v3": "v3",     "mode_v4": "v4",
        "mode_exe": "exe",   "mode_pyc": "pyc",
        "mode_pyz": "pyz",
    }
    if d in mode_map:
        if not is_allowed(uid): _answer(call, "🚫 Нет доступа"); return
        _answer(call)
        mode = mode_map[d]
        emoji, name, desc = MODE_INFO[mode]
        set_mode(uid, mode)
        face = random.choice(ASTOLFO_FACES)
        text = (
            f"{emoji} {name}\n{DIVIDER}\n\n"
            f"{face}\n\n"
            f"{desc}\n\n"
            f"{DIVIDER}\n"
            f"✅ Отправь файл~ 💕"
        )
        try: bot.edit_message_text(text, cid, mid, reply_markup=kb_back())
        except: _send(cid, text, kb_back())
        return

# ════════════════════════════════════════════════════════════════════
#  DOCUMENT HANDLER
# ════════════════════════════════════════════════════════════════════
@bot.message_handler(content_types=["document"])
def handle_document(msg):
    uid  = int(msg.from_user.id)
    cid  = msg.chat.id
    name = msg.from_user.first_name or "анон"
    uname = getattr(msg.from_user, "username", "") or ""

    if is_banned(uid):
        _send(cid, "🚫 Ты в бан-листе~"); return

    if not is_allowed(uid):
        _send(cid, f"{LOGO}\n\n🔒 Доступ закрыт~\nОбратись к {BOT_TAG}~"); return

    ensure_user(uid, name, uname)

    mode = get_mode(uid)
    if not mode:
        _send(cid,
            f"⚠️ Сначала выбери режим!\n\n{random.choice(ASTOLFO_FACES)}\n\nНажми кнопку в меню~",
            kb_main(is_admin(uid)))
        return

    doc   = msg.document
    fname = doc.file_name or "file"
    ext   = os.path.splitext(fname.lower())[1]
    size  = doc.file_size or 0

    if size > MAX_FILE_MB * 1024 * 1024:
        _send(cid, f"⚠️ Файл слишком большой ({size//1024//1024:.1f} MB)\nМакс: {MAX_FILE_MB} MB"); return

    if mode not in ("exe", "pyz") and ext not in ALLOWED_EXT and ext:
        _send(cid, f"⚠️ Неподдерживаемый формат: {ext}\n\nПоддерживается: {', '.join(sorted(ALLOWED_EXT))}"); return

    set_mode(uid, None)
    face = random.choice(ASTOLFO_FACES)
    wait = _send(cid, f"📥 Загружаю {fname}...\n\n{face}")
    if not wait: return

    def process():
        try:
            _typing(cid)
            file_info = bot.get_file(doc.file_id)
            data      = bot.download_file(file_info.file_path)

            # Update user file counter
            key = str(uid)
            if key in users:
                users[key]["files"] = users[key].get("files", 0) + 1
            log_action(f"FILE uid={uid} mode={mode} file={fname} size={size}")

            emoji, mode_name, _ = MODE_INFO.get(mode, ("🔓", mode, ""))

            # EXE
            if mode == "exe" or (mode == "auto" and ext in ('.exe','.pyd','.so','.elf')):
                _do_exe(cid, wait.message_id, uid, data, fname)
                return

            # PYC
            if mode == "pyc" or (ext == ".pyc" and mode != "auto"):
                _edit(cid, wait.message_id, f"📟 Декомпилирую .pyc\n{DIVIDER}\n📄 {fname}\n💾 {size:,} байт\n\n{face}\n\n⏳ uncompyle6 / marshal+dis...")
                result, method = _v3_pyc_decompile(data)
                if result: _send_result(cid, wait.message_id, uid, fname, result, f"pyc: {method}", size, len(result), mode)
                else: _send_fail(cid, wait.message_id, fname, method, mode)
                return

            # PYZ
            if mode == "pyz" or ext in (".pyz",):
                _edit(cid, wait.message_id, f"🗜️ Извлекаю архив\n{DIVIDER}\n📄 {fname}\n\n⏳ Распаковываю...")
                result, method = _v3_pyz_extract(data)
                if result: _send_result(cid, wait.message_id, uid, fname, result, f"pyz: {method}", size, len(result), mode)
                else: _send_fail(cid, wait.message_id, fname, method, mode)
                return

            # Python source
            try:
                code = data.decode("utf-8", errors="replace")
            except:
                _edit(cid, wait.message_id, "❌ Не удалось прочитать файл как текст", kb_main(is_admin(uid))); return

            chars_in = len(code)

            if mode == "detect":
                _do_detect(cid, wait.message_id, uid, fname, code, chars_in)

            elif mode == "v1":
                _animate_decode(cid, wait.message_id, fname, f"🔓 v1")
                result, method = deobfuscate_v1(code)
                if result: _send_result(cid, wait.message_id, uid, fname, result, f"v1: {method}", chars_in, len(result), mode)
                else: _send_fail(cid, wait.message_id, fname, method, mode)

            elif mode == "v2":
                _animate_decode(cid, wait.message_id, fname, f"🔩 v2")
                result = deobfuscate_v2(code)
                _send_result(cid, wait.message_id, uid, fname, result, "v2: Ренди 2.0", chars_in, len(result), mode)

            elif mode == "v3":
                _animate_decode(cid, wait.message_id, fname, f"🧬 v3")
                result, method = deobfuscate_v3(code)
                if result: _send_result(cid, wait.message_id, uid, fname, result, f"v3: {method}", chars_in, len(result), mode)
                else: _send_fail(cid, wait.message_id, fname, method, mode)

            elif mode == "v4":
                _animate_decode(cid, wait.message_id, fname, f"🆕 v4 CFF+MBA")
                result, method = deobfuscate_v4(code)
                if result: _send_result(cid, wait.message_id, uid, fname, result, f"v4: {method}", chars_in, len(result), mode)
                else: _send_fail(cid, wait.message_id, fname, method, mode)

            else:  # AUTO
                _do_auto(cid, wait.message_id, uid, fname, code, chars_in)

        except Exception as e:
            print(f"[process] {traceback.format_exc()}")
            try: _edit(cid, wait.message_id, f"❌ Ошибка: {e}", kb_main(is_admin(uid)))
            except: pass

    threading.Thread(target=process, daemon=True).start()


def _do_detect(cid, mid, uid, filename, code, chars_in):
    face = random.choice(ASTOLFO_FACES)
    _edit(cid, mid, f"🔬 Анализирую {filename}\n{DIVIDER}\n\n{face}\n\n⏳ Сканирую паттерны...")
    time.sleep(0.8)
    info = detect_all_methods(code)
    v1m = info.get("v1", "") or ""
    lines = [
        f"🔬 Анализ завершён\n{DIVIDER}\n\n"
        f"📄 {filename}\n"
        f"📊 {info['lines']:,} строк · {info['chars']:,} символов\n"
        f"{DIVIDER}\n\n"
        f"МЕТОДЫ:\n\n"
    ]
    if v1m: lines.append(f"✅ v1: {v1m}\n")
    else:   lines.append(f"◽ v1: не обнаружен\n")

    flags = [
        ("exec() вызовы",   info.get("has_exec"),         "🔴"),
        ("Base64 данные",   info.get("has_base64"),        "🟡"),
        ("XOR",             info.get("has_xor"),           "🔴"),
        ("State-machine",   info.get("has_state_machine"), "🔴"),
        ("Call-wrappers",   info.get("has_wrappers"),      "🟡"),
        ("marshal",         info.get("has_marshal"),       "🔴"),
        ("PyArmor",         info.get("has_pyarmor"),       "⛔"),
        ("CFF dispatcher",  info.get("has_cff"),           "🔴"),
        ("MBA arithmetic",  info.get("has_mba"),           "🟡"),
        ("Opaque predicates",info.get("has_opaque"),       "🟡"),
        ("rot13",           info.get("has_rot13"),         "🟡"),
        ("[::-1] reverse",  info.get("has_reverse"),       "🟡"),
        ("bz2/lzma",        info.get("has_bz2") or info.get("has_lzma"), "🟡"),
    ]
    chr_n = info.get("has_chr", 0)
    if chr_n: flags.append((f"chr() × {chr_n}", True, "🟡"))

    lines.append(f"\n{DIVIDER_THIN}\nПРИЗНАКИ:\n\n")
    found = [(n, e) for n, v, e in flags if v]
    if found:
        for n, e in found: lines.append(f"  {e} {n}\n")
    else:
        lines.append("  ◽ Явных признаков не обнаружено\n")

    lines.append(f"\n{DIVIDER_THIN}\n💡 РЕКОМЕНДАЦИЯ:\n")
    if info.get("has_cff") or info.get("has_mba"): lines.append("  → 🆕 v4 (CFF+MBA) или ⚡ АВТО\n")
    elif v1m: lines.append(f"  → ⚡ АВТО или 🔓 v1\n")
    elif info.get("has_xor") or info.get("has_state_machine"): lines.append("  → ⚡ АВТО или 🔩 v2\n")
    else: lines.append("  → ⚡ АВТО — перебирает все методы\n")

    k = types.InlineKeyboardMarkup(row_width=1)
    k.add(types.InlineKeyboardButton("⚡ Декодировать АВТО", callback_data="mode_auto"))
    k.row(
        types.InlineKeyboardButton("🔓 v1", callback_data="mode_v1"),
        types.InlineKeyboardButton("🔩 v2", callback_data="mode_v2"),
        types.InlineKeyboardButton("🧬 v3", callback_data="mode_v3"),
        types.InlineKeyboardButton("🆕 v4", callback_data="mode_v4"),
    )
    k.add(types.InlineKeyboardButton("◀ Меню", callback_data="back_main"))
    _edit(cid, mid, "".join(lines), k)


def _do_auto(cid, mid, uid, filename, code, chars_in):
    face = random.choice(ASTOLFO_FACES)
    total = 4
    prev = ""

    _animate_auto(cid, mid, filename, chars_in, 1, total, face, prev)
    r, m = deobfuscate_v1(code)
    if r: _send_result(cid, mid, uid, filename, r, f"v1: {m}", chars_in, len(r), "auto"); return
    prev = "v1"

    _animate_auto(cid, mid, filename, chars_in, 2, total, face, prev)
    r, m = deobfuscate_v3(code)
    if r: _send_result(cid, mid, uid, filename, r, f"v3: {m}", chars_in, len(r), "auto"); return
    prev = "v1 v3"

    _animate_auto(cid, mid, filename, chars_in, 3, total, face, prev)
    r, m = deobfuscate_v4(code)
    if r: _send_result(cid, mid, uid, filename, r, f"v4: {m}", chars_in, len(r), "auto"); return
    prev = "v1 v3 v4"

    _animate_auto(cid, mid, filename, chars_in, 4, total, face, prev)
    result = deobfuscate_v2(code)
    _send_result(cid, mid, uid, filename, result, "v2: Ренди 2.0 (fallback)", chars_in, len(result), "auto")


def _do_exe(cid, mid, uid, data, filename):
    exe_type = detect_exe_type(data)
    face = random.choice(ASTOLFO_FACES)
    frames = [
        f"📦 EXE Extractor\n{DIVIDER}\n📄 {filename}\n💾 {len(data):,} байт\n🔍 {exe_type}\n\n{face}\n\n▱▱▱▱▱▱▱▱▱▱  0%",
        f"📦 EXE Extractor\n{DIVIDER}\n📄 {filename}\n💾 {len(data):,} байт\n🔍 {exe_type}\n\n{face}\n\n▰▰▰▱▱▱▱▱▱▱ 30%\n⏳ Сканирую сигнатуры...",
        f"📦 EXE Extractor\n{DIVIDER}\n📄 {filename}\n💾 {len(data):,} байт\n🔍 {exe_type}\n\n{face}\n\n▰▰▰▰▰▰▱▱▱▱ 60%\n⏳ Извлекаю Python блоки...",
        f"📦 EXE Extractor\n{DIVIDER}\n📄 {filename}\n💾 {len(data):,} байт\n🔍 {exe_type}\n\n{face}\n\n▰▰▰▰▰▰▰▰▰▰ 100% ✅\n⏳ Финализирую...",
    ]
    for frame in frames:
        try: bot.edit_message_text(frame, cid, mid)
        except: pass
        time.sleep(0.8)

    out_dir = tempfile.mkdtemp(prefix="togaff_")
    try:
        ok, msg_txt, files = extract_from_exe(data, out_dir, filename)
        icon = "✅" if ok else "⚠️"
        if not files:
            _edit(cid, mid, f"❌ Не удалось извлечь\n{DIVIDER}\n📄 {filename}\n🔍 {exe_type}\n{msg_txt}", kb_main(is_admin(uid))); return
        _edit(cid, mid, f"{icon} Готово!\n{DIVIDER}\n📄 {filename}\n🔍 {exe_type}\n{icon} {msg_txt}\n\n📂 Отправляю {min(len(files),15)} файлов...")
        sent = 0
        _typing(cid)
        for fp in files[:15]:
            try:
                with open(fp, "rb") as f:
                    bot.send_document(cid, f, visible_file_name=os.path.basename(fp), caption=f"📦 {exe_type} | {os.path.basename(fp)}")
                sent += 1; time.sleep(0.3)
            except Exception as e: print(f"[send_exe_file] {e}")
        if len(files) > 15: _send(cid, f"⚠️ Показаны {sent}/{len(files)} файлов")
        # Stats
        key = str(uid)
        if key in users:
            m_key = f"exe-{exe_type}"
            users[key].setdefault("methods", {})[m_key] = users[key]["methods"].get(m_key, 0) + 1
        update_stats(f"exe-{exe_type}"); save_all()
        log_action(f"EXE uid={uid} {filename} type={exe_type} files={len(files)}")
        face2 = random.choice(ASTOLFO_FACES)
        _send(cid, f"✅ Готово~ {face2}\n📦 {exe_type} → {sent} файлов\n\nОтправь ещё~ 💕", kb_main(is_admin(uid)))
    finally:
        try: shutil.rmtree(out_dir)
        except: pass


def _send_result(cid, mid, uid, filename, result, method, chars_in, chars_out, mode):
    face = random.choice(ASTOLFO_FACES)
    red  = max(0, round(100 * (1 - chars_out / max(chars_in, 1))))
    lines_out = result.count('\n') + 1 if result else 0
    _edit(cid, mid,
        f"✅ Декодировано! 🌸\n{DIVIDER}\n📄 {filename}\n\n{face}\n\n"
        f"▰▰▰▰▰▰▰▰▰▰ 100% ✅\n\n"
        f"🔑 Метод:    {method}\n"
        f"💬 Символов: {chars_in:,} → {chars_out:,}  (-{red}%)\n"
        f"📝 Строк:    {lines_out:,}"
    )
    time.sleep(0.3)
    out_name = "decoded_" + filename
    out_path = f"/tmp/togaff_{out_name}"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result)
        _typing(cid)
        with open(out_path, "rb") as f:
            bot.send_document(cid, f, visible_file_name=out_name,
                caption=f"🔓 {method}\n📄 {filename}\n💬 {chars_in:,} → {chars_out:,} (-{red}%)")
    except Exception as e: print(f"[send_result] {e}")
    finally:
        try: os.remove(out_path)
        except: pass
    # Stats
    key = str(uid)
    if key in users:
        m_key = method.split(":")[0].strip() if ":" in method else method
        users[key].setdefault("methods", {})[m_key] = users[key]["methods"].get(m_key, 0) + 1
    update_stats(method); save_all()
    log_action(f"DECODED uid={uid} {filename} method={method} {chars_in}→{chars_out}")
    _send(cid, f"{random.choice(DONE_MSGS)}\n\nОтправь ещё файл~ 💕", kb_after(mode))


def _send_fail(cid, mid, filename, reason, mode):
    face = random.choice(ASTOLFO_FACES)
    _edit(cid, mid,
        f"❌ Не удалось декодировать\n{DIVIDER}\n📄 {filename}\n\n{face}\n\n"
        f"Причина: {reason}\n\n💡 {random.choice(FAIL_MSGS)}~",
        kb_after(mode) if mode else kb_main()
    )


@bot.message_handler(func=lambda m: True)
def handle_any(msg):
    uid = msg.from_user.id
    if uid in _bcast and _bcast.get(uid): return
    if is_banned(uid): return
    if not is_allowed(uid): return
    _send(msg.chat.id,
        f"Привет~ 🌸\n\n{random.choice(ASTOLFO_FACES)}\n\n"
        f"Отправь файл, но сначала выбери режим!",
        kb_main(is_admin(uid)))

# ════════════════════════════════════════════════════════════════════
#  LAUNCH
# ════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("═" * 55)
    print(f"  🔓 {BOT_NAME} v{VERSION}  by {BOT_TAG}")
    print(f"  Admins:  {ADMIN_IDS}")
    print(f"  Users:   {len(users)}")
    print(f"  Access:  {'OPEN (everyone)' if OPEN_ACCESS else 'WHITELIST'}")
    print("═" * 55)
    print("🌸 Бот запущен~")
    bot.infinity_polling(timeout=30, long_polling_timeout=20)
