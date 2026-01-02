import argparse
import json
from urllib.request import urlopen

from astropy.table import Table
from numpy.ma import masked
from geopy.geocoders import Nominatim, GoogleV3
from bs4 import BeautifulSoup

# Default geolocator is Nominatim
# Can be overridden in main() if Google API key is provided
geolocator = Nominatim(user_agent="PassiveHouseDatabaseHarvester")


def extract_project_data(soup):
    '''Extract data from a single project in the overview page
    
    On the project page, most of the data on project is saved like this:
    ```
    <article class="teaser js-link-event" data-has-image="false" data-result-type="project">
    [...]
    <span class="status final-certified">Final Certified</span></div>
    [...]
    <a class="js-link-event-link" href="/certified-project-database/tenney-residence">Tenney Residence</a>
    [...]
    <span class="building-function">Single-Family</span>
    <span class="project-type">New Construction</span></span>
    <span class="climate-zone">5B - Cool - Dry</span><div class="stats">
    <span class="sq-ft">3450 sq. ft.</span>
    [...]
    ```
    
    Most of the fields in the input data are just copied verbatim into a dict, but
    some field are processed, extracting the URL to the project detail page, and 
    converting completion date and floor area to numbers.
    
    Returns
    -------
    extracted_data : dict
    '''
    extracted_data = {}
    atag = soup.find('a')
    extracted_data['link'] = 'https://www.phius.org' + atag.get('href')
    extracted_data['title'] = atag.get_text()
    # k matches the keys that I find in "strucutred-data" on the detail pages of each project
    # v is what class is called in this page
    for v, k in [('Status', 'status'), 
                 ('Building Function', 'building-function'), 
                 ('Project Type', 'project-type'), 
                 ('ASHRAE Climate Zone', 'climate-zone'), 
                 ('INT. Conditioned Floor Area', 'sq-ft'), 
                ]:
        tag = soup.find(attrs={'class': k})
        if tag:
            extracted_data[v] = tag.get_text().strip()

    completion = soup.find(attrs={'class': 'completion-date'})
    # Text is something like "Completed 2019" be we want to get only the date
    if completion:
        extracted_data["Construction Completion"] = int(
            completion.get_text().strip().split(" ")[1]
        )
    if 'INT. Conditioned Floor Area' in extracted_data:
        extracted_data["Floor area"] = float(
            extracted_data["INT. Conditioned Floor Area"].strip().replace("sq. ft.", "")
        )
    return extracted_data


def extract_project_detail(soup):
    '''Extract data from PHIUS project detail page
    
    On the project page, most of the data on project is saved like this:
    
      <ul class="structured-data">
        <li>
          <div class="label">Annual Heating Demand</div>
          <div class="value">2.11</div>
        </li>
      [...]
    
    Some of the data comes in formats that can be make more useful
    (e.g. the date could be parsed into ISO or the area converted to a number)
    but that is outside of the scope of this function.
    
    
    Parameters
    ----------
    soup : 
        BeautifulSoup4 parsed html page
    
    Returns
    -------
    extracted_data : dict
        Data will all structured fields from the website
    '''
    extracted_data = {}
    for d in soup.find_all(attrs={'class': 'structured-data'}):
        for li in d.find_all('li'):
            key = li.find(attrs={"class": "label"}).text.strip()
            value = li.find(attrs={"class": "value"}).text.strip()
            extracted_data[key] = value

    loc = soup.find(attrs={'class': 'location'})
    if loc:
        extracted_data['location'] = loc.get_text().strip()
    return extracted_data


