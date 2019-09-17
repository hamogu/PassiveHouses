from __future__ import print_function

from collections import OrderedDict
import os
import json
import numpy as np

from geopy.geocoders import Nominatim
from astropy.table import Table

tab = Table.read('http://www.phius.org/phius-certification-for-buildings-products/certified-projects-database', format='html')

geolocator = Nominatim()

if os.path.exists("coords_temp.json"):
    with open("coords_temp.json", 'w') as f:
        loc_by_hand = json.load(f)

else:
    loc_by_hand = {'West Moberly, BC': {'coordinates': [-121.8553452, 55.8277321], 'type': 'Point'},
               'St. Joseph, IL': {'coordinates': [-88.0419502, 40.1136387], 'type': 'Point'},
               'Unicorporated Adams County, CO': {'coordinates': [-104.9785223, 39.9212746], 'type': 'Point'},
               'Yokohama City, Japan': {'coordinates': [139.5490381, 35.4619297], 'type': 'Point'},
               'Va. Beach, VA': {'coordinates': [-76.2935035, 36.7953392], 'type': 'Point'},
               'Elk, WA': {'coordinates': [-117.2853794, 48.0162853], 'type': 'Point'},
               'Lake Geneva (Jainsville/Rock County, WI climate data set), WI': {'coordinates': [-88.4509902, 42.5866519], 'type': 'Point'},
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
        prop["marker-color"] = "#C4F09E"
    elif row['Status'] == 'Certified':
        prop["marker-color"] = "#79BD9A"
    else:
        prop["marker-color"] = "#FFFFFF"

    if row['Floor area'] > 10000:
        prop["marker-size"] = "large"
    else:
        prop["marker-symbol"] = "building"

    prop['name'] = "<a href='http://www.phius.org/projects/{}'>{}</a>".format(row['No.'],
                                                                              row['Project'])
    desc = '<table>'
    desc = desc + '<tr><td>Certified by</td><td><a href="https://www.phius.org">PHIUS</a></td></tr>'

    for col in ['Builder', 'Const. type', 'Bldg. function', 'Floor area', 'Project type']:
        desc = desc + '<tr><td><strong>{}</strong></td><td>{}</td></tr>'.format(col, row[col])
    desc = desc + '</table>'
    prop['description'] = desc

    out['features'].append({"type": "Feature",
                            "geometry": loc,
                            "properties": prop})

# Save so I don't need to get all the data from th eInternet next time, only the new locations.
with open("coords_temp.json", 'w') as f:
    json.dump(loc_by_hand, f)


with open("PHIUS.geojson", 'w') as f:
    json.dump(out, f, indent=2, separators=(',', ': '))
