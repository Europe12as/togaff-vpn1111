"""
╔══════════════════════════════════════════════════════════════════════╗
║        🔓 TOGAFF DEOBFUSCATOR BOT v4.0  —  ALL-IN-ONE 🌸           ║
║        by @ArrhythmiaFucksn                                         ║
╠══════════════════════════════════════════════════════════════════════╣
║  ЗАПУСК:                                                            ║
║    pip install pyTelegramBotAPI uncompyle6                          ║
║    python3 togaff_deobf.py                                          ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import re, base64, zlib, gzip, lzma, bz2, marshal, types, dis, io
import struct, os, sys, codecs, ast, binascii, hashlib, hmac
import threading, subprocess, tempfile, shutil, zipfile, tarfile
import itertools, string, random
from typing import Optional, Tuple, List, Dict, Any

# ════════════════════════════════════════════════════════
#   УТИЛИТЫ
# ════════════════════════════════════════════════════════

DEOBF_TAG  = "# 🔓 DECODED BY @ArrhythmiaFucksn | TOGAFF DEOBFUSCATOR v4.0\n\n"
VERSION    = "4.0"

def _b64_pad(s: str) -> str:
    pad = len(s) % 4
    return s + "=" * (4 - pad) if pad else s

def _safe_decode(data: bytes, hints: list = None) -> str:
    encs = hints or ["utf-8", "utf-16-le", "utf-16-be", "latin-1", "cp1251", "cp1252", "ascii"]
    for enc in encs:
        try:
            return data.decode(enc)
        except: pass
    return data.decode("utf-8", errors="replace")

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

def _is_python(text: str, min_len: int = 30) -> bool:
    if len(text) < min_len: return False
    kws = ["def ", "class ", "import ", "print(", "return ", "if ", "for ", "while ",
           "__name__", "self.", "lambda ", "= ", "():", "():"]
    return sum(1 for k in kws if k in text) >= 2

def _try_marshal_to_source(code_obj) -> Optional[str]:
    for lib in ("uncompyle6", "decompile3"):
        try:
            m = __import__(lib)
            buf = io.StringIO()
            if hasattr(m, 'decompile_code'):
                m.decompile_code(code_obj, buf)
            elif hasattr(m, 'decompile'):
                m.decompile(sys.version_info[:2], code_obj, buf)
            r = buf.getvalue()
            if r and len(r) > 5: return r
        except: pass
    try:
        buf = io.StringIO()
        dis.dis(code_obj, file=buf)
        return f"# [bytecode disassembly — install uncompyle6 for source]\n{buf.getvalue()}"
    except: pass
    return None

def _marshal_loads_safe(data: bytes) -> Optional[Any]:
    for offset in (0, 4, 8, 12, 16, 20):
        try:
            obj = marshal.loads(data[offset:])
            return obj
        except: pass
    return None

# ════════════════════════════════════════════════════════
#   V1 — BASE ENCODING + COMPRESSION
# ════════════════════════════════════════════════════════

_EXEC_PATS = [
    re.compile(r'exec\s*\(\s*\(?\s*_+\s*\)?\s*\(\s*b[\'\"]([\s\S]+?)[\'\"]\s*\)\s*\)', re.DOTALL),
    re.compile(r'exec\s*\(\s*\(?\s*_+\s*\)?\s*\(\s*[\'\"]([\s\S]+?)[\'\"]\s*\)\s*\)',  re.DOTALL),
    re.compile(r'exec\s*\(\s*_+\s*\(\s*b?[\'\"]([\s\S]+?)[\'\"]\s*\)\s*\)',             re.DOTALL),
]

_V1_LAMBDA_MAP = {
    "base64":     r"_\s*=\s*lambda\s+__\s*:\s*__import__\('base64'\)\.b64decode\(__\[::-1\]\)",
    "base32":     r"_\s*=\s*lambda\s+__\s*:\s*__import__\('base64'\)\.b32decode\(__\[::-1\]\)",
    "base16":     r"_\s*=\s*lambda\s+__\s*:\s*__import__\('base64'\)\.b16decode\(__\[::-1\]\)",
    "zlib":       r"_\s*=\s*lambda\s+__\s*:\s*__import__\('zlib'\)\.decompress\(__\[::-1\]\)",
    "gzip":       r"_\s*=\s*lambda\s+__\s*:\s*__import__\('gzip'\)\.decompress\(__\[::-1\]\)",
    "lzma":       r"_\s*=\s*lambda\s+__\s*:\s*__import__\('lzma'\)\.decompress\(__\[::-1\]\)",
    "bz2":        r"_\s*=\s*lambda\s+__\s*:\s*__import__\('bz2'\)\.decompress\(__\[::-1\]\)",
    "base64+zlib":r"_\s*=\s*lambda\s+__\s*:.*?zlib.*?b64decode",
    "base64+gzip":r"_\s*=\s*lambda\s+__\s*:.*?gzip.*?b64decode",
    "base64+lzma":r"_\s*=\s*lambda\s+__\s*:.*?lzma.*?b64decode",
    "base64+bz2": r"_\s*=\s*lambda\s+__\s*:.*?bz2.*?b64decode",
    "base32+zlib":r"_\s*=\s*lambda\s+__\s*:.*?zlib.*?b32decode",
    "base32+gzip":r"_\s*=\s*lambda\s+__\s*:.*?gzip.*?b32decode",
    "base32+lzma":r"_\s*=\s*lambda\s+__\s*:.*?lzma.*?b32decode",
    "base16+zlib":r"_\s*=\s*lambda\s+__\s*:.*?zlib.*?b16decode",
    "base16+gzip":r"_\s*=\s*lambda\s+__\s*:.*?gzip.*?b16decode",
    "base16+lzma":r"_\s*=\s*lambda\s+__\s*:.*?lzma.*?b16decode",
    "rendy":      r"_\s*=\s*lambda\s+__\s*:.*?marshal.*?gzip.*?lzma.*?zlib.*?base64",
}

def _v1_detect(code: str) -> Optional[str]:
    for name, pat in _V1_LAMBDA_MAP.items():
        if re.search(pat, code, re.DOTALL): return name
    for pat in _EXEC_PATS:
        if pat.search(code):
            if "marshal" in code and "gzip" in code: return "rendy"
            if "b64decode" in code:
                for c, n in [("zlib","base64+zlib"),("gzip","base64+gzip"),("lzma","base64+lzma"),("bz2","base64+bz2")]:
                    if c in code: return n
                return "base64"
            if "b32decode" in code:
                for c, n in [("zlib","base32+zlib"),("gzip","base32+gzip"),("lzma","base32+lzma")]:
                    if c in code: return n
                return "base32"
            if "b16decode" in code:
                for c, n in [("zlib","base16+zlib"),("gzip","base16+gzip"),("lzma","base16+lzma")]:
                    if c in code: return n
                return "base16"
            for c, n in [("zlib","zlib"),("gzip","gzip"),("lzma","lzma"),("bz2","bz2")]:
                if c in code: return n
    return None

def _v1_exec_sub(code: str, fn) -> str:
    changed = True; passes = 0
    while changed and passes < 25:
        changed = False; passes += 1
        for pat in _EXEC_PATS:
            def rep(m):
                try: return fn(m.group(1))
                except Exception as e: return f"# [decode_err: {e}]\n"
            new = pat.sub(rep, code)
            if new != code: code = new; changed = True
    return code

def _v1_deobf(code: str, method: str) -> str:
    decode_map = {
        "base64":     lambda s: _safe_decode(base64.b64decode(_b64_pad(s[::-1]))),
        "base32":     lambda s: _safe_decode(base64.b32decode(_b64_pad(s[::-1]).upper())),
        "base16":     lambda s: _safe_decode(base64.b16decode(s[::-1].upper())),
        "zlib":       lambda s: _safe_decode(zlib.decompress(s[::-1].encode("latin-1"))),
        "gzip":       lambda s: _safe_decode(gzip.decompress(s[::-1].encode("latin-1"))),
        "lzma":       lambda s: _safe_decode(lzma.decompress(s[::-1].encode("latin-1"))),
        "bz2":        lambda s: _safe_decode(bz2.decompress(s[::-1].encode("latin-1"))),
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
        "rendy":      None,
    }
    if method == "rendy": return _v1_rendy(code)
    fn = decode_map.get(method)
    if not fn: return code
    result = _v1_exec_sub(code, fn)
    # Удаляем lambda-определение
    result = re.sub(r"_\s*=\s*lambda\s+__\s*:.*?(?:;|\n)", "", result, flags=re.DOTALL)
    result = _strip_comments(result)
    return _clean(result)

def _v1_rendy(code: str) -> str:
    patterns = [
        r"exec\s*\(\s*_\s*\(\s*b['\"]([A-Za-z0-9+/=\r\n]+)['\"]\s*\)\s*\)",
        r"exec\s*\(\s*_+\s*\(\s*['\"]([A-Za-z0-9+/=\r\n]+)['\"]\s*\)\s*\)",
        r"b['\"]([A-Za-z0-9+/=\n]{80,})['\"]",
    ]
    for pat in patterns:
        for m in re.finditer(pat, code, re.DOTALL):
            enc = re.sub(r'[\r\n\s]', '', m.group(1))
            # Пробуем все варианты rendy
            combos = [
                lambda d: marshal.loads(gzip.decompress(lzma.decompress(zlib.decompress(base64.b64decode(_b64_pad(d[::-1])))))),
                lambda d: marshal.loads(zlib.decompress(lzma.decompress(gzip.decompress(base64.b64decode(_b64_pad(d[::-1])))))),
                lambda d: marshal.loads(lzma.decompress(gzip.decompress(zlib.decompress(base64.b64decode(_b64_pad(d[::-1])))))),
                lambda d: marshal.loads(zlib.decompress(base64.b64decode(_b64_pad(d[::-1])))),
                lambda d: marshal.loads(gzip.decompress(base64.b64decode(_b64_pad(d[::-1])))),
                lambda d: marshal.loads(lzma.decompress(base64.b64decode(_b64_pad(d[::-1])))),
            ]
            for combo in combos:
                try:
                    obj = combo(enc)
                    if isinstance(obj, bytes): return DEOBF_TAG + _safe_decode(obj)
                    if isinstance(obj, types.CodeType):
                        src = _try_marshal_to_source(obj)
                        if src: return DEOBF_TAG + src
                    return DEOBF_TAG + str(obj)
                except: pass
    return code

def deobfuscate_v1(code: str) -> Tuple[Optional[str], str]:
    method = _v1_detect(code)
    if not method: return None, "v1: паттерн не обнаружен"
    try:
        result = _v1_deobf(code, method)
        if result and result.strip() != code.strip() and len(result) > 10:
            return DEOBF_TAG + result, method
        return None, f"v1: не удалось декодировать ({method})"
    except Exception as e:
        return None, f"v1 error: {e}"

# ════════════════════════════════════════════════════════
#   V2 — РЕНДИ 2.0 UNIVERSAL
# ════════════════════════════════════════════════════════

def _r2_decompress_chain(data: bytes, depth=0, max_depth=16) -> bytes:
    if depth >= max_depth: return data
    for fn in [
        lambda d: base64.b64decode(d + b"=="),
        lambda d: base64.b64decode(d[::-1] + b"=="),
        zlib.decompress,
        gzip.decompress,
        lzma.decompress,
        bz2.decompress,
    ]:
        try:
            r = fn(data)
            if r and r != data and len(r) > 5:
                deeper = _r2_decompress_chain(r, depth+1, max_depth)
                return deeper if deeper != r else r
        except: pass
    # Marshal
    obj = _marshal_loads_safe(data)
    if obj:
        if isinstance(obj, bytes): return _r2_decompress_chain(obj, depth+1, max_depth)
        if isinstance(obj, types.CodeType):
            src = _try_marshal_to_source(obj)
            if src: return src.encode()
    return data

def _r2_extract_blobs(source: str) -> List[str]:
    results = []
    for pat in [
        r"b['\"]([A-Za-z0-9+/=\r\n]{80,})['\"]",
        r"['\"]([A-Za-z0-9+/=\r\n]{200,})['\"]",
    ]:
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
    # Pattern: bytes([b ^ KEY for b in bytes.fromhex('...')])
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
    # zip xor
    zip_pat = re.compile(
        r"bytes\(\[a\s*\^\s*b\s+for\s+a\s*,\s*b\s+in\s+zip\("
        r"bytes\.fromhex\(['\"]([0-9a-fA-F]+)['\"]\)\s*,.*?"
        r"bytes\.fromhex\(['\"]([0-9a-fA-F]+)['\"]\).*?\)\]\)"
    )
    def zip_rep(m):
        try:
            data = bytes.fromhex(m.group(1)); key = bytes.fromhex(m.group(2))
            return repr(bytes([a ^ key[i % len(key)] for i, a in enumerate(data)]).decode("utf-8", errors="replace"))
        except: return m.group(0)
    source = zip_pat.sub(zip_rep, source)
    return source

def _r2_decode_hex_escapes(source: str) -> str:
    for pat, decode in [
        (re.compile(r"b'((?:\\x[0-9a-fA-F]{2}){4,})'"),
         lambda m: repr(_safe_decode(bytes.fromhex(re.sub(r'\\x', '', m.group(1)))))),
        (re.compile(r'b"((?:\\x[0-9a-fA-F]{2}){4,})"'),
         lambda m: repr(_safe_decode(bytes.fromhex(re.sub(r'\\x', '', m.group(1)))))),
    ]:
        try: source = pat.sub(decode, source)
        except: pass
    return source

def _r2_decode_unicode_escapes(source: str) -> str:
    pat = re.compile(r"'((?:\\u[0-9a-fA-F]{4}){3,})'")
    def rep(m):
        try: return repr(m.group(1).encode().decode("unicode_escape"))
        except: return m.group(0)
    return pat.sub(rep, source)

def _r2_decode_b64_arrays(source: str) -> str:
    pat = re.compile(
        r'(\w+)\s*=\s*\[([\'"][A-Za-z0-9+/=]+[\'"](?:\s*,\s*[\'"][A-Za-z0-9+/=]+[\'"])+)\s*\]'
    )
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

def _r2_decode_exec_eval(source: str) -> str:
    pats = [
        (re.compile(r"exec\s*\(\s*(?:base64\.b64decode|__import__\(['\"]base64['\"]\)\.b64decode)\s*\(\s*b?['\"]([A-Za-z0-9+/=]+)['\"]\s*\)(?:\.decode\([^)]*\))?\s*\)"),
         lambda m: _safe_decode(base64.b64decode(_b64_pad(m.group(1))))),
        (re.compile(r"exec\s*\(\s*zlib\.decompress\s*\(\s*base64\.b64decode\s*\(\s*b?['\"]([A-Za-z0-9+/=]+)['\"]\s*\)\s*\)(?:\.decode\([^)]*\))?\s*\)"),
         lambda m: _safe_decode(zlib.decompress(base64.b64decode(_b64_pad(m.group(1)))))),
        (re.compile(r"exec\s*\(\s*gzip\.decompress\s*\(\s*base64\.b64decode\s*\(\s*b?['\"]([A-Za-z0-9+/=]+)['\"]\s*\)\s*\)(?:\.decode\([^)]*\))?\s*\)"),
         lambda m: _safe_decode(gzip.decompress(base64.b64decode(_b64_pad(m.group(1)))))),
    ]
    for pat, fn in pats:
        def make_rep(f):
            def rep(m):
                try: return f(m)
                except: return m.group(0)
            return rep
        try: source = pat.sub(make_rep(fn), source)
        except: pass
    return source

def _r2_simplify_wrappers(source: str) -> str:
    wrapper_names = list(set(re.findall(
        r'def\s+(\w+)\s*\(\s*\w+\s*,\s*\w+\s*,\s*\w+\s*\)', source
    )))
    wrapper_names = [w for w in wrapper_names if len(w) >= 3]
    if not wrapper_names: return source
    for wname in wrapper_names:
        for _ in range(8):
            new = re.sub(
                re.escape(wname) + r'\s*\(\s*([^,\n]+?)\s*,\s*\[([^\[\]\n]*?)\]\s*,\s*\{\s*\}\s*\)',
                lambda m: f'{m.group(1).strip()}({m.group(2).strip()})' if m.group(2).strip() else f'{m.group(1).strip()}()',
                source
            )
            new = re.sub(
                re.escape(wname) + r'\s*\(\s*([^,\n]+?)\s*,\s*\[([^\[\]\n]*?)\]\s*,\s*\{([^{}\n]+?)\}\s*\)',
                lambda m: f'{m.group(1).strip()}({m.group(2).strip()}, {re.sub(chr(39)+"(\\w+)"+chr(39)+r":\s*", r"\1=", m.group(3).strip())})',
                new
            )
            if new == source: break
            source = new
    return source

def _r2_remove_state_machine(source: str) -> str:
    lines = source.split('\n'); result = []; i = 0
    while i < len(lines):
        line = lines[i]; s = line.strip()
        indent = len(line) - len(line.lstrip()) if s else 0
        if re.match(r'^while\s+\w+\s*!=\s*\d+\s*:\s*$', s): i += 1; continue
        if re.match(r'^(?:if|elif)\s+\w+\s*==\s*\d{4,}\s*:\s*$', s): i += 1; continue
        if re.match(r'^\w+\s*=\s*\d{5,}\s*$', s): i += 1; continue
        if re.match(r'^if\s+\([^)]+\)\s*%\s*2\s*==\s*0\s*:\s*$', s):
            i += 1
            while i < len(lines):
                bl = lines[i]; bs = bl.strip()
                if bs and (len(bl)-len(bl.lstrip())) <= indent: break
                if bs: result.append(bl[4:] if bl.startswith('    ') else bl)
                i += 1
            continue
        result.append(line); i += 1
    return '\n'.join(result)

def _r2_remove_dummies(source: str) -> str:
    lines = source.split('\n'); result = []
    for line in lines:
        s = line.strip()
        m = re.match(r'^(\w+)\s*=\s*(?:\d+|None|True|False|["\'][^"\']{0,20}["\'])\s*$', s)
        if m:
            vname = m.group(1)
            if (vname.startswith('_') and vname.count('_') >= 2) or re.match(r'^[a-z]{1,3}[0-9]+$', vname):
                if len(re.findall(r'\b' + re.escape(vname) + r'\b', source)) <= 2:
                    continue
        result.append(line)
    return '\n'.join(result)

def _r2_simplify_getattr(source: str) -> str:
    source = re.sub(r"getattr\((\w+),\s*['\"]([a-zA-Z_]\w*)['\"](?:,\s*None)?\)", r"\1.\2", source)
    source = re.sub(r"getattr\(__import__\(['\"](\w+)['\"]\),\s*['\"]([a-zA-Z_]\w*)['\"].*?\)", r"__import__('\1').\2", source)
    return source

def _r2_decode_decimal_array(source: str) -> str:
    # exec(''.join(chr(x) for x in [72,101,108,108,111]))
    pat = re.compile(
        r"exec\s*\(\s*['\"]?\s*['\"]?\s*\.join\s*\(\s*chr\s*\([^)]+\)\s+for\s+\w+\s+in\s+\[([0-9,\s]+)\]\s*\)\s*['\"]?\s*\)"
    )
    def rep(m):
        try:
            nums = [int(x.strip()) for x in m.group(1).split(",") if x.strip()]
            return "".join(chr(n) for n in nums)
        except: return m.group(0)
    return pat.sub(rep, source)

def _r2_decode_chr_join(source: str) -> str:
    # ''.join([chr(72), chr(101), ...])
    pat = re.compile(r"['\"]?\s*['\"]?\s*\.join\s*\(\s*\[?((?:chr\s*\(\s*\d+\s*\)\s*(?:,\s*)?){3,})\]?\s*\)")
    def rep(m):
        nums = re.findall(r'chr\s*\(\s*(\d+)\s*\)', m.group(1))
        try: return repr("".join(chr(int(n)) for n in nums))
        except: return m.group(0)
    return pat.sub(rep, source)

def _r2_decode_octal(source: str) -> str:
    # b'\101\102\103' -> 'ABC'
    pat = re.compile(r"b'((?:\\[0-7]{1,3}){4,})'")
    def rep(m):
        try:
            raw = bytes([int(x, 8) for x in re.findall(r'\\([0-7]{1,3})', m.group(1))])
            return repr(_safe_decode(raw))
        except: return m.group(0)
    return pat.sub(rep, source)

def _r2_decode_binary_strings(source: str) -> str:
    # int('01001000', 2)
    pat = re.compile(r"int\s*\(\s*['\"]([01]{8,})['\"],\s*2\s*\)")
    def rep(m):
        try: return str(int(m.group(1), 2))
        except: return m.group(0)
    return pat.sub(rep, source)

def deobfuscate_v2(source: str) -> str:
    original = source
    # 1. Binary payload extraction
    blobs = _r2_extract_blobs(source)
    if blobs:
        best = max(blobs, key=len)
        if len(best) > max(len(source) * 0.25, 100):
            source = best
    # 2. exec/eval static decode
    source = _r2_decode_exec_eval(source)
    # 3. XOR strings
    source = _r2_decode_xor(source)
    # 4. Hex escapes
    source = _r2_decode_hex_escapes(source)
    # 5. Unicode escapes
    source = _r2_decode_unicode_escapes(source)
    # 6. Base64 arrays
    source = _r2_decode_b64_arrays(source)
    # 7. Decimal arrays / chr joins
    source = _r2_decode_decimal_array(source)
    source = _r2_decode_chr_join(source)
    # 8. Octal / binary
    source = _r2_decode_octal(source)
    source = _r2_decode_binary_strings(source)
    # 9. Call wrappers
    source = _r2_simplify_wrappers(source)
    # 10. State machine
    source = _r2_remove_state_machine(source)
    # 11. Dummy vars
    source = _r2_remove_dummies(source)
    # 12. getattr
    source = _r2_simplify_getattr(source)
    # 13. Cleanup
    source = _clean(source)
    if source == original:
        return DEOBF_TAG + "# [v2: явных трансформаций не обнаружено]\n\n" + source
    return DEOBF_TAG + source

# ════════════════════════════════════════════════════════
#   V3 — ПОПУЛЯРНЫЕ МЕТОДЫ
# ════════════════════════════════════════════════════════

def _v3_rot13(code: str) -> Tuple[Optional[str], str]:
    patterns = [
        re.compile(r"exec\s*\(\s*codecs\.decode\s*\(['\"](.+?)['\"]\s*,\s*['\"]rot[_-]?13['\"]\s*\)\s*\)", re.DOTALL),
        re.compile(r"exec\s*\(\s*['\"](.+?)['\"]\s*\.encode\(\)\s*\.decode\s*\(['\"]rot[_-]?13['\"]\s*\)\s*\)", re.DOTALL),
        re.compile(r"exec\s*\(\s*codecs\.encode\s*\(['\"](.+?)['\"]\s*,\s*['\"]rot[_-]?13['\"]\s*\)\s*\)", re.DOTALL),
    ]
    for pat in patterns:
        m = pat.search(code)
        if m:
            try: return DEOBF_TAG + codecs.decode(m.group(1), 'rot_13'), "rot13"
            except: pass
    # Whole-file rot13
    if "rot_13" in code or "rot-13" in code.lower() or "'rot13'" in code.lower():
        for m2 in re.finditer(r"['\"]([a-zA-Z0-9+/=\\]{100,})['\"]", code):
            try:
                dec = codecs.decode(m2.group(1), 'rot_13')
                if _is_python(dec): return DEOBF_TAG + dec, "rot13"
            except: pass
    return None, ""

def _v3_xor_fixed(code: str) -> Tuple[Optional[str], str]:
    # exec(bytes([b ^ KEY for b in b'...']))
    patterns = [
        (re.compile(r"(?:key|KEY|_k)\s*=\s*(0x[0-9a-fA-F]+|\d+).*?(?:data|_d|payload)\s*=\s*b['\"](.+?)['\"]\s*.*?exec\s*\(\s*bytes\s*\(\s*\[\s*b\s*\^\s*(?:key|KEY|_k)\s+for\s+b\s+in\s+(?:data|_d|payload)", re.DOTALL),
         lambda m: bytes([b ^ int(m.group(1),0) for b in m.group(2).encode("latin-1").decode("unicode_escape").encode("latin-1")])),
        (re.compile(r"exec\s*\(\s*bytes\s*\(\s*\[\s*b\s*\^\s*(\d+)\s+for\s+b\s+in\s+b['\"](.+?)['\"]\s*\]\s*\)\s*\)"),
         lambda m: bytes([b ^ int(m.group(1)) for b in m.group(2).encode("latin-1").decode("unicode_escape").encode("latin-1")])),
        (re.compile(r"exec\s*\(\s*bytes\s*\(\s*\[\s*b\s*\^\s*(\d+)\s+for\s+b\s+in\s+bytes\.fromhex\s*\(\s*['\"]([0-9a-fA-F]+)['\"]\s*\)\s*\]\s*\)\s*\)"),
         lambda m: bytes([b ^ int(m.group(1)) for b in bytes.fromhex(m.group(2))])),
    ]
    for pat, dec in patterns:
        m = pat.search(code)
        if m:
            try:
                result = _safe_decode(dec(m))
                if _is_python(result): return DEOBF_TAG + result, "xor-fixed-key"
            except: pass
    return None, ""

def _v3_plain_b64(code: str) -> Tuple[Optional[str], str]:
    pats = [
        re.compile(r"exec\s*\(\s*base64\.b64decode\s*\(\s*b?['\"]([A-Za-z0-9+/=]{20,})['\"]", re.DOTALL),
        re.compile(r"exec\s*\(\s*__import__\(['\"]base64['\"]\)\.b64decode\s*\(\s*b?['\"]([A-Za-z0-9+/=]{20,})['\"]", re.DOTALL),
    ]
    for pat in pats:
        for m in pat.finditer(code):
            enc = m.group(1).replace("\n","").replace(" ","")
            try:
                dec = base64.b64decode(_b64_pad(enc)).decode("utf-8")
                if len(dec) > 5:
                    result = dec
                    for _ in range(15):
                        found = False
                        for pat2 in pats:
                            m2 = pat2.search(result)
                            if m2:
                                enc2 = m2.group(1).replace("\n","").replace(" ","")
                                try: result = base64.b64decode(_b64_pad(enc2)).decode("utf-8"); found = True; break
                                except: pass
                        if not found: break
                    return DEOBF_TAG + result, "plain-base64"
            except: pass
    return None, ""

def _v3_multilayer_b64(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(
        r"exec\s*\(\s*(?:base64\.b64decode|__import__\(['\"]base64['\"]\)\.b64decode)\s*\(['\"]?([A-Za-z0-9+/=\n]+)['\"]?\s*\)"
    )
    current = code; layers = 0
    while layers < 30:
        m = pat.search(current)
        if not m: break
        enc = re.sub(r'\s','', m.group(1))
        try: current = base64.b64decode(_b64_pad(enc)).decode("utf-8"); layers += 1
        except: break
    if layers >= 2:
        return DEOBF_TAG + f"# Снято слоёв base64: {layers}\n\n" + current, f"multilayer-base64 ({layers} layers)"
    return None, ""

def _v3_hex_exec(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"exec\s*\(\s*['\"]([\\x0-9a-fA-F\\u0-9a-fA-F]{20,})['\"](?:\.encode\(\))?\s*\)")
    m = pat.search(code)
    if m:
        try:
            raw = m.group(1).encode("latin-1").decode("unicode_escape")
            if _is_python(raw): return DEOBF_TAG + raw, "hex-exec"
        except: pass
    return None, ""

def _v3_compile_marshal(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(
        r"marshal\.loads\s*\(\s*(?:(?:zlib|gzip|lzma)\.decompress\s*\()?(?:base64\.b64decode\s*\()?['\"]([A-Za-z0-9+/=\n]+)['\"]\)?(?:\))?\s*\)"
    )
    for m in pat.finditer(code, re.DOTALL):
        enc = re.sub(r'\s','', m.group(1))
        for transform in [
            lambda x: base64.b64decode(_b64_pad(x)),
            lambda x: zlib.decompress(base64.b64decode(_b64_pad(x))),
            lambda x: gzip.decompress(base64.b64decode(_b64_pad(x))),
            lambda x: lzma.decompress(base64.b64decode(_b64_pad(x))),
            lambda x: base64.b64decode(_b64_pad(x[::-1])),
            lambda x: zlib.decompress(base64.b64decode(_b64_pad(x[::-1]))),
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
    chr_count = len(re.findall(r'\bchr\s*\(\s*\d+\s*\)', code))
    if chr_count < 5: return None, ""
    result = re.sub(r'chr\s*\(\s*(\d+)\s*\)', lambda m: repr(chr(int(m.group(1)))), code)
    for _ in range(10):
        new = re.sub(r"'([^'\\]*)'\s*\+\s*'([^'\\]*)'", lambda m: repr(m.group(1)+m.group(2)), result)
        if new == result: break
        result = new
    if result != code:
        return DEOBF_TAG + f"# chr() раскрыто: {chr_count} вызовов\n\n" + result, f"chr-obfuscate ({chr_count})"
    return None, ""

def _v3_pyarmor(code: str) -> Tuple[Optional[str], str]:
    if "__pyarmor__" not in code and "pyarmor_runtime" not in code: return None, ""
    result = re.sub(r"from\s+pyarmor_runtime\s+import.*?\n", "", code)
    result = re.sub(r"import\s+pyarmor_runtime.*?\n", "", result)
    result = re.sub(r"__pyarmor__\s*\([^)]+\)", "# [PyArmor call removed]", result)
    note = (
        "# ⚠️  PYARMOR — полный декод без ключа невозможен\n"
        "# Wrapper удалён. Зашифрованный payload остался.\n\n"
    )
    return DEOBF_TAG + note + result, "pyarmor (partial)"

def _v3_hyperion(code: str) -> Tuple[Optional[str], str]:
    if not (re.search(r'range\s*\(\s*256\s*\)', code) and
            re.search(r'def\s+\w+\s*\(\s*\w+\s*,\s*\w+\s*\)', code)):
        return None, ""
    # Пробуем выполнить RC4-подобный cipher статически
    note = (
        "# ⚠️  HYPERION — RC4-like cipher обнаружен\n"
        "# Для декода нужен динамический анализ\n\n"
    )
    return DEOBF_TAG + note + code, "hyperion (detected)"

def _v3_opy(code: str) -> Tuple[Optional[str], str]:
    if "__pragma__" not in code and not re.search(r'\bO0O0O0\b|\bO0O0\b|\bl1l1l1\b', code): return None, ""
    result = re.sub(r"__pragma__\s*\([^)]+\)", "", code)
    result = _clean(result)
    if result != code: return DEOBF_TAG + result, "opy"
    return None, ""

def _v3_reverse_string(code: str) -> Tuple[Optional[str], str]:
    # exec('...string...'[::-1])
    pat = re.compile(r"exec\s*\(\s*['\"](.{30,})['\"](?:\s*\.\s*encode\(\))?\s*\[\s*::-1\s*\]\s*(?:\.decode\([^)]*\))?\s*\)")
    m = pat.search(code)
    if m:
        try:
            dec = m.group(1)[::-1]
            if _is_python(dec): return DEOBF_TAG + dec, "reverse-string"
        except: pass
    return None, ""

def _v3_lambda_chain(code: str) -> Tuple[Optional[str], str]:
    # (lambda x: (lambda y: exec(y))(base64.b64decode(x)))('...')
    pat = re.compile(
        r"\(lambda\s+\w+\s*:.*?exec.*?\)\s*\(\s*['\"]([A-Za-z0-9+/=]{30,})['\"]",
        re.DOTALL
    )
    m = pat.search(code)
    if m:
        enc = m.group(1).replace("\n","")
        for fn in [
            lambda x: base64.b64decode(_b64_pad(x)).decode(),
            lambda x: base64.b64decode(_b64_pad(x[::-1])).decode(),
            lambda x: zlib.decompress(base64.b64decode(_b64_pad(x))).decode(),
        ]:
            try:
                dec = fn(enc)
                if _is_python(dec): return DEOBF_TAG + dec, "lambda-chain"
            except: pass
    return None, ""

def _v3_caesar(code: str) -> Tuple[Optional[str], str]:
    # exec(bytes([b-N for b in b'...']))
    for shift in range(1, 256):
        pat = re.compile(
            r"exec\s*\(\s*bytes\s*\(\s*\[\s*b\s*-\s*" + str(shift) + r"\s+for\s+b\s+in\s+b['\"](.+?)['\"]\s*\]\s*\)\s*(?:\.decode\([^)]*\))?\s*\)"
        )
        m = pat.search(code)
        if m:
            try:
                raw = bytes([(b - shift) % 256 for b in m.group(1).encode("latin-1").decode("unicode_escape").encode("latin-1")])
                dec = _safe_decode(raw)
                if _is_python(dec): return DEOBF_TAG + dec, f"caesar (shift={shift})"
            except: pass
    return None, ""

def _v3_base85(code: str) -> Tuple[Optional[str], str]:
    # exec(base64.b85decode('...'))
    pat = re.compile(r"exec\s*\(\s*(?:base64\.b85decode|__import__\(['\"]base64['\"]\)\.b85decode)\s*\(\s*b?['\"]([A-Za-z0-9!#$%&()*+\-;<=>?@^_`{|}~]{20,})['\"]")
    m = pat.search(code)
    if m:
        try:
            dec = base64.b85decode(m.group(1)).decode("utf-8")
            if _is_python(dec): return DEOBF_TAG + dec, "base85"
        except: pass
    return None, ""

def _v3_base32_plain(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"exec\s*\(\s*(?:base64\.b32decode|__import__\(['\"]base64['\"]\)\.b32decode)\s*\(\s*b?['\"]([A-Z2-7=]{20,})['\"]")
    m = pat.search(code)
    if m:
        try:
            dec = base64.b32decode(_b64_pad(m.group(1))).decode("utf-8")
            if len(dec) > 5: return DEOBF_TAG + dec, "plain-base32"
        except: pass
    return None, ""

def _v3_string_split_join(code: str) -> Tuple[Optional[str], str]:
    # ''.join(['pa','rt','1','...'])
    pat = re.compile(r"exec\s*\(\s*['\"]['\"]\.join\s*\(\s*\[([^\]]{20,})\]\s*\)\s*\)")
    m = pat.search(code)
    if m:
        try:
            parts = re.findall(r"['\"]([^'\"]*)['\"]", m.group(1))
            joined = "".join(parts)
            if _is_python(joined): return DEOBF_TAG + joined, "string-split-join"
        except: pass
    return None, ""

def _v3_builtins_hide(code: str) -> Tuple[Optional[str], str]:
    # getattr(__builtins__, 'exec')('...')
    pat = re.compile(
        r"getattr\s*\(\s*(?:__builtins__|builtins)\s*,\s*['\"]exec['\"]\s*\)\s*\(\s*['\"](.{30,})['\"]"
    )
    m = pat.search(code)
    if m:
        raw = m.group(1)
        if _is_python(raw): return DEOBF_TAG + raw, "builtins-hide"
    return None, ""

def _v3_decimal_array(code: str) -> Tuple[Optional[str], str]:
    # exec(''.join(chr(x) for x in [72,101,...]))
    pat = re.compile(
        r"exec\s*\(\s*['\"]?\s*['\"]?\s*\.join\s*\(\s*(?:map\s*\(\s*chr\s*,|chr\s*\([^)]+\)\s+for\s+\w+\s+in)\s*\[([0-9,\s]+)\]"
    )
    m = pat.search(code)
    if m:
        try:
            nums = [int(x.strip()) for x in m.group(1).split(",") if x.strip()]
            dec = "".join(chr(n) for n in nums)
            if _is_python(dec): return DEOBF_TAG + dec, "decimal-array"
        except: pass
    # map(chr, [...])
    pat2 = re.compile(r"exec\s*\(\s*['\"]?\s*['\"]?\s*\.join\s*\(\s*map\s*\(\s*chr\s*,\s*\[([0-9,\s]+)\]\s*\)\s*\)")
    m2 = pat2.search(code)
    if m2:
        try:
            nums = [int(x.strip()) for x in m2.group(1).split(",") if x.strip()]
            dec = "".join(chr(n) for n in nums)
            if _is_python(dec): return DEOBF_TAG + dec, "map-chr"
        except: pass
    return None, ""

def _v3_eval_b64(code: str) -> Tuple[Optional[str], str]:
    # eval(base64.b64decode(...))
    pat = re.compile(r"eval\s*\(\s*base64\.b64decode\s*\(\s*b?['\"]([A-Za-z0-9+/=]{20,})['\"]")
    m = pat.search(code)
    if m:
        try:
            dec = base64.b64decode(_b64_pad(m.group(1))).decode("utf-8")
            if len(dec) > 5: return DEOBF_TAG + dec, "eval-base64"
        except: pass
    return None, ""

def _v3_rc4(code: str) -> Tuple[Optional[str], str]:
    # Ищем RC4-подобный код
    if not (re.search(r'range\s*\(256\)', code) and re.search(r'swap|S\[|KSA|PRGA', code, re.I)):
        return None, ""
    # RC4 implementation in code — детектируем и сообщаем
    return DEOBF_TAG + "# ⚠️  RC4 шифрование обнаружено\n# Нужен ключ для декодирования\n\n" + code, "rc4 (detected)"

def _v3_fake_import(code: str) -> Tuple[Optional[str], str]:
    # import-like obf: __import__('os').__class__.__mro__[...]
    if "__class__.__mro__" not in code and "__subclasses__" not in code: return None, ""
    # Разворачиваем цепочки
    result = re.sub(r"__import__\s*\(\s*['\"](\w+)['\"]\s*\)", r"__import__('\1')", code)
    if result != code:
        return DEOBF_TAG + "# Цепочки импортов упрощены\n\n" + result, "fake-import-chains"
    return None, ""

def _v3_swap_bytes(code: str) -> Tuple[Optional[str], str]:
    # bytes are swapped pairs: b'\x68\x65' -> 'eh'
    pat = re.compile(
        r"exec\s*\(\s*bytes\s*\(\s*\[b\[i\+1\]\s+if\s+i\s*%\s*2\s*==\s*0\s+else\s+b\[i-1\]\s+for\s+i.*?\]\s*\)"
    )
    m = pat.search(code)
    if m: return DEOBF_TAG + "# Swap-bytes obfuscation detected\n\n" + code, "swap-bytes (detected)"
    return None, ""

def _v3_pyc_decompile(pyc_data: bytes) -> Tuple[Optional[str], str]:
    # Пробуем uncompyle6
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
    # Пробуем marshal + dis
    for offset in (8, 12, 16):
        try:
            obj = marshal.loads(pyc_data[offset:])
            if isinstance(obj, types.CodeType):
                src = _try_marshal_to_source(obj)
                if src: return DEOBF_TAG + src, "pyc-marshal"
        except: pass
    return None, "pyc: не удалось декомпилировать (установи uncompyle6)"

def _v3_pyz_extract(pyz_data: bytes) -> Tuple[Optional[str], str]:
    """Извлекает из .pyz (zip) файла."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".pyz", delete=False) as f:
            f.write(pyz_data); fname = f.name
        with zipfile.ZipFile(fname) as zf:
            files = zf.namelist()
            results = []
            for fn in files:
                if fn.endswith(('.py', '.pyc', '__main__.py')):
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

