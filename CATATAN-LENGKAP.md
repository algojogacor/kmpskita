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
| `/kemahasiswaan/presensi-kuliah` | GET | ✅ 8 MK: TM, HADIR, PROSEN |
| `/kemahasiswaan/riwayat-khs` | POST + `semester` | ✅ nilai per MK (SKS, NILAI, NILAI_HURUF) |
| `/kemahasiswaan/pembayaran` | GET | ✅ UKT (bank, nominal, status) |
| `/kemahasiswaan/hist-her` | GET | ✅ |
| `/kemahasiswaan/penyerahan-ktm` | GET | ✅ |
| `/kemahasiswaan/inbox`, `tkm` | GET | ⛔ kosong |

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

## Belum dipecahkan

- `/api/auth/login` apicybercampus (token sistem berbeda; semua varian balas
  "Username / password tidak boleh kosong") → submit presensi belum bisa.
- `unairsatu.unair.ac.id/token/ambil-token-v2` → 500 selalu.
- E-Learning hebat (SSO UNAIR) tidak dibutuhkan — cukup link
  `https://hebat.elearning.unair.ac.id/hebat-v2/`.

## Batasan & Etika

- Semua akses pakai kredensial & token **milik user sendiri** (akun & HP sendiri).
- Data presensi yang ditampilkan adalah data asli dari server. **Memalsukan
  kehadiran (fake 100%) tidak didukung** — bukan teknisnya saja, tapi itu
  kecurangan akademik. Pengganti: badge "● PRESENSI SEKARANG" di wrapper saat jam
  kuliah berlangsung, supaya tidak ada pertemuan yang terlewat.
- Kode berisi kredensial user (token) — jangan commit config.json ke repo publik.
