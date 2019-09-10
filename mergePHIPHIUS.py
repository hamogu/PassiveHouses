import json

with open("PHIUS.geojson", 'r') as f:
    phius = json.load(f)

with open("PHI.geojson", 'r') as f:
    phi = json.load(f)

phius['features'].extend(phi['features'])

with open("PHIPHIUS.geojson", 'w') as f:
    json.dump(phius, f, indent=2, separators=(',', ': '))
