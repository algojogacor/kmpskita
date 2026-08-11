#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kk_lite.py — Kampus Kita Mahasiswa API client (ringan, tanpa aplikasi Flutter).
Reverse-engineered from id.ac.unair.kampuskitamahasiswa v2.1.2 (libapp.so AOT strings).

Login TERVERIFIKASI (dari dump HP + binary):
  POST https://apikampuskita-mahasiswa.unair.ac.id/auth/login
  body: EMAIL_PENGGUNA=<email kampus>  DRIVE_PASS=sha256(<password>)
  -> respon berisi JWT (HS256) payload {IDMhs, IDPengguna, exp, username}

Hosts:
  https://apikampuskita-mahasiswa.unair.ac.id   -> /auth/login, /akademik/*, /kemahasiswaan/* (token via ?token= atau header)
  https://apicybercampus.unair.ac.id/api        -> /mahasiswa/presensi (presensi live)
  https://unairsatu.unair.ac.id                 -> /token/ambil-token-v2 (SSO, masih 500 — belum dipakai)

CATATAN JARINGAN: server apikampuskita (210.57.208.253) MEMBLOKIR IP rumah/PC
(TCP timeout), tapi OKE dari data seluler. Solusi: USB tethering dari HP, atau
jalankan dari WiFi kampus. JWT hasil login berlaku ~1 tahun (exp Jan 2027).

Stdlib only. Python 3.8+.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime

VERSION = "0.4.0"
BASE_KK   = "https://apikampuskita-mahasiswa.unair.ac.id"
BASE_UN   = "https://unairsatu.unair.ac.id"
BASE_CYB  = "https://apicybercampus.unair.ac.id"
CFG_PATH  = os.path.join(os.path.expanduser("~"), ".kk_lite", "config.json")

# ---- config ----------------------------------------------------------------
def load_cfg():
    if os.path.exists(CFG_PATH):
        try:
            with open(CFG_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_cfg(cfg):
    os.makedirs(os.path.dirname(CFG_PATH), exist_ok=True)
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

# ---- http ------------------------------------------------------------------
_CTX = ssl.create_default_context()

def http(method, url, data=None, headers=None, timeout=20):
    """Return (status, text). No redirect following for POST; GET follows."""
    h = {"User-Agent": "Dart/3.3 (dart:io)"}
    if headers:
        h.update(headers)
    body = None
    if data is not None:
        if isinstance(data, str):
            body = data.encode()
        elif isinstance(data, dict):
            body = urllib.parse.urlencode(data).encode()
        h.setdefault("Content-Type", "application/x-www-form-urlencoded")
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)

def parse_maybe(text):
    try:
        return json.loads(text)
    except Exception:
        return None

def api_call(method, path, token, params=None, body=None, host=BASE_KK):
    """Request ke apikampuskita. Selalu kirim Bearer header + token query.
    jadwal-kuliah dan beberapa endpoint lain butuh POST; GET jalan untuk lainnya."""
    url = host + path
    if token:
        q = {"token": token}
        if params:
            q.update(params)
        url += "?" + urllib.parse.urlencode(q)
    st, txt = http(method, url, data=body, headers={"Authorization": "Bearer " + token} if token else None)
    return st, txt

def api_get(path, token, params=None, host=BASE_KK):
    return api_call("GET", path, token, params, host=host)

# ---- login (multi-format explorer) -----------------------------------------
HEX_KEY = "23e68bc98222339eb30959aade856a732c4f3ea04e5c229e00cede6c5378c2ed"

def sha256s(s):
    return hashlib.sha256(s.encode()).hexdigest()

def login_formats(email, password):
    """Yield (label, method, url, payload). Format benar (dari dump HP):
    POST apikampuskita /auth/login, EMAIL_PENGGUNA + DRIVE_PASS=sha256(pw)."""
    pwd = password
    base = [
        # -- format TERVERIFIKASI dari app (prioritas) --
        ("kk-auth-emailpass-sha256",  "POST", BASE_KK + "/auth/login", {"EMAIL_PENGGUNA": email, "DRIVE_PASS": sha256s(pwd)}),
        ("kk-auth-emailpass-plain",   "POST", BASE_KK + "/auth/login", {"EMAIL_PENGGUNA": email, "DRIVE_PASS": pwd}),
        ("kk-auth-json-emailpass-sha","POST", BASE_KK + "/auth/login", json.dumps({"EMAIL_PENGGUNA": email, "DRIVE_PASS": sha256s(pwd)})),
        # -- fallback explorer --
        ("kk-auth-login-form",        "POST", BASE_KK + "/auth/login", {"email": email, "password": pwd}),
        ("kk-auth-login-json",        "POST", BASE_KK + "/auth/login", json.dumps({"email": email, "password": pwd})),
        ("kk-auth-login-sha256",      "POST", BASE_KK + "/auth/login", {"email": email, "password": sha256s(pwd)}),
        ("unairsatu-v1-form-plain",   "POST", BASE_UN + "/token/ambil-token", {"email": email, "password": pwd}),
        ("unairsatu-v1-form-uep",     "POST", BASE_UN + "/token/ambil-token", {"user_email": email, "user_pass": pwd}),
        ("kk-v2-form-sha256",         "POST", BASE_KK + "/token/ambil-token-v2", {"email": email, "password": sha256s(pwd)}),
        ("kk-v2-json-sha256",         "POST", BASE_KK + "/token/ambil-token-v2", json.dumps({"email": email, "password": sha256s(pwd)})),
    ]
    return base

