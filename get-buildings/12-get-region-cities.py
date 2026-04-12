#region = '0bb7fa19-736d-49cf-ad0e-9774c4dae09b'
region = '1490490e-49c5-421c-9572-5673ba5d80c8'

import httpx

response = httpx.get('https://dom.gosuslugi.ru/nsi/api/rest/services/nsi/fias/v4/cities', 
                        params={
                            'actual':'true',
                            'itemsPerPage':100,
                            'page':1,
                            'regionCode':region
                        })
cities = response.json()

for city in cities:
    print(city['aoGuid'], city['formalName'], city['shortName'])

response = httpx.get('https://dom.gosuslugi.ru/nsi/api/rest/services/nsi/fias/v4/areas', 
                        params={
                            'actual':'true',
                            'itemsPerPage':100,
                            'page':1,
                            'regionCode':region
                        })
areas = response.json()

for area in areas:
    response = httpx.get('https://dom.gosuslugi.ru/nsi/api/rest/services/nsi/fias/v4/cities', 
                        params={
                            'actual':'true',
                            'itemsPerPage':100,
                            'page':1,
                            'regionCode':region,
                            'areaCode':area['aoGuid']
                        })
    cities = response.json()
    for city in cities:
        print('AREA =', area['aoGuid'], area['formalName'], area['shortName'], '  CITY =', city['aoGuid'], city['formalName'], city['shortName'])

    response = httpx.get('https://dom.gosuslugi.ru/nsi/api/rest/services/nsi/fias/v4/settlements', 
                    params={
                        'actual':'true',
                        'itemsPerPage':1000,
                        'page':1,
                        'regionCode':region,
                        'areaCode':area['aoGuid']
                    })
    cities = response.json()
    for city in cities:
        print('AREA =',area['aoGuid'], area['formalName'], area['shortName'], '  SETTLEMENT =', city['aoGuid'], city['formalName'], city['shortName'])