def _v3_marshal_chain(code: str) -> Tuple[Optional[str], str]:
    """Многослойный marshal."""
    pat = re.compile(r"exec\s*\(\s*marshal\.loads\s*\(\s*b['\"](.+?)['\"]", re.DOTALL)
    m = pat.search(code)
    if m:
        try:
            raw = m.group(1).encode("latin-1").decode("unicode_escape").encode("latin-1")
            obj = _marshal_loads_safe(raw)
            if isinstance(obj, types.CodeType):
                src = _try_marshal_to_source(obj)
                if src: return DEOBF_TAG + src, "marshal-exec"
        except: pass
    return None, ""

def _v3_zstd(code: str) -> Tuple[Optional[str], str]:
    """zstd компрессия."""
    pat = re.compile(r"exec\s*\(\s*(?:zstd|zstandard)\.decompress\s*\(\s*b?['\"]([A-Za-z0-9+/=]{20,})['\"]")
    m = pat.search(code)
    if m:
        try:
            import zstd
            raw = base64.b64decode(_b64_pad(m.group(1)))
            dec = _safe_decode(zstd.decompress(raw))
            if _is_python(dec): return DEOBF_TAG + dec, "zstd"
        except: pass
    return None, ""

def _v3_bz2_plain(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"exec\s*\(\s*bz2\.decompress\s*\(\s*b?['\"]([A-Za-z0-9+/=]{20,})['\"]")
    m = pat.search(code)
    if m:
        try:
            raw = base64.b64decode(_b64_pad(m.group(1)))
            dec = _safe_decode(bz2.decompress(raw))
            if _is_python(dec): return DEOBF_TAG + dec, "bz2"
        except: pass
    return None, ""