def extract_token(text):
    """Try to pull a token out of any response shape (incl. JWT)."""
    if not text:
        return None
    m = re.search(r'"token"\s*:\s*"([^"]+)"', text)
    if m:
        return m.group(1)
    m = re.search(r'"access_token"\s*:\s*"([^"]+)"', text)
    if m:
        return m.group(1)
    m = re.search(r'eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}', text)
    if m:
        return m.group(0)
    return None

def cmd_login(args):
    email = args.email or load_cfg().get("email")
    pwd = args.password
    if not email or not pwd:
        sys.exit("[!] usage: kk_lite login --email E --password P")
    print(f"[*] email: {email}")
    for label, method, url, payload in login_formats(email, pwd):
        headers = {}
        body = payload
        if isinstance(payload, str):
            headers = {"Content-Type": "application/json"}
        st, txt = http(method, url, body, headers)
        tok = extract_token(txt)
        snippet = txt[:160].replace("\n", " ")
        mark = "TOKEN!" if tok else ""
        print(f"  [{label}] HTTP {st} {mark}  {snippet}")
        if tok:
            cfg = load_cfg()
            cfg.update(email=email, token=tok, login_label=label)
            save_cfg(cfg)
            print(f"[+] Token tersimpan: {tok[:40]}... (-> {CFG_PATH})")
            return 0
    print("[!] Semua format login gagal. Gunakan `kk_lite dumpimport <file>` dengan hasil dump HP, atau cek token manual.")
    return 1

# ---- API field names (dari libapp.so — konvensi UPPERCASE_SNAKE) ------------
# Jadwal kuliah:
J = {
    "mk":   ["NM_MATA_KULIAH", "nama_mk", "mata_kuliah", "matakuliah"],
    "kode": ["KD_MATA_KULIAH", "kode_mk"],
    "hari": ["NM_JADWAL_HARI", "hari", "nama_hari"],
    "mulai":["WAKTU_MULAI", "jam_mulai", "jam_awal", "mulai"],
    "selesai":["WAKTU_SELESAI", "jam_selesai", "jam_akhir", "selesai"],
    "ruang":["NM_RUANGAN", "ruang", "ruangan"],
    "gedung":["NM_GEDUNG"],
    "dosen":["NM_DOSEN", "dosen", "nama_dosen"],
    "kelas":["NAMA_KELAS", "kelas"],
    "semester":["ID_SEMESTER", "TIPE_SEMESTER", "GROUP_SEMESTER"],
    "validasi":["VALIDASI_KOMTING"],
    "qr":    ["QR_CODE"],
}
# Profil / status:
P = {
    "nama":   ["NM_PENGGUNA", "nama"],
    "nim":    ["NIM_MHS", "nim"],
    "id_mhs": ["ID_MHS"],
    "email":  ["EMAIL_PENGGUNA", "email"],
    "status": ["NM_STATUS_PENGGUNA"],
    "jenjang":["NM_JENJANG", "ID_JENJANG"],
    "prodi":  ["NM_PROGRAM_STUDI", "PROGRAM_STUDI"],
    "ipk":    ["IPK_MHS"],
    "sks_lulus": ["SKS_LULUS"],
    "sks_tempuh": ["SKS_TEMPUH"],
    "ibu":    ["NM_IBU_MHS"], "ayah": ["NM_AYAH_MHS"],
}
HARI_ID = {"Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
           "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu",
           "Sunday": "Minggu"}

def pick(d, keys):
    for k in keys:
        v = d.get(k)
        if v not in (None, "", "null"):
            return v
    return ""

def rows_from(j):
    """Normalize any response shape into a list of dicts.
    Jadwal-kuliah bentuknya {"data":[{"Senin":[...]}, {"Selasa":[...]}]} -> flatten."""
    if isinstance(j, list):
        out = []
        for r in j:
            if isinstance(r, dict):
                if all(isinstance(v, list) for v in r.values()):
                    for lst in r.values():
                        out.extend(x for x in lst if isinstance(x, dict))
                else:
                    out.append(r)
        return out
    if isinstance(j, dict):
        for k in ("data", "result", "jadwal", "rows", "list", "data_jadwal",
                  "data_presensi", "jadwal_kuliah"):
            v = j.get(k)
            if isinstance(v, list):
                return rows_from(v)
            if isinstance(v, dict) and all(isinstance(x, list) for x in v.values()):
                return rows_from(list(v.values()))
        return []
    return []

# ---- read endpoints ---------------------------------------------------------
def token_or(args):
    tok = args.token or load_cfg().get("token")
    if not tok:
        sys.exit("[!] Tidak ada token. Jalankan `kk_lite login` dulu atau `--token`.")
    return tok

