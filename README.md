
Process to update the PHIUS project geocoding addresses
=======================================================

Most projects in the PHIUS database have a location set, typically in the form "city, state". 
When we resolve that, we first try to find the location in the USA and if that fails we try Canada. For locations in other countries, the country names must be included, e.g. "Ogano-Machi Chichibu-Gun, Saitama, Japan". This will place a marker on the map in the center of the city. However, for some cities (notably NYC and cities in Massachusetts where Passive house is code minimum in many locations) that means that a lot of projects are shown on top of each other. For those projects, it would be good to have the full address. However, that is not public in the PHIUS database. Yet, many projects use the address as project names e.g. "18 Webster". 

This code write a CSV files with three columns: project name, location given, and project name + location given. In many cases, the latter is useless, but in others it resolves to a real address that can be geocoded more precisely.
However, there is no consistent format for addresses and many have comments in them that trip up geocoding, e.g. "Lighthouse 47 (47 Leavitt Street)". It's not easy to correct that automatically, so this code write a table that can then be manually cleaned up.

The edited table will be read in with:

- An empty values in the address column will mean to use the location as given by PHIUS.
- A filled-in address will be used instead for geocoding, falling back to the location if it can't be resolved (with an error printed).  The value in the "address" column could be the full address (from project name + location or googleling or our own knowledge of the project) or just a corrected version of (city, state) to correct typos in the PHIUS database.
- "NO CITY" in the address means that the project name contains the street address, but we don't know the city (e.g. 128 Main Street, MA - could be almost anywhere in MA). Will fall back to the location given by PHIUS (the state only), but the "NO CITY" marker is there to indicate that these cases should be revisited if the projects are updates in the PHIUS database later.
