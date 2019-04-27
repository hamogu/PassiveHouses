from __future__ import print_function

from collections import OrderedDict
import json
import numpy as np

from geopy.geocoders import Nominatim
from astropy.table import Table

tab = Table.read('http://www.phius.org/phius-certification-for-buildings-products/certified-projects-database', format='html')

geolocator = Nominatim()



loc_by_hand = {'West Moberly, BC': {'coordinates': [-121.8553452, 55.8277321], 'type': 'Point'},
               'St. Joseph, IL': {'coordinates': [-88.0419502, 40.1136387], 'type': 'Point'},
               'Unicorporated Adams County, CO': {'coordinates': [-104.9785223, 39.9212746], 'type': 'Point'},
               'Yokohama City, Japan': {'coordinates': [139.5490381, 35.4619297], 'type': 'Point'},
               'Va. Beach, VA': {'coordinates': [-76.2935035, 36.7953392], 'type': 'Point'},
               'Elk, WA': {'coordinates': [-117.2853794, 48.0162853], 'type': 'Point'},
               'Lake Geneva (Jainsville/Rock County, WI climate data set), WI': {},
               'Belingham, WA':  {'coordinates': [-122.5313497, 48.753404], 'type': 'Point'},
               'Wurtsburo, NY':  {'coordinates': [-74.4945967, 41.5765227], 'type': 'Point'},
               'Shaw Island, San Juan Islands, WA':  {'coordinates': [-122.9949629, 48.570948], 'type': 'Point'},
}


out = {'type': "FeatureCollection", 'features': []}
for row in tab:
    if row['Location'] is np.ma.masked:
        print('Skipping project {} - No location given.'.format(row['No.']))
        continue
    print('Looking up: ', row['Location'])
    if row['Location'] in loc_by_hand:
        loc = loc_by_hand[row['Location']]
    else:
        loc = geolocator.geocode(row['Location'] + ', USA', timeout=10)
        if loc is None:
            loc = geolocator.geocode(row['Location'] + ', Canada', timeout=10)
        if loc is None:
            loc = geolocator.geocode(row['Location'], timeout=10)
        if loc is None:
            print('Skipping project {} - location not found {}'.format(row['No.'], row['Location']))
            continue
        loc = {"type": "Point", "coordinates": [loc.longitude, loc.latitude]}
        # Save values so the same location is looked up only once for speed
        loc_by_hand[row['Location']] = loc

    prop = OrderedDict()
    if row['Status'] == 'Pre-certified':
        prop["marker-color"] = "#FFFF00"
    elif row['Status'] == 'Certified':
        prop["marker-color"] = "#FF8C00"
    else:
        prop["marker-color"] = "#FFFFFF"

    if row['Floor area'] > 10000:
        prop["marker-size"] = "large"
    else:
        prop["marker-symbol"] = "building"

    prop['name'] = "<a href='http://www.phius.org/projects/{}'>{}</a>".format(row['No.'],
                                                                              row['Project'])
    desc = '<table>'
    for col in ['Builder', 'Const. type', 'Bldg. function', 'Floor area', 'Project type']:
        desc = desc + '<tr><td><strong>{}</strong></td><td>{}</td></tr>'.format(col, row[col])
    desc = desc + '</table>'
    prop['description'] = desc

    out['features'].append({"type": "Feature",
                            "geometry": loc,
                            "properties": prop})


with open("PHIUS.geojson", 'w') as f:
    json.dump(out, f, indent=2, separators=(',', ': '))