def fetch_json(path, args, params=None):
    tok = token_or(args)
    st, txt = api_get(path, tok, params)
    if st == 405:  # endpoint ini ternyata POST
        st, txt = api_call("POST", path, tok, params)
    j = parse_maybe(txt)
    if st != 200 or (isinstance(j, dict) and j.get("status") in ("error", "failed", "invalid")):
        print(f"[!] {path} -> HTTP {st}: {txt[:300]}")
        return None
    return j

def pretty(j):
    return json.dumps(j, indent=2, ensure_ascii=False)

def jam_parts(r):
    """Return (mulai, selesai). Field JAM gabungan '13:00 - 15:00' atau terpisah."""
    m = pick(r, J["mulai"])
    s = pick(r, J["selesai"])
    if not m:
        jam = pick(r, ["JAM", "jam", "waktu"])
        mm = re.match(r"(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})", str(jam))
        if mm:
            return mm.group(1), mm.group(2)
    return m, s

def cmd_jadwal(args):
    j = fetch_json("/akademik/jadwal-kuliah", args)
    if j is None:
        return 1
    if args.raw:
        print(pretty(j)); return 0
    rows = rows_from(j)
    if not rows:
        print(pretty(j)); return 0
    today_name = HARI_ID[datetime.now().strftime("%A")]
    show = []
    for r in rows:
        if args.today:
            h = str(pick(r, J["hari"]))
            if h and h.lower() != today_name.lower():
                continue
        show.append(r)
    print(f"[*] Total jadwal: {len(rows)}  |  hari ini ({today_name}): {len(show)}")
    for r in show:
        mk = pick(r, J["mk"]) or "?"
        kd = pick(r, J["kode"])
        t, jm = jam_parts(r)
        rn = pick(r, J["ruang"])
        gd = pick(r, J["gedung"])
        d = pick(r, J["dosen"])
        kl = pick(r, J["kelas"])
        v = pick(r, J["validasi"])
        loc = " • ".join(x for x in (rn, gd, kl) if x)
        parts = [f"{t}–{jm}", mk, f"[{loc}]", d, v]
        if not args.today:
            parts.insert(0, pick(r, J["hari"]))
        print("  " + "  ".join(x for x in parts if x))
    return 0

def cmd_presensi(args):
    j = fetch_json("/kemahasiswaan/presensi-kuliah", args)
    if j is None: return 1
    rows = rows_from(j)
    if not rows:
        print(pretty(j)); return 0
    print(f"[*] Presensi semester ini ({len(rows)} MK):")
    for r in rows:
        mk = pick(r, J["mk"]) or "?"
        tm = pick(r, ["TM", "TOTAL_MINGGU"])
        hd = pick(r, ["HADIR", "JUMLAH_HADIR"])
        pn = pick(r, ["PROSEN", "PERSENTASE"])
        st = pick(r, ["STATUS", "status"])
        kl = pick(r, ["NAMA_KELAS", "kelas"])
        sks = pick(r, ["KREDIT_SEMESTER", "sks"])
        pct = ""
        try:
            if pn not in ("", "0"):
                pct = f" ({pn}%)"
        except Exception:
            pass
        print(f"  {mk}  [{kl}]  {sks} SKS  |  hadir {hd}/{tm}  {pct}  {st}")
    return 0

def cmd_status(args):
    j = fetch_json("/akademik/status-mhs", args)
    if j is None: return 1
    rows = rows_from(j)
    r = rows[0] if rows else j
    cfg = load_cfg()
    if isinstance(r, dict):
        print(f"  Nama   : {pick(r, P['nama']) or cfg.get('name', '-')}")
        print(f"  NIM    : {pick(r, P['nim'])}")
        print(f"  Status : {pick(r, P['status'])}")
        print(f"  Jenjang: {pick(r, P['jenjang'])}")
        print(f"  Prodi  : {pick(r, P['prodi'])}")
        st, txt = api_get("/akademik/sks-aktif", token_or(args))
        j2 = parse_maybe(txt)
        r2 = rows_from(j2) if isinstance(j2, dict) else []
        if r2:
            print(f"  SKS    : tempuh={pick(r2[0], P['sks_tempuh'])}  MK={pick(r2[0], ['JUM_MK'])}")
    else:
        print(pretty(j))
    return 0

def cmd_get(args, path):
    j = fetch_json(path, args)
    if j is None: return 1
    print(pretty(j))
    return 0

