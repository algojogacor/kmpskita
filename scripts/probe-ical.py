# Probe jalur iCal HE-BAT (Moodle): feed kalender pribadi via authtoken,
# tanpa sesi login dan tanpa token webservice (yang dimatikan admin).
#
# Authtoken didapat dari UI: login hebat.elearning.unair.ac.id ->
# Calendar -> Import or export calendars -> Get calendar URL.
#
# Penggunaan:
#   set KK_ICAL_USERID=<id user moodle>   (angka di URL, param userid=)
#   set KK_ICAL_AUTHTOKEN=<40 hex>        (param authtoken=)
#   python probe-ical.py
#
# Catatan: export_execute.php TIDAK mengirim header CORS, jadi dari browser
# butuh proxy (lihat api/moodle-cal.js di repo web).

import os
import urllib.request
import time
import re

USERID = os.environ.get("KK_ICAL_USERID", "")
AUTHTOKEN = os.environ.get("KK_ICAL_AUTHTOKEN", "")
assert USERID and AUTHTOKEN, "set KK_ICAL_USERID dan KK_ICAL_AUTHTOKEN dulu"

BASE = "https://hebat.elearning.unair.ac.id/calendar/export_execute.php"
start = int(time.time()) - 90 * 86400      # ~3 bulan lalu
end = start + 490 * 86400                  # s/d ~16 bulan ke depan
url = (
    f"{BASE}?userid={USERID}&authtoken={AUTHTOKEN}"
    f"&preset_what=all&preset_time=custom&starttime={start}&endtime={end}"
)

req = urllib.request.Request(url, headers={"User-Agent": "kk-lite/1.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    print("HTTP", r.status)
    ics = r.read().decode("utf-8", "replace")

# parse sederhana: VEVENT -> {SUMMARY, CATEGORIES, DTSTART}
events, cur, last = [], None, ""
for raw in ics.splitlines():
    line = raw.rstrip("\r")
    m = re.match(r"^([A-Z-]+);?[^:]*:(.*)$", line)
    if not m:
        if cur and last and line[:1] in (" ", "\t"):
            cur[last] += line.strip()
        continue
    k, v = m.group(1), m.group(2)
    if k == "BEGIN":
        cur = {}
    elif k == "END":
        if cur:
            events.append(cur)
        cur, last = None, ""
    elif cur and k in ("SUMMARY", "CATEGORIES", "DTSTART"):
        cur[k] = v
        last = k

print("event:", len(events))
for e in events:
    print("-", e.get("SUMMARY"), "|", e.get("CATEGORIES"), "|", e.get("DTSTART"))
