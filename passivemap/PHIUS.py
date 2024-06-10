import json
from urllib.request import urlopen

from geopy.geocoders import Nominatim
from bs4 import BeautifulSoup

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


def download_new_project_details(current_project_list, update_all=False):
    '''Compare new list of objects with old list. Add details for missing objects.
    
    This function takes on input a dict of objects with title and link to the detail page. 
    It loads the database from the data/PHIUS.json file. For objects not in that database,
    it downloads the details from the PHIUS website and add the object to the database.
    In the end, the database is written back to the file.
    '''
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


def add_location():
    with open("data/PHIUS.json", 'r') as f:
        known_projects = json.load(f)
    with open("data/known_coords.json", 'r') as f:
        known_locs = json.load(f)

    for k, v in known_projects.items():
        # If we have a string location, but no Location object
        if ('location' in v):
            loc = v['location']
            if "Location" not in v:
                # If we have a string location, but no Location object
                if loc in known_locs:
                    v['Location'] = known_locs[loc]
                else:
                    print(f'Searching locations for {loc}')
                    geoloc = geolocator.geocode(loc + ', USA', timeout=10)
                    if geoloc is None:
                        geoloc = geolocator.geocode(loc + ', Canada', timeout=10)
                    if loc is None:
                        geoloc = geolocator.geocode(loc, timeout=10)
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
    url = "https://www.phius.org/certified-project-database?_page=1&keywords=&_limit=10000"
    html = urlopen(url).read()
    allsoup = BeautifulSoup(html, features="lxml")
    current_project_list = get_list_all_projects()
    print(len(current_project_list))
    download_new_project_details(current_project_list)
    add_location()
    #json2geojson()