def cmd_nilai(args):
    """KHS nilai per MK: semester terbaru otomatis, atau --semester <id>."""
    tok = token_or(args)
    if args.semester:
        sms = args.semester
    else:
        st, txt = api_get("/akademik/semester-khs", tok)
        j = parse_maybe(txt)
        rows = rows_from(j)
        if not rows:
            print("[!] Tidak ada semester KHS."); return 1
        sms = pick(rows[0], ["ID_SEMESTER"])
        ta = pick(rows[0], ["TAHUN_AJARAN"]) + " " + pick(rows[0], ["NM_SEMESTER"])
        print(f"[*] Semester terbaru: {ta} (id {sms})")
    st, txt = api_call("POST", "/kemahasiswaan/riwayat-khs", tok, params={"semester": sms})
    j = parse_maybe(txt)
    if st != 200:
        print(f"[!] riwayat-khs -> HTTP {st}: {txt[:300]}"); return 1
    rows = rows_from(j)
    if not rows:
        print(pretty(j)); return 0
    tot_sks = 0
    print(f"{'KODE':<12} {'MATA KULIAH':<28} {'KELAS':<8} {'SKS':<4} {'NILAI':<7} {'HURUF':<6}")
    print("-" * 72)
    for r in rows:
        kd = pick(r, ["KODE", "KD_MATA_KULIAH"])
        mk = pick(r, ["NAMA", "NM_MATA_KULIAH"])
        kl = pick(r, ["NAMA_KELAS"])
        sks = pick(r, ["SKS"])
        n = pick(r, ["NILAI"])
        hf = pick(r, ["NILAI_HURUF"])
        try:
            tot_sks += int(sks)
        except Exception:
            pass
        print(f"  {kd:<10} {mk:<28} {kl:<8} {sks:<4} {n:<7} {hf:<6}")
    print("-" * 72)
    print(f"  Total SKS: {tot_sks}")
    return 0

