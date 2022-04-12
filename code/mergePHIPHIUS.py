import json

with open("PHIUS.geojson", 'r') as f:
    phius = json.load(f)

with open("PHI.geojson", 'r') as f:
    phi = json.load(f)

# Append only those in North America
for r in phi['features']:
    # These liens where used ti limit to North America. Now we do all.
    # lon, lat = r['geometry']['coordinates']
    # if (lat > 15) and (lon<-40):
        phius['features'].append(r)

# Now homogenize so that leaflet groups the markers together in zoom out
for r in phius['features']:
    r['geometry']['type'] = 'Point'
    r['properties']['marker-color'] = '#C02942'
    for n in ['marker-size', 'marker-symbol']:
        if n in r['properties']:
            del r['properties'][n]

with open("PHIPHIUS.geojson", 'w') as f:
    json.dump(phius, f, indent=2, separators=(',', ': '))
