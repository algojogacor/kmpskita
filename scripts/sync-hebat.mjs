// Sync hebat-links.json — ambil URL halaman tugas dari dashboard HE-BAT
// via Kimi WebBridge (butuh: daemon jalan + Chrome sudah login HE-BAT).
// Jalankan: node scripts/sync-hebat.mjs  lalu commit/push hasilnya.
import { readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const DAEMON = 'http://127.0.0.1:10086/command';
const SESSION = 'hebat-sync';
const here = dirname(fileURLToPath(import.meta.url));
const linksFile = resolve(here, '../hebat-links.json');

async function cmd(action, args = {}) {
  const r = await fetch(DAEMON, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, args, session: SESSION }),
  });
  const j = await r.json();
  if (!j.ok) throw new Error(JSON.stringify(j.error || j));
  return j.data;
}

await cmd('navigate', { url: 'https://hebat.elearning.unair.ac.id/my/', newTab: true, group_title: 'Sync tugas HE-BAT' });
await new Promise(r => setTimeout(r, 4000));

const code = `JSON.stringify([...document.querySelectorAll('a')].filter(a=>/assign\\/view/i.test(a.href||'')).map(a=>({t:a.textContent.trim().replace(/\\s+/g,' '), h:a.href})).filter(x=>x.t&&x.h&&x.h.includes('mod/assign/view.php')))`;
const d = await cmd('evaluate', { code });
const items = JSON.parse(d.value);

// nama bersih: prefer teks yang berakhiran "is due"/"due" (identik dengan SUMMARY feed iCal)
const clean = t => t.replace(/\s+(is due|due)$/i, '').trim();
const cands = items
  .filter(it => /(is due|due)$/i.test(it.t) || !/\d{4}Ganjil/i.test(it.t))
  .map(it => ({ name: clean(it.t), url: it.h }));

const cur = JSON.parse(readFileSync(linksFile, 'utf8'));
const seen = new Set(cur.tasks.map(t => t.url));
let added = 0;
for (const it of cands) {
  if (seen.has(it.url)) continue;
  cur.tasks.push(it);
  seen.add(it.url);
  added++;
}
cur.generated = new Date().toISOString().slice(0, 10);
writeFileSync(linksFile, JSON.stringify(cur, null, 2) + '\n');
console.log(`hebat-links.json: ${cur.tasks.length} tugas (baru: ${added})`);
for (const t of cur.tasks) console.log('-', t.name, '->', t.url);
await cmd('close_tab', {});
