# 📚 KK Lite — Panduan Pengguna (untuk teman)

Web ringan untuk lihat **jadwal kuliah, presensi, nilai (KHS), status mahasiswa,
UKT, dan link e-learning** — tanpa aplikasi "Kampus Kita Mahasiswa" yang lemot.
Ini **bukan app resmi UNAIR** — hanya "jendela" ke data akun kamu sendiri.

## Mulai (1 menit)

1. Buka **https://kmpskita.vercel.app** di browser HP atau PC.
2. Klik **Masuk** → isi **email kampus** (`nama@student.unair.ac.id`) dan
   **password** kamu (sama dengan login app Kampus Kita).
3. Selesai — jadwal hari ini langsung muncul. Token tersimpan otomatis di
   perangkat itu (tidak dikirim ke server mana pun selain ke UNAIR).

> ⚠️ **Login pertama harus dari jaringan yang dibolehkan server UNAIR:**
> pakai **data seluler** atau **WiFi kampus**. WiFi rumah/indihome sering
> diblokir. Setelah login pertama, token berlaku ~1 tahun — baru perlu login
> lagi kalau token kedaluwarsa.

## Jadikan "app" di HP (opsional)

- Chrome HP → buka menu ⋮ → **Add to Home screen** → muncul ikon di layar utama.
- Setelah itu buka dari ikon itu, seperti app biasa. Bisa jalan meski laptop
  yang menghosting web ini mati.

## Isi halaman

| Tab | Isi |
|---|---|
| 🗓 Hari Ini | Jadwal kuliah hari ini + badge **● PRESENSI SEKARANG** saat jam kuliah aktif |
| 📅 Minggu Ini | Jadwal seminggu penuh |
| ✅ Presensi | Kehadiran per mata kuliah (hadir/total + persen) — data asli dari server |
| 📖 Nilai | KHS semester terbaru (SKS, nilai angka & huruf) |
| 🎓 Status | Profil mahasiswa, SKS aktif, pembayaran UKT, kalender akademik |
| 📋 Tugas | Deadline tugas dari HE-BAT (e-learning) — badge **LEWAT** (merah), **SEBENTAR** (kuning), atau H-x hari |
| 💻 E-Learning | Link ke HE-BAT (e-learning UNAIR) |

### Tab 📋 Tugas — siapkan sekali (1 menit)

HEBAT tidak menyediakan token aplikasi, tapi memberi **URL kalender pribadi**
yang bisa dibaca web ini:

1. Buka **hebat.elearning.unair.ac.id** → login (NIM + password).
2. Buka **Calendar → Import or export calendars**.
3. Klik **Get calendar URL** → salin URL yang muncul.
4. Kembali ke web ini, tab **📋 Tugas** → tempel URL → **Simpan Kalender HE-BAT**.

Selesai — deadline tugas muncul tanpa perlu login HE-BAT lagi. URL kalender
itu berisi kunci khusus akunmu, jadi jangan dibagikan ke orang lain.

Di tiap tugas ada:
- **📄 buka tugas** → halaman tugas di HE-BAT (status kumpul, file, tempat
  mengumpulkan).
- **🏛 buka kursus** → halaman kursus (materi + semua aktivitas).
- **📝 isi penugasan / info** → ketuk untuk membuka detail instruksi
  penugasannya (diambil dari halaman kursus) — tampil untuk tugas yang
  dosennya menuliskan instruksi di kursus.

Tombol & detail ini muncul untuk data yang sudah terdaftar di
`hebat-links.json` (milik pemilik repo). Web ini memilih file **per-user**
(`hebat-links-<userid>.json`, userid dari URL kalender) kalau ada — jadi
mahasiswa fakultas/kelas lain juga dapat tombol yang benar, tanpa perlu
pemilik repo.

## Buat tombolmu sendiri (untuk fakultas/kelas lain, tanpa install)

Kalau kartu tugasmu belum ada tombolnya, tab **📋 Tugas** menampilkan
bagian **"✨ belum ada tombol tugas? buat datamu sendiri"**:

1. Buka **hebat.elearning.unair.ac.id** di tab baru (login HE-BAT kamu).
   Tekan **F12** → tab **Console** (kalau muncul peringatan, ketik
   `allow pasting` lalu Enter).
2. Salin kode dari web ini (tombol **📋 salin kode**) → tempel di Console →
   Enter. File `hebat-links-<userid>.json` terunduh.
3. Seret file itu ke kotak **"seret file ke sini"** di web ini.

Data dibuat **di browser kamu** (sesi login kamu) — tidak ada password yang
melewati web ini. Setelah terkirim, tombol muncul ±1 menit kemudian (muat
ulang halamannya). Semua URL divalidasi hanya `hebat.elearning.unair.ac.id`.

## Kalau ada masalah

- **"Gagal: HTTP 0" / timeout** → jaringan kamu diblokir server (WiFi rumah).
  Ganti ke data seluler / WiFi kampus.
- **Login gagal "email dan password wajib"** → pastikan email pakai
  `@student.unair.ac.id` dan password sesuai akun Kampus Kita.
- **Mau ganti akun** → ketuk tombol ⏻ di pojok kanan atas, lalu login ulang.
- **Jadwal/presensi kosong** → wajar kalau belum ada data semester itu.

## Privasi & keamanan

- Semua data = **akun kamu sendiri** (kredensial & token milikmu).
- Token cuma disimpan di perangkatmu (`localStorage`). Halaman ini tidak punya
  database; tombol login hanya meneruskan ke server resmi UNAIR.
- Jangan bagikan email+password atau token ke siapa pun. Kalau ada teman yang
  mau pakai, cukup kasih link web ini — dia login dengan akunnya sendiri.

---

*Untuk teknis (CLI, API, arsip penemuan): baca [CATATAN-LENGKAP.md](CATATAN-LENGKAP.md).*