def write_address_table_of_new_projects():
    '''Write a CSV file with all projects that need address hand-editing
    1. Load PHIUS.json and known_coords.json
    2. Loop over all projects in PHIUS.json
       - If there is a 'location' field, but no 'address' field, add to table
    3. Write table to PHIUS_locations.csv
    '''
    with open("data/PHIUS.json", 'r') as f:
        known_projects = json.load(f)
    name = []
    location = []
    address = []
    for k, v in known_projects.items():
        # Skip projects without location
        if 'location' not in v:
            continue
        # If 'address' field exists, then we already did a hand-edit
        # But bring up those project again we marked as "NO CITY"
        if 'address' in v and v['address'] != "NO CITY":
            continue
        name.append(k)
        location.append(v['location'])
        address.append(f'{k}, {v["location"]}')
    if len(name) > 0:
        t = Table([name, location, address], names=('name', 'location', 'address'))
        t.write('PHIUS_locations.csv', format='csv', overwrite=True)
        print(f'Wrote {len(name)} entries to PHIUS_locations.csv - check and edit addresses there!')


def apply_address_edits_from_file(address_file):
    '''Apply address edits from a CSV file to PHIUS.json

    Parameters
    ----------
    address_file : str
        Path to CSV file with columns 'name', 'location', 'address'
    '''
    with open("data/PHIUS.json", 'r') as f:
        known_projects = json.load(f)
    t_edited = Table.read(address_file, format='csv')
    # Remove empty rows that a spreadsheet may have added
    t_edited = t_edited[~t_edited['name'].mask]

    for name, loc, addr in zip(t_edited['name'], t_edited['location'], t_edited['address']):
        if addr is masked:
            known_projects[name]['address'] = ''
        else:
            known_projects[name]['address'] = addr
        if addr != 'NO CITY':
            # If we update, remove Location object to force re-geocoding
            if 'Location' in known_projects[name]:
                del known_projects[name]['Location']
            print(f'Updated {name} with address {addr}')

    with open("data/PHIUS.json", 'w') as f:
        json.dump(known_projects, f, indent=2)


def get_list_all_projects():
    url = "https://www.phius.org/certified-project-database?_page=1&keywords=&_limit=10000"
    html = urlopen(url).read()
    allsoup = BeautifulSoup(html, features="lxml")
    projectlist = allsoup.find_all(
        "article", attrs={"data-result-type": "designguide-project"}
    )
    all_projects = {}
    for p in projectlist:
        out = extract_project_data(p)
        title = out.pop("title").strip()
        all_projects[title] = out
    return all_projects


def compare_project_lists(all_projects):
    '''Compare old and new project lists and print added/removed projects'''
    with open("data/PHIUS.json", 'r') as f:
        known_projects = json.load(f)

    old_db = set(known_projects.keys())
    new_db = set(all_projects.keys())
    added_projects = new_db - old_db
    removed_projects = old_db - new_db
    print(f'PHIUS added projects: {added_projects}')
    print(f'PHIUS removed projects: {removed_projects}')

def download_new_project_details(current_project_list, update_all=False):
    '''Compare new list of objects with old list. Add details for missing objects.
    
    This function takes on input a dict of objects with title and link to the detail page. 
    It loads the database from the data/PHIUS.json file. For objects not in that database,
    it downloads the details from the PHIUS website and adds the object to the database.
    In the end, the database is written back to the file.
    '''
    known_projects = {}
    if not update_all:
        with open("data/PHIUS.json", 'r') as f:
            known_projects = json.load(f)

    for k, v in current_project_list.items():
        if update_all or (k not in known_projects) or ('location' not in known_projects[k]):
            print(f'Getting details for {k}')
            html = urlopen(v['link']).read()
            onesoup = BeautifulSoup(html, features="lxml")
            v.update(extract_project_detail(onesoup))
            known_projects[k] = v

    with open("data/PHIUS.json", 'w') as f:
        json.dump(known_projects, f, indent=2)


def _geocode(location, countries=[', USA', ', Canada', '']):
    '''Try to geocode a location, appending different country names if needed'''
    geoloc = None
    for country in countries:
        geoloc = geolocator.geocode(location + country, timeout=10)
        if geoloc is not None:
            print(f'Resolved: {geoloc}')
            return geoloc
    print(f'Location not found: {location}')
    return None

