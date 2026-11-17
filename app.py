import base64, gzip, json, socket, ssl, struct, threading, time
import urllib.parse, urllib.request, os
from flask import Flask, request, jsonify
from datetime import datetime

# ------------------------------------------------------------------ config ----
STATIC_KEY = b"Yg&tc%DEuh6%Zc^8"
STATIC_IV  = b"6oyZDr22E3ychjM%"
CLIENT_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
APP_ID = "100067"
OAUTH_URL = "https://100067.connect.garena.com/oauth/guest/token/grant"
MAJOR_LOGIN_URL = "https://loginbp.ppmainecoonghj.com/MajorLogin"
DEFAULT_CLIENT_HOST = "https://client.ind.freefiremobile.com"
CLIENT_VERSION, RELEASE_VERSION, REGION = "2.133.11", "OB55", "IND"

AUTH_OPCODES = (0x93, 0x95, 0x89, 0x7B, 0x69, 0x8F, 0x78, 0x83)
ONLINE_OPCODES = (0x8D, 0x86, 0x67) + AUTH_OPCODES
REGION_BYTE = {"BD": 0x19, "IND": 0x14}

TEMPLATE_UID, TEMPLATE_CODE = b"18827556186", b"9809812"
JOIN_TEMPLATE_B64 = (
    "CAQSzwoiCAEJChIZICcpKgc5ODA5ODEyMAZAAUq5CQoZSU5ESUFfTk9USU5JVD8xODgyNzU1NjE4NhAXGvcDd19ZUBQDCEQEAg4I"
    "U1YNB1ABWwMCWQJUVwQOVgAIU1ddAA9TAlMLABsAB0R0W0VBThoIFAAfGwAESQVRfHoLXm5Ja3l/Z05Eem5ff3wHcA1gfABxdQwV"
    "CU1jBV9hVV5oZ1J/BG9vB39EcU1+A0x3XWRWdH8FG1dZVkUZZn0adUhIA0pgXHB9Yl1jTmBYZlRZVwVUUVoPUX4DCXkCA3wKEQkL"
    "TVFcVll9V2Zac2gHHVNmUUMNA2Rgc35ES3pacAgUCkRMBmYXWmVnGm0LfEtrXEtaRHxeThl2E15OS3ALFgdLaHx2AWdqYlcAZH9r"
    "am9QYktERAF0AEJTS1BBBRIPSX1eQmJfY2ZIRldNYw9HDl0CAAB6XH14XlZQXwwVCQlKckdAe05hQ3J9WlQAZ3N5anx/d09iemUa"
    "WXpPBRIFRF9/e08HHUJ/Vn5Td2J9c0RweghCWHoJeVABVA8bDE1bSEl8TFNBfmB1eFBQUmxvY0RUam12BklTWlIIFAAIRFJsQGMG"
    "TGVNXXQXYWxaYH13YWBDXXBiT0AAbwgWAk5gVnpkSnAGVwx6dloTf3hNfExgBhxnanxaVwgMFQJJZlluSX0ZAXB7UQMcClZ8WXd9"
    "f0VPQm9QAE5aCxsHSnsMeVhZXGJ8aEFEAG1HeQ4AclAMcHENeW5lAAUiBHldVl0wDjoKEnB2YG9zZ2QcHEIIMi4xMzMuMTJIAlAC"
    "Wv0EA2JiU1E2ekhJMkFzSUFkVjJLeW9WbGRtZ201L3lmUE1Hd09oMmlnekdJd0xKKzRxb2JJZU1ybkxOUm1xU1kxcjh3Nm5Lb3M2"
    "Y1lqcEk0RWVUVnE2YWhLcUttN1hEVEc4UlFIWjNvOWpBMzFKbXZyRFFncmZXb3Z4YU5VbU9CNXF6UTlGZ0tGbEtqRS9hd25oOXhQ"
    "cTdqVUlxMVUxTHpreWIydXV1QXYzemRQYkxpbUQva1FwMVMxNEpjbmdyd2NtQUtvWmE0ZHpJOFkyanZ3ZTJ3QWVLbERxMU5VWSsx"
    "WDVhcXY3Unl1bDIzVVR0eUkzajBhbEI3NC91SkhGUC83NFhncVFHRHhzcDRJeUIxUWFDcWZ1M3I0VVdheUlMd1BXMGhdC9sQkF4"
    "Um43RUg5aXhBUTdleEdVdWdHVzBVZ0NrMHBXenAvNWNWZVB0cTRybzlWRmNHN1VWbVlTY1oxZm1lWjdvUHIrNXpuemlSS1V5bUR1"
    "L1JhNHMyY2VUczVaKzFzZ1RwVXAwZk5mNXV5dzBDd1VzeTdsVTdzTGtVZWJ3NThjeGtSYkNVUUFTVWVudGk4NGNyazVhdks4aXVS"
    "elFsbVpNb3VSb1M4ZGhxWFo2NU1FTDlyVzFTWmFtMEVxNnRFajYxMHgxSEFjUzlVUlVLUG15OHg1QWc3Z2pqVnpIQU1DbWtUVXda"
    "TTVlYzFaazRFZ2lPd3dBbFhOeDFncGpoZW4zWlhCeTlYSFQyOXI0SkJlc3VYWlA0cEJlSkkwRjB3NGduRUFMaFZsZll2ekRiY3NO"
    "S3pRSVhvWjk4S0ZsYW01a1pTUlhiN0RkZ1NOVFhsV2xWWER3enFrPVoNCgRJREMxED0aA0lORFoNCgRJREMyEBEaA0lORGoCZW6C"
    "AQQ3T1IZogEFCAMQ+QKiAQUIBBCHA6IBBQgFEJ8BogEFCB0QyAGiAQQIFhBcogEFCA4QkAGiAQIIFboBFWFfNTg2OTU0NjgyNDM0"
    "MTM4Mzk3N9oBBAgCEAQ="
)

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    _AES_BACKEND = "pycryptodome"
    def aes_enc(data, key=STATIC_KEY, iv=STATIC_IV):
        return AES.new(key, AES.MODE_CBC, iv).encrypt(pad(data, 16))
    def aes_dec(data, key=STATIC_KEY, iv=STATIC_IV):
        return unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(data), 16)
