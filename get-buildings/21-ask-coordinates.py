from pathlib import Path
import json
import httpx
import time
from tqdm import tqdm

folder = Path.cwd() / 'get-buildings' / 'lipetsk'

# Load houses
with open(folder / 'houses.dom.gosuslugi.ru.json', encoding='utf-8') as f:
    houses = json.load(f)

# Read prevois coordinates
coords = {}
try:
    with open(folder / 'pkk.txt', encoding='utf-8') as f:
        for line in f:
            data = line.rstrip().split(',')
            coords[data[0]] = (data[1],data[2])
except:
    None

# Recursively extract all [x, y] leaf points from GeoJSON coordinates structure
def extract_points(coords, points):
    if coords and isinstance(coords[0], (int, float)):
        points.append(coords[:2])
    else:
        for item in coords:
            extract_points(item, points)

# Loop through houses
for house in tqdm(houses, desc='Fetching coordinates'):
    if house['cadastre']:
        print (house['cadastre'])
        if house['cadastre'] in coords.keys():
            print('Already exist, skipping...')
            continue
        # Send request to pkk, retry on timeout
        while True:
            try:
                response = httpx.get(
                    'https://nspd.gov.ru/api/geoportal/v2/search/geoportal',
                    params={'query': house['cadastre']},
                    headers={'Referer': 'https://nspd.gov.ru/map?thematic=PKK'},
                    verify=False
                )
                break
            except httpx.TimeoutException:
                tqdm.write('Timeout, retrying in 10 seconds...')
                time.sleep(10)
        data = response.json()
        features = data.get('data', {}).get('features', [])
        if features:
            all_points = []
            for feature in features:
                extract_points(feature.get('geometry', {}).get('coordinates', []), all_points)
            if all_points:
                cx = sum(p[0] for p in all_points) / len(all_points)
                cy = sum(p[1] for p in all_points) / len(all_points)
                print(cx, cy)
                with open(folder / 'pkk.txt', 'a', encoding='utf-8') as f:
                    f.write(house['cadastre']+","+str(cx)+","+str(cy)+"\n")
            else:
                print('No coordinates')
                with open(folder / 'pkk.txt', 'a', encoding='utf-8') as f:
                    f.write(house['cadastre']+",,\n")
        else:
            print('Not found')
            with open(folder / 'pkk.txt', 'a', encoding='utf-8') as f:
                f.write(house['cadastre']+",,\n")
        time.sleep(1)