def add_location():
    '''Add locations to all projects in PHIUS.json

    - Loop over all projects in PHIUS.json:
      - If there is a 'location' field (and possible and 'address'), but no 'Location' field, try to geocode it
        - First try 'address' field if it exists
        - Then try 'location' field
      - If geocoding is successful, add a 'Location' field with GeoJSON Point format
    - Save known locations to known_coords.json to speed up future runs
    - Save updated project data back to PHIUS.json
    '''
    with open("data/PHIUS.json", 'r') as f:
        known_projects = json.load(f)
    with open("data/known_coords.json", 'r') as f:
        known_locs = json.load(f)

    for k, v in known_projects.items():
        # If we have a string location, but no Location object
        if ('location' in v) and 'Location' not in v:
            geoloc = None
            if 'address' in v and v['address'] != "NO CITY":
                loc = v['address']
                if loc in known_locs:
                    v['Location'] = known_locs[loc]
                    continue
                geoloc = _geocode(loc)

            if geoloc is None:
                loc = v['location']
                if loc in known_locs:
                    v['Location'] = known_locs[loc]
                    continue
                geoloc = _geocode(loc)

            if geoloc is None:
                print(f'Skipping project {k} - location not found {v["location"]}')
                continue
            locobj = {"type": "Point", "coordinates": [geoloc.longitude, geoloc.latitude]}
            # Save values so the same location is looked up only once for speed
            known_locs[loc] = locobj
            # And also add to the database of objects
            v['Location'] = locobj

    with open("data/PHIUS.json", 'w') as f:
        json.dump(known_projects, f, indent=2)
    with open("data/known_coords.json", 'w') as f:
        json.dump(known_locs, f, indent=2)


statuscolor = {'Pre-certified': "#C4F09E", 'Design Certified': "#C4F09E",
               'Certified': "#79BD9A", 'Final Certified': '#79BD9A',
                'Registered': "#FFFFFF", None: "#FFFFFF"}

def json2geojson():
    with open("data/PHIUS.json", 'r') as f:
        known_projects = json.load(f)

    out = {'type': "FeatureCollection", 'features': []}

    for k, v in known_projects.items():
        if "Location" not in v:
            print(f'Skipping {k} - unknown location')
            continue
        prop = {}
        status = v.get('Status', None)
        prop["marker-color"] = statuscolor[status]

        if v.get('Floor area', 0) > 10000:
            prop["marker-size"] = "large"
        else:
            prop["marker-symbol"] = "building"

        link = v['link']
        prop['name'] = f"<a href='{link}'>{k}</a>"
        desc = '<table>'
        desc = desc + '<tr><td>Certified by</td><td><a href="https://www.phius.org">PHIUS</a></td></tr>'

        for col in ['Project Type', 'Building Function', 'Construction Type', 'INT. Conditioned Floor Area']:
            if col in v:
                desc = desc + f'<tr><td><strong>{col}</strong></td><td>{v[col]}</td></tr>'
        desc = desc + '</table>'
        prop['description'] = desc

        out['features'].append({"type": "Feature",
                                "geometry": v['Location'],
                                "properties": prop})

    with open("data/PHIUS.geojson", 'w') as f:
        json.dump(out, f, indent=2, separators=(',', ': '))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Webscrape PHIUS database')
    parser.add_argument('--redownload', action='store_true', help='Download all project details to get recent changes')
    parser.add_argument('--address-file', type=str, default='', help='CSV file with edited addresses')
    parser.add_argument('--google-api-key-file', type=str, default='', help='File containing Google API key for geocoding (otherwise uses Nominatim)')
    args = parser.parse_args()

    if args.google_api_key_file:
        with open(args.google_api_key_file, "r") as f:
            apikey = f.read().strip()
        geolocator = GoogleV3(api_key=apikey)

    current_project_list = get_list_all_projects()
    print(f'Found {len(current_project_list)} projects in PHIUS database')

    if args.address_file:
        print(f'-- Applying address edits from {args.address_file} --')
        apply_address_edits_from_file(args.address_file)

    compare_project_lists(current_project_list)
    download_new_project_details(current_project_list, update_all=args.redownload)
    write_address_table_of_new_projects()
    add_location()
    #json2geojson()