# ---- web server (wrapper: jadwal + presensi + nilai + status + e-learning) ---
PAGE = """<!doctype html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0f172a">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>KK Lite — Kampus Kita</title>
<link rel="manifest" href="/manifest.json">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%93%9A%3C/text%3E%3C/svg%3E">
<style>
:root{--bg:#0f172a;--card:#1e293b;--fg:#e2e8f0;--muted:#94a3b8;--accent:#38bdf8;--ok:#4ade80;--warn:#fbbf24;--bad:#f87171}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;max-width:760px;margin:auto;padding-bottom:84px}
header{padding:18px 20px 10px;position:sticky;top:0;background:var(--bg);z-index:5}
h1{font-size:1.25em} #meta{color:var(--muted);font-size:.82em;margin-top:2px}
#err{display:none;background:#7f1d1d;color:#fecaca;padding:10px 14px;border-radius:10px;margin:10px 20px 0}
main{padding:6px 16px}
#count{color:var(--muted);font-size:.85em;margin:8px 4px 10px}
.card{background:var(--card);border-radius:14px;padding:14px 16px;margin-bottom:10px;border-left:4px solid var(--accent)}
.card.done{border-left-color:var(--ok)} .card.next{border-left-color:var(--warn)}
.time{font-weight:700;color:var(--accent);font-size:1.05em}
.mk{font-weight:600;font-size:1.02em;margin-top:2px}
.ruang,.dosen{color:var(--muted);font-size:.88em}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;font-size:.72em;font-weight:700;margin-top:6px}
.badge.live{background:#14532d;color:#86efac;animation:pulse 1.6s infinite}
.badge.soon{background:#78350f;color:#fde68a}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.55}}
.empty{color:var(--muted);text-align:center;padding:28px}
.hdr{font-size:.95em;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin:16px 4px 8px}
.bar{background:#0f172a;border-radius:999px;height:8px;margin-top:8px;overflow:hidden}
.bar i{display:block;height:100%;background:var(--ok);border-radius:999px;transition:width .5s}
.row{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #33415555;font-size:.92em}
.row:last-child{border-bottom:0}
table{width:100%;border-collapse:collapse;font-size:.88em}
th,td{padding:7px 6px;text-align:left;border-bottom:1px solid #33415555}
th{color:var(--muted);font-size:.78em;text-transform:uppercase;letter-spacing:.03em}
nav{position:fixed;bottom:0;left:0;right:0;background:#0b1220ee;backdrop-filter:blur(8px);border-top:1px solid #334155;display:flex;max-width:760px;margin:auto}
nav button{flex:1;background:none;border:0;color:var(--muted);padding:10px 2px 12px;font-size:.68em;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:3px}
nav button .ic{font-size:1.3em;line-height:1}
nav button.on{color:var(--accent)}
a{color:var(--accent)}
.link-btn{display:block;background:var(--card);border-radius:14px;padding:14px 16px;margin-bottom:10px;text-decoration:none;color:var(--fg);border-left:4px solid var(--accent)}
.link-btn .t{font-weight:600} .link-btn .s{color:var(--muted);font-size:.85em}
</style></head><body>
<header>
  <h1>📚 KK Lite</h1>
  <div id="meta">memuat…</div>
</header>
<div id="err"></div>
<main id="view"></main>
<nav id="nav">
  <button data-v="today" class="on"><span class="ic">🗓</span>Hari Ini</button>
  <button data-v="week"><span class="ic">📅</span>Minggu Ini</button>
  <button data-v="presensi"><span class="ic">✅</span>Presensi</button>
  <button data-v="nilai"><span class="ic">📖</span>Nilai</button>
  <button data-v="status"><span class="ic">🎓</span>Status</button>
  <button data-v="elearn"><span class="ic">💻</span>E-Learning</button>
</nav>
<script>
const $=id=>document.getElementById(id);
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=s=>{ if(!s) return ''; const m=String(s).match(/^(\\d{4}-\\d{2}-\\d{2})/); return m? m[1].split('-').reverse().join('/') : s; };
async function api(p){ const r=await fetch('/api/'+p); if(!r.ok) throw new Error(await r.text()); return r.json(); }
let META=null;
async function boot(){
  try{ META=await api('meta'); $('meta').textContent=META.name+' · '+META.nim+' · '+META.day+', '+META.date; }
  catch(e){ $('meta').textContent='token/API error'; }
}
function cardJadwal(x){
  const now=new Date(), cur=now.getHours()*60+now.getMinutes();
  const [a]=x.jam.split('–'); let cls='';
  let m0=0,m1=0; if(a){const p=a.split(':'); m0=+p[0]*60+(+p[1]||0);}
  const b=x.jam.split('–')[1]; if(b){const p=b.split(':'); m1=+p[0]*60+(+p[1]||0);}
  let badge='';
  if(cur>=m0&&cur<=m1) cls='done',badge='<span class="badge live">● PRESENSI SEKARANG</span>';
  else if(m0>cur&&m0-cur<=120) cls='next',badge='<span class="badge soon">sebentar lagi</span>';
  return '<div class="card '+cls+'"><div class="time">'+x.jam+'</div><div class="mk">'+esc(x.mk)+'</div>'+
    '<div class="ruang">📍 '+esc(x.ruang)+'</div><div class="dosen">'+esc(x.dosen)+'</div>'+badge+'</div>';
}
const VIEWS={
  today:async()=>{
    const d=await api('today');
    $('view').innerHTML='<div id="count">'+d.total+' jadwal hari ini</div><div id="list"></div>';
    if(!d.items.length){$('list').innerHTML='<div class="empty">✅ Hari ini tidak ada kuliah.</div>';return;}
    $('list').innerHTML=d.items.map(cardJadwal).join('');
  },
  week:async()=>{
    const d=await api('week');
    let h='';
    for(const day of d.days){
      if(!day.items.length) continue;
      h+='<div class="hdr">'+day.name+' ('+day.date+')</div>'+day.items.map(cardJadwal).join('');
    }
    $('view').innerHTML=h||'<div class="empty">Belum ada jadwal.</div>';
  },
  presensi:async()=>{
    const d=await api('presensi');
    $('view').innerHTML='<div id="count">'+d.total+' mata kuliah</div>'+
      d.items.map(x=>'<div class="card"><div class="mk">'+esc(x.mk)+' <span style="color:var(--muted);font-size:.85em">['+esc(x.kelas)+'] '+x.sks+' SKS</span></div>'+
      '<div class="ruang">hadir '+x.hadir+' / '+x.tm+' &nbsp;·&nbsp; <b>'+x.prosen+'%</b></div>'+
      '<div class="bar"><i style="width:'+Math.min(100,+x.prosen)+'%"></i></div></div>').join('');
  },
  nilai:async()=>{
    const d=await api('nilai');
    $('view').innerHTML='<div id="count">'+d.semester+' · '+d.total+' MK · total '+d.sks+' SKS</div>'+
      '<div class="card" style="padding:8px 12px"><table><tr><th>Kode</th><th>Mata Kuliah</th><th>SKS</th><th>Nilai</th></tr>'+
      d.items.map(x=>'<tr><td style="color:var(--muted)">'+esc(x.kode)+'</td><td>'+esc(x.nama)+'</td><td>'+x.sks+'</td><td><b>'+esc(x.huruf)+'</b></td></tr>').join('')+'</table></div>';
  },
  status:async()=>{
    const d=await api('status');
    $('view').innerHTML='<div class="card">'+
      '<div class="mk">'+esc(d.nama)+'</div>'+
      '<div class="row"><span>NIM</span><b>'+esc(d.nim)+'</b></div>'+
      '<div class="row"><span>Status</span><b>'+esc(d.status)+'</b></div>'+
      '<div class="row"><span>Jenjang</span><b>'+esc(d.jenjang)+'</b></div>'+
      '<div class="row"><span>Prodi</span><b>'+esc(d.prodi)+'</b></div>'+
      '<div class="row"><span>SKS</span><b>'+d.sks+' ('+d.mk+' MK)</b></div>'+
      '</div>'+
      '<div class="hdr">Pembayaran</div><div class="card">'+
      d.pay.map(x=>'<div class="row"><span>'+esc(x.semester)+'</span><b>'+esc(x.status)+' · '+esc(x.nominal)+'</b></div>').join('')+'</div>'+
      '<div class="hdr">Kalender Akademik</div><div class="card">'+
      d.kalender.map(x=>'<div class="row"><span>'+esc(x.nama)+'</span><b style="color:var(--muted)">'+fmt(x.mulai)+' s.d. '+fmt(x.selesai)+'</b></div>').join('')+'</div>';
  },
  elearn:()=>{
    $('view').innerHTML=
      '<a class="link-btn" href="https://hebat.elearning.unair.ac.id/hebat-v2/" target="_blank" rel="noopener"><div class="t">💻 HE-BAT (e-Learning UNAIR)</div><div class="s">hebat.elearning.unair.ac.id/hebat-v2/ · buka di tab baru</div></a>'+
      '<a class="link-btn" href="https://apikampuskita-mahasiswa.unair.ac.id/" target="_blank" rel="noopener"><div class="t">🏛 Portal Kampus Kita (API)</div><div class="s">sumber data app</div></a>';
  }
};
document.querySelectorAll('nav button').forEach(b=>b.onclick=async()=>{
  document.querySelectorAll('nav button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on');
  const err=$('err'); err.style.display='none'; $('view').innerHTML='<div class="empty">memuat…</div>';
  try{ await VIEWS[b.dataset.v](); }catch(e){ err.style.display='block'; err.textContent='Gagal: '+e.message; }
});
boot();
document.querySelectorAll('nav button')[0].click();
</script></body></html>"""

