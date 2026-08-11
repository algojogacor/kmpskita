# Kampus Kita Lite — Catatan Lengkap

> Dokumen pegangan proyek (mirror dari Claude memory). Update jika ada temuan baru.
> Terakhir diperbarui: 2026-08-12.

## Profil

- **Nama**: Arya Rizky Ardhi Pratama — UNAIR Fakultas Hukum, S1, NIM 626103051310
- **Angkatan**: 2026 · kelas: A-2 / C-2 / PDB93 · 20 SKS (Ganjil 2026/2027)
- **ID internal**: idMhs 265756 · idPengguna 487101 · prodi 51 (Ilmu Hukum)
- **Email kampus**: arya.rizky.ardhi.fh-2026@student.unair.ac.id
- **Login app**: email + password (login TIDAK menerima NIM). Password tidak
  disimpan di dokumen ini — hash sha256 ada sebagai `flutter.validPassword` di HP
  (lihat `dumpphone`).

## File & Lokasi

| Item | Path |
|---|---|
| Client CLI | `D:\Projects\kampuskita-lite\kk_lite.py` |
| Token tersimpan | `C:\Users\Arya Rizky\.kk_lite\config.json` |
| Web statis (deploy Vercel) | `D:\Projects\kampuskita-lite\web\` |
| APK debug (untuk dumpphone) | `D:\Projects\kampuskita-standalone-aligned-signed.apk` |
| adb | `D:\Projects\platform-tools\adb.exe` |
| Binary reverse-engineered | `D:\Projects\kampuskita-split-arm64\lib\arm64-v8a\libapp.so` |
| Claude memory | `C:\Users\Arya Rizky\.claude\projects\D--\memory\` (user-arya-rizky, project-kampuskita-kklite, feedback-kampuskita-network) |

## API — Fakta Terverifikasi

### Login
```
POST https://apikampuskita-mahasiswa.unair.ac.id/auth/login
Body (form): EMAIL_PENGGUNA=<email kampus>  DRIVE_PASS=sha256(<password>)
→ JSON berisi JWT HS256, payload {IDMhs, IDPengguna, exp, username}
```
JWT berlaku ~1 tahun (exp Jan 2027). Cara refresh:
1. HP terhubung USB (adb) + app sudah login → `python kk_lite.py dumpphone`
2. atau `python kk_lite.py login -e <email> -p <password>` (butuh jaringan yang tembus)

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
2. **web/ (PWA statis)** — untuk Vercel: fetch langsung ke API, token di
   localStorage HP. Ikon home screen via "Add to Home screen".
3. **CATATAN-LENGKAP.md** — dokumen ini.

## Status verifikasi web statis (2026-08-12)

- `web/` (PWA statis) **terbukti end-to-end**: host di PC → buka dari browser HP
  via adb → fetch langsung ke API (CORS lolos) → jadwal tampil di HP.
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
