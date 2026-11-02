"""Télécharge les radars (OpenStreetMap, highway=speed_camera) de France, Espagne et pays voisins
et écrit radars.json : [[id, lat, lon, limite], ...]. Lancé chaque semaine par GitHub Actions."""
import json, sys, time, urllib.parse, urllib.request

MIRRORS = ["https://overpass-api.de/api/interpreter",
           "https://overpass.kumi.systems/api/interpreter",
           "https://overpass.private.coffee/api/interpreter",
           "https://overpass.openstreetmap.fr/api/interpreter"]
BOXES = [(41.2, -5.3, 51.2, 9.7),   # France
         (35.9, -9.5, 43.9, 4.4)]   # Espagne, Andorre, Portugal

def fetch(box):
    q = '[out:json][timeout:300];node["highway"="speed_camera"](%s,%s,%s,%s);out;' % box
    data = urllib.parse.urlencode({"data": q}).encode()
    for rnd in range(3):
        for m in MIRRORS:
            try:
                req = urllib.request.Request(m, data=data, headers={"User-Agent": "vigie-route/1.0 (github.com/Arnola79/vigie-route)"})
                with urllib.request.urlopen(req, timeout=330) as r:
                    j = json.load(r)
                if "elements" in j:
                    print(m, box, len(j["elements"]), "radars")
                    return j["elements"]
            except Exception as e:
                print("échec", m, e, file=sys.stderr)
        time.sleep(60)
    raise SystemExit("aucun serveur Overpass n'a répondu")

def limit(v):
    try:
        n = int(str(v).split(";")[0].strip().split(" ")[0])
        return n if 20 <= n <= 150 else 0
    except Exception:
        return 0

out, seen = [], set()
for b in BOXES:
    for e in fetch(b):
        if e.get("type") != "node" or e["id"] in seen:
            continue
        seen.add(e["id"])
        out.append([e["id"], round(e["lat"], 5), round(e["lon"], 5), limit((e.get("tags") or {}).get("maxspeed"))])
out.sort()
if len(out) < 500:
    raise SystemExit("liste anormalement courte (%d), fichier non remplacé" % len(out))
with open("radars.json", "w") as f:
    json.dump(out, f, separators=(",", ":"))
print("total", len(out))
