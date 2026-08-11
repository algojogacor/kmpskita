// KK Lite — proxy login (Vercel serverless).
// Browser tidak bisa baca Set-Cookie UNAIR (HttpOnly + domain=localhost),
// jadi fungsi ini forward login ke API UNAIR, ambil JWT dari Set-Cookie,
// lalu kembalikan ke browser untuk disimpan di localStorage.
// Tidak ada data disimpan — stateless proxy.
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'POST only' });
    return;
  }
  const { email, password } = req.body || {};
  if (!email || !password) {
    res.status(400).json({ error: 'email dan password wajib' });
    return;
  }
  const UNAIR = 'https://apikampuskita-mahasiswa.unair.ac.id/auth/login';
  try {
    const r = await fetch(UNAIR, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Dart/3.3 (dart:io)',
      },
      body: new URLSearchParams({ email, password }),
      redirect: 'manual',
    });
    const body = await r.text();
    const setCookie = r.headers.get('set-cookie') || '';
    const m = setCookie.match(/token=([^;]+)/);
    if (m) {
      res.status(200).json({ token: m[1], name: 'ok' });
      return;
    }
    let msg = 'login gagal (HTTP ' + r.status + ')';
    try {
      const j = JSON.parse(body);
      if (j && j.message) msg = j.message;
    } catch (e) { /* body bukan json */ }
    res.status(401).json({ error: msg });
  } catch (e) {
    res.status(502).json({ error: 'gagal hubungi server UNAIR: ' + e.message });
  }
}
