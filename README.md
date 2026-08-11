# kk_lite — Kampus Kita Mahasiswa (ringan)

Akses data akademik UNAIR **tanpa aplikasi Flutter yang berat**.
Hasil reverse-engineering dari `id.ac.unair.kampuskitamahasiswa` v2.1.2
(string literals di `libapp.so` + verifikasi dari dump HP).

Repo ini **bukan cuma web deploy** — ini arsip lengkap proyek (guidebook):
CLI, web PWA, proxy login, probe scripts, dan catatan temuan. Kalau isi laptop
hilang, semua yang dibutuhkan untuk mereproduksi ada di sini.

- **Pemakai non-teknis (teman)**: baca [PANDUAN-PENGGUNA.md](PANDUAN-PENGGUNA.md)
  — cukup buka web → login email+password.
- **Dokumen teknis & arsip temuan**: [CATATAN-LENGKAP.md](CATATAN-LENGKAP.md).
- Python 3.8+ — **stdlib only** (urllib, json, hashlib, base64). Tanpa pip install.

## Cara pakai

### Jalur 1 — Impor token dari HP (paling gampang, disarankan)
HP terhubung USB (USB debugging aktif), app sudah login.
```
python kk_lite.py dumpphone
```
→ Menarik `flutter.token` (JWT) + profil langsung dari HP via `adb run-as`,
menyimpannya ke `%USERPROFILE%\.kk_lite\config.json`. Tanpa install APK apapun.

### Jalur 2 — Login langsung via API (tanpa HP!)
```
python kk_lite.py login -e "email@student.unair.ac.id" -p "password"
```
Format login **terverifikasi** (2026-08-12) — **email + password plaintext**:
```
POST https://apikampuskita-mahasiswa.unair.ac.id/auth/login
email=<email kampus>
password=<password>
```
→ HTTP 200; JWT (HS256) keluar via header `Set-Cookie: token=…`, payload
`{IDMhs, IDPengguna, exp, username}`. JWT berlaku lama (exp ~Jan 2027).
Catatan: format lama `EMAIL_PENGGUNA` + `DRIVE_PASS=sha256(...)` **ditolak API**
(422) — hash sha256 hanya tersisa sebagai `flutter.validPassword` di HP.

### ⚠️ Jaringan
Server apikampuskita (`210.57.208.253`) **memblokir IP rumah/PC** (TCP timeout),
tapi **OK dari data seluler / WiFi kampus**. Solusi:
- **USB tethering** dari HP (biar PC ikut lewat data seluler), atau
- jalankan kk_lite saat di WiFi kampus.

Kalau `kk_lite` print `HTTP 0` / timeout, itu berarti PC masih di jaringan
yang diblokir — bukan token yang salah.

## Perintah

| Perintah | Fungsi |
|---|---|
| `dumpphone` | Tarik token JWT langsung dari HP via adb (HP login dulu) |
| `jadwal -t` | Jadwal kuliah **hari ini** (penanda kapan kuliah) |
| `jadwal` | Semua jadwal kuliah (per hari) |
| `presensi` | Presensi semester ini: hadir/total + persen per MK |
| `nilai` | KHS nilai per MK (semester terbaru otomatis, `--semester <id>`) |
| `status` | Status mahasiswa (profil + SKS aktif) |
| `khs` | Daftar semester KHS |
| `kalender` | Kalender akademik (UTS, UAS, KBM, KRS…) |
| `masa-studi` / `sks-aktif` | Masa studi & SKS |
| `dosen-wali` / `peserta-mk` | Dosen wali, peserta MK |
| `pembayaran` | Riwayat pembayaran UKT |
| `hist-her` / `penyerahan-ktm` | HER registrasi, KTM |
| `serve -P 8888` | **Wrapper web (PWA)**: tab Hari Ini / Minggu Ini / Presensi / Nilai / Status / E-Learning. Buka di PC atau HP (jaringan sama). Di HP: *Add to Home screen* = jadi app |
| `token --token XXX --set` | Simpan token manual |
| `token` | Tes token tersimpan |

## Endpoint (hasil verifikasi 2026-08-12, token JWT app)

Semua pakai `Authorization: Bearer <JWT>` (+ `?token=` query). Status:
✅ = hidup & data nyata, ⛔ = belum ada data untuk angkatan ini.

| Endpoint | Method | Status |
|---|---|---|
| `/akademik/status-mhs` | GET | ✅ NIM, angkatan, jenjang, prodi, status |
| `/akademik/jadwal-kuliah` | **POST** | ✅ jadwal per hari (JAM "13:00 - 15:00", ruang, dosen, kelas) |
| `/akademik/semester-khs` | GET | ✅ daftar semester (id untuk riwayat-khs) |
| `/akademik/kalender-akademik` | GET | ✅ 15 kegiatan (KBM 10 Agu–27 Nov, UTS 28 Sep–9 Okt, UAS 7–18 Des) |
| `/akademik/masa-studi` | GET | ✅ |
| `/akademik/sks-aktif` | GET | ✅ SKS tempuh + jumlah MK |
| `/akademik/dosen-wali` | GET | ✅ |
| `/akademik/peserta-mata-kuliah` | GET | ✅ 10 MK (kuota, kelas, ruang, hari) |
| `/akademik/ipk` | GET | ⛔ bug server: IPK_MHS NULL → 500 |
| `/akademik/ips`, `sks-lulus`, `skor-skp`, `tes-elpt` | GET | ⛔ data belum ada → 404 |
| `/kemahasiswaan/presensi-kuliah` | GET | ✅ 8 MK: TM, HADIR, PROSEN per MK |
| `/kemahasiswaan/riwayat-khs` | **POST** `semester=<id>` | ✅ nilai per MK (SKS, NILAI, NILAI_HURUF) |
| `/kemahasiswaan/pembayaran` | GET | ✅ UKT (bank, nominal, status bayar) |
| `/kemahasiswaan/hist-her` | GET | ✅ HER registrasi |
| `/kemahasiswaan/penyerahan-ktm` | GET | ✅ |
| `/kemahasiswaan/inbox`, `tkm` | GET | ⛔ kosong |