def _v3_lzma_plain(code: str) -> Tuple[Optional[str], str]:
    pat = re.compile(r"exec\s*\(\s*lzma\.decompress\s*\(\s*b?['\"]([A-Za-z0-9+/=]{20,})['\"]")
    m = pat.search(code)
    if m:
        try:
            raw = base64.b64decode(_b64_pad(m.group(1)))
            dec = _safe_decode(lzma.decompress(raw))
            if _is_python(dec): return DEOBF_TAG + dec, "lzma-plain"
        except: pass
    return None, ""

def _v3_integer_source(code: str) -> Tuple[Optional[str], str]:
    """exec(int.to_bytes(...).decode())"""
    pat = re.compile(r"exec\s*\(\s*\((\d{10,})\)\.to_bytes\s*\(\s*(\d+)\s*,\s*['\"](?:big|little)['\"]\s*\)(?:\.decode\([^)]*\))?\s*\)")
    m = pat.search(code)
    if m:
        try:
            n, length = int(m.group(1)), int(m.group(2))
            dec = n.to_bytes(length, 'big').decode("utf-8")
            if _is_python(dec): return DEOBF_TAG + dec, "integer-encoded"
        except: pass
    return None, ""

def _v3_unicode_names(code: str) -> Tuple[Optional[str], str]:
    """\\N{LATIN SMALL LETTER A} unicode names."""
    if r'\N{' not in code: return None, ""
    try:
        import unicodedata
        result = re.sub(
            r'\\N\{([^}]+)\}',
            lambda m: unicodedata.lookup(m.group(1)),
            code
        )
        if result != code: return DEOBF_TAG + result, "unicode-names"
    except: pass
    return None, ""

def _v3_vigenere(code: str) -> Tuple[Optional[str], str]:
    """Попытка vigenere декодирования зашифрованных строк."""
    # Ищем vigenere-like код
    if not ("key" in code.lower() and re.search(r'ord\s*\(', code) and re.search(r'chr\s*\(', code)):
        return None, ""
    # Детектируем, не декодируем
    return DEOBF_TAG + "# ⚠️  Vigenere-подобное шифрование обнаружено\n# Нужен ключ\n\n" + code, "vigenere (detected)"

def deobfuscate_v3(code: str) -> Tuple[Optional[str], str]:
    methods = [
        _v3_plain_b64, _v3_multilayer_b64, _v3_rot13, _v3_xor_fixed,
        _v3_hex_exec, _v3_compile_marshal, _v3_chr_obfuscate, _v3_decimal_array,
        _v3_reverse_string, _v3_lambda_chain, _v3_eval_b64, _v3_caesar,
        _v3_base85, _v3_base32_plain, _v3_string_split_join, _v3_marshal_chain,
        _v3_integer_source, _v3_unicode_names, _v3_bz2_plain, _v3_lzma_plain,
        _v3_fake_import, _v3_rc4, _v3_builtins_hide, _v3_swap_bytes,
        _v3_pyarmor, _v3_hyperion, _v3_opy, _v3_vigenere, _v3_zstd,
    ]
    for fn in methods:
        try:
            r, m = fn(code)
            if r: return r, m
        except: pass
    return None, "v3: метод не обнаружен"

# ════════════════════════════════════════════════════════
#   V4 — ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ
# ════════════════════════════════════════════════════════

