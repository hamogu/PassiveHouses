import json
from urllib.request import urlopen


standard = {
    "0": "PHI Low Energy Building",
    "1": "EnerPHit",
    "2": "Passive House",
    "3": "EnerPHit Retrofit",
    "4": "EnerPHit Retrofit",
    "p": "Passive House",
    "u": "EnerPHit unit",
    "e": "EnerPHit Retrofit",
}

def json2geojson():
    with open("data/PHI.json", 'r') as f:
        known_projects = json.load(f)

    out = {'type': "FeatureCollection", 'features': []}
    for row in known_projects:
        # Don't know what 5 is. I notice those projects don't have a pid either,
        # so I can't look up any additional details anyway.
        if row['std'] == '5':
            continue
        loc = {"type": "Point", "coordinates": [row['lon'], row['lat']]}

        prop = {}
        prop["marker-color"] = "#C02942"
        if row['pid']:
            prop['name'] = f"<a href='https://passivehouse-database.org/index.php?lang=en#d_{row['pid']}'>{standard[row['std']]}</a>"
        else:
            prop['name'] = standard[row['std']]
    
        desc = '<table>'
        desc = desc + '<tr><td>Certified by</td><td><a href="https://passiv.de/">PHI</a></td></tr>'
        for col in ['type', 'year']:
            if row[col]:
                desc = desc + '<tr><td><strong>{}</strong></td><td>{}</td></tr>'.format(col, row[col])
        desc = desc + '<tr><td>Note</td><td>Location is approximate</td></tr>'
        desc = desc + '</table>'
        prop['description'] = desc

        out['features'].append({"type": "Feature",
                                "geometry": loc,
                                "properties": prop})

    with open("data/PHI.geojson", 'w') as f:
        json.dump(out, f, indent=2, separators=(',', ': '))


if __name__ == '__main__':
    url = "https://database.passivehouse.com/buildings/get_buildings/"
    webjson = urlopen(url).read()
    known_projects = json.loads(webjson)
    with open("data/PHI.json", 'w') as f:
        json.dump(known_projects, f, indent=2)
    #json2geojson()