Catatan:
- `jadwal-kuliah` & `riwayat-khs` = **POST**; yang lain GET (kk_lite otomatis
  retry POST kalau dapat HTTP 405).
- `unairsatu.unair.ac.id/token/ambil-token[-v2]` — SSO (masih 500, tidak dipakai).
- `apicybercampus.unair.ac.id/api/mahasiswa/presensi` — submit presensi (token
  sistem berbeda — JWT app tidak berlaku di sini; belum dipecahkan).
- Foto: `https://uacc.unair.ac.id/foto/mahasiswa-apps?nim=...`

## Wrapper web (pengganti app asli)

`python kk_lite.py serve` → server lokal (bind 0.0.0.0, port 8888):
- **PC**: http://127.0.0.1:8888
- **HP** (satu jaringan: tethering/hotspot): http://<IP-PC>:8888 — lalu di Chrome
  buka menu → *Add to Home screen* → muncul ikon app "KK Lite" di HP.
- Fitur: Hari Ini (badge **● PRESENSI SEKARANG** saat jam kuliah aktif),
  Minggu Ini, Presensi (bar % kehadiran), Nilai per MK, Status (profil + UKT +
  kalender akademik), dan tab E-Learning berisi link
  **https://hebat.elearning.unair.ac.id/hebat-v2/**.

Token tidak pernah masuk browser — semua request diteruskan server.
Catatan: kk_lite harus jalan dari jaringan yang bisa tembus API (tethering/WiFi kampus).

## Versi web statis (deploy Vercel — laptop bisa mati)

Repo root = PWA statis (index.html + manifest + sw di akar repo). **Browser fetch
langsung ke API UNAIR** — CORS server terbuka (echo origin + izinkan
`authorization`), terbukti end-to-end dari browser HP (tes 2026-08-12). Jadi:

- Vercel/GitHub Pages hanya menyajikan file statis — **tidak butuh server**.
- HP mengakses API dari jaringannya sendiri → pakai **data seluler / WiFi kampus**
  (WiFi rumah diblokir server, seluler & IP datacenter diterima — VPN juga jalan).
- **Login di web cukup email + password kampus** — form login memanggil
  `api/login.js` (Vercel serverless, stateless) yang meneruskan ke API UNAIR dan
  membaca JWT dari Set-Cookie (browser tidak bisa baca karena HttpOnly).
  Alternatif tetap ada: paste token manual (untuk host tanpa serverless, atau
  `?t=<token>`).
- Install: buka di Chrome → menu → *Add to Home screen*.

Deploy Vercel:
```
npx vercel          # pertama kali: vercel login (browser), lalu deploy
npx vercel --prod   # update ke produksi
```
Atau via dashboard: import repo GitHub → **Root Directory kosong (root repo)**
→ Deploy. Kalau halaman 404, itu tandanya Root Directory masih `web` — kosongkan.
Tanpa Vercel juga bisa: upload isi repo (index.html dkk) ke GitHub Pages /
Netlify Drop — sama saja.

## Struktur repo (arsip)

```
index.html, manifest.json, sw.js, vercel.json  → PWA web (deploy Vercel)
api/login.js                                    → proxy login serverless (Vercel)
kk_lite.py                                      → CLI + server lokal (serve)
scripts/                                        → probe scripts (arsip temuan API)
PANDUAN-PENGGUNA.md                             → panduan non-teknis untuk teman
CATATAN-LENGKAP.md                              → catatan teknis lengkap (guidebook)
```

## Catatan

- Token tersimpan di `%USERPROFILE%\.kk_lite\config.json` (token = milik user sendiri,
  diambil dari HP sendiri).
- Submit presensi butuh token apicybercampus (sistem berbeda, belum dipecahkan).
  Data presensi yang TAMPAK di app & wrapper adalah data asli dari server —
  bukan hasil manipulasi.

## Etika & legal

- **Bukan app resmi UNAIR.** Semua akses memakai kredensial & token akun **sendiri**
  (login resmi ke server resmi) — tidak ada akses ke data orang lain.
- Jangan commit `config.json` / token / password ke repo publik (sudah di `.gitignore`).
- Jangan bagikan APK hasil modifikasi/re-sign ke publik (distribusi app UNAIR
  bukan kewenangan kita) — dokumentasi cara mendapatkannya saja.
- Data yang ditampilkan adalah data asli server; **memalsukan kehadiran (fake
  100%) tidak didukung** — itu kecurangan akademik.