def _v4_base62(code: str) -> Tuple[Optional[str], str]:
    """Base62 кодирование."""
    CHARS = string.digits + string.ascii_letters
    def decode(s: str) -> bytes:
        n = 0
        for c in s:
            n = n * 62 + CHARS.index(c)
        return n.to_bytes((n.bit_length() + 7) // 8, 'big')

    pat = re.compile(r"exec\s*\(\s*['\"]([0-9a-zA-Z]{20,})['\"]")
    for m in pat.finditer(code):
        try:
            dec = decode(m.group(1)).decode("utf-8")
            if _is_python(dec): return DEOBF_TAG + dec, "base62"
        except: pass
    return None, ""

def _v4_base58(code: str) -> Tuple[Optional[str], str]:
    """Base58 (Bitcoin style)."""
    ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    def decode(s: str) -> bytes:
        n = 0
        for c in s:
            if c not in ALPHABET: return b''
            n = n * 58 + ALPHABET.index(c)
        return n.to_bytes((n.bit_length() + 7) // 8, 'big')

    pat = re.compile(r"exec\s*\(\s*['\"]([1-9A-HJ-NP-Za-km-z]{20,})['\"]")
    for m in pat.finditer(code):
        try:
            dec = decode(m.group(1)).decode("utf-8")
            if _is_python(dec): return DEOBF_TAG + dec, "base58"
        except: pass
    return None, ""

def _v4_bitwise_not(code: str) -> Tuple[Optional[str], str]:
    """bytes([~b & 0xFF for b in b'...'])"""
    pat = re.compile(
        r"exec\s*\(\s*bytes\s*\(\s*\[\s*~b\s*&\s*0xFF\s+for\s+b\s+in\s+b['\"](.+?)['\"]\s*\]\s*\)"
    )
    m = pat.search(code)
    if m:
        try:
            raw = bytes([~b & 0xFF for b in m.group(1).encode("latin-1").decode("unicode_escape").encode("latin-1")])
            dec = _safe_decode(raw)
            if _is_python(dec): return DEOBF_TAG + dec, "bitwise-NOT"
        except: pass
    return None, ""

def _v4_rol_ror(code: str) -> Tuple[Optional[str], str]:
    """ROL/ROR bit rotation."""
    # exec(bytes([(b >> N | b << (8-N)) & 0xFF for b in b'...']))
    pat = re.compile(
        r"exec\s*\(\s*bytes\s*\(\s*\[\s*\(b\s*>>\s*(\d+)\s*\|\s*b\s*<<\s*(\d+)\)\s*&\s*0xFF\s+for\s+b\s+in\s+b['\"](.+?)['\"]\s*\]\s*\)"
    )
    m = pat.search(code)
    if m:
        try:
            n = int(m.group(1))
            raw = m.group(3).encode("latin-1").decode("unicode_escape").encode("latin-1")
            dec = _safe_decode(bytes([(b >> n | b << (8-n)) & 0xFF for b in raw]))
            if _is_python(dec): return DEOBF_TAG + dec, f"ROL/ROR (n={n})"
        except: pass
    return None, ""

def _v4_multi_xor(code: str) -> Tuple[Optional[str], str]:
    """Многоключевой XOR: b ^ k1 ^ k2 ^ k3."""
    pat = re.compile(
        r"exec\s*\(\s*bytes\s*\(\s*\[b\s*\^\s*(\d+)\s*\^\s*(\d+)(?:\s*\^\s*(\d+))?\s+for\s+b\s+in\s+bytes\.fromhex\(['\"]([0-9a-fA-F]+)['\"]\)\]\)"
    )
    m = pat.search(code)
    if m:
        try:
            keys = [int(x) for x in [m.group(1), m.group(2), m.group(3)] if x]
            key = 0
            for k in keys: key ^= k
            raw = bytes([b ^ key for b in bytes.fromhex(m.group(4))])
            dec = _safe_decode(raw)
            if _is_python(dec): return DEOBF_TAG + dec, f"multi-xor ({'^'.join(str(k) for k in keys)})"
        except: pass
    return None, ""

def _v4_zlib_b64_norev(code: str) -> Tuple[Optional[str], str]:
    """zlib(b64decode(data)) без реверса."""
    pat = re.compile(
        r"exec\s*\(\s*zlib\.decompress\s*\(\s*base64\.b64decode\s*\(\s*b?['\"]([A-Za-z0-9+/=]{20,})['\"]"
    )
    m = pat.search(code)
    if m:
        try:
            dec = _safe_decode(zlib.decompress(base64.b64decode(_b64_pad(m.group(1)))))
            if _is_python(dec): return DEOBF_TAG + dec, "zlib+base64-norev"
        except: pass
    return None, ""

def _v4_hex_string_literal(code: str) -> Tuple[Optional[str], str]:
    """exec(bytes.fromhex('4865...'))"""
    pat = re.compile(r"exec\s*\(\s*bytes\.fromhex\s*\(\s*['\"]([0-9a-fA-F]{20,})['\"]\s*\)(?:\.decode\([^)]*\))?\s*\)")
    m = pat.search(code)
    if m:
        try:
            dec = _safe_decode(bytes.fromhex(m.group(1)))
            if _is_python(dec): return DEOBF_TAG + dec, "hex-fromhex"
        except: pass
    return None, ""

def _v4_eval_chain(code: str) -> Tuple[Optional[str], str]:
    """eval(eval(eval(...('...'))))"""
    pat = re.compile(r"((?:eval\s*\()+)\s*['\"]([A-Za-z0-9+/=]{20,})['\"]\s*((?:\))+)")
    m = pat.search(code)
    if m:
        depth = m.group(1).count('eval(')
        enc = m.group(2)
        result = enc
        for _ in range(depth):
            try:
                dec = base64.b64decode(_b64_pad(result)).decode("utf-8")
                result = dec
            except: break
        if _is_python(result): return DEOBF_TAG + result, f"eval-chain (depth={depth})"
    return None, ""

def _v4_string_multiply(code: str) -> Tuple[Optional[str], str]:
    """'a' * 100 + 'b' * 50 обфускация."""
    pat = re.compile(r"exec\s*\(\s*(.+?)\s*\)", re.DOTALL)
    m = pat.search(code)
    if m:
        expr = m.group(1)
        if "* " in expr or " *" in expr:
            try:
                # Безопасная оценка строкового выражения
                safe_expr = re.sub(r'[^a-zA-Z0-9\'"*+\[\]\(\)\s]', '', expr)
                result = eval(safe_expr)
                if isinstance(result, str) and _is_python(result):
                    return DEOBF_TAG + result, "string-multiply"
            except: pass
    return None, ""

def _v4_compressed_marshal(code: str) -> Tuple[Optional[str], str]:
    """marshal.loads внутри многослойной компрессии."""
    # Ищем любой длинный bytes literal и пробуем marshal
    pat = re.compile(r"b['\"]([\\x0-9a-fA-F]{50,})['\"]")
    for m in pat.finditer(code):
        try:
            raw = m.group(1).encode("latin-1").decode("unicode_escape").encode("latin-1")
            result = _r2_decompress_chain(raw)
            text = _safe_decode(result)
            if _is_python(text, 50): return DEOBF_TAG + text, "compressed-marshal"
        except: pass
    return None, ""

def _v4_add_sub_cipher(code: str) -> Tuple[Optional[str], str]:
    """bytes([b + N for b in b'...']) или [(b - N) % 256 ...]"""
    for op, name in [(r'\+', 'add'), (r'\-', 'sub')]:
        pat = re.compile(
            r"exec\s*\(\s*bytes\s*\(\s*\[\s*(?:b\s*" + op + r"\s*(\d+)|(\d+)\s*" + op + r"\s*b)\s+for\s+b\s+in\s+b['\"](.+?)['\"]\s*\]\s*\)"
        )
        m = pat.search(code)
        if m:
            n = int(m.group(1) or m.group(2))
            try:
                raw = m.group(3).encode("latin-1").decode("unicode_escape").encode("latin-1")
                if name == 'add':
                    dec = _safe_decode(bytes([(b + n) % 256 for b in raw]))
                else:
                    dec = _safe_decode(bytes([(b - n) % 256 for b in raw]))
                if _is_python(dec): return DEOBF_TAG + dec, f"add-sub-cipher ({name}, n={n})"
            except: pass
    return None, ""

def _v4_obfuscated_print_calls(code: str) -> Tuple[Optional[str], str]:
    """Деобфускация через анализ паттернов без исполнения."""
    # Деобфускаторы типа obfuscator.io для Python
    if not (code.count('__') > 20 and len(re.findall(r'\b_[0-9a-f]{4,}\b', code)) > 5):
        return None, ""
    # Переименование переменных — просто добавляем заметку
    return DEOBF_TAG + "# Обнаружена обфускация именованием переменных (hash-based)\n# Используй v2 для очистки state-machine\n\n" + code, "hash-rename (detected)"

def deobfuscate_v4(code: str) -> Tuple[Optional[str], str]:
    methods = [
        _v4_hex_string_literal, _v4_zlib_b64_norev, _v4_bitwise_not,
        _v4_multi_xor, _v4_rol_ror, _v4_base62, _v4_base58,
        _v4_eval_chain, _v4_add_sub_cipher, _v4_compressed_marshal,
        _v4_string_multiply, _v4_obfuscated_print_calls,
    ]
    for fn in methods:
        try:
            r, m = fn(code)
            if r: return r, m
        except: pass
    return None, "v4: метод не обнаружен"

# ════════════════════════════════════════════════════════
#   EXE EXTRACTOR — ВСЕ ФОРМАТЫ
# ════════════════════════════════════════════════════════

def _detect_exe_type(data: bytes) -> str:
    if b'MEI\x0c\x0b\x0a\x0b\x0e' in data: return "pyinstaller"
    if b'PYZ\x00' in data: return "pyinstaller"
    if b'MEIPASS' in data: return "pyinstaller"
    if b'_MEIPASS2' in data: return "pyinstaller"
    if b'__nuitka__' in data: return "nuitka"
    if b'NUITKA_PACKAGE' in data: return "nuitka"
    if b'nuitka' in data[:8192].lower(): return "nuitka"
    if b'__pyx_' in data: return "cython"
    if b'cython' in data[:4096].lower(): return "cython"
    if b'cx_Freeze' in data[:8192]: return "cx_freeze"
    if b'py2exe' in data[:8192].lower(): return "py2exe"
    if b'zipimport' in data and data[:2] == b'MZ': return "pyinstaller"
    if data[:2] == b'PK': return "zipapp"
    if data[:4] == b'\x7fELF':
        if b'__pyx_' in data: return "cython-elf"
        return "elf-unknown"
    if data[:2] == b'MZ': return "pe-unknown"
    return "unknown"

detect_exe_type = _detect_exe_type

def _extract_pyinstaller(data: bytes, out_dir: str) -> Tuple[bool, str, List[str]]:
    files = []
    # Метод 1: pyinstxtractor через subprocess
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
    else:
        print("FAIL")
except Exception as e:
    print("ERR:" + str(e))
""")
        r = subprocess.run([sys.executable, script, exe_path],
                           cwd=out_dir, capture_output=True, text=True, timeout=90)
        for line in r.stdout.split("\n"):
            if line.startswith("OK:"):
                extracted = line[3:].strip()
                if os.path.exists(extracted):
                    for root, dirs, fnames in os.walk(extracted):
                        for fname in fnames:
                            if fname.endswith(('.py', '.pyc', '.pyz')):
                                files.append(os.path.join(root, fname))
                if files:
                    # Декомпилируем .pyc файлы
                    decompiled = []
                    for fp in files:
                        if fp.endswith('.pyc'):
                            with open(fp, 'rb') as f: pyc = f.read()
                            src, _ = _v3_pyc_decompile(pyc)
                            if src:
                                out = fp.replace('.pyc', '_decompiled.py')
                                with open(out, 'w') as f: f.write(src)
                                decompiled.append(out)
                        else:
                            decompiled.append(fp)
                    return True, f"PyInstaller: извлечено {len(decompiled)} файлов", decompiled
    except Exception as e:
        print(f"[pyinstxtractor] {e}")

    # Метод 2: ручное сканирование
    return _extract_pyinstaller_manual(data, out_dir)

def _extract_pyinstaller_manual(data: bytes, out_dir: str) -> Tuple[bool, str, List[str]]:
    files = []; count = 0

    # Ищем zlib-сжатые блоки (PyInstaller использует zlib для .pyc)
    pos = 0
    while pos < len(data) - 4:
        if data[pos:pos+2] == b'\x78\x9c' or data[pos:pos+2] == b'\x78\xda' or data[pos:pos+2] == b'\x78\x01':
            for size in range(64, min(len(data) - pos, 5_000_000), 512):
                try:
                    raw = zlib.decompress(data[pos:pos+size])
                    if len(raw) > 100:
                        text = None
                        # Пробуем как .pyc
                        for off in (8, 12, 16):
                            try:
                                obj = marshal.loads(raw[off:])
                                if isinstance(obj, types.CodeType):
                                    src = _try_marshal_to_source(obj)
                                    if src:
                                        text = DEOBF_TAG + src
                                        break
                            except: pass
                        if not text:
                            try:
                                text2 = _safe_decode(raw)
                                if _is_python(text2, 80): text = DEOBF_TAG + text2
                            except: pass
                        if text:
                            fname = os.path.join(out_dir, f"block_{count:04d}.py")
                            with open(fname, 'w') as f: f.write(text)
                            files.append(fname); count += 1
                        break
                except: pass
        pos += 1
        if count >= 50 or pos > 20_000_000: break

    # Ищем строки Python-файлов
    py_strings = []
    for magic_str in [b'import ', b'def ', b'class ', b'print(', b'#!/usr/bin/env python']:
        p = 0
        while True:
            idx = data.find(magic_str, p)
            if idx == -1: break
            start = max(0, idx - 200)
            chunk = data[start:idx+4096]
            try:
                text = chunk.decode("utf-8", errors="ignore")
                if _is_python(text, 40):
                    clean = re.sub(r'[^\x09\x0a\x0d\x20-\x7e]', '', text).strip()
                    if clean not in py_strings and len(clean) > 40:
                        py_strings.append(clean)
            except: pass
            p = idx + 1
            if len(py_strings) > 30: break

    if py_strings:
        fname = os.path.join(out_dir, "extracted_strings.py")
        with open(fname, 'w') as f:
            f.write(DEOBF_TAG + "# PyInstaller — извлечённые Python-фрагменты\n\n")
            for i, s in enumerate(py_strings[:50]):
                f.write(f"# === Fragment {i+1} ===\n{s}\n\n")
        files.append(fname)

    if files:
        return True, f"PyInstaller (manual): {len(files)} файлов", files
    return False, "PyInstaller: не удалось извлечь", []

def _extract_nuitka(data: bytes, out_dir: str) -> Tuple[bool, str, List[str]]:
    files = []
    note = ("# ⚠️  NUITKA EXE\n"
            "# Nuitka компилирует Python → C → machine code.\n"
            "# Полный реверс невозможен без оригинальных исходников.\n"
            "# Извлечены доступные фрагменты.\n\n")

    # Извлекаем строки
    strings = []
    i = 0; cur = []
    while i < min(len(data), 20_000_000):
        b = data[i]
        if 32 <= b < 127: cur.append(chr(b))
        else:
            if len(cur) >= 12:
                s = "".join(cur)
                if any(kw in s for kw in ["import ", "def ", "class ", ".py", "print(", "__"]):
                    strings.append(s)
            cur = []
        i += 1

    # Ищем embedded Python файлы
    embedded = []
    for start_marker in [b'# -*-', b'#!/usr/bin/env python', b'import sys\nimport', b'#!/usr']:
        pos = 0
        while True:
            idx = data.find(start_marker, pos)
            if idx == -1: break
            chunk = data[idx:idx+8192]
            try:
                text = chunk.decode("utf-8", errors="ignore")
                if _is_python(text, 50): embedded.append((idx, text[:2000]))
            except: pass
            pos = idx + 1
            if len(embedded) > 20: break

    fname = os.path.join(out_dir, "nuitka_analysis.py")
    with open(fname, 'w') as f:
        f.write(DEOBF_TAG + note)
        if embedded:
            f.write("# === Embedded Python Fragments ===\n")
            for off, text in embedded[:20]:
                f.write(f"# --- offset 0x{off:08x} ---\n{text}\n\n")
        if strings:
            f.write("# === Python-like Strings ===\n")
            for s in strings[:200]:
                f.write(f"# {s}\n")
    files.append(fname)

    # Создаём инструкцию
    guide = os.path.join(out_dir, "REVERSE_GUIDE.txt")
    with open(guide, 'w') as f:
        f.write("NUITKA REVERSE GUIDE\n" + "="*50 + "\n\n"
                "1. strings <exe> | grep -E 'def |import |class '\n"
                "2. IDA Pro + Python FLIRT signatures\n"
                "3. Ghidra + Python decompiler plugin\n"
                "4. frida --runtime=qjs -l hook.js <exe>\n"
                "5. x64dbg + ScyllaHide + Python hooking\n"
                "6. Search for __pyx_ symbols in binary\n")
    files.append(guide)
    return bool(embedded or strings), f"Nuitka: фрагменты извлечены", files

def _extract_cython(data: bytes, filepath: Optional[str], out_dir: str) -> Tuple[bool, str, List[str]]:
    files = []
    # Пробуем загрузить модуль
    if filepath and os.path.exists(filepath):
        try:
            import importlib.util, inspect
            spec = importlib.util.spec_from_file_location("_mod", filepath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            src_lines = [DEOBF_TAG, "# Cython module stubs\n\n"]
            for name, obj in inspect.getmembers(mod):
                if name.startswith("_"): continue
                if inspect.isfunction(obj) or inspect.isbuiltin(obj):
                    try:
                        sig = inspect.signature(obj)
                        doc = inspect.getdoc(obj) or ""
                        src_lines.append(f'def {name}{sig}:\n    """{doc}"""\n    ...\n\n')
                    except: src_lines.append(f"def {name}(...):\n    ...\n\n")
                elif inspect.isclass(obj):
                    src_lines.append(f"class {name}:\n")
                    for mn, mo in inspect.getmembers(obj):
                        if not mn.startswith("_"):
                            try: sig = inspect.signature(mo)
                            except: sig = ""
                            src_lines.append(f"    def {mn}(self{(', ' + str(sig)[1:]) if str(sig) != '()' else ''}):\n        ...\n\n")
            fname = os.path.join(out_dir, "cython_stubs.py")
            with open(fname, 'w') as f: f.writelines(src_lines)
            files.append(fname)
            return True, "Cython: stub-сигнатуры извлечены", files
        except: pass

    # Строки из бинарника
    strings = []
    cur = []; i = 0
    while i < min(len(data), 5_000_000):
        b = data[i]
        if 32 <= b < 127: cur.append(chr(b))
        else:
            if len(cur) >= 8:
                s = "".join(cur)
                if any(kw in s for kw in ["def ", "class ", "return", ".pyx", "import", "cython"]):
                    strings.append(s)
            cur = []
        i += 1

    fname = os.path.join(out_dir, "cython_strings.txt")
    with open(fname, 'w') as f:
        f.write(DEOBF_TAG + "# Cython .pyd — извлечённые строки\n\n")
        for s in strings[:300]: f.write(f"# {s}\n")
    files.append(fname)
    return bool(strings), f"Cython: {len(strings)} строк извлечено", files

def _extract_cx_freeze(data: bytes, out_dir: str) -> Tuple[bool, str, List[str]]:
    """cx_Freeze — ищет library.zip внутри."""
    files = []
    # cx_Freeze хранит Python в library.zip
    pos = data.find(b'PK\x03\x04')
    if pos != -1:
        try:
            zip_data = data[pos:]
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False, dir=out_dir) as f:
                f.write(zip_data); zpath = f.name
            with zipfile.ZipFile(zpath) as zf:
                for name in zf.namelist():
                    if name.endswith(('.py', '.pyc')):
                        content = zf.read(name)
                        if name.endswith('.pyc'):
                            src, _ = _v3_pyc_decompile(content)
                            if src:
                                out = os.path.join(out_dir, name.replace('/', '_').replace('.pyc', '.py'))
                                with open(out, 'w') as f: f.write(src)
                                files.append(out)
                        else:
                            out = os.path.join(out_dir, name.replace('/', '_'))
                            with open(out, 'wb') as f: f.write(content)
                            files.append(out)
            os.unlink(zpath)
        except: pass

    if files: return True, f"cx_Freeze: {len(files)} файлов", files
    return False, "cx_Freeze: library.zip не найден", []

def _extract_zipapp(data: bytes, out_dir: str) -> Tuple[bool, str, List[str]]:
    """ZIP/PYZ архивы."""
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
    if files: return True, f"ZIP/PYZ: {len(files)} файлов", files
    return False, "ZIP: не удалось извлечь", []

def _extract_py2exe(data: bytes, out_dir: str) -> Tuple[bool, str, List[str]]:
    """py2exe — ищет library.zip."""
    # py2exe хранит library.zip рядом или вшитую
    pos = data.find(b'library.zip')
    note = "# py2exe: library.zip найден\n# Распакуй и декомпилируй .pyc файлы\n\n"
    fname = os.path.join(out_dir, "py2exe_info.txt")
    with open(fname, 'w') as f:
        f.write("py2exe EXE REVERSE:\n"
                "1. Скопируй library.zip из папки с exe\n"
                "2. unzip library.zip\n"
                "3. python -m uncompyle6 *.pyc\n")
    # Пробуем извлечь встроенный zip
    return _extract_cx_freeze(data, out_dir)

def extract_from_exe(data: bytes, out_dir: str, filename: str = "") -> Tuple[bool, str, List[str]]:
    os.makedirs(out_dir, exist_ok=True)
    exe_type = _detect_exe_type(data)

    if exe_type == "pyinstaller":
        return _extract_pyinstaller(data, out_dir)
    elif exe_type == "nuitka":
        return _extract_nuitka(data, out_dir)
    elif exe_type in ("cython", "cython-elf"):
        return _extract_cython(data, filename if filename and os.path.exists(filename) else None, out_dir)
    elif exe_type == "cx_freeze":
        return _extract_cx_freeze(data, out_dir)
    elif exe_type == "py2exe":
        return _extract_py2exe(data, out_dir)
    elif exe_type == "zipapp":
        return _extract_zipapp(data, out_dir)
    elif exe_type in ("pe-unknown", "elf-unknown"):
        # Пробуем всё по очереди
        for fn in [_extract_pyinstaller, _extract_cx_freeze, lambda d, o: _extract_nuitka(d, o)]:
            try:
                ok, msg, files = fn(data, out_dir)
                if ok: return ok, msg, files
            except: pass
        return _extract_nuitka(data, out_dir)
    else:
        ok, msg, files = _extract_pyinstaller(data, out_dir)
        if ok: return ok, msg, files
        return _extract_zipapp(data, out_dir)

# ════════════════════════════════════════════════════════
#   ГЛАВНЫЙ ИНТЕРФЕЙС
# ════════════════════════════════════════════════════════

def auto_deobfuscate(code: str) -> Tuple[Optional[str], str]:
    """v1 → v3 → v4 → v2"""
    r, m = deobfuscate_v1(code)
    if r: return r, f"v1: {m}"
    r, m = deobfuscate_v3(code)
    if r: return r, f"v3: {m}"
    r, m = deobfuscate_v4(code)
    if r: return r, f"v4: {m}"
    result = deobfuscate_v2(code)
    if result and result != code:
        return result, "v2: Ренди 2.0 Universal"
    return None, "Метод не обнаружен — возможно уже чистый код"

def detect_all_methods(code: str) -> dict:
    return {
        "v1":              _v1_detect(code),
        "v3":              detect_v3_method(code),
        "has_exec":        bool(re.search(r'exec\s*\(', code)),
        "has_base64":      bool(re.search(r'[A-Za-z0-9+/=]{50,}', code)),
        "has_xor":         bool(re.search(r'bytes\.fromhex|b\s*\^\s*\d+|\[\s*b\s*\^\s*', code)),
        "has_state_machine":bool(re.search(r'while\s+\w+\s*!=\s*\d+', code)),
        "has_wrappers":    bool(re.search(r'def\s+\w+\s*\(\s*\w+\s*,\s*\w+\s*,\s*\w+\s*\)', code)),
        "has_chr":         len(re.findall(r'\bchr\s*\(\s*\d+\s*\)', code)),
        "has_marshal":     "marshal" in code,
        "has_pyarmor":     "__pyarmor__" in code or "pyarmor_runtime" in code,
        "has_hyperion":    bool(re.search(r"range\s*\(\s*256\s*\)", code)),
        "has_rot13":       "rot_13" in code or "rot-13" in code.lower(),
        "has_lambda_chain":bool(re.search(r'\(lambda\s+\w+\s*:', code)),
        "has_decimal_array":bool(re.search(r'chr\s*\(\s*\d{2,3}\s*\)', code)),
        "has_reverse":     "[::-1]" in code,
        "has_bz2":         "bz2" in code,
        "has_lzma":        "lzma" in code,
        "lines":           code.count('\n') + 1,
        "chars":           len(code),
    }

def detect_v3_method(code: str) -> str:
    checks = {
        "plain-base64":    lambda c: bool(re.search(r"exec\s*\(\s*(?:base64\.b64decode|__import__\(['\"]base64['\"]\)\.b64decode)", c)),
        "rot13":           lambda c: "rot_13" in c or "rot-13" in c.lower(),
        "xor-fixed-key":   lambda c: bool(re.search(r"bytes\(\[b\s*\^\s*\w+\s+for\s+b\s+in", c)),
        "hex-exec":        lambda c: bool(re.search(r"exec\s*\(\s*['\"](?:\\x[0-9a-fA-F]{2}){10,}['\"]", c)),
        "compile+marshal": lambda c: "marshal.loads" in c,
        "chr-obfuscate":   lambda c: len(re.findall(r'\bchr\s*\(\s*\d+\s*\)', c)) >= 5,
        "pyarmor":         lambda c: "__pyarmor__" in c or "pyarmor_runtime" in c,
        "hyperion":        lambda c: bool(re.search(r"range\s*\(\s*256\s*\)", c) and re.search(r"def\s+\w+\s*\(\s*\w+\s*,\s*\w+\s*\)", c)),
        "opy":             lambda c: "__pragma__" in c,
        "reverse-string":  lambda c: "[::-1]" in c and "exec" in c,
        "lambda-chain":    lambda c: bool(re.search(r'\(lambda\s+\w+\s*:', c) and "exec" in c),
        "decimal-array":   lambda c: bool(re.search(r'chr\s*\(\s*\d{2,3}\s*\)', c) and c.count('chr(') > 3),
        "bz2":             lambda c: "bz2.decompress" in c,
        "lzma":            lambda c: "lzma.decompress" in c and "base64" in c,
    }
    detected = [name for name, fn in checks.items() if fn(code)]
    return ", ".join(detected) if detected else "не определён"

# Публичные псевдонимы
decode_xor_strings   = _r2_decode_xor
decode_hex_escapes   = _r2_decode_hex_escapes
v3_pyc_decompile     = _v3_pyc_decompile
v3_pyz_extract       = _v3_pyz_extract
v3_plain_b64         = _v3_plain_b64
v3_rot13             = _v3_rot13
v3_pyobfuscate       = _v3_chr_obfuscate
v3_pyarmor           = _v3_pyarmor
v3_hyperion          = _v3_hyperion
v3_marshal_chain     = _v3_marshal_chain


# ════════════════════════════════════════════════════════════
#   BOT
# ════════════════════════════════════════════════════════════

import telebot, threading, os, shutil, tempfile, time, json, re, sys
import hashlib, random, traceback
from datetime import datetime, timedelta
from telebot import types
# Engine is embedded above
# ══════════════════════════════════════════════════════
#   КОНФИГ
# ══════════════════════════════════════════════════════
TOKEN      = "8603769389:AAFNrImTZhMY0ctceejoFbNkosE54cNsE30"
ADMIN_IDS  = {7321093872}
BOT_NAME   = "Togaff Deobfuscator"
BOT_TAG    = "@ArrhythmiaFucksn"
BOT_VER    = f"v{VERSION}"

USERS_FILE  = "users.json"
BANNED_FILE = "banned.json"
STATS_FILE  = "stats.json"
LOG_FILE    = "activity.log"

ALLOWED_EXT = {'.py', '.pyc', '.pyw', '.exe', '.pyd', '.so', '.pyz', '.zip', '.pyc2', '.pyc3'}
MAX_FILE_MB = 25

# ══════════════════════════════════════════════════════
#   ПЕРСОНАЖИ — ASTOLFO PACK
# ══════════════════════════════════════════════════════
ASTOLFO_FACES = [
    "(\\(\\  ∧＿∧\n(｡•ω•｡)つ━━✿✿✿",
    "(\\(\\  ˘ω˘ )\n(っ･∀･)っ━━★",
    "(\\(\\  ^•ω•^\n(⁠っ⁠˘⁠ω⁠˘⁠ς⁠)  ✿",
    "( ˘ω˘ )つ━━✿",
    "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧",
    "(◕‿◕✿) ⋆⭐",
    "≧◡≦ ✨",
    "( •̀ ω •́ )✧",
    "(。◕‿‿◕。)♡",
    "♡(˃͈ દ ˂͈ ༶ )",
]

LOADING_FRAMES = [
    "▱▱▱▱▱▱▱▱▱▱  0%",
    "▰▱▱▱▱▱▱▱▱▱ 10%",
    "▰▰▰▱▱▱▱▱▱▱ 30%",
    "▰▰▰▰▰▱▱▱▱▱ 50%",
    "▰▰▰▰▰▰▰▱▱▱ 70%",
    "▰▰▰▰▰▰▰▰▰▱ 90%",
    "▰▰▰▰▰▰▰▰▰▰ 100% ✅",
]

SPIN_FRAMES = ["⣾","⣽","⣻","⢿","⡿","⣟","⣯","⣷"]

DECODE_MSGS = [
    "Взламываю защиту", "Анализирую паттерны", "Снимаю слои шифрования",
    "Дешифрую payload", "Разворачиваю обфускацию", "Раскрываю секреты кода",
    "Обходю PyArmor", "Парсю байткод", "Декодирую строки", "Финальная очистка",
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

# ══════════════════════════════════════════════════════
#   ХРАНИЛИЩЕ
# ══════════════════════════════════════════════════════
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
    except Exception as e:
        print(f"[save] {e}")

_lock = threading.Lock()
users:  dict = _load(USERS_FILE,  {})
banned: set  = set(_load(BANNED_FILE, []))
stats:  dict = _load(STATS_FILE,  {"total_files": 0, "total_users": 0, "methods": {}, "daily": {}})

def save_all():
    with _lock:
        _save(USERS_FILE,  {str(k): v for k, v in users.items()})
        _save(BANNED_FILE, list(banned))
        _save(STATS_FILE,  stats)

def log(msg: str):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {msg}\n")
    except: pass

def ts(): return datetime.now().strftime("%d.%m %H:%M")
def today(): return datetime.now().strftime("%Y-%m-%d")

def is_admin(uid): return int(uid) in ADMIN_IDS
def is_banned(uid): return int(uid) in {int(b) for b in banned}
def is_allowed(uid):
    uid = int(uid)
    if is_admin(uid): return True
    if is_banned(uid): return False
    return str(uid) in users or uid in users

def get_user(uid) -> dict:
    return users.get(str(uid), users.get(uid, {}))

def update_stats(method: str):
    stats["total_files"] = stats.get("total_files", 0) + 1
    m = stats.setdefault("methods", {})
    m[method] = m.get(method, 0) + 1
    d = stats.setdefault("daily", {})
    d[today()] = d.get(today(), 0) + 1
    if len(d) > 30:
        oldest = sorted(d.keys())[0]
        del d[oldest]

# ══════════════════════════════════════════════════════
#   БОТ
# ══════════════════════════════════════════════════════
bot = telebot.TeleBot(TOKEN, parse_mode=None)

def _send(cid, text, kb=None, **kw):
    try: return bot.send_message(cid, text, reply_markup=kb, **kw)
    except Exception as e: print(f"[send] {e}")

def _edit(cid, mid, text, kb=None):
    try: return bot.edit_message_text(text, cid, mid, reply_markup=kb)
    except Exception as e: print(f"[edit] {e}")

def _delete(cid, mid):
    try: bot.delete_message(cid, mid)
    except: pass

def _answer(call, text="", alert=False):
    try: bot.answer_callback_query(call.id, text, show_alert=alert)
    except: pass

# ══════════════════════════════════════════════════════
#   АНИМАЦИИ
# ══════════════════════════════════════════════════════
def animate_loading(cid, mid, prefix="", steps=None, delay=0.45):
    """Анимирует прогресс-бар."""
    frames = steps or LOADING_FRAMES
    for frame in frames:
        try:
            bot.edit_message_text(f"{prefix}\n\n{frame}", cid, mid)
            time.sleep(delay)
        except: time.sleep(delay)

def animate_spinner(cid, mid, text, seconds=2.0, suffix=""):
    """Крутящийся спиннер."""
    end = time.time() + seconds
    i = 0
    while time.time() < end:
        f = SPIN_FRAMES[i % len(SPIN_FRAMES)]
        try:
            bot.edit_message_text(f"{f} {text}{suffix}", cid, mid)
        except: pass
        time.sleep(0.12)
        i += 1

def animate_decode_steps(cid, mid, filename: str, mode_name: str):
    """Многошаговая анимация декодирования."""
    face = random.choice(ASTOLFO_FACES)
    total_steps = 6
    for step, msg in enumerate(random.sample(DECODE_MSGS, min(total_steps, len(DECODE_MSGS))), 1):
        bar_done = "█" * step
        bar_left = "░" * (total_steps - step)
        pct = int(step / total_steps * 100)
        text = (
            f"🔓 {mode_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📄 {filename}\n\n"
            f"{face}\n\n"
            f"[{bar_done}{bar_left}] {pct}%\n"
            f"⏳ {msg}..."
        )
        try: bot.edit_message_text(text, cid, mid)
        except: pass
        time.sleep(0.55)

def show_typing(cid):
    try: bot.send_chat_action(cid, 'upload_document')
    except: pass

# ══════════════════════════════════════════════════════
#   ДИЗАЙН — ASCII ART
# ══════════════════════════════════════════════════════
LOGO = (
    "╔══════════════════════════════════╗\n"
    "║  🔓 TOGAFF DEOBFUSCATOR v4.0   ║\n"
    "║  (\\.\\  ∧＿∧                    ║\n"
    "║  (｡•ω•｡)つ━━✿✿✿               ║\n"
    "║     Astolfo Edition 💕          ║\n"
    "╚══════════════════════════════════╝"
)

DIVIDER       = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
DIVIDER_THIN  = "──────────────────────────────"

METHODS_FULL = (
    "📦 v1  — base64 / base32 / base16\n"
    "          zlib · gzip · lzma · bz2\n"
    "          base64+zlib/gzip/lzma/bz2\n"
    "          base32+zlib/gzip/lzma\n"
    "          base16+zlib/gzip/lzma\n"
    "          Rendy (marshal+gzip+lzma+zlib+b64)\n"
    "\n"
    "🔩 v2  — Ренди 2.0 Universal\n"
    "          XOR строки · State-machine\n"
    "          Call-wrappers · Dummy vars\n"
    "          getattr-chains · hex/unicode escapes\n"
    "          base64-arrays · decimal/chr arrays\n"
    "          octal · binary strings · zip-xor\n"
    "\n"
    "🧬 v3  — rot13 · xor-fixed-key\n"
    "          plain-base64 · multilayer-base64\n"
    "          hex-exec · compile+marshal\n"
    "          chr()-obfuscate · decimal-array\n"
    "          reverse-string · lambda-chain\n"
    "          eval-base64 · caesar-cipher\n"
    "          base85 · base32-plain · bz2 · lzma\n"
    "          string-split-join · marshal-chain\n"
    "          integer-encoded · unicode-names\n"
    "          fake-imports · builtins-hide\n"
    "          swap-bytes · PyArmor · Hyperion\n"
    "          OPy · RC4-detect · Vigenere-detect\n"
    "\n"
    "🆕 v4  — base62 · base58 · bitwise-NOT\n"
    "          ROL/ROR · multi-xor · add/sub cipher\n"
    "          zlib+b64-norev · hex-fromhex\n"
    "          eval-chain · compressed-marshal\n"
    "          hash-rename · string-multiply\n"
    "\n"
    "📦 EXE — PyInstaller (full) · Nuitka\n"
    "          Cython · cx_Freeze · py2exe\n"
    "          zipapp / .pyz · self-extract\n"
    "          ELF · PE-unknown"
)

# ══════════════════════════════════════════════════════
#   СОСТОЯНИЕ ПОЛЬЗОВАТЕЛЕЙ
# ══════════════════════════════════════════════════════
# uid → dict
_state: dict  = {}   # mode, last_file, history, etc.
_bcast: dict  = {}   # uid → True (ожидает текст рассылки)
_waiting: dict = {}  # uid → callback для следующего сообщения

def get_state(uid) -> dict:
    if uid not in _state:
        _state[uid] = {"mode": None, "history": [], "files_today": 0, "last_day": today()}
    s = _state[uid]
    if s.get("last_day") != today():
        s["files_today"] = 0
        s["last_day"] = today()
    return s

def set_mode(uid, mode):
    get_state(uid)["mode"] = mode

# ══════════════════════════════════════════════════════
#   КЛАВИАТУРЫ
# ══════════════════════════════════════════════════════
def kb_main(is_adm=False):
    k = types.InlineKeyboardMarkup(row_width=1)
    k.add(types.InlineKeyboardButton("⚡  АВТО  ─ рекомендуется",         callback_data="mode_auto"))
    k.add(types.InlineKeyboardButton("🔬  Анализ  ─ без декодирования",   callback_data="mode_detect"))
    k.add(types.InlineKeyboardButton("" + "─"*30,                         callback_data="noop"))
    row1 = [
        types.InlineKeyboardButton("🔓 v1",  callback_data="mode_v1"),
        types.InlineKeyboardButton("🔩 v2",  callback_data="mode_v2"),
    ]
    row2 = [
        types.InlineKeyboardButton("🧬 v3",  callback_data="mode_v3"),
        types.InlineKeyboardButton("🆕 v4",  callback_data="mode_v4"),
    ]
    k.row(*row1)
    k.row(*row2)
    k.add(types.InlineKeyboardButton("" + "─"*30,                         callback_data="noop"))
    k.add(types.InlineKeyboardButton("📦  EXE/PYD/SO  Extractor",        callback_data="mode_exe"))
    k.add(types.InlineKeyboardButton("📟  .pyc  Decompiler",              callback_data="mode_pyc"))
    k.add(types.InlineKeyboardButton("🗜️   .pyz  ZIP Extractor",          callback_data="mode_pyz"))
    k.add(types.InlineKeyboardButton("" + "─"*30,                         callback_data="noop"))
    k.add(types.InlineKeyboardButton("📊  Статистика",                    callback_data="show_stats"))
    k.add(types.InlineKeyboardButton("❓  Методы",                        callback_data="show_methods"))
    if is_adm:
        k.add(types.InlineKeyboardButton("👑  Admin Panel",               callback_data="admin_panel"))
    return k

def kb_back(prev="main"):
    k = types.InlineKeyboardMarkup()
    k.add(types.InlineKeyboardButton("◀  Назад",  callback_data=f"back_{prev}"))
    return k

def kb_back_mode():
    k = types.InlineKeyboardMarkup(row_width=2)
    k.row(
        types.InlineKeyboardButton("◀  Назад",         callback_data="back_main"),
        types.InlineKeyboardButton("❌  Отмена",        callback_data="cancel_mode"),
    )
    return k

def kb_admin():
    k = types.InlineKeyboardMarkup(row_width=2)
    k.row(
        types.InlineKeyboardButton("👥 Юзеры",       callback_data="adm_users"),
        types.InlineKeyboardButton("🚫 Баны",         callback_data="adm_bans"),
    )
    k.row(
        types.InlineKeyboardButton("📊 Статы",        callback_data="adm_stats"),
        types.InlineKeyboardButton("📝 Логи",          callback_data="adm_logs"),
    )
    k.row(
        types.InlineKeyboardButton("📢 Рассылка",     callback_data="adm_broadcast"),
        types.InlineKeyboardButton("🗑️  Очистить логи",callback_data="adm_clearlogs"),
    )
    k.add(types.InlineKeyboardButton("◀  Назад",      callback_data="back_main"))
    return k

def kb_after_decode(mode: str):
    k = types.InlineKeyboardMarkup(row_width=2)
    k.row(
        types.InlineKeyboardButton("🔄  Ещё файл",   callback_data=f"mode_{mode}"),
        types.InlineKeyboardButton("🏠  Меню",        callback_data="back_main"),
    )
    return k

def kb_mode_info(mode: str):
    k = types.InlineKeyboardMarkup(row_width=1)
    k.add(types.InlineKeyboardButton(f"✅  Отправить файл  ({mode.upper()})", callback_data=f"mode_{mode}"))
    k.add(types.InlineKeyboardButton("◀  Назад",  callback_data="back_main"))
    return k

# ══════════════════════════════════════════════════════
#   MODE DESCRIPTIONS
# ══════════════════════════════════════════════════════
MODE_INFO = {
    "auto": {
        "title":   "⚡  АВТО-деобфускатор",
        "emoji":   "⚡",
        "name":    "АВТО",
        "desc":    "Умный перебор: v1 → v3 → v4 → v2\nАвтоматически определяет метод и декодирует",
        "formats": "Все поддерживаемые форматы",
    },
    "detect": {
        "title":   "🔬  Режим анализа",
        "emoji":   "🔬",
        "name":    "Анализ",
        "desc":    "Полный анализ без декодирования\nПоказывает метод, признаки и рекомендации",
        "formats": ".py .pyw",
    },
    "v1": {
        "title":   "🔓  v1  ─ Base Encoding",
        "emoji":   "🔓",
        "name":    "v1",
        "desc":    "base64/32/16 + zlib/gzip/lzma/bz2\nВсе комбинации + Rendy marshal-chain",
        "formats": ".py .pyw",
    },
    "v2": {
        "title":   "🔩  v2  ─ Ренди 2.0 Universal",
        "emoji":   "🔩",
        "name":    "v2",
        "desc":    "XOR · State-machine · Call-wrappers\nHex/unicode escapes · Dummy vars · getattr\nchr-arrays · octal · binary · zip-xor",
        "formats": ".py .pyw",
    },
    "v3": {
        "title":   "🧬  v3  ─ Продвинутые методы",
        "emoji":   "🧬",
        "name":    "v3",
        "desc":    "rot13 · xor-key · plain-b64 · multilayer\nhex-exec · chr() · marshal · caesar · base85\nreverse · lambda-chain · unicode-names\nPyArmor · Hyperion · OPy · RC4 · Vigenere",
        "formats": ".py .pyw .pyc",
    },
    "v4": {
        "title":   "🆕  v4  ─ Расширенные методы",
        "emoji":   "🆕",
        "name":    "v4",
        "desc":    "base62 · base58 · bitwise-NOT · ROL/ROR\nmulti-xor · add/sub cipher · eval-chain\ncompressed-marshal · hex-fromhex · zlib+b64",
        "formats": ".py .pyw",
    },
    "exe": {
        "title":   "📦  EXE Extractor",
        "emoji":   "📦",
        "name":    "EXE",
        "desc":    "PyInstaller · Nuitka · Cython · cx_Freeze\npy2exe · zipapp · ELF · PE-unknown\nАвтодетект типа + полное извлечение",
        "formats": ".exe .pyd .so .elf",
    },
    "pyc": {
        "title":   "📟  .pyc Decompiler",
        "emoji":   "📟",
        "name":    "PYC",
        "desc":    "Декомпиляция Python байткода\nuncompyle6 / marshal + dis",
        "formats": ".pyc",
    },
    "pyz": {
        "title":   "🗜️   .pyz Extractor",
        "emoji":   "🗜️",
        "name":    "PYZ",
        "desc":    "Извлечение из ZIP/PYZ архивов\n+ декомпиляция .pyc внутри",
        "formats": ".pyz .zip",
    },
}

# ══════════════════════════════════════════════════════
#   /start
# ══════════════════════════════════════════════════════
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    uid   = int(msg.from_user.id)
    name  = msg.from_user.first_name or "анон"
    uname = getattr(msg.from_user, "username", "") or ""

    if is_banned(uid):
        _send(msg.chat.id,
            f"{LOGO}\n\n"
            f"🚫 Ты в бан-листе.\n\n"
            f"Обратись к {BOT_TAG} для разбана~")
        return

    is_new = str(uid) not in users and uid not in users
    if is_admin(uid) and is_new:
        users[str(uid)] = {
            "name": name, "username": uname,
            "added": ts(), "files": 0, "role": "admin",
            "methods": {}
        }
        save_all()

    if not is_allowed(uid):
        _send(msg.chat.id,
            f"{LOGO}\n\n"
            f"Привет, {name}! 🌸\n"
            f"{DIVIDER}\n\n"
            f"🔒 Доступ по приглашению\n\n"
            f"Бот работает по вайтлисту~\n"
            f"Напиши {BOT_TAG} для получения доступа!\n\n"
            f"✨ Возможности:\n"
            f"{METHODS_FULL}"
        )
        log(f"BLOCKED {uid} @{uname} ({name}) tried to access")
        return

    if is_new and not is_admin(uid):
        users[str(uid)] = {
            "name": name, "username": uname,
            "added": ts(), "files": 0, "role": "user",
            "methods": {}
        }
        stats["total_users"] = stats.get("total_users", 0) + 1
        save_all()
        log(f"NEW USER {uid} @{uname} ({name})")
    else:
        # Обновляем имя
        if str(uid) in users:
            users[str(uid)]["name"] = name
            if uname: users[str(uid)]["username"] = uname

    adm_badge = "  👑 ADMIN" if is_admin(uid) else ""
    user_info = get_user(uid)
    file_count = user_info.get("files", 0)

    face = random.choice(ASTOLFO_FACES)
    text = (
        f"{LOGO}\n\n"
        f"Привет, {name}!{adm_badge} 🌸\n"
        f"{DIVIDER}\n"
        f"{face}\n"
        f"{DIVIDER}\n\n"
        f"📁 Файлов декодировано: {file_count}\n\n"
        f"Выбери режим и отправь файл~ 💕\n\n"
        f"📌 /help — помощь\n"
        f"📌 /methods — все методы\n"
        f"📌 /stats — моя статистика"
    )
    if is_admin(uid):
        text += "\n📌 /admin — панель"

    _send(msg.chat.id, text, kb_main(is_admin(uid)))

# ══════════════════════════════════════════════════════
#   /help
# ══════════════════════════════════════════════════════
@bot.message_handler(commands=["help"])
def cmd_help(msg):
    if not is_allowed(msg.from_user.id): return
    _send(msg.chat.id,
        f"❓ Помощь — {BOT_NAME} {BOT_VER}\n"
        f"{DIVIDER}\n\n"
        f"КАК ИСПОЛЬЗОВАТЬ:\n\n"
        f"1️⃣ Нажми кнопку с нужным режимом\n"
        f"2️⃣ Отправь файл боту\n"
        f"3️⃣ Получи декодированный файл~\n\n"
        f"{DIVIDER}\n\n"
        f"РЕЖИМЫ:\n\n"
        f"⚡ АВТО — лучший выбор, перебирает v1→v3→v4→v2\n"
        f"🔬 Анализ — только определяет метод без декода\n"
        f"🔓 v1 — base64/32/16 + компрессия + Rendy\n"
        f"🔩 v2 — Ренди 2.0 Universal (XOR, state-machine)\n"
        f"🧬 v3 — rot13, chr(), PyArmor, Hyperion и др.\n"
        f"🆕 v4 — base62, bitwise-NOT, ROL/ROR и др.\n"
        f"📦 EXE — PyInstaller/Nuitka/Cython/cx_Freeze\n"
        f"📟 .pyc — декомпиляция байткода\n"
        f"🗜️ .pyz — извлечение из ZIP архива\n\n"
        f"{DIVIDER}\n\n"
        f"ФОРМАТЫ: .py .pyc .pyw .exe .pyd .so .pyz .zip\n\n"
        f"/methods — подробный список методов\n"
        f"/stats — твоя статистика\n"
        f"/cancel — отменить режим",
        kb_back()
    )

# ══════════════════════════════════════════════════════
#   /methods
# ══════════════════════════════════════════════════════
@bot.message_handler(commands=["methods"])
def cmd_methods(msg):
    if not is_allowed(msg.from_user.id): return
    _send(msg.chat.id,
        f"🧬 Все методы деобфускации\n"
        f"{DIVIDER}\n\n"
        f"{METHODS_FULL}",
        kb_back()
    )

# ══════════════════════════════════════════════════════
#   /stats
# ══════════════════════════════════════════════════════
@bot.message_handler(commands=["stats"])
def cmd_stats_user(msg):
    uid = int(msg.from_user.id)
    if not is_allowed(uid): return
    u = get_user(uid)
    file_count = u.get("files", 0)
    methods_used = u.get("methods", {})
    top_methods = sorted(methods_used.items(), key=lambda x: -x[1])[:5]
    top_str = "\n".join(f"  {i+1}. {m}: {n}×" for i, (m, n) in enumerate(top_methods)) or "  нет данных"

    _send(msg.chat.id,
        f"📊 Твоя статистика\n"
        f"{DIVIDER}\n\n"
        f"👤 {u.get('name','?')} (@{u.get('username','?')})\n"
        f"📅 Дата входа: {u.get('added','?')}\n"
        f"📁 Файлов всего: {file_count}\n\n"
        f"Топ методов:\n{top_str}",
        kb_back()
    )

# ══════════════════════════════════════════════════════
#   /cancel
# ══════════════════════════════════════════════════════
@bot.message_handler(commands=["cancel"])
def cmd_cancel(msg):
    uid = msg.from_user.id
    if uid in _state: _state[uid]["mode"] = None
    _bcast.pop(uid, None)
    _waiting.pop(uid, None)
    _send(msg.chat.id, "❌ Отменено~", kb_main(is_admin(uid)) if is_allowed(uid) else None)

# ══════════════════════════════════════════════════════
#   /admin
# ══════════════════════════════════════════════════════
@bot.message_handler(commands=["admin"])
def cmd_admin(msg):
    if not is_admin(msg.from_user.id):
        _send(msg.chat.id, "🚫 Нет доступа~"); return
    _send(msg.chat.id, _admin_text(), kb_admin())

def _admin_text():
    total_files = sum(u.get("files", 0) for u in users.values())
    today_files = stats.get("daily", {}).get(today(), 0)
    top_m = sorted(stats.get("methods", {}).items(), key=lambda x: -x[1])[:5]
    top_str = "  " + " | ".join(f"{m}:{n}" for m, n in top_m) if top_m else "  нет данных"
    return (
        f"👑 Admin Panel — {BOT_NAME}\n"
        f"{DIVIDER}\n\n"
        f"👥 Пользователей:  {len(users)}\n"
        f"🚫 В бане:         {len(banned)}\n"
        f"📁 Файлов всего:   {total_files}\n"
        f"📅 Сегодня:        {today_files}\n\n"
        f"Топ методов:\n{top_str}\n"
        f"{DIVIDER}"
    )

# ══════════════════════════════════════════════════════
#   ADMIN COMMANDS
# ══════════════════════════════════════════════════════
@bot.message_handler(commands=["add"])
def cmd_add(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.strip().split(None, 2)
    if len(parts) < 2: _send(msg.chat.id, "Использование: /add <user_id> [имя]"); return
    try: target = int(parts[1])
    except: _send(msg.chat.id, "❌ Неверный ID"); return
    banned.discard(target); banned.discard(str(target))
    name = parts[2] if len(parts) > 2 else f"User {target}"
    users[str(target)] = {
        "name": name, "username": "", "added": ts(), "files": 0,
        "role": "user", "methods": {}, "invited_by": msg.from_user.id
    }
    save_all()
    log(f"ADD {target} ({name}) by {msg.from_user.id}")
    _send(msg.chat.id, f"✅ Добавлен {name} (ID: {target}) 🌸")
    try:
        bot.send_message(target,
            f"{LOGO}\n\n"
            f"🌸 Поздравляю!\n\n"
            f"Тебе открыт доступ к {BOT_NAME} {BOT_VER}!\n\n"
            f"Нажми /start чтобы начать~ 💕\n\n"
            f"{DIVIDER}\n"
            f"by {BOT_TAG}")
    except: pass

@bot.message_handler(commands=["remove", "del"])
def cmd_remove(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.strip().split()
    if len(parts) < 2: _send(msg.chat.id, "/remove <user_id>"); return
    try: target = int(parts[1])
    except: return
    key = str(target)
    if key in users:
        name = users[key].get("name", "?")
        del users[key]; save_all()
        log(f"REMOVE {target} ({name}) by {msg.from_user.id}")
        _send(msg.chat.id, f"✅ Удалён {name} ({target})")
    else:
        _send(msg.chat.id, f"❌ Пользователь {target} не найден")

@bot.message_handler(commands=["ban"])
def cmd_ban(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.strip().split()
    if len(parts) < 2: _send(msg.chat.id, "/ban <user_id>"); return
    try: target = int(parts[1])
    except: return
    if is_admin(target): _send(msg.chat.id, "❌ Нельзя банить администратора"); return
    banned.add(target); banned.add(str(target))
    if str(target) in users: del users[str(target)]
    save_all()
    log(f"BAN {target} by {msg.from_user.id}")
    _send(msg.chat.id, f"🚫 Пользователь {target} забанен")
    try: bot.send_message(target, "🚫 Твой доступ был заблокирован.")
    except: pass

@bot.message_handler(commands=["unban"])
def cmd_unban(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.strip().split()
    if len(parts) < 2: _send(msg.chat.id, "/unban <user_id>"); return
    try: target = int(parts[1])
    except: return
    banned.discard(target); banned.discard(str(target)); save_all()
    log(f"UNBAN {target} by {msg.from_user.id}")
    _send(msg.chat.id, f"✅ Разбанен {target} 🌸")

@bot.message_handler(commands=["users"])
def cmd_users(msg):
    if not is_admin(msg.from_user.id): return
    if not users: _send(msg.chat.id, "Пользователей нет~"); return
    lines = [f"👥 Пользователи ({len(users)})\n{DIVIDER}\n\n"]
    for i, (uid_s, u) in enumerate(list(users.items())[:40], 1):
        uname = f"@{u['username']}" if u.get('username') else f"ID:{uid_s}"
        role = " 👑" if u.get("role") == "admin" else ""
        lines.append(f"{i}. {u.get('name','?')}{role} {uname}\n"
                     f"   📁 {u.get('files',0)} файлов · {u.get('added','?')}\n\n")
    if len(users) > 40: lines.append(f"...и ещё {len(users)-40}")
    _send(msg.chat.id, "".join(lines))

@bot.message_handler(commands=["broadcast"])
def cmd_broadcast_start(msg):
    if not is_admin(msg.from_user.id): return
    _bcast[msg.from_user.id] = True
    _send(msg.chat.id, "📢 Отправь текст рассылки~ (/cancel для отмены)")

@bot.message_handler(commands=["info"])
def cmd_info(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.strip().split()
    if len(parts) < 2: _send(msg.chat.id, "/info <user_id>"); return
    try: target = str(int(parts[1]))
    except: return
    if target in users:
        u = users[target]
        text = (
            f"👤 Пользователь {target}\n"
            f"{DIVIDER}\n\n"
            f"Имя: {u.get('name','?')}\n"
            f"Username: @{u.get('username','?')}\n"
            f"Роль: {u.get('role','user')}\n"
            f"Файлов: {u.get('files',0)}\n"
            f"Добавлен: {u.get('added','?')}\n"
            f"Пригласил: {u.get('invited_by','?')}\n\n"
            f"Методы:\n" +
            "\n".join(f"  {m}: {n}×" for m, n in u.get('methods', {}).items()) or "  нет"
        )
        _send(msg.chat.id, text)
    else:
        _send(msg.chat.id, f"Пользователь {target} не найден")

# ══════════════════════════════════════════════════════
#   РАССЫЛКА
# ══════════════════════════════════════════════════════
@bot.message_handler(func=lambda m: int(m.from_user.id) in _bcast and _bcast.get(int(m.from_user.id)))
def handle_broadcast(msg):
    if not is_admin(msg.from_user.id): return
    _bcast.pop(int(msg.from_user.id), None)
    ok = fail = 0
    wait = _send(msg.chat.id, f"📢 Рассылка {len(users)} пользователям...")
    for uid_str in list(users.keys()):
        try:
            bot.send_message(int(uid_str),
                f"📢 Сообщение от {BOT_NAME} 🌸\n"
                f"{DIVIDER}\n\n"
                f"{msg.text}\n\n"
                f"{DIVIDER}\n"
                f"by {BOT_TAG}")
            ok += 1
            time.sleep(0.05)
        except: fail += 1
    _edit(msg.chat.id, wait.message_id, f"✅ Рассылка завершена\n\n✅ Доставлено: {ok}\n❌ Ошибок: {fail}")

# ══════════════════════════════════════════════════════
#   CALLBACKS
# ══════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: True)
def on_callback(call):
    uid  = int(call.from_user.id)
    d    = call.data
    cid  = call.message.chat.id
    mid  = call.message.message_id

    # noop
    if d == "noop": _answer(call); return

    # back to main
    if d in ("back_main", "cancel_mode"):
        _answer(call)
        if uid in _state: _state[uid]["mode"] = None
        face = random.choice(ASTOLFO_FACES)
        try:
            bot.edit_message_text(
                f"{LOGO}\n\n"
                f"{face}\n\n"
                f"Выбери режим и отправь файл~ 💕",
                cid, mid, reply_markup=kb_main(is_admin(uid))
            )
        except: _send(cid, "Главное меню~", kb_main(is_admin(uid)))
        return

    # back generic
    if d.startswith("back_"):
        _answer(call)
        _send(cid, "◀ Назад~", kb_main(is_admin(uid))); return

    # show stats
    if d == "show_stats":
        _answer(call)
        total_files = sum(u.get("files",0) for u in users.values())
        today_f = stats.get("daily", {}).get(today(), 0)
        top_m = sorted(stats.get("methods",{}).items(), key=lambda x:-x[1])[:7]
        top_str = "\n".join(f"  {i+1}. {m}: {n}×" for i,(m,n) in enumerate(top_m)) or "  нет данных"
        try:
            bot.edit_message_text(
                f"📊 Статистика бота\n"
                f"{DIVIDER}\n\n"
                f"👥 Пользователей: {len(users)}\n"
                f"📁 Файлов всего:  {total_files}\n"
                f"📅 Сегодня:       {today_f}\n\n"
                f"Топ методов:\n{top_str}",
                cid, mid, reply_markup=kb_back()
            )
        except: pass
        return

    # show methods
    if d == "show_methods":
        _answer(call)
        try:
            bot.edit_message_text(
                f"🧬 Методы деобфускации\n"
                f"{DIVIDER}\n\n"
                f"{METHODS_FULL}",
                cid, mid, reply_markup=kb_back()
            )
        except: pass
        return

    # admin panel
    if d == "admin_panel":
        if not is_admin(uid): _answer(call, "🚫 Нет доступа", True); return
        _answer(call)
        try: bot.edit_message_text(_admin_text(), cid, mid, reply_markup=kb_admin())
        except: _send(cid, _admin_text(), kb_admin())
        return

    # admin actions via callback
    if d.startswith("adm_"):
        if not is_admin(uid): _answer(call, "🚫", True); return
        _answer(call)

        if d == "adm_users":
            lines = [f"👥 Пользователи ({len(users)})\n{DIVIDER}\n\n"]
            for i, (uid_s, u) in enumerate(list(users.items())[:25], 1):
                uname = f"@{u['username']}" if u.get('username') else f"ID:{uid_s}"
                role = " 👑" if u.get("role") == "admin" else ""
                lines.append(f"{i}. {u.get('name','?')}{role} {uname} — {u.get('files',0)} файлов\n")
            if len(users) > 25: lines.append(f"...ещё {len(users)-25}")
            try: bot.edit_message_text("".join(lines), cid, mid, reply_markup=kb_back("admin"))
            except: _send(cid, "".join(lines), kb_back("admin"))

        elif d == "adm_bans":
            text = (f"🚫 Бан-лист ({len(banned)})\n{DIVIDER}\n\n" +
                    "\n".join(f"• {b}" for b in list(banned)[:40])) if banned else "🚫 Бан-лист пуст~"
            try: bot.edit_message_text(text, cid, mid, reply_markup=kb_back("admin"))
            except: _send(cid, text, kb_back("admin"))

        elif d == "adm_stats":
            total_files = sum(u.get("files",0) for u in users.values())
            today_f = stats.get("daily",{}).get(today(),0)
            top_m = sorted(stats.get("methods",{}).items(), key=lambda x:-x[1])[:10]
            top_str = "\n".join(f"  {i+1}. {m}: {n}×" for i,(m,n) in enumerate(top_m)) or "  нет"
            week = sorted(stats.get("daily",{}).items())[-7:]
            week_str = "\n".join(f"  {d_}: {n}" for d_,n in week)
            text = (
                f"📊 Детальная статистика\n{DIVIDER}\n\n"
                f"👥 Пользователей: {len(users)}\n"
                f"🚫 В бане: {len(banned)}\n"
                f"📁 Файлов всего: {total_files}\n"
                f"📅 Сегодня: {today_f}\n\n"
                f"Топ методов:\n{top_str}\n\n"
                f"По дням (7д):\n{week_str}"
            )
            try: bot.edit_message_text(text, cid, mid, reply_markup=kb_back("admin"))
            except: _send(cid, text, kb_back("admin"))

        elif d == "adm_logs":
            try:
                if os.path.exists(LOG_FILE):
                    with open(LOG_FILE, 'r') as f:
                        lines = f.readlines()
                    last = "".join(lines[-30:]) if len(lines) >= 30 else "".join(lines)
                    text = f"📝 Последние записи лога\n{DIVIDER}\n\n{last}"
                    if len(text) > 4000: text = text[-4000:]
                    try: bot.edit_message_text(text, cid, mid, reply_markup=kb_back("admin"))
                    except: _send(cid, text, kb_back("admin"))
                else:
                    _send(cid, "Лог пустой~")
            except Exception as e:
                _send(cid, f"Ошибка чтения лога: {e}")

        elif d == "adm_broadcast":
            _bcast[uid] = True
            try: bot.edit_message_text("📢 Отправь текст рассылки~ (/cancel отмена)", cid, mid, reply_markup=kb_back("admin"))
            except: _send(cid, "📢 Отправь текст рассылки~")

        elif d == "adm_clearlogs":
            try:
                open(LOG_FILE, 'w').close()
                _send(cid, "✅ Логи очищены~")
            except: _send(cid, "Ошибка очистки")

        elif d == "back_admin":
            try: bot.edit_message_text(_admin_text(), cid, mid, reply_markup=kb_admin())
            except: _send(cid, _admin_text(), kb_admin())
        return

    # mode selection
    mode_map = {
        "mode_auto":   "auto",
        "mode_detect": "detect",
        "mode_v1":     "v1",
        "mode_v2":     "v2",
        "mode_v3":     "v3",
        "mode_v4":     "v4",
        "mode_exe":    "exe",
        "mode_pyc":    "pyc",
        "mode_pyz":    "pyz",
    }
    if d in mode_map:
        if not is_allowed(uid): _answer(call, "🔒 Нет доступа", True); return
        _answer(call)
        mode = mode_map[d]
        info = MODE_INFO[mode]
        set_mode(uid, mode)
        face = random.choice(ASTOLFO_FACES)
        text = (
            f"{info['title']}\n"
            f"{DIVIDER}\n\n"
            f"{face}\n\n"
            f"{info['desc']}\n\n"
            f"{DIVIDER}\n"
            f"📎 Форматы: {info['formats']}\n\n"
            f"✅ Отправь файл~ 💕"
        )
        try: bot.edit_message_text(text, cid, mid, reply_markup=kb_back_mode())
        except: _send(cid, text, kb_back_mode())
        return

# ══════════════════════════════════════════════════════
#   ОБРАБОТКА ДОКУМЕНТОВ
# ══════════════════════════════════════════════════════
@bot.message_handler(content_types=["document"])
def handle_document(msg):
    uid   = int(msg.from_user.id)
    cid   = msg.chat.id

    if not is_allowed(uid):
        _send(cid, f"{LOGO}\n\n🔒 Доступ закрыт~\nНапиши {BOT_TAG} для доступа!")
        return

    mode = get_state(uid).get("mode")
    if not mode:
        _send(cid,
            f"⚠️ Сначала выбери режим!\n\n"
            f"{random.choice(ASTOLFO_FACES)}\n\n"
            f"Нажми кнопку в меню~",
            kb_main(is_admin(uid)))
        return

    doc   = msg.document
    fname = doc.file_name or "file"
    ext   = os.path.splitext(fname.lower())[1]
    size  = doc.file_size or 0

    # Проверка размера
    if size > MAX_FILE_MB * 1024 * 1024:
        _send(cid,
            f"⚠️ Файл слишком большой ({size//1024//1024:.1f} MB)\n\n"
            f"Максимум: {MAX_FILE_MB} MB")
        return

    # Проверка расширения (для не-exe режимов)
    if mode not in ("exe",) and ext not in ALLOWED_EXT and ext != '':
        _send(cid,
            f"⚠️ Неподдерживаемый формат: {ext or 'без расширения'}\n\n"
            f"Поддерживается: {', '.join(sorted(ALLOWED_EXT))}")
        return

    # Очищаем режим
    get_state(uid)["mode"] = None

    face = random.choice(ASTOLFO_FACES)
    wait = _send(cid,
        f"📥 Загружаю {fname}...\n\n"
        f"{face}"
    )
    if not wait: return

    def process():
        try:
            show_typing(cid)
            file_info = bot.get_file(doc.file_id)
            data      = bot.download_file(file_info.file_path)

            # Счётчики
            key = str(uid)
            if key in users:
                users[key]["files"] = users[key].get("files", 0) + 1
            get_state(uid)["files_today"] = get_state(uid).get("files_today", 0) + 1

            info = MODE_INFO.get(mode, {"name": mode, "emoji": "🔓"})
            mode_name = f"{info['emoji']} {info['name']}"

            log(f"FILE {uid} mode={mode} file={fname} size={size}")

            # ── EXE ──────────────────────────────────
            if mode == "exe" or (mode == "auto" and ext in ('.exe', '.pyd', '.so', '.elf')):
                _process_exe(cid, wait.message_id, uid, data, fname)
                return

            # ── PYC ──────────────────────────────────
            if mode == "pyc" or ext == ".pyc":
                _edit(cid, wait.message_id,
                    f"📟 Декомпилирую .pyc\n"
                    f"{DIVIDER}\n"
                    f"📄 {fname}\n"
                    f"💾 {size:,} байт\n\n"
                    f"{face}\n\n"
                    f"⏳ Загружаю маршал...")
                time.sleep(0.4)
                _edit(cid, wait.message_id,
                    f"📟 Декомпилирую .pyc\n"
                    f"{DIVIDER}\n"
                    f"📄 {fname}\n\n"
                    f"⏳ uncompyle6 / marshal+dis...")
                result, method = _v3_pyc_decompile(data)
                if result:
                    _send_result(cid, wait.message_id, uid, fname, result, f"pyc: {method}", size, len(result), mode)
                else:
                    _send_fail(cid, wait.message_id, fname, method, mode)
                return

            # ── PYZ ──────────────────────────────────
            if mode == "pyz" or ext in (".pyz", ".zip"):
                _edit(cid, wait.message_id,
                    f"🗜️ Извлекаю архив\n"
                    f"{DIVIDER}\n"
                    f"📄 {fname}\n"
                    f"💾 {size:,} байт\n\n"
                    f"⏳ Распаковываю...")
                result, method = _v3_pyz_extract(data)
                if result:
                    _send_result(cid, wait.message_id, uid, fname, result, f"pyz: {method}", size, len(result), mode)
                else:
                    _send_fail(cid, wait.message_id, fname, method, mode)
                return

            # ── Python source ─────────────────────────
            try:
                code = data.decode("utf-8", errors="replace")
            except:
                _edit(cid, wait.message_id, "❌ Не удалось прочитать файл как текст", kb_main(is_admin(uid)))
                return

            chars_in = len(code)
            lines_in = code.count('\n') + 1

            if mode == "detect":
                _process_detect(cid, wait.message_id, uid, fname, code, lines_in, chars_in)
            elif mode == "v1":
                animate_decode_steps(cid, wait.message_id, fname, mode_name)
                result, method = deobfuscate_v1(code)
                if result:
                    _send_result(cid, wait.message_id, uid, fname, result, f"v1: {method}", chars_in, len(result), mode)
                else:
                    _send_fail(cid, wait.message_id, fname, method or "паттерн не найден", mode)
            elif mode == "v2":
                animate_decode_steps(cid, wait.message_id, fname, mode_name)
                result = deobfuscate_v2(code)
                _send_result(cid, wait.message_id, uid, fname, result, "v2: Ренди 2.0", chars_in, len(result), mode)
            elif mode == "v3":
                animate_decode_steps(cid, wait.message_id, fname, mode_name)
                result, method = deobfuscate_v3(code)
                if result:
                    _send_result(cid, wait.message_id, uid, fname, result, f"v3: {method}", chars_in, len(result), mode)
                else:
                    _send_fail(cid, wait.message_id, fname, method or "метод не найден", mode)
            elif mode == "v4":
                animate_decode_steps(cid, wait.message_id, fname, mode_name)
                result, method = deobfuscate_v4(code)
                if result:
                    _send_result(cid, wait.message_id, uid, fname, result, f"v4: {method}", chars_in, len(result), mode)
                else:
                    _send_fail(cid, wait.message_id, fname, method or "метод не найден", mode)
            else:
                # AUTO
                _process_auto(cid, wait.message_id, uid, fname, code, chars_in, mode)

        except Exception as e:
            print(f"[process] {traceback.format_exc()}")
            try: _edit(cid, wait.message_id, f"❌ Ошибка: {e}", kb_main(is_admin(uid)))
            except: pass

    threading.Thread(target=process, daemon=True).start()


def _process_detect(cid, mid, uid, filename, code, lines_in, chars_in):
    """Анализ без декода с красивым выводом."""
    face = random.choice(ASTOLFO_FACES)
    _edit(cid, mid,
        f"🔬 Анализирую {filename}\n{DIVIDER}\n\n"
        f"{face}\n\n"
        f"⏳ Сканирую паттерны...")
    time.sleep(0.6)

    info = detect_all_methods(code)

    _edit(cid, mid,
        f"🔬 Сканирую признаки обфускации...\n\n"
        f"▰▰▰▰▰▰▰▰▰▰ 100% ✅")
    time.sleep(0.4)

    v1m  = info.get("v1", "") or ""
    v3m  = info.get("v3", "") or ""

    lines = [
        f"🔬 Анализ завершён\n"
        f"{DIVIDER}\n\n"
        f"📄 {filename}\n"
        f"📊 {lines_in:,} строк · {chars_in:,} символов\n"
        f"{DIVIDER}\n\n"
        f"ОБНАРУЖЕННЫЕ МЕТОДЫ:\n\n"
    ]

    if v1m:
        lines.append(f"✅ v1: {v1m}\n")
    else:
        lines.append(f"◽ v1: не обнаружен\n")

    if v3m and v3m != "не определён":
        lines.append(f"✅ v3/v4: {v3m}\n")
    else:
        lines.append(f"◽ v3/v4: не обнаружен\n")

    lines.append(f"\n{DIVIDER_THIN}\nПРИЗНАКИ:\n\n")

    checks = [
        ("exec() вызовы",    info.get("has_exec"),        "🔴"),
        ("Base64 данные",    info.get("has_base64"),       "🟡"),
        ("XOR шифрование",   info.get("has_xor"),          "🔴"),
        ("State-machine",    info.get("has_state_machine"),"🔴"),
        ("Call-wrappers",    info.get("has_wrappers"),     "🟡"),
        ("marshal",          info.get("has_marshal"),      "🔴"),
        ("PyArmor",          info.get("has_pyarmor"),      "⛔"),
        ("Hyperion/RC4",     info.get("has_hyperion"),     "🔴"),
        ("rot13",            info.get("has_rot13"),        "🟡"),
        ("Реверс строк",     info.get("has_reverse"),      "🟡"),
        ("bz2/lzma",         info.get("has_bz2") or info.get("has_lzma"), "🟡"),
    ]
    chr_n = info.get("has_chr", 0)
    if chr_n: checks.append((f"chr() × {chr_n}", True, "🟡"))

    found = [(n, e) for n, v, e in checks if v]
    if found:
        for n, e in found: lines.append(f"  {e} {n}\n")
    else:
        lines.append("  ◽ Явных признаков не обнаружено\n")

    lines.append(f"\n{DIVIDER_THIN}\n💡 РЕКОМЕНДАЦИЯ:\n\n")
    if v1m:
        lines.append(f"  → ⚡ АВТО или 🔓 v1 ({v1m})\n")
    elif v3m and v3m != "не определён":
        lines.append(f"  → ⚡ АВТО или 🧬 v3 ({v3m.split(',')[0]})\n")
    elif info.get("has_xor") or info.get("has_state_machine") or info.get("has_wrappers"):
        lines.append(f"  → ⚡ АВТО или 🔩 v2 (Ренди 2.0)\n")
    else:
        lines.append(f"  → ⚡ АВТО — перебирает все методы\n")

    k = types.InlineKeyboardMarkup(row_width=1)
    k.add(types.InlineKeyboardButton("⚡ Декодировать АВТО",    callback_data="mode_auto"))
    k.row(
        types.InlineKeyboardButton("🔓 v1", callback_data="mode_v1"),
        types.InlineKeyboardButton("🔩 v2", callback_data="mode_v2"),
        types.InlineKeyboardButton("🧬 v3", callback_data="mode_v3"),
    )
    k.add(types.InlineKeyboardButton("◀ Главное меню",         callback_data="back_main"))
    _edit(cid, mid, "".join(lines), k)


def _process_auto(cid, mid, uid, filename, code, chars_in, mode):
    """АВТО — умный перебор с анимацией."""
    face = random.choice(ASTOLFO_FACES)

    def step_msg(step, total, name, status="⏳"):
        bar_done = "█" * step
        bar_left = "░" * (total - step)
        pct = int(step / total * 100)
        return (
            f"⚡ АВТО-деобфускация\n"
            f"{DIVIDER}\n"
            f"📄 {filename}\n"
            f"📊 {chars_in:,} символов\n\n"
            f"{face}\n\n"
            f"[{bar_done}{bar_left}] {pct}%\n"
            f"{status} {name}..."
        )

    total = 4

    # v1
    _edit(cid, mid, step_msg(1, total, "v1 base64/zlib/rendy"))
    time.sleep(0.5)
    r, m = deobfuscate_v1(code)
    if r:
        _send_result(cid, mid, uid, filename, r, f"v1: {m}", chars_in, len(r), mode)
        return

    # v3
    _edit(cid, mid, step_msg(2, total, "v3 rot13/xor/chr/marshal", "✗ v1"))
    time.sleep(0.5)
    r, m = deobfuscate_v3(code)
    if r:
        _send_result(cid, mid, uid, filename, r, f"v3: {m}", chars_in, len(r), mode)
        return

    # v4
    _edit(cid, mid, step_msg(3, total, "v4 base62/xor-multi/eval-chain", "✗ v1 v3"))
    time.sleep(0.5)
    r, m = deobfuscate_v4(code)
    if r:
        _send_result(cid, mid, uid, filename, r, f"v4: {m}", chars_in, len(r), mode)
        return

    # v2 (всегда что-то делает)
    _edit(cid, mid, step_msg(4, total, "v2 Ренди 2.0 Universal (финал)", "✗ v1 v3 v4"))
    time.sleep(0.6)
    result = deobfuscate_v2(code)
    _send_result(cid, mid, uid, filename, result, "v2: Ренди 2.0 (fallback)", chars_in, len(result), mode)


def _process_exe(cid, mid, uid, data, filename):
    """EXE — все форматы."""
    exe_type = detect_exe_type(data)
    face = random.choice(ASTOLFO_FACES)

    frames = [
        f"📦 EXE Extractor\n{DIVIDER}\n📄 {filename}\n💾 {len(data):,} байт\n🔍 Тип: {exe_type}\n\n{face}\n\n▱▱▱▱▱▱▱▱▱▱  0%",
        f"📦 EXE Extractor\n{DIVIDER}\n📄 {filename}\n💾 {len(data):,} байт\n🔍 Тип: {exe_type}\n\n{face}\n\n▰▰▰▱▱▱▱▱▱▱ 30%\n⏳ Сканирую сигнатуры...",
        f"📦 EXE Extractor\n{DIVIDER}\n📄 {filename}\n💾 {len(data):,} байт\n🔍 Тип: {exe_type}\n\n{face}\n\n▰▰▰▰▰▱▱▱▱▱ 50%\n⏳ Извлекаю архивы...",
        f"📦 EXE Extractor\n{DIVIDER}\n📄 {filename}\n💾 {len(data):,} байт\n🔍 Тип: {exe_type}\n\n{face}\n\n▰▰▰▰▰▰▰▱▱▱ 70%\n⏳ Декомпилирую .pyc...",
        f"📦 EXE Extractor\n{DIVIDER}\n📄 {filename}\n💾 {len(data):,} байт\n🔍 Тип: {exe_type}\n\n{face}\n\n▰▰▰▰▰▰▰▰▰▰ 100% ✅\n⏳ Финализирую...",
    ]
    for frame in frames:
        try: bot.edit_message_text(frame, cid, mid)
        except: pass
        time.sleep(0.8)

    out_dir = tempfile.mkdtemp(prefix="togaff_exe_")
    try:
        ok, msg_text, files = extract_from_exe(data, out_dir, filename)
        icon = "✅" if ok else "⚠️"

        if not files:
            _edit(cid, mid,
                f"❌ EXE: не удалось извлечь\n{DIVIDER}\n\n"
                f"📄 {filename}\n"
                f"🔍 Тип: {exe_type}\n"
                f"Причина: {msg_text}",
                kb_main(is_admin(uid)))
            return

        _edit(cid, mid,
            f"{icon} EXE извлечено!\n{DIVIDER}\n\n"
            f"📄 {filename}\n"
            f"🔍 Тип: {exe_type}\n"
            f"{icon} {msg_text}\n\n"
            f"📂 Отправляю {min(len(files),15)} файл(ов)...")

        show_typing(cid)
        sent = 0
        for fpath in files[:15]:
            try:
                with open(fpath, "rb") as f:
                    fn = os.path.basename(fpath)
                    ext_f = os.path.splitext(fn)[1]
                    cap = f"📦 {exe_type} | {fn}"
                    bot.send_document(cid, f, visible_file_name=fn, caption=cap)
                    sent += 1
                time.sleep(0.3)
            except Exception as e:
                print(f"[send exe file] {e}")

        if len(files) > 15:
            _send(cid, f"⚠️ Показаны {sent}/{len(files)} файлов")

        # Обновляем счётчик
        key = str(uid)
        if key in users:
            users[key]["files"] = users[key].get("files", 0) + 1
            m_key = f"exe-{exe_type}"
            users[key].setdefault("methods", {})[m_key] = users[key]["methods"].get(m_key, 0) + 1
        update_stats(f"exe-{exe_type}")
        save_all()
        log(f"EXE {uid} {filename} type={exe_type} files={len(files)}")

        face2 = random.choice(ASTOLFO_FACES)
        _send(cid,
            f"✅ Готово~ {face2}\n\n"
            f"📦 {exe_type} → {sent} файлов\n\n"
            f"Отправь ещё файл~ 💕",
            kb_main(is_admin(uid)))

    finally:
        try: shutil.rmtree(out_dir)
        except: pass


def _send_result(cid, mid, uid, filename, result, method, chars_in, chars_out, mode):
    """Отправляет декодированный файл с красивой анимацией."""
    face = random.choice(ASTOLFO_FACES)
    red  = max(0, round(100 * (1 - chars_out / max(chars_in, 1))))
    lines_out = result.count('\n') + 1 if result else 0

    # Анимация "готово"
    done_text = (
        f"✅ Декодировано!\n"
        f"{DIVIDER}\n"
        f"📄 {filename}\n\n"
        f"{face}\n\n"
        f"▰▰▰▰▰▰▰▰▰▰ 100% ✅\n\n"
        f"🔑 Метод:    {method}\n"
        f"💬 Символов: {chars_in:,} → {chars_out:,}  (-{red}%)\n"
        f"📝 Строк:    {lines_out:,}"
    )
    _edit(cid, mid, done_text)
    time.sleep(0.3)

    out_name = "decoded_" + filename
    out_path = f"/tmp/togaff_{out_name}"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result)
        show_typing(cid)
        with open(out_path, "rb") as f:
            caption = (
                f"🔓 {method}\n"
                f"📄 {filename}\n"
                f"💬 {chars_in:,} → {chars_out:,} символов (-{red}%)"
            )
            bot.send_document(cid, f, visible_file_name=out_name, caption=caption)
    except Exception as e:
        print(f"[send result] {e}")
    finally:
        try: os.remove(out_path)
        except: pass

    # Обновляем статистику
    key = str(uid)
    if key in users:
        m_key = method.split(":")[0].strip() if ":" in method else method
        users[key].setdefault("methods", {})[m_key] = users[key]["methods"].get(m_key, 0) + 1
    update_stats(method)
    save_all()
    log(f"DECODED {uid} {filename} method={method} {chars_in}→{chars_out}")

    done_msg = random.choice(DONE_MSGS)
    _send(cid,
        f"{done_msg}\n\n"
        f"Отправь ещё файл~ 💕",
        kb_after_decode(mode))


def _send_fail(cid, mid, filename, reason, mode):
    """Красивое сообщение об ошибке."""
    face = random.choice(ASTOLFO_FACES)
    fail_msg = random.choice(FAIL_MSGS)
    _edit(cid, mid,
        f"❌ Не удалось декодировать\n"
        f"{DIVIDER}\n\n"
        f"📄 {filename}\n\n"
        f"{face}\n\n"
        f"Причина: {reason}\n\n"
        f"💡 {fail_msg}~",
        kb_main())

# ══════════════════════════════════════════════════════
#   ERROR HANDLER
# ══════════════════════════════════════════════════════
@bot.message_handler(func=lambda m: True)
def handle_unknown(msg):
    uid = msg.from_user.id
    if uid in _bcast and _bcast.get(uid): return  # handled above
    if not is_allowed(uid): return
    _send(msg.chat.id,
        f"Привет~ 🌸\n\n"
        f"Отправь мне файл для декодирования,\n"
        f"но сначала выбери режим!\n\n"
        f"{random.choice(ASTOLFO_FACES)}",
        kb_main(is_admin(uid)))

# ══════════════════════════════════════════════════════
#   ЗАПУСК
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    print("═" * 60)
    print(f"  🔓 {BOT_NAME} {BOT_VER}")
    print(f"  by {BOT_TAG}")
    print(f"  Admins: {ADMIN_IDS}")
    print(f"  Users:  {len(users)}")
    print(f"  Banned: {len(banned)}")
    print("═" * 60)
    print("🌸 Бот запущен~")
    print()
    bot.infinity_polling(timeout=30, long_polling_timeout=20)
