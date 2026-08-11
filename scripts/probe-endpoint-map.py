# Probe peta endpoint API Kampus Kita UNAIR — arsip (2026-08-12)
# Token dibaca dari ~/.kk_lite/config.json (hasilkan dengan kk_lite.py login/dumpphone).
# Endpoint yang butuh POST: /akademik/jadwal-kuliah, /kemahasiswaan/riwayat-khs
# (riwayat-khs juga butuh param `semester=<id>` dari /akademik/semester-khs).
import json, os, urllib.request

tok = json.load(open(os.path.expanduser("~/.kk_lite/config.json")))["token"]
BASE = "https://apikampuskita-mahasiswa.unair.ac.id"

ENDPOINTS = [
    # akademik
    "/akademik/status-mhs", "/akademik/semester-khs", "/akademik/jadwal-kuliah",
    "/akademik/ipk", "/akademik/ips", "/akademik/kalender-akademik", "/akademik/masa-studi",
    "/akademik/sks-aktif", "/akademik/sks-lulus", "/akademik/skor-skp",
    "/akademik/dosen-wali", "/akademik/peserta-mata-kuliah", "/akademik/tes-elpt",
    # kemahasiswaan
    "/kemahasiswaan/presensi-kuliah", "/kemahasiswaan/inbox", "/kemahasiswaan/pembayaran",
    "/kemahasiswaan/riwayat-khs", "/kemahasiswaan/hist-her",
    "/kemahasiswaan/penyerahan-ktm", "/kemahasiswaan/tkm",
]

def call(method, path):
    req = urllib.request.Request(BASE + path + "?token=" + tok, data=b"", method=method)
    req.add_header("User-Agent", "Dart/3.3 (dart:io)")
    req.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)

def summarize(text):
    try:
        j = json.loads(text)
    except Exception:
        return ("plain", text[:80].replace("\n", " "))
    if isinstance(j, dict):
        msg = str(j.get("message", ""))[:60]
        data = j.get("data")
        if data is None:
            return ("none", msg or "no data")
        if isinstance(data, list):
            if not data:
                return ("empty-list", msg)
            d0 = data[0]
            if isinstance(d0, dict):
                return ("list[%d]" % len(data), msg + " | keys: " + ", ".join(list(d0.keys())[:8]))
            return ("list-scalar", msg)
        if isinstance(data, dict):
            return ("dict", msg + " | keys: " + ", ".join(list(data.keys())[:8]))
    return ("other", text[:80].replace("\n", " "))

print(f"{'ENDPOINT':<38} {'M':<4} {'ST':<4} TYPE/INFO")
print("-" * 100)
for ep in ENDPOINTS:
    for method in ("GET", "POST"):
        st, txt = call(method, ep)
        if st == 405:
            continue
        kind, info = summarize(txt)
        print(f"{ep:<38} {method:<4} {st:<4} {kind}: {info}")
        break
    else:
        print(f"{ep:<38} {'-':<4} {'405':<4} method both rejected")
