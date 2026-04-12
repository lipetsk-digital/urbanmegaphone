import httpx
import json
import time
from pathlib import Path

#region = '0bb7fa19-736d-49cf-ad0e-9774c4dae09b'
#area = '47e1fc4c-4ad1-4d03-91f7-981184adcbe7'
#city = None
#settlement = '36022007-8503-4d34-92d9-cc82dfb7a496'
#resultdir = Path.cwd() / 'get-buildings' / 'gunib'

region = '1490490e-49c5-421c-9572-5673ba5d80c8'
area = None
city = 'eacb5f15-1a2e-432e-904a-ca56bd635f1b'
settlement = None
resultdir = Path.cwd() / 'get-buildings' / 'lipetsk'

def GetBuildings(request,id):
    reqURL = 'https://dom.gosuslugi.ru/homemanagement/api/rest/services/houses/public/searchByAddress'
    reqHeaders={
        'Request-GUID': '9b12126e-630e-431c-8008-9df34af6d753',
        'Session-GUID': '30d32344-e667-4a01-bdc3-8df2809d9f1c'
        }
    reqParams = {
        'pageIndex':0,
        'elementsPerPage' : 100
    }
    reqJson = {
        'regionCode' : region,
        'areaCode' : area,
        'cityCode' : city,
        'settlementCode' : settlement
    } | request
    index = 0
    needNextRequest = True
    while needNextRequest:
        reqParams['pageIndex'] = reqParams['pageIndex']+1
        currentIndex = 0

        resultPath = resultdir / 'gosuslugi' / (id+'-'+str(reqParams['pageIndex'])+'.json')
        if resultPath.is_file():
            print("File ",resultPath," exists. Skipping")
            with open(resultPath, 'r', encoding='utf8') as f:
                respJson = json.load(f)
                index += len(respJson['items'])
                currentIndex = len(respJson['items'])
        else:
            time.sleep(3)
            response = httpx.post(url=reqURL,headers=reqHeaders,params=reqParams,json=reqJson)
            print('Response: ',response)           
            with open(resultPath, 'wb') as fb:
                for chunk in response.iter_bytes(chunk_size=128):
                    fb.write(chunk)
            try:
                respJson = response.json()
            except:
                print("Request pageIndex=",reqParams['pageIndex'],' failed')
                continue
            for building in respJson['items']:
                index = index+1
                currentIndex = currentIndex+1
                print(index, building['cadastreNumber'], building['address']['formattedAddress'])

        if (currentIndex == 100):  # if this is a full page
            needNextRequest = True
        else:
            needNextRequest = False


# =======================================================================
# Get territories

response = httpx.get('https://dom.gosuslugi.ru/nsi/api/rest/services/nsi/fias/v4/planning/structure/elements', 
                    params={
                        'actual':'true',
                        'itemsPerPage':1000,
                        'page':1,
                        'regionCode':region,
                        'areaCode':area,
                        'cityCode':city,
                        'settlementCode':settlement
                    })
territories = response.json()
with open(resultdir / 'territories.json', 'w', encoding='utf8') as f:
    json.dump(territories, f, ensure_ascii=False, indent=4)

# =======================================================================
# Loop through territories

for territory in territories:
    print(territory['aoGuid'], territory['formalName'])
    GetBuildings({'planningStructureElementCode' : territory['aoGuid']},territory['aoGuid'])

# =======================================================================
# Get streets

response = httpx.get('https://dom.gosuslugi.ru/nsi/api/rest/services/nsi/fias/v4/streets', 
                    params={
                        'actual':'true',
                        'itemsPerPage':1000,
                        'page':1,
                        'regionCode':region,
                        'areaCode':area,
                        'cityCode':city,
                        'settlementCode':settlement
                    })
streets = response.json()
with open(resultdir / 'streets.json', 'w', encoding='utf8') as f:
    json.dump(streets, f, ensure_ascii=False, indent=4)

# =======================================================================
# Loop through streets

for street in streets:
    print(street['aoGuid'], street['formalName'])
    GetBuildings({'streetCode' : street['aoGuid']},street['aoGuid'])
