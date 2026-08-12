# Kampus Kita Lite — Catatan Lengkap (arsip)

> Dokumen pegangan proyek (mirror dari Claude memory). Update jika ada temuan baru.
> Terakhir diperbarui: 2026-08-12. Versi publik — data pribadi diganti
> placeholder `<…>`; isi asli hanya di perangkat pemilik (config.json & memory).

## Profil

- **Nama**: `<nama>` — UNAIR Fakultas Hukum, S1, NIM `<NIM>`
- **Angkatan**: `<tahun>` · kelas: `<kelas>` · `<SKS>` SKS
- **ID internal**: idMhs `<idMhs>` · idPengguna `<idPengguna>` · prodi `<kode>`
- **Email kampus**: `<nama>@student.unair.ac.id`
- **Login app**: email kampus + password (login TIDAK menerima NIM). Password
  tidak disimpan di dokumen ini. Format valid = **email + password PLAINTEXT**
  (bukan sha256, lihat bagian Login).

## File & Lokasi

| Item | Path |
|---|---|
| Client CLI | `kk_lite.py` (root repo ini) |
| Token tersimpan | `~/.kk_lite/config.json` (`%USERPROFILE%\.kk_lite\config.json` di Windows) |
| Web statis (deploy Vercel) | root repo ini (`index.html`; repo `algojogacor/kmpskita`) |
| Proxy login serverless | `api/login.js` (folder `api/` = Vercel functions) |
| Probe scripts (arsip) | `scripts/` di repo ini |
| Panduan teman | `PANDUAN-PENGGUNA.md` |
| adb (untuk dumpphone) | SDK platform-tools (`adb.exe`) |
| Binary app reverse-engineered | dari APK `id.ac.unair.kampuskitamahasiswa` (libapp.so) |

## API — Fakta Terverifikasi

### Login (format TERVERIFIKASI 2026-08-12)
```
POST https://apikampuskita-mahasiswa.unair.ac.id/auth/login
Body (form): email=<email kampus>  password=<password PLAINTEXT>
→ HTTP 200, JWT baru keluar via header Set-Cookie: token=<JWT>; domain=localhost;
  HttpOnly; SameSite=Lax  (body juga berisi profil lengkap + token)
```
- Format **lama** app (`EMAIL_PENGGUNA` + `DRIVE_PASS=sha256(password)`) → **422**
  "Email is required / Password is required". API cuma terima email+password
  plaintext. (Hash sha256 lama tetap ada di HP sebagai `flutter.validPassword`.)
- JWT HS256, payload `{IDMhs, IDPengguna, exp, username}`, berlaku ~1 tahun.
- `domain=localhost` di Set-Cookie = bug config dev server UNAIR + `HttpOnly` →
  browser tidak bisa baca → web butuh proxy serverless (`api/login.js`).
- Refresh token:
  1. `python kk_lite.py login -e <email> -p <password>` — **login penuh dari PC,
     tanpa HP** (butuh jaringan yang tembus: data seluler / USB tethering).
  2. atau `python kk_lite.py dumpphone` (HP USB + app sudah login).

### Autentikasi endpoint
- Header `Authorization: Bearer <JWT>` **wajib** (query `?token=` saja tidak cukup
  untuk endpoint POST).
- `GET /akademik/status-mhs` menerima query `?token=` saja.

### Metode per endpoint
- **POST**: `/akademik/jadwal-kuliah`, `/kemahasiswaan/riwayat-khs` (butuh param
  `semester=<id>` dari `/akademik/semester-khs`)
- **GET**: semua yang lain. kk_lite otomatis retry POST saat dapat 405.

