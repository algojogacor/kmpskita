# Probe CORS API Kampus Kita UNAIR — arsip (2026-08-12)
# Temuan: server meng-echo origin apa pun + Allow-Headers: authorization,
# content-type + Allow-Methods GET/POST/HEAD/PUT/DELETE/PATCH
# → browser bisa fetch LANGSUNG ke API dari halaman web mana pun
# (dasar arsitektur PWA statis di Vercel, tanpa proxy kecuali untuk LOGIN).
import json, os, urllib.request

tok = json.load(open(os.path.expanduser("~/.kk_lite/config.json")))["token"]
BASE = "https://apikampuskita-mahasiswa.unair.ac.id"

def show_headers(r):
    for h, v in r.headers.items():
        if "access-control" in h.lower() or "allow" in h.lower():
            print(f"  {h}: {v}")

req = urllib.request.Request(BASE + "/akademik/status-mhs?token=" + tok, method="GET")
req.add_header("User-Agent", "Dart/3.3 (dart:io)")
req.add_header("Authorization", "Bearer " + tok)
req.add_header("Origin", "http://localhost:8888")
try:
    with urllib.request.urlopen(req, timeout=25) as r:
        print("status:", r.status)
        show_headers(r)
except urllib.error.HTTPError as e:
    print("status:", e.code)
    show_headers(e)

# tes preflight OPTIONS (dipicu browser saat header Authorization dipakai)
req2 = urllib.request.Request(BASE + "/akademik/status-mhs", method="OPTIONS")
req2.add_header("Origin", "http://localhost:8888")
req2.add_header("Access-Control-Request-Method", "GET")
req2.add_header("Access-Control-Request-Headers", "authorization")
try:
    with urllib.request.urlopen(req2, timeout=25) as r:
        print("OPTIONS status:", r.status)
        show_headers(r)
except urllib.error.HTTPError as e:
    print("OPTIONS status:", e.code)
    show_headers(e)
except Exception as e:
    print("OPTIONS ERR:", e)