except ImportError:
    from cryptography.hazmat.primitives import padding as _pd
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    _AES_BACKEND = "cryptography"
    def aes_enc(data, key=STATIC_KEY, iv=STATIC_IV):
        p = _pd.PKCS7(128).padder()
        c = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
        return c.update(p.update(data) + p.finalize()) + c.finalize()
    def aes_dec(data, key=STATIC_KEY, iv=STATIC_IV):
        c = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
        u = _pd.PKCS7(128).unpadder()
        return u.update(c.update(data) + c.finalize()) + c.finalize()

def aes_dec_raw(data, key=STATIC_KEY, iv=STATIC_IV):
    if not data or len(data) % 16 != 0:
        return None
    try:
        if _AES_BACKEND == "pycryptodome":
            return AES.new(key, AES.MODE_CBC, iv).decrypt(data)
        c = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
        return c.update(data) + c.finalize()
    except Exception:
        return None

def _wv(n):
    out = bytearray()
    while True:
        b = n & 0x7F; n >>= 7
        if n: out.append(b | 0x80)
        else: out.append(b); return bytes(out)

def _rv(b, i):
    n = s = 0
    while True:
        c = b[i]; i += 1
        n |= (c & 0x7F) << s; s += 7
        if not c & 0x80: return n, i

def pb_parse(b):
    i, out = 0, []
    while i < len(b):
        k, i = _rv(b, i)
        f, w = k >> 3, k & 7
        if f == 0: raise ValueError("field 0")
        if w == 0: v, i = _rv(b, i)
        elif w == 2:
            l, i = _rv(b, i)
            if i + l > len(b): raise ValueError("overrun")
            v, i = b[i:i + l], i + l
        elif w == 1: v, i = b[i:i + 8], i + 8
        elif w == 5: v, i = b[i:i + 4], i + 4
        else: raise ValueError("wire type")
        out.append((f, w, v))
    return out