### Peta endpoint (status 2026-08-12)
| Endpoint | Method | Status & isi |
|---|---|---|
| `/akademik/status-mhs` | GET | ✅ NIM, angkatan, jenjang, prodi, status |
| `/akademik/jadwal-kuliah` | POST | ✅ per hari `{"Senin":[...]}`, field JAM "13:00 - 15:00", NM_RUANGAN, NM_DOSEN, NAMA_KELAS |
| `/akademik/semester-khs` | GET | ✅ daftar semester (ID_SEMESTER utk riwayat-khs) |
| `/akademik/kalender-akademik` | GET | ✅ 15 kegiatan (KBM 10 Agu–27 Nov, UTS 28 Sep–9 Okt, UAS 7–18 Des) |
| `/akademik/masa-studi` | GET | ✅ |
| `/akademik/sks-aktif` | GET | ✅ SKS_TEMPUH, JUM_MK |
| `/akademik/dosen-wali` | GET | ✅ |
| `/akademik/peserta-mata-kuliah` | GET | ✅ 10 MK |
| `/akademik/ipk` | GET | ⛔ bug server (IPK_MHS NULL → 500), bukan salah client |
| `/akademik/ips`, `sks-lulus`, `skor-skp`, `tes-elpt` | GET | ⛔ data belum ada (angkatan baru) |
| `/akademik/elpt-maba` | GET | ✅ **BARU** skor ELPT maba (LISTENING/READING/STRUCTURE/SCORE) |
| `/akademik/pedoman-prosedur` | POST | ✅ **BARU** dokumen PP kemahasiswaan (KODE_DOKUMEN, NAMA_FILE) |
| `/akademik/prosen-nilai-D`, `training-elpt` | GET | ⛔ kosong (ada di binary app) |
| `/kemahasiswaan/presensi-kuliah` | GET | ✅ 8 MK: TM, HADIR, PROSEN, ID_PENGAMBILAN_MK |
| `/kemahasiswaan/presensi-kuliah-detail/{id}` | GET | ⛔ ada di binary, format path param, data kosong utk ID dites |
| `/kemahasiswaan/riwayat-khs` | POST + `semester` | ✅ nilai per MK (SKS, NILAI, NILAI_HURUF) |
| `/kemahasiswaan/pembayaran` | GET | ✅ UKT (bank, nominal, status) |
| `/kemahasiswaan/hist-her` | GET | ✅ |
| `/kemahasiswaan/penyerahan-ktm` | GET | ✅ |
| `/kemahasiswaan/inbox`, `tkm`, `khp/` | GET | ⛔ kosong / 404 |
| `/kemahasiswaan/update-status-*` (inbox) | POST? | ⚠️ ada di binary, method GET → 405, TIDAK dicoba (mutasi) |
| `/auth/profile` | GET | ✅ **BARU** profil lengkap termasuk ALAMAT_MHS (PII berlebih, lihat Temuan) |
| `/auth/one-drive`, `/auth/reset-password` | POST | ⚠️ **reset-password = TEMUAN KRITIS, lihat bagian Temuan Keamanan** |

### CORS (penting untuk web statis)
- API **meng-echo origin mana pun** (`Access-Control-Allow-Origin: <origin>`) +
  `Access-Control-Allow-Headers: authorization` + `Allow-Methods: GET,POST,...`
- Artinya **browser bisa fetch langsung** ke API dari halaman web mana pun
  (PWA di Vercel / GitHub Pages jalan tanpa proxy).
- Bukti: IP datacenter (AWS) menerima 401 (bukan timeout) → IP Vercel/AWS tidak
  diblokir; yang diblokir hanya IP rumah tertentu (TCP timeout), OK dari seluler.

### Jaringan
- Server `210.57.208.253` memblokir IP rumah/PC (TCP timeout), **OK dari data
  seluler** dan IP datacenter. WiFi kampus = OK (belum dites, asumsi).
- Solusi harian: USB tethering HP (sudah dipakai user).
- Dengan PWA statis: browser HP di jaringan seluler fetch langsung — **laptop
  tidak perlu nyala**.

## Komponen

1. **kk_lite.py** — CLI + server lokal (`serve`, port 8888, bind 0.0.0.0, wrapper
   tab Hari Ini/Minggu Ini/Presensi/Nilai/Status/E-Learning).
2. **PWA statis (root repo, deploy Vercel)** — `index.html` fetch langsung ke API
   (CORS terbuka), token di localStorage HP. Ikon home screen via "Add to Home
   screen". Setup view punya **form login email+password** → POST `api/login.js`
   (Vercel serverless proxy baca JWT dari Set-Cookie, stateless) + fallback paste
   token untuk host tanpa serverless.
3. **api/login.js** — proxy login serverless (Vercel). Browser tidak bisa baca
   Set-Cookie UNAIR (HttpOnly + domain=localhost), jadi fungsi ini forward login,
   ambil JWT dari Set-Cookie, kembalikan ke browser. Tanpa state, tanpa simpan
   apa pun.
4. **CATATAN-LENGKAP.md** — dokumen ini.

## Status verifikasi web statis (2026-08-12)

- PWA statis (index.html di root repo) **terbukti end-to-end**: host di PC →
  buka dari browser HP via adb → fetch langsung ke API (CORS lolos) → jadwal
  tampil di HP.
