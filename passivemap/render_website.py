import json
import folium
from folium.plugins import MarkerCluster
from jinja2 import Environment, FileSystemLoader, select_autoescape


PHIUSstatuscolor = {'Pre-certified': "darkgreen", 'Design Certified': "darkgreen",
               'Certified': "gray", 'Final Certified': 'gray',
                'Registered': "lightgray", None: "lightgray"}

PHIstandard = {'0': 'PHI Low Energy Building',
               '1': 'EnerPHit',
               '2': 'Passive House',
               # In Dec 2022 there is only one building with std=4 and according to the text
               # on the PHI website for that project, it's a "Passive house".
               # So, this might just be an error in the database.
               '4': 'Passive House'}



def PHIUS_data():
    locations = []
    popups = []
    icons = []

    # Available colors
    # [‘red’, ‘blue’, ‘green’, ‘purple’, ‘orange’, ‘darkred’,
    # lightred’, ‘beige’, ‘darkblue’, ‘darkgreen’, ‘cadetblue’, ‘darkpurple’, 
    # ‘white’, ‘pink’, ‘lightblue’, ‘lightgreen’, ‘gray’, ‘black’, ‘lightgray’

    with open("data/PHIUS.json", 'r') as f:
        known_projects = json.load(f)

    
    for k, v in known_projects.items():
        if not 'Location' in v:
            print(f'Skipping {k} - unknown location')
            continue
        locations.append([v['Location']['coordinates'][1], v['Location']['coordinates'][0]])
    
        link = v['link']
        name = f"<a href='{link}' target='_blank'>{k}</a>"
        desc = '<table>'
        desc = desc + '<tr><td>Certified by</td><td><a href="https://www.phius.org">PHIUS</a></td></tr>'

        for col in ['Project Type', 'Building Function', 'Construction Type', 'INT. Conditioned Floor Area']:
            if col in v:
                desc = desc + f'<tr><td><strong>{col}</strong></td><td>{v[col]}</td></tr>'
        desc = desc + '</table>'
        
        popups.append(folium.Popup(html=name + desc, parse_html=False))
        if v.get('Floor area', 0) > 10000:
           icon = 'building'
        else:
          icon = 'house'
        
        status = v.get('Status', None)

        icons.append(folium.map.Icon(icon=icon, prefix='fa', color=PHIUSstatuscolor[status]))
    return locations, popups, icons


def PHI_data():
    locations = []
    popups = []
    icons = []

    with open("data/PHI.json", 'r') as f:
        known_projects = json.load(f)

    for row in known_projects:
        # Don't know what 5 is. I notice those projects don't have a pid either,
        # so I can't look up any additional details anyway.
        if row['std'] == '5':
            continue

        locations.append([row['lat'], row['lon']])

        if row['pid']:
            name = f"<a href='https://passivehouse-database.org/index.php?lang=en#d_{row['pid']}' target='_blank'>{PHIstandard[row['std']]}</a>"
        else:
            name = PHIstandard[row['std']]

        desc = '<table>'
        desc = desc + '<tr><td>Certified by</td><td><a href="https://passiv.de/">PHI</a></td></tr>'
        for col in ['type', 'year']:
            if row[col]:
                desc = desc + '<tr><td><strong>{}</strong></td><td>{}</td></tr>'.format(col, row[col])
        desc = desc + '<tr><td>Note</td><td>Location is approximate</td></tr>'
        desc = desc + '</table>'

        popups.append(folium.Popup(html=name + desc, parse_html=False))
        icons.append(folium.map.Icon(prefix='fa', color='purple'))
    return locations, popups, icons

def make_map(locations, popups, icons, name='Passive Houses'):
    m = folium.Map(
    #location=[40.1759, -100.6016],
    location=[0, 0],
    tiles="cartodbpositron",
    #zoom_start=4,
    zoom_start=2,
    )

    MarkerCluster(locations=locations, popups=popups, icons=icons, name=name).add_to(m)

    return m

PHI_loc, PHI_popup, PHI_icon = PHI_data()
PHIUS_loc, PHIUS_popup, PHIUS_icon = PHIUS_data()

env = Environment(loader=FileSystemLoader('html_templates'),
                  autoescape=select_autoescape(['html']))

template = env.get_template('index.html')
with open('docs/index.html', "w") as f:
    m = make_map(PHI_loc + PHIUS_loc, PHI_popup + PHIUS_popup, PHI_icon + PHIUS_icon)
    f.write(template.render(map_html=m._repr_html_()))


template = env.get_template('PHI.html')
with open('docs/PHI.html', "w") as f:
    m = make_map(PHI_loc, PHI_popup, PHI_icon)
    f.write(template.render(map_html=m._repr_html_()))

template = env.get_template('PHIUS.html')
with open('docs/PHIUS.html', "w") as f:
    m = make_map(PHIUS_loc, PHIUS_popup, PHIUS_icon)
    f.write(template.render(map_html=m._repr_html_()))