def pb_build(fields):
    out = bytearray()
    for f, w, v in fields:
        out += _wv(f << 3 | w)
        out += _wv(v) if w == 0 else (_wv(len(v)) + v if w == 2 else v)
    return bytes(out)

def pb_get(fields, n):
    for f, w, v in fields:
        if f == n: return v

def pb_encode(d):
    out = []
    for k, v in d.items():
        if isinstance(v, int): out.append((k, 0, v))
        else: out.append((k, 2, v.encode() if isinstance(v, str) else bytes(v)))
    return pb_build(out)

def retarget(b, repl, depth=0):
    if b and all(32 <= c < 127 for c in b):
        for old, new in repl.items(): b = b.replace(old, new)
        return b
    try:
        fields = pb_parse(b)
        if depth < 8 and fields and pb_build(fields) == b:
            return pb_build([(f, w, retarget(v, repl, depth + 1) if w == 2 else v) for f, w, v in fields])
    except Exception: pass
    for old, new in repl.items(): b = b.replace(old, new)
    return b

def http_post(url, data, headers, verify=True, timeout=30):
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    ctx = None if verify else ssl._create_unverified_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.status, r.read()

def _v_major_login(fields):
    nums = {f for f, w, v in fields}
    if 8 in nums:
        for f, w, v in fields:
            if f == 8 and w == 2:
                if isinstance(v, bytes):
                    try:
                        if v.decode("utf-8", "ignore").count(".") == 2: return True
                    except Exception: pass
                elif isinstance(v, str) and v.count(".") == 2: return True
        return False
    return 1 in nums and 21 in nums

def _v_login_data(fields):
    for f, w, v in fields:
        if f == 14 and w == 2 and isinstance(v, bytes):
            try:
                s = v.decode("utf-8", "ignore")
                return ":" in s and s.count(".") >= 1
            except Exception: return False
    return False

def parse_response(raw, validator):
    if raw[:2] == b"\x1f\x8b":
        try: raw = gzip.decompress(raw)
        except Exception: pass
    candidates = []
    try: candidates.append(("aes", aes_dec(raw, STATIC_KEY, STATIC_IV)))
    except Exception:
        d = aes_dec_raw(raw, STATIC_KEY, STATIC_IV)
        if d: candidates.append(("aes-raw", d))
    if len(raw) > 64:
        try: candidates.append(("aes@64", aes_dec(raw[64:], STATIC_KEY, STATIC_IV)))
        except Exception:
            d = aes_dec_raw(raw[64:], STATIC_KEY, STATIC_IV)
            if d: candidates.append(("aes-raw@64", d))
        candidates.append(("raw@64", raw[64:]))
    candidates.append(("raw", raw))
    for label, buf in candidates:
        if not buf: continue
        try: fields = pb_parse(buf)
        except Exception: continue
        if fields and validator(fields): return fields
    raise ValueError("cannot parse server response")

def _s(fields, n, default=""):
    v = pb_get(fields, n)
    return v.decode(errors="ignore") if isinstance(v, bytes) else default

def oauth(uid, password, verify):
    body = urllib.parse.urlencode({"uid": uid, "password": password, "response_type": "token",
                                   "client_type": "2", "client_secret": CLIENT_SECRET,
                                   "client_id": APP_ID}).encode()
    st, raw = http_post(OAUTH_URL, body, {
        "User-Agent": "GarenaMSDK/4.0.19P9(SM-M526B ;Android 13;en;IN;)",
        "Content-Type": "application/x-www-form-urlencoded", "Connection": "close"}, verify, 20)
    j = json.loads(raw)
    if not j.get("open_id") or not j.get("access_token"):
        raise RuntimeError("OAuth failed: %s" % j)
    return j["open_id"], j["access_token"]