def cmd_serve(args):
    import http.server, socket
    port = args.port
    cfg = load_cfg()
    email = cfg.get("email", "")
    name = cfg.get("name", "")
    nim = cfg.get("nim", "")
    token = token_or(args)

    def jadwal_rows():
        st, txt = api_call("POST", "/akademik/jadwal-kuliah", token)
        j = parse_maybe(txt)
        return rows_from(j) if isinstance(j, dict) else []

    def today_items():
        today_name = HARI_ID[datetime.now().strftime("%A")]
        items = []
        for r in jadwal_rows():
            h = str(pick(r, J["hari"]))
            if h and h.lower() != today_name.lower():
                continue
            m0, m1 = jam_parts(r)
            items.append({
                "jam": "–".join(x for x in (m0, m1) if x),
                "mk": pick(r, J["mk"]) or "?",
                "ruang": " • ".join(x for x in (pick(r, J["ruang"]), pick(r, J["gedung"])) if x) or "?",
                "dosen": pick(r, J["dosen"]),
            })
        items.sort(key=lambda x: x["jam"])
        return items

    DAY_ORDER = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

    def presensi_items():
        st, txt = api_get("/kemahasiswaan/presensi-kuliah", token)
        j = parse_maybe(txt)
        rows = rows_from(j)
        return [{
            "mk": pick(r, J["mk"]) or "?",
            "kelas": pick(r, ["NAMA_KELAS"]),
            "sks": pick(r, ["KREDIT_SEMESTER"]),
            "tm": pick(r, ["TM"]), "hadir": pick(r, ["HADIR"]),
            "prosen": pick(r, ["PROSEN"]),
        } for r in rows]

    def nilai_data():
        st, txt = api_get("/akademik/semester-khs", token)
        j = parse_maybe(txt)
        rows = rows_from(j)
        if not rows:
            return {"semester": "-", "items": [], "sks": 0}
        sms = pick(rows[0], ["ID_SEMESTER"])
        ta = pick(rows[0], ["TAHUN_AJARAN"]) + " " + pick(rows[0], ["NM_SEMESTER"])
        st, txt = api_call("POST", "/kemahasiswaan/riwayat-khs", token, params={"semester": sms})
        j2 = parse_maybe(txt)
        rows2 = rows_from(j2)
        tot = 0
        items = []
        for r in rows2:
            sks = pick(r, ["SKS"])
            try:
                tot += int(sks)
            except Exception:
                pass
            items.append({
                "kode": pick(r, ["KODE", "KD_MATA_KULIAH"]),
                "nama": pick(r, ["NAMA", "NM_MATA_KULIAH"]),
                "sks": sks, "huruf": pick(r, ["NILAI_HURUF"]),
            })
        return {"semester": ta, "items": items, "sks": tot}

    def status_data():
        j = parse_maybe(http_get_json("/akademik/status-mhs"))
        rows = rows_from(j) if isinstance(j, dict) else []
        r = rows[0] if rows else {}
        j2 = parse_maybe(http_get_json("/akademik/sks-aktif"))
        r2 = (rows_from(j2) or [{}])[0] if isinstance(j2, dict) else {}
        j3 = parse_maybe(http_get_json("/kemahasiswaan/pembayaran"))
        pay = []
        for pr in rows_from(j3) if isinstance(j3, dict) else []:
            pay.append({
                "semester": (pick(pr, ["TAHUN_AJARAN"]) + " " + pick(pr, ["NM_SEMESTER"])).strip(),
                "status": pick(pr, ["NAMA_STATUS"]),
                "nominal": "Rp " + format(int(float(pick(pr, ["NOMINAL_BAYAR"]) or 0)), ",").replace(",", "."),
            })
        j4 = parse_maybe(http_get_json("/akademik/kalender-akademik"))
        kal = []
        for kr in rows_from(j4) if isinstance(j4, dict) else []:
            kal.append({
                "nama": pick(kr, ["NM_KEGIATAN"]),
                "mulai": pick(kr, ["TGL_MULAI_JSF"]),
                "selesai": pick(kr, ["TGL_SELESAI_JSF"]),
            })
        return {
            "nama": pick(r, P["nama"]) or name,
            "nim": pick(r, P["nim"]), "status": pick(r, P["status"]),
            "jenjang": pick(r, P["jenjang"]), "prodi": pick(r, P["prodi"]),
            "sks": pick(r2, P["sks_tempuh"]), "mk": pick(r2, ["JUM_MK"]),
            "pay": pay, "kalender": kal,
        }

    def http_get_json(path):
        st, txt = api_get(path, token)
        return txt

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            p = self.path.split("?")[0]
            if p.startswith("/api/"):
                route = p[5:]
                out = {"error": "unknown"}
                try:
                    if route == "meta":
                        now = datetime.now()
                        out = {"name": name, "nim": nim, "email": email,
                               "date": now.strftime("%d/%m/%Y"),
                               "day": HARI_ID[now.strftime("%A")]}
                    elif route == "today":
                        items = today_items()
                        out = {"total": len(items), "items": items}
                    elif route == "week":
                        days, byday = [], {}
                        for r in jadwal_rows():
                            h = str(pick(r, J["hari"])) or "?"
                            m0, m1 = jam_parts(r)
                            byday.setdefault(h, []).append({
                                "jam": "–".join(x for x in (m0, m1) if x),
                                "mk": pick(r, J["mk"]) or "?",
                                "ruang": " • ".join(x for x in (pick(r, J["ruang"]), pick(r, J["gedung"])) if x) or "?",
                                "dosen": pick(r, J["dosen"]),
                            })
                        for d in DAY_ORDER:
                            if d in byday:
                                byday[d].sort(key=lambda x: x["jam"])
                                days.append({"name": d, "date": "", "items": byday[d]})
                        out = {"days": days}
                    elif route == "presensi":
                        items = presensi_items()
                        out = {"total": len(items), "items": items}
                    elif route == "nilai":
                        d = nilai_data()
                        out = {"semester": d["semester"], "total": len(d["items"]),
                               "sks": d["sks"], "items": d["items"]}
                    elif route == "status":
                        out = status_data()
                except Exception as e:
                    out = {"error": str(e)}
                data = json.dumps(out, ensure_ascii=False).encode()
                self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
            elif p == "/manifest.json":
                b = json.dumps({
                    "name": "KK Lite", "short_name": "KK Lite",
                    "start_url": "/", "display": "standalone",
                    "background_color": "#0f172a", "theme_color": "#0f172a",
                }).encode()
                self.send_response(200); self.send_header("Content-Type", "application/manifest+json")
                self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
            else:
                b = PAGE.encode()
                self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    print(f"[*] PC        : http://127.0.0.1:{port}")
    print(f"[*] HP/others : http://{ip}:{port}   (harus satu jaringan — tethering/hotspot)")
    print("[*] Di HP: Chrome -> menu 'Add to Home screen' = jadi app. Ctrl+C untuk stop.")
    http.server.ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()

