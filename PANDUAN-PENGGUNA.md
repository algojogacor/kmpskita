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

Di tiap tugas ada tombol **📄 buka tugas** → langsung ke halaman tugas di
HE-BAT (di sana ada status kumpul, file, dan tempat mengumpulkan). Tombol ini
hanya muncul untuk tugas yang sudah terdaftar di `hebat-links.json`; kalau ada
tugas baru yang belum ada tombolnya, beri tahu pemilik repo untuk sync.

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
