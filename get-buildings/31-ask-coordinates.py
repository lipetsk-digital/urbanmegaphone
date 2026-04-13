from pathlib import Path
import json
import httpx
import time

folder = Path.cwd() / 'get-buildings' / 'lipetsk'
APIkey = '12345678-1234-1234-1234-123456789012'

# Load houses
with open(folder / 'houses.dom.gosuslugi.ru.json', encoding='utf-8') as f:
    houses = json.load(f)

# Read prevois coordinates
coords = {}
with open(folder / 'pkk.txt', encoding='utf-8') as f:
    for line in f:
        data = line.rstrip().split(',')
        coords[data[0]] = (data[1],data[2])

# Load prevois Yandex requests
ResultFolder= folder / 'yandex'
ResultFolder.mkdir(parents=True, exist_ok=True)

countPPK = 0
countYandexExists = 0
countYandexNeedRequest = 0
# Loop through houses
for house in houses:
    if house['cadastre'] in coords.keys():
        if coords[house['cadastre']][0]:
            print(house['address'],'Already exist on PKK, skipping...')
            countPPK = countPPK + 1
            continue
    ResultFile = ResultFolder / (house['fias']+'.json')
    if ResultFile.is_file():
        print(house['address'],'Already exist on Yandex, skipping...')
        countYandexExists += 1
        continue

    print(house['address'],'Asking...')
    #time.sleep(3)
    countYandexNeedRequest += 1
    response = httpx.get('https://geocode-maps.yandex.ru/1.x',
                        params={
                            'apikey':APIkey,
                            'geocode':house['address'],
                            'format':'json'
                        })
    data = response.json()
    with open(ResultFile, "wb") as f:
        f.write(response.content)

    print("\t = ",data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos'],
          data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['name'],
          data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['description'])

print("Existst on PPK: ", countPPK)
print("Existst on Yandex: ", countYandexExists)
print("Need request to Yandex: ", countYandexNeedRequest)