def cmd_dumpphone(args):
    """Tarik token JWT + profil langsung dari HP via adb (run-as, app debuggable)."""
    import subprocess
    adb = args.adb
    pkg = "id.ac.unair.kampuskitamahasiswa"
    if not os.path.isfile(adb):
        sys.exit(f"[!] adb tidak ada: {adb}. --adb <path> / pastikan platform-tools ter-download.")
    try:
        out = subprocess.run([adb, "shell", f"run-as {pkg} cat shared_prefs/FlutterSharedPreferences.xml"],
                             capture_output=True, text=True, timeout=30)
    except Exception as e:
        sys.exit(f"[!] Gagal jalankan adb: {e}")
    xml = out.stdout or ""
    if "flutter.token" not in xml:
        sys.exit("[!] FlutterSharedPreferences.xml tidak terbaca. Cek: HP terhubung USB + USB debugging, "
                 "app debuggable (debug APK), sudah login di app.\n"
                 f"    debug: {adb} shell 'run-as {pkg} ls shared_prefs/'")
    vals = dict(re.findall(r'name="flutter\.([^"]+)"[^>]*>([^<]*)<', xml))
    tok = vals.get("token", "").strip()
    if not tok:
        sys.exit("[!] flutter.token kosong — login dulu di app.")
    cfg = load_cfg()
    cfg["token"] = tok
    for k in ("email", "name", "nim", "idMhs", "prodi", "idPengguna"):
        if vals.get(k):
            cfg[k] = vals[k]
    save_cfg(cfg)
    print(f"[+] Token dari HP: {tok[:60]}...")
    print(f"[+] Nama: {cfg.get('name')}  NIM: {cfg.get('nim')}  Email: {cfg.get('email')}")
    print(f"[+] Tersimpan di {CFG_PATH}")
    return 0