def _client_info(open_id, access_token, platform="4", extra=None):
    d = {3: datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 4: "free fire", 5: 1, 7: CLIENT_VERSION,
         8: "Android OS 10 / API-29 (QP1A.190711.020/1617006012)", 9: "Handheld", 10: "Vi India", 11: "WIFI",
         12: 1600, 13: 720, 14: "320", 15: "ARM64 FP ASIMD AES | 2301 | 8", 16: 2799,
         17: "PowerVR Rogue GE8320", 18: "OpenGL ES 3.2 build 1.11@5425693",
         19: "Google|9f7d6b8b-b10c-454a-852d-06332cd498eb", 20: "151.158.158.220", 21: "en",
         22: open_id, 23: platform, 24: "Handheld", 25: "realme RMX2189", 26: REGION,
         29: access_token, 30: 1, 41: "Vi India", 42: "WIFI", 57: "1ac4b80ecf0478a44203bf8fac6120f5",
         60: 19799, 61: 2536, 62: 5056, 64: 2768, 65: 19999, 66: 2536, 67: 19799, 73: 1,
         74: "/data/app/com.dts.freefiremax-ShI7E0dK8p1IiZ785pvuVQ==/lib/arm64", 76: 2,
         77: "38f4751a330688ab124c2c804cec90a5|/data/app/com.dts.freefiremax-ShI7E0dK8p1IiZ785pvuVQ==/base.apk",
         78: 2, 79: 2, 81: "64", 83: "2019118527", 86: "OpenGLES3", 87: 3071, 88: 4, 92: 67920,
         93: "android_max",
         94: "KqsHT+UrR1HKqb6+1db+Ofei+NtZr2+hbiBo3yKDL8w+8E3S5qF2IgEEe1fFQFyHRzl4iyHjHp+QsfeLbjJ6+DidTiKxm0ak2uYYa6QR4nAUdlZR",
         95: 111107, 96: '{"cur_rate":null,"support_etc2":true}', 97: 1, 98: 1, 99: platform, 100: platform,
         102: "", 104: 83812, 105: 1,
         106: "https://dl-bs.ggpolarbear.com/live/ABHotUpdates/|https://core-bs.ggpolarbear.com/live/ABHotUpdates/|a4332cb1c1a84e51dd77441e4856ed5a",
         107: "1.9393e7b8e53e8aeb"}
    d.update(extra or {})
    return pb_encode(d)

def _ga_headers(bearer=""):
    return {
        "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Accept": "*/*", "Accept-Encoding": "deflate, gzip",
        "X-GA-SV": str(int(time.time())), "Authorization": "Bearer " + bearer,
        "X-GA": "v1 1", "ReleaseVersion": RELEASE_VERSION,
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.12f1",
    }

def major_login(open_id, access_token, verify):
    st, raw = http_post(MAJOR_LOGIN_URL, aes_enc(_client_info(open_id, access_token)), _ga_headers(), verify)
    r = parse_response(raw, _v_major_login)
    bot_uid = pb_get(r, 1)
    jwt = _s(r, 8)
    key = pb_get(r, 22)
    iv  = pb_get(r, 23)
    return {"jwt": jwt, "key": bytes(key), "iv": bytes(iv),
            "uid": bot_uid, "kts": pb_get(r, 21) or int(time.time()),
            "client_url": _s(r, 10) or DEFAULT_CLIENT_HOST}

