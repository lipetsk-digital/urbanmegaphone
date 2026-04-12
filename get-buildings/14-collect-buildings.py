from pathlib import Path
import json
import re
import requests

folder = Path.cwd() / 'get-buildings' / 'lipetsk'
passport_dir = folder / 'passport'
passport_dir.mkdir(exist_ok=True)

# These GUIDs must be updated periodically — inspect any house passport request
# in the browser DevTools (dom.gosuslugi.ru) to get fresh values
REQUEST_GUID = '108a70f0-06b8-4006-bf52-c920aba15137'
SESSION_GUID = '3009be70-8a18-4009-8b3d-314cb064feaa'

houses = []
counter = 0
apartment_buildings = 0
individual_houses = 0
total_flats = 0

for file in Path('.',folder/'gosuslugi').glob("*-*-*-*-*-?.json", case_sensitive=False):
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
        for item in data['items']:
            counter = counter + 1
            house = {}
            house['guid'] = item['guid']
            house['fias'] = item['address']['house']['houseGuid']
            house['address'] = item['address']['formattedAddress']
            print(f"\n{counter}. {house['address']}", end='')
            house['cadastre'] = item['cadastreNumber']
            house['type'] = item['houseType']['houseTypeName']
            if item['managementOrganization'] is not None:
                house['uk'] = item['managementOrganization']['shortName']
            # Covert floors to integer
            try:
                if item['maxFloorCount'] is None:
                    floors = 1
                else:
                    floors = int(item['maxFloorCount'])
            except:
                a =re.findall(r"\d+",item['maxFloorCount'])
                b = [int(item) for item in a]
                if len(b)>1:
                    floors = max(b)
                else:
                    floors = 1               
                print(" (" + str(item['maxFloorCount']) + " = " + str(floors) + ")", end='')
            house['floors'] = floors
            print(f" -> {floors} floors", end='')
            # Assign one flat to individual houses
            try:
                flats = int(item['residentialPremiseCount'])
                if flats ==0:
                    flats = 1
            except:
                flats = 1
            house['flats'] = flats
            # Search for duplicates
            found = False
            for house2 in houses:
                # Find duplicates with one address
                if house['address'] == house2['address']:
                    if house2['flats'] < house['flats']:
                        total_flats = total_flats - house2['flats'] + house['flats']
                        house2['flats'] = house['flats']
                    if house2['floors'] is None:
                        house2['floors'] = house['floors']
                    elif house['floors'] is not None:
                        if house2['floors'] < house['floors']:
                            house2['floors'] = house['floors']
                    if house2['cadastre'] is None:
                        house2['cadastre'] = house['cadastre']
                    house2['fias'] = house['fias']
                    found = True
                # Find duplicates with one cadastre
                if house['cadastre'] == house2['cadastre']:
                    # Clear cadastres of both houses
                    house['cadastre'] = None
                    house2['cadastre'] = None
            if not(found):
                houses.append(house)
                if house['flats'] == 1:
                    individual_houses = individual_houses + 1
                else:
                    apartment_buildings = apartment_buildings + 1
                total_flats = total_flats + house['flats']

            # Fetch entrance count from house passports for buildings with >= 5 floors
            if house['floors'] >= 5:
                cache_file = passport_dir / f"{house['guid']}.json"
                if cache_file.exists():
                    print(f" [cached]", end='')
                    with open(cache_file, encoding='utf-8') as f:
                        passport_data = json.load(f)
                else:
                    print(f" [request]", end='')
                    resp = requests.post(
                        'https://dom.gosuslugi.ru/homemanagement/api/rest/services/passports/search',
                        headers={
                            'Content-Type': 'application/json',
                            'Request-GUID': REQUEST_GUID,
                            'Session-GUID': SESSION_GUID,
                        },
                        json={"houseGuid": house['guid'], "page": 1, "itemsPerPage": 500}
                    )
                    passport_data = resp.json()
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(passport_data, f, ensure_ascii=False, indent=4)
                # paramCode "2.10" = number of entrances (подъездов)
                entrance = 1
                try:
                    for param in passport_data.get('parameters', []):
                        if param.get('paramCode') == '2.10':
                            entrance = int(param['value'])
                            print(f" -> {entrance} entrances found", end='')
                            break
                except (ValueError, TypeError, KeyError):
                    entrance = 1
                house['entrance'] = entrance

print("Total living houses found: ",counter)
print("Unique living houses: ",len(houses))
print("including ",apartment_buildings," apartment buildings and ",individual_houses," individual houses")
print("Total flats found: ",total_flats)

with open(folder / 'houses.dom.gosuslugi.ru.json', 'w', encoding='utf8') as f:
    json.dump(houses, f, ensure_ascii=False, indent=4)