# ---- main -------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="kk_lite — Kampus Kita API client ringan", prog="kk_lite")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("login", help="coba berbagai format login, simpan token")
    pl.add_argument("--email", "-e"); pl.add_argument("--password", "-p"); pl.set_defaults(fn=cmd_login)

    pt = sub.add_parser("token", help="tes token tersimpan / import token manual")
    pt.add_argument("--token"); pt.add_argument("--set", action="store_true"); pt.set_defaults(fn=cmd_token)

    pd = sub.add_parser("dumpimport", help="impor token dari hasil dump HP (kk_dump/)")
    pd.add_argument("--dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kk_dump"))
    pd.set_defaults(fn=cmd_dumpimport)

    pn = sub.add_parser("dumpphone", help="ambil token JWT langsung dari HP via adb (run-as) — HP harus terhubung USB")
    pn.add_argument("--adb", default=r"D:\Projects\platform-tools\adb.exe")
    pn.set_defaults(fn=cmd_dumpphone)

    pj = sub.add_parser("jadwal", help="jadwal kuliah (--today hanya hari ini)")
    pj.add_argument("--token"); pj.add_argument("--today", "-t", action="store_true")
    pj.add_argument("--raw", action="store_true"); pj.set_defaults(fn=cmd_jadwal)

    pp = sub.add_parser("presensi", help="riwayat presensi kuliah"); pp.add_argument("--token"); pp.set_defaults(fn=cmd_presensi)

    ps = sub.add_parser("status", help="GET /akademik/status-mhs (profil terformat)")
    ps.add_argument("--token"); ps.set_defaults(fn=cmd_status)

    for name, path in [("khs", "/akademik/semester-khs"),
                       ("kalender", "/akademik/kalender-akademik"), ("masa-studi", "/akademik/masa-studi"),
                       ("sks-aktif", "/akademik/sks-aktif"), ("sks-lulus", "/akademik/sks-lulus"),
                       ("skor-skp", "/akademik/skor-skp"), ("dosen-wali", "/akademik/dosen-wali"),
                       ("peserta-mk", "/akademik/peserta-mata-kuliah"), ("tes-elpt", "/akademik/tes-elpt"),
                       ("inbox", "/kemahasiswaan/inbox"), ("pembayaran", "/kemahasiswaan/pembayaran"),
                       ("hist-her", "/kemahasiswaan/hist-her"),
                       ("penyerahan-ktm", "/kemahasiswaan/penyerahan-ktm"), ("tkm", "/kemahasiswaan/tkm")]:
        ps = sub.add_parser(name, help="GET " + path); ps.add_argument("--token"); ps.set_defaults(fn=lambda a, p=path: cmd_get(a, p))

    pn = sub.add_parser("nilai", help="KHS nilai per MK (semester terbaru otomatis, atau --semester <id>)")
    pn.add_argument("--semester"); pn.add_argument("--token"); pn.set_defaults(fn=cmd_nilai)

    ps = sub.add_parser("serve", help="web server lokal: jadwal hari ini (penanda kapan kuliah)")
    ps.add_argument("--token"); ps.add_argument("--port", "-P", type=int, default=8888); ps.set_defaults(fn=cmd_serve)

    a = p.parse_args()
    a.fn(a)

def cmd_dumpimport(args):
    """Scan kk_dump/ for token & credentials from the phone's app data dump."""
    import glob
    dump = args.dir
    if not os.path.isdir(dump):
        sys.exit(f"[!] Folder dump tidak ada: {dump}. Jalankan kampuskita-dump.ps1 dulu.")
    print(f"[*] Scanning {dump} ...")
    found = {}
    for f in sorted(glob.glob(os.path.join(dump, "**", "*"), recursive=True)):
        if not os.path.isfile(f):
            continue
        name = os.path.basename(f)
        try:
            raw = open(f, "rb").read()
        except Exception:
            continue
        # skip SQLite binary but scan for printable strings
        try:
            text = raw.decode("utf-8", "replace")
        except Exception:
            text = ""
        for key in ("token", "EMAIL_PENGGUNA", "DRIVE_EMAIL", "DRIVE_PASS", "password", "id_mhs", "nim", "email"):
            for m in re.finditer(re.escape(key) + r'[^=<>]{0,10}(?:=|>|:)\s*["\']?([^"\'<>\s,;]{6,})', text, re.I):
                val = m.group(1).strip()
                if val and val.lower() not in ("null", "false", "true") and val not in found.get(key, []):
                    found.setdefault(key, []).append(val)
    for k, v in found.items():
        for x in v[:5]:
            print(f"  {k}: {x[:100]}")
    tok = None
    for k in ("token", "TOKEN", "access_token"):
        if found.get(k):
            tok = found[k][0]
            break
    if tok:
        cfg = load_cfg(); cfg["token"] = tok; save_cfg(cfg)
        print(f"[+] Token diimpor: {tok[:50]}...")
        # validate
        st, txt = api_get("/akademik/status-mhs", tok)
        print(f"[*] Cek token -> HTTP {st}: {txt[:150]}")
    else:
        print("[!] Token tidak ditemukan di dump. Periksa isi FlutterSharedPreferences.xml.")
    return 0

def cmd_token(args):
    cfg = load_cfg()
    if args.token:
        tok = args.token
    else:
        tok = cfg.get("token")
    if not tok:
        sys.exit("[!] Tidak ada token. --token <TOKEN> atau login dulu.")
    if args.set:
        cfg["token"] = tok; save_cfg(cfg); print("[+] Token disimpan.")
        return 0
    st, txt = api_get("/akademik/status-mhs", tok)
    print(f"[*] /akademik/status-mhs -> HTTP {st}")
    print(txt[:500])
    if st == 200 and "Token Invalid" not in txt and "Required Parameter" not in txt:
        print("[+] Token VALID.")
    else:
        print("[!] Token ditolak."); return 1
    return 0

if __name__ == "__main__":
    main()