def get_login_data(login, open_id, access_token, verify):
    body = aes_enc(_client_info(open_id, access_token, "4",
                                {20: "27.59.76.15", 90: "New Delhi", 91: "DL", 99: "0"}))
    st, raw = http_post(login["client_url"].rstrip("/") + "/GetLoginData",
                        body, _ga_headers(login["jwt"]), verify, 20)
    r = parse_response(raw, _v_login_data)
    online = _s(r, 14)
    return {"online": online, "region": _s(r, 3, REGION).upper()}

def frame(ptype_hex, payload, key, iv):
    ct = aes_enc(payload, key, iv)
    return bytes.fromhex(ptype_hex) + struct.pack(">I", len(ct)) + ct

def build_auth(opcode, region, uid, kts, jwt, key, iv):
    enc = aes_enc(jwt.encode(), key, iv)
    return (bytes([opcode, REGION_BYTE.get(region.upper(), 0x15)]) + int(uid).to_bytes(8, "big")
            + int(kts).to_bytes(4, "big") + b"\x00\x00\x00\x00" + struct.pack(">I", len(enc)) + enc)

def build_join(team_code, uid, key, iv):
    tpl = base64.b64decode("".join(JOIN_TEMPLATE_B64))
    return frame("0514", retarget(tpl, {TEMPLATE_UID: str(uid).encode(),
                                        TEMPLATE_CODE: str(team_code).encode()}), key, iv)

def build_exit(key, iv):
    return frame("0514", pb_build([(1, 0, 7), (2, 2, pb_build([(1, 0, 0)]))]), key, iv)

# ---------------------------------------------------------------- Flask API ----
app = Flask(__name__)
_api_lock = threading.Lock()

BOT_ACCOUNTS = [
    ("4556621217", "S7LDEVR90TK0-S1X_TEAM"),
    ("4556621305", "S7LG16WVVPEX-S1X_TEAM"),
    ("4556621393", "S7L2LLJ7CDXN-S1X_TEAM"),
    ("4556621575", "S7LBZVOMQGLD-S1X_TEAM")
]

def full_spam_worker(uid, password, team_code):
    try:
        # خطوات تسجيل الدخول الأصلية والكاملة بالكامل
        open_id, access_token = oauth(uid, password, True)
        login = major_login(open_id, access_token, True)
        login_data = get_login_data(login, open_id, access_token, True)
        
        host, port = login_data["online"].rsplit(":", 1)
        region = login_data["region"]
        key, iv = login["key"], login["iv"]
        bot_uid = login["uid"]

        # إنشاء الاتصال بالـ TCP سرفر الخاص باللعبة
        s = socket.create_connection((host, int(port)), timeout=10)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        # إرسال حزمة المصادقة (Auth) لفتح الجلسة
        auth_pkt = build_auth(0x8D, region, bot_uid, login["kts"], login["jwt"], key, iv)
        s.sendall(auth_pkt)
        time.sleep(0.2)

        # 🚀 حلقة السبام المكثف داخل نفس الاتصال (دخول وخروج متكرر بسرعة قوية)
        for _ in range(12):
            try:
                s.sendall(build_join(team_code, bot_uid, key, iv))
                time.sleep(0.08) # فترة زمنية دقيقة جداً بين الدخول والخروج
                s.sendall(build_exit(key, iv))
                time.sleep(0.08)
            except Exception:
                break
        
        s.close()
    except Exception as e:
        print(f"[Full Spam Error {uid}]:", e)

@app.get("/rishu")
def rishu_endpoint():
    team_code = (request.args.get("Tc") or "").strip()
    if not team_code.isdigit():
        return jsonify(ok=False, error="Tc must be a numeric team code"), 400

    try:
        with _api_lock:
            threads = []
            for uid, pwd in BOT_ACCOUNTS:
                if not uid:
                    continue
                t = threading.Thread(target=full_spam_worker, args=(uid, pwd, team_code))
                t.start()
                threads.append(t)
            
            for t in threads:
                t.join(timeout=8.0)

        return jsonify(ok=True, Team_Code=team_code, message="Full spam execution completed!"), 200
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), threaded=True)
