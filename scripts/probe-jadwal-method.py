# Probe metode & autentikasi /akademik/jadwal-kuliah — arsip (2026-08-12)
# Temuan: GET → 405; yang diterima = POST + Authorization Bearer (+ query token).
# Kombinasi header lain (token: / X-Access-Token / body JSON ID_MHS) ditolak.
import json, os, urllib.request

tok = json.load(open(os.path.expanduser("~/.kk_lite/config.json")))["token"]
url = "https://apikampuskita-mahasiswa.unair.ac.id/akademik/jadwal-kuliah"

tests = [
    ("POST-Bearer", "POST", False, {"Authorization": "Bearer " + tok}, None),
    ("POST-Bearer+query", "POST", True, {"Authorization": "Bearer " + tok}, None),
    ("POST-Token-hdr", "POST", False, {"token": tok}, None),
    ("POST-X-Auth", "POST", False, {"X-Access-Token": tok}, None),
    ("GET-Bearer", "GET", False, {"Authorization": "Bearer " + tok}, None),
    ("GET-Bearer+query", "GET", True, {"Authorization": "Bearer " + tok}, None),
]

for name, method, qtok, headers, body in tests:
    try:
        u = url + ("?token=" + tok if qtok else "")
        data = body.encode() if body else b""
        req = urllib.request.Request(u, data=data, method=method)
        req.add_header("User-Agent", "Dart/3.3 (dart:io)")
        if body:
            req.add_header("Content-Type", "application/json")
        for k, v in headers.items():
            req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=25) as r:
            print(name, r.status, r.read().decode()[:400])
    except urllib.error.HTTPError as e:
        print(name, e.code, e.read().decode()[:400])
    except Exception as e:
        print(name, "ERR", e)
