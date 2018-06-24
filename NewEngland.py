'''Very simple script to read Laurenslist.txt and reformat it to value
geojson.'''


from __future__ import print_function
from collections import OrderedDict
import json

from geopy.geocoders import Nominatim
geolocator = Nominatim()

out = {'type': "FeatureCollection", 'features': []}

def item_to_json(item):
    if len(item) > 4:
        raise ValueError()

    name = item[0]
    loc = geolocator.geocode(item[1] + ', USA')
    print(loc.address)

    prop = OrderedDict({"marker-color": "#f00"})


    # If sq ft is not given, treat it as a small home
    sqft = 0
    sqft_txt = ''
    # default URL
    url = 'http://lowcarbonproductions.net/phne-2017-flipbook/index.html'

    for i in item:
        if 'sq ft' in i:
            # If sqft given use that value
            sqft = int(i.split()[0].replace(',', ''))
            sqft_txt = i
        if 'http' in i:
            url = i

    if sqft > 10000:
        prop["marker-size"] = "large"
    else:
        prop["marker-symbol"] = "building"

    prop['name'] = "<a href='{}'>{}</a>".format(url, name)
    if sqft_txt != '':
        prop['description'] = sqft_txt

    out['features'].append({"type": "Feature",
                            "geometry": {"type": "Point",
                                         "coordinates": [loc.longitude, loc.latitude]},
                            "properties": prop})



item = []
with open("Laurenslist.txt") as f:
    for line in f:
        line = line[:-1]
        if line == "":
            item_to_json(item)
            item = []
        else:
            item.append(line)

with open("NewEngland.geojson", 'w') as f:
    json.dump(out, f, indent=2, separators=(',', ': '))
