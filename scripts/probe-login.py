# Probe login API Kampus Kita UNAIR — arsip temuan (2026-08-12)
#
# JALUR PENEMUAN (dari binary app + percobaan):
#  1. Format lama app: EMAIL_PENGGUNA + DRIVE_PASS=sha256(password) → HTTP 422
#     "Email is required / Password is required" (ditolak API)
#  2. Format yang BENAR: email + password PLAINTEXT → HTTP 200
#  3. JWT tidak diharuskan keluar dari body — dia keluar via header
#     `Set-Cookie: token=<JWT>; domain=localhost; HttpOnly; SameSite=Lax`
#     (domain=localhost = bug config server dev UNAIR; HttpOnly = tak terbaca
#     browser → web butuh proxy serverless, lihat api/login.js)
#  4. JWT HS256 payload {IDMhs, IDPengguna, exp, username}, berlaku ~1 tahun.
#
# PENTING: isi EMAIL/PW sebelum dijalankan, atau export env KK_EMAIL / KK_PW.
import os, re, json, base64, urllib.request, urllib.parse, hashlib

BASE = "https://apikampuskita-mahasiswa.unair.ac.id"
EMAIL = os.environ.get("KK_EMAIL", "<email kampus>")
PW = os.environ.get("KK_PW", "<password>")

def call(fields, show=200):
    body = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(BASE + "/auth/login", data=body, method="POST")
    req.add_header("User-Agent", "Dart/3.3 (dart:io)")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.headers.get("Set-Cookie", ""), r.read().decode()[:show]
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Set-Cookie", ""), e.read().decode()[:show]

# --- 1. format lama (gagal) vs format baru (berhasil) ---
variants = [
    ("email+password sha256", {"email": EMAIL, "password": hashlib.sha256(PW.encode()).hexdigest()}),
    ("EMAIL_PENGGUNA+DRIVE_PASS", {"EMAIL_PENGGUNA": EMAIL, "DRIVE_PASS": hashlib.sha256(PW.encode()).hexdigest()}),
    ("email+password plaintext", {"email": EMAIL, "password": PW}),
]
for label, fields in variants:
    st, setc, txt = call(fields)
    print(f"[{label}] HTTP {st}  set-cookie={'ADA' if setc else '-'}  {txt[:80]!r}")

# --- 2. ambil JWT dari Set-Cookie dan validasi ---
st, setc, txt = call({"email": EMAIL, "password": PW})
m = re.search(r"token=([^;]+)", setc)
if not m:
    print("\nTidak ada token di Set-Cookie — cek body:")
    print(txt)
    raise SystemExit(1)
tok = m.group(1)
print("\nJWT dari Set-Cookie: len", len(tok))

payload = tok.split(".")[1]
payload += "=" * (-len(payload) % 4)
print("payload:", json.loads(base64.urlsafe_b64decode(payload).decode()))

req2 = urllib.request.Request(BASE + "/akademik/status-mhs?token=" + tok, method="GET")
req2.add_header("Authorization", "Bearer " + tok)
req2.add_header("User-Agent", "Dart/3.3 (dart:io)")
with urllib.request.urlopen(req2, timeout=25) as r2:
    print("validasi /akademik/status-mhs:", r2.status, r2.read().decode()[:130])
