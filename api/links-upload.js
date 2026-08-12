// Vercel serverless: terima file data tombol dari browser mahasiswa lain,
// validasi ketat, lalu auto-commit ke repo publik via GitHub Contents API.
// Stateless: token dari env GITHUB_TOKEN. Kredensial HE-BAT TIDAK PERNAH
// lewat endpoint ini — file dihasilkan di browser pemilik akun (generator-hebat.js).
// Keamanan: hanya hebat-links-<userid>.json (file utama tak tersentuh), semua
// URL wajib hebat.elearning.unair.ac.id (anti phishing), whitelist skema,
// batas ukuran, rate limit per IP & per userid.
const OWNER = 'algojogacor';
const REPO = 'kmpskita';
const reId = /^\d{4,12}$/;
const reHref = /^https:\/\/hebat\.elearning\.unair\.ac\.id\//;
const reCourseUrl = /^https:\/\/hebat\.elearning\.unair\.ac\.id\/course\/view\.php\?id=\d+$/;
const MAX_BODY = 512 * 1024;

const rate = new Map(); // key -> [timestamp] (in-memory per instance, cukup utk skala ini)
function rl(key, limit, windowMs) {
  const now = Date.now();
  const arr = (rate.get(key) || []).filter(t => now - t < windowMs);
  if (arr.length >= limit) return false;
  arr.push(now);
  rate.set(key, arr);
  return true;
}

// Whitelist: bangun ulang struktur murni dari kode ini; kembalikan {out} atau {error}.
function sanitize(data) {
  if (!data || typeof data !== 'object') return { error: 'bukan objek JSON' };
  const s = x => (typeof x === 'string' && x.length <= 500 ? x : null);
  if (!Array.isArray(data.courses) || data.courses.length > 60) return { error: 'courses harus array ≤ 60' };
  if (!Array.isArray(data.tasks) || data.tasks.length > 100) return { error: 'tasks harus array ≤ 100' };
  const out = { generated: new Date().toISOString().slice(0, 10), note: s(data.note) || '', courses: [], tasks: [] };
  for (const c of data.courses) {
    if (!c || typeof c !== 'object' || typeof c.id !== 'number') return { error: 'kursus: id harus angka' };
    const name = s(c.name);
    const url = typeof c.url === 'string' && reCourseUrl.test(c.url) ? c.url : null;
    if (name === null || url === null) return { error: 'kursus: nama/url tidak valid (url harus halaman kursus HEBAT)' };
    if (!Array.isArray(c.sections) || c.sections.length > 60) return { error: 'sections harus array ≤ 60' };
    const sections = [];
    for (const sec of c.sections) {
      if (!sec || typeof sec !== 'object') return { error: 'section bukan objek' };
      const secName = s(sec.name) || '';
      const summary = typeof sec.summary === 'string' && sec.summary.length <= 20000 ? sec.summary : null;
      if (summary === null) return { error: 'summary terlalu panjang (> 20000)' };
      if (!Array.isArray(sec.activities) || sec.activities.length > 60) return { error: 'activities harus array ≤ 60' };
      const acts = [];
      for (const a of sec.activities) {
        if (!a || typeof a !== 'object') return { error: 'aktivitas bukan objek' };
        const href = typeof a.href === 'string' && reHref.test(a.href) ? a.href : null; // HANYA URL HEBAT
        if (href === null) return { error: 'aktivitas: url bukan hebat.elearning.unair.ac.id' };
        const mod = typeof a.mod === 'string' && a.mod.length <= 30 ? a.mod : '';
        const an = typeof a.name === 'string' && a.name.length <= 300 ? a.name : '';
        acts.push({ mod, href, name: an });
      }
      sections.push({ name: secName, summary, activities: acts });
    }
    out.courses.push({ id: c.id, period: s(c.period) || '', code: s(c.code) || '', name, class: s(c.class) || '', url, sections });
  }
  for (const t of data.tasks) {
    if (!t || typeof t !== 'object') return { error: 'tugas bukan objek' };
    const name = s(t.name);
    const url = typeof t.url === 'string' && reHref.test(t.url) ? t.url : null;
    if (name === null || url === null) return { error: 'tugas: nama/url tidak valid (url harus HEBAT)' };
    out.tasks.push({ name, url, courseId: typeof t.courseId === 'number' ? t.courseId : 0 });
  }
  return { out };
}

export default async function handler(req, res) {
  if (req.method !== 'POST') { res.status(405).json({ error: 'POST saja' }); return; }
  const ip = (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || '?';
  if (!rl('ip:' + ip, 5, 10 * 60 * 1000)) { res.status(429).json({ error: 'terlalu sering — coba lagi 10 menit lagi' }); return; }
  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch { body = null; } }
  if (!body || typeof body !== 'object') { res.status(400).json({ error: 'body JSON wajib' }); return; }
  if (JSON.stringify(body).length > MAX_BODY) { res.status(413).json({ error: 'file terlalu besar (maks 512 KB)' }); return; }
  const userid = String(body.userid || '');
  if (!reId.test(userid)) { res.status(400).json({ error: 'userid tidak valid (harus angka)' }); return; }
  if (!rl('uid:' + userid, 3, 10 * 60 * 1000)) { res.status(429).json({ error: 'terlalu sering untuk user ini — coba lagi nanti' }); return; }
  const s = sanitize(body.data);
  if (s.error) { res.status(400).json({ error: 'data tidak valid: ' + s.error }); return; }

  const token = process.env.GITHUB_TOKEN;
  if (!token) { res.status(503).json({ error: 'upload belum aktif — pemilik repo belum mengisi GITHUB_TOKEN (lihat panduan)' }); return; }

  const path = 'hebat-links-' + userid + '.json';
  const gh = 'https://api.github.com/repos/' + OWNER + '/' + REPO + '/contents/' + path;
  const headers = { Authorization: 'Bearer ' + token, 'User-Agent': 'kk-lite' };

  // sha bila file sudah ada (update, bukan create)
  let sha = null;
  try {
    const g = await fetch(gh, { headers });
    if (g.status === 200) { const j = await g.json(); sha = j.sha; }
    else if (g.status !== 404) { res.status(502).json({ error: 'gagal cek file lama: HTTP ' + g.status }); return; }
  } catch (e) { res.status(502).json({ error: 'gagal jangkau GitHub: ' + e.message }); return; }

  const content = Buffer.from(JSON.stringify(s.out, null, 2) + '\n').toString('base64');
  let pr;
  try {
    pr = await fetch(gh, {
      method: 'PUT',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'sync ' + path + ' (upload dari browser)', content, sha }),
    });
  } catch (e) { res.status(502).json({ error: 'gagal jangkau GitHub: ' + e.message }); return; }
  const p = await pr.json().catch(() => ({}));
  if (!pr.ok) { res.status(502).json({ error: 'gagal commit: ' + (p.message || ('HTTP ' + pr.status)) }); return; }

  res.setHeader('Cache-Control', 'no-store');
  res.json({ ok: true, path, commit: p.commit ? p.commit.sha : null, size: content.length });
}
