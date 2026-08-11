# Probe /kemahasiswaan/riwayat-khs (butuh param semester) — arsip (2026-08-12)
# Temuan: POST + param `semester=<ID_SEMESTER>` (dari /akademik/semester-khs);
# tanpa param → 422 "semester tidak ada". Isi presensi-kuliah juga dicetak.
import json, os, urllib.request

tok = json.load(open(os.path.expanduser("~/.kk_lite/config.json")))["token"]
BASE = "https://apikampuskita-mahasiswa.unair.ac.id"

def call(method, path, body=None, q=None):
    u = BASE + path + "?token=" + tok
    if q:
        u += "&" + "&".join(f"{k}={v}" for k, v in q.items())
    data = body.encode() if body else b""
    req = urllib.request.Request(u, data=data, method=method)
    req.add_header("User-Agent", "Dart/3.3 (dart:io)")
    req.add_header("Authorization", "Bearer " + tok)
    if body:
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)

# 1. riwayat-khs dengan param semester (form & query) vs tanpa param
for lbl, kw, body in [
    ("q-smes", {"semester": "<ID_SEMESTER>"}, None),
    ("q-idsem", {"ID_SEMESTER": "<ID_SEMESTER>"}, None),
    ("f-smes", None, "semester=<ID_SEMESTER>"),
    ("tanpa-param", None, None),
]:
    st, txt = call("POST", "/kemahasiswaan/riwayat-khs", body=body, q=kw)
    print(f"[{lbl}] riwayat-khs -> HTTP {st}: {txt[:300]}")
    print()

# 2. isi presensi-kuliah (baris per MK: TM, HADIR, PROSEN)
st, txt = call("GET", "/kemahasiswaan/presensi-kuliah")
j = json.loads(txt)
print(f"presensi-kuliah HTTP {st} — {len(j.get('data', []))} baris")
for r in j.get("data", []):
    print("  ", {k: r.get(k) for k in list(r.keys())[:12]})