- IP datacenter (AWS/Vercel) **diterima** server (dapat 401, bukan timeout) →
  deploy Vercel layak. WiFi rumah diblokir; seluler OK; VPN ke luar negeri juga
  tembus (IP datacenter diterima).

## Temuan Keamanan (2026-08-12) — semuanya dari posisi "akun sendiri"

### 🔴 KRITIS — `/auth/reset-password` tanpa verifikasi password lama + tanpa validasi input
```
POST /auth/reset-password   (header: Authorization: Bearer <JWT>)
```
- Body `{password: <baru>}` → **mengganti password TANPA perlu password lama**
  (server tidak memverifikasi old password sama sekali).
- Body **kosong** → tetap `200 "Berhasil ganti password"` dan password diubah ke
  nilai kosong/null → **akun terkunci** (login asli 401; login kosong 422).
- Dampak: siapa pun yang memegang token valid akun korban (bocor token,
  perangkat bersama, XSS di mana pun token disimpan) bisa **mengambil alih
  akun** dan **mengunci pemiliknya**. Tanpa token, endpoint 401 "You are not
  logged in" (jadi tidak bisa dipakai tanpa sesi).
- **Teruji nyata pada akun sendiri 2026-08-12**: password asli sempat tidak
  bisa login, lalu **dipulihkan** via endpoint yang sama `{password: <asli>}`
  + verifikasi login berhasil. Tidak ada data lain yang tersentuh.
- Saran perbaikan (untuk laporan): wajib verifikasi password lama,
  validasi `password` tidak boleh kosong, rate-limit.

### 🟡 MINOR — temuan lain
- `/auth/profile` mengembalikan PII berlebih (alamat rumah lengkap) — lebih
  banyak dari yang dibutuhkan status-mhs.
- CORS echo origin apa pun **+** `Access-Control-Allow-Credentials: true`
  (kombinasi berisiko jika auth cookie pernah dipakai; saat ini token Bearer
  di storage, tidak eksploitatif langsung).
- `Server: nginx/1.22.1` (versi 2022 ter-expose).
- Binary app berisi URL **`http://210.57.208.213:9092`** (HTTP plaintext, IP
  lama/dev) dan `https://cybercampus.unair.ac.id/foto_mhs/<NIM>.JPG` tanpa
  autentikasi (foto mahasiswa publik via NIM).

### ✅ Diuji & aman
- JWT `alg:none` (tanpa signature) → **ditolak 401** (verifikasi signature jalan).
- TLS 1.3, cipher kuat (TLS_AES_256_GCM_SHA384), sertifikat Sectigo valid.
- HSTS (1 thn + includeSubDomains), X-Frame-Options SAMEORIGIN, nosniff, CSP.
- Binary `libapp.so`: **tidak ada** API key Google/Firebase/private key/JWT
  hardcoded (higienis).

### Kontak resmi (dari binary app, untuk responsible disclosure)
- `direktorat@ditsi.unair.ac.id` · Telegram resmi: `t.me/ULT_UNAIR`

## HE-BAT (e-Learning UNAIR) — Moodle (terverifikasi 2026-08-12)

### Jalur token webservice: MATI untuk mahasiswa (diteliti tuntas)
- Web service REST **AKTIF** (`webservice/rest/server.php` balas `invalidtoken`),
  CORS `*` di token.php + webservice.
- **`login/token.php` MENOLAK password yang sama yang diterima form web**
  (NIM maupun email) → "Invalid login". Konfirmasi: web login = form Moodle
  standar yang diterima untuk **NIM + password** (username = NIM; email juga
  diterima), tetapi token.php memakai jalur auth yang berbeda (plugin SSO
  kustom UNAIR tidak meneruskan verifikasi ke token.php).
- **Preferences → Security keys** (`user/managetoken.php`): halaman KOSONG,
  menu tidak ada di Preferences → pembuatan token oleh user **dimatikan admin**
  (capability `moodle/webservice:createtoken` dicabut). `?action=create` juga
  tidak merender form.
- Kesimpulan: **token webservice untuk akun mahasiswa tidak bisa dibuat** di
  HEBAT. jangan dibuang waktu — pakai jalur iCal di bawah.

