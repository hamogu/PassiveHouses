import json

with open("PHIUS.geojson", 'r') as f:
    phius = json.load(f)

with open("PHI.geojson", 'r') as f:
    phi = json.load(f)

# Append only those in North America
for r in phi['features']:
    lon, lat = r['geometry']['coordinates']
    if (lat > 15) and (lon<-40):
        phius['features'].append(r)

with open("PHIPHIUS.geojson", 'w') as f:
    json.dump(phius, f, indent=2, separators=(',', ': '))
