from collections import OrderedDict
import json

# input data from:  wget https://database.passivehouse.com/buildings/get_buildings/
with open("PHI.json", 'r') as f:
    phi = json.load(f)

standard = {'0': 'PHI Low Energy Building',
            '1': 'EnerPHit',
            '2': 'Passive House'}

out = {'type': "FeatureCollection", 'features': []}
for row in phi:
    loc = {"type": "Point", "coordinates": [row['lon'], row['lat']]}

    prop = OrderedDict()
    prop["marker-color"] = "#C02942"
    if row['pid'] is None:
        prop['name'] = standard[row['std']]
    else:
        prop['name'] = "<a href='https://passivehouse-database.org/#d_{}'>{}</a>".format(row['pid'],
                                                                                  standard[row['std']])
    desc = '<table>'
    desc = desc + '<tr><td>Certified by</td><td><a href="https://passiv.de/">PHI</a></td></tr>'
    for col in ['type', 'year']:
        if not row[col] is None:
            desc = desc + '<tr><td><strong>{}</strong></td><td>{}</td></tr>'.format(col, row[col])
    desc = desc + '<tr><td>Note</td><td>Location is approximate</td></tr>'
    desc = desc + '</table>'
    prop['description'] = desc

    out['features'].append({"type": "Feature",
                            "geometry": loc,
                            "properties": prop})


with open("PHI.geojson", 'w') as f:
    json.dump(out, f, indent=2, separators=(',', ': '))