### Jalur yang DIPAKAI: iCal authtoken (tanpa login, tanpa token webservice)
- `GET /calendar/export_execute.php?userid=<id>&authtoken=<kunci>&preset_what=all&preset_time=custom&starttime=<unix>&endtime=<unix>`
- Authtoken didapat dari UI: login web → **Calendar → Import or export
  calendars → Get calendar URL** → URL berisi `userid` + `authtoken`.
- **Bisa diakses TANPA sesi login** (diverifikasi dari PC tanpa cookie, HTTP 200).
  Range `custom` menerima `starttime`/`endtime` unix → satu semester penuh.
- Isi: event `SUMMARY` = "… is due" (deadline tugas), `CATEGORIES` = nama
  kursus penuh (folded line, perlu digabung), `DTSTART` = UTC.
- **TIDAK ada header CORS** di export_execute.php (beda dari webservice) →
  browser diblokir → butuh proxy serverless `api/moodle-cal.js` (Vercel,
  stateless, fetch server-side + parse → JSON).
- Di web: tab **📋 Tugas** pakai `localStorage['kk_moodle_cal']` (URL kalender
  yang ditempel user) → render deadline: LEWAT / SEBENTAR / H-x.
- **Detail tugas**: halaman tugas HEBAT memang tanpa deskripsi, TAPI **halaman
  KURSUS** (`course/view.php?id=<courseid>`) memuatnya: section summary berisi
  instruksi penugasan lengkap (ketentuan, pertanyaan, deadline) + semua
  aktivitas (materi URL/file, tugas). Contoh: Assessment HAM = section
  "11 Agustus 2026: Assessment HAM" di course 16332 memuat instruksi
  self-study lengkap (5 pertanyaan, ketentuan pengumpulan); PIH (16319) tidak
  punya summary; PHI (16495) punya info perkuliahan gabungan.
- **`hebat-links.json` v2** (generated oleh `scripts/sync-hebat.mjs`):
  - `courses[]`: `{id, period, code, name, class, url, sections[]}`; tiap
    section = `{name, summary (isi penugasan, paragraf dosen dipertahankan),
    activities: [{mod, href, name}]}`. Course-global, bukan data pribadi —
    status kumpul/file milik user TIDAK masuk repo publik. Catatan: summary
    adalah konten dosen — keputusan user agar tampil di web.
  - `tasks[]`: index `{name, url, courseId}` utk mencocokkan feed iCal.
  - Crawl: daftar kursus via **AJAX Moodle**
    (`lib/ajax/service.php?sesskey=…&info=core_course_get_enrolled_courses_by_timeline_classification`
    — method yang dipakai /my/courses.php sendiri; /my/courses.php me-render
    kartu kursus secara LAZY, tab background tak pernah memuat kartunya;
    `core_course_get_contents` tidak diaktifkan di HEBAT → section & summary
    di-scrape dari DOM halaman kursus (server-rendered:
    `li.section.course-section > .section-item`; buang elemen UI: tombol
    Collapse/Expand, select, `.bulkselect`, label "Select section …").
  - Di web: kartu tugas punya **📄 buka tugas**, **🏛 buka kursus**, dan
    **📝 isi penugasan / info** (details — summary section kursus).
  - Refresh: `node scripts/sync-hebat.mjs` (WebBridge, butuh Chrome login
    HE-BAT) lalu push. Personal check (status kumpul/file): halaman tugas
    `mod/assign/view.php?id=<cmid>` pakai sesi sendiri.
- Temuan minor: error webservice bocor **stacktrace path server**
  (`/public/lib/...`) + `reproductionlink` — info disclosure kecil.

## Belum dipecahkan

- `/api/auth/login` apicybercampus (token sistem berbeda; semua varian balas
  "Username / password tidak boleh kosong") → submit presensi belum bisa.
- `unairsatu.unair.ac.id/token/ambil-token-v2` → 500 selalu.
- `hebat-v2` (`/hebat-v2/`) ternyata **landing page marketing** saja — tidak ada
  API sendiri, jangan dijadikan jalur.

## Batasan & Etika

- Semua akses pakai kredensial & token **milik user sendiri** (akun & HP sendiri).
- Data presensi yang ditampilkan adalah data asli dari server. **Memalsukan
  kehadiran (fake 100%) tidak didukung** — bukan teknisnya saja, tapi itu
  kecurangan akademik. Pengganti: badge "● PRESENSI SEKARANG" di wrapper saat jam
  kuliah berlangsung, supaya tidak ada pertemuan yang terlewat.
- Kode berisi kredensial user (token) — jangan commit config.json ke repo publik.
