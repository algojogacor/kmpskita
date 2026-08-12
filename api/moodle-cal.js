// Vercel serverless: proxy iCal kalender HE-BAT (Moodle) -> JSON event tugas.
// Kenapa butuh proxy: export_execute.php TIDAK mengirim header CORS
// (berbeda dari webservice/rest yang ACAO:*), jadi browser tidak bisa
// fetch langsung. Stateless: authtoken lewat query, tidak disimpan.
const FEED = 'https://hebat.elearning.unair.ac.id/calendar/export_execute.php';

export default async function handler(req, res) {
  const { userid, authtoken } = req.query;
  if (!userid || !authtoken) {
    res.status(400).json({ error: 'butuh param userid & authtoken (ambil dari "Get calendar URL" di HE-BAT)' });
    return;
  }
  // Range kustom: ~90 hari ke belakang + 400 hari ke depan (satu semester penuh)
  const start = Math.floor(Date.now() / 1000) - 90 * 86400;
  const end = start + 490 * 86400;
  const u = FEED + '?userid=' + encodeURIComponent(userid) +
    '&authtoken=' + encodeURIComponent(authtoken) +
    '&preset_what=all&preset_time=custom&starttime=' + start + '&endtime=' + end;
  let r;
  try { r = await fetch(u, { headers: { 'User-Agent': 'kk-lite/1.0' } }); }
  catch (e) { res.status(502).json({ error: 'gagal jangkau HE-BAT: ' + e.message }); return; }
  if (!r.ok) { res.status(502).json({ error: 'feed HE-BAT: HTTP ' + r.status }); return; }
  const txt = await r.text();
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('Content-Type', 'application/json');
  res.json({ events: parseIcs(txt) });
}

function parseIcs(t) {
  const events = []; let cur = null, last = '';
  const keys = ['SUMMARY', 'DESCRIPTION', 'DTSTART', 'DTEND', 'CATEGORIES', 'UID'];
  for (const raw of t.split(/\r?\n/)) {
    const line = raw.replace(/\r$/, '');
    const m = line.match(/^([A-Z-]+);?[^:]*:(.*)$/);
    if (!m) {
      // baris lanjutan (folded line): sambungkan ke properti sebelumnya
      if (cur && last && /^[ \t]/.test(line)) cur[last] += line.trim();
      continue;
    }
    const k = m[1], v = m[2];
    if (k === 'BEGIN') cur = {};
    else if (k === 'END') { if (cur) events.push(cur); cur = null; last = ''; }
    else if (cur && keys.includes(k)) { cur[k] = v; last = k; }
  }
  return events;
}
