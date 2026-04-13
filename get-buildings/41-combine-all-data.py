from pathlib import Path
import json
import geojson
import pandas as pd
import geopandas as gpd

folder = Path.cwd() / 'get-buildings' / 'lipetsk' # Folder of workspace
max_distance = 50 # Max distance to assign House point to a OSM building, meter, integer value. Recomended value: 30-50 m 
individual_home_dimentions = 9.0 # Dimentions of created individual home squared polygons, meter. Recomended value: 9.0 m 

# Load DOM.GOSUSLUGI.RU houses data
with open(folder / 'houses.dom.gosuslugi.ru.json', encoding='utf-8') as f:
    houses = json.load(f)
dfHouses = pd.DataFrame.from_dict(houses) 
dfHouses['entrance'] = dfHouses['entrance'].fillna(0)
dfHouses['uk'] = dfHouses['uk'].fillna('')

# Remove houses with null cadastre number
null_mask = dfHouses['cadastre'].isnull()
removed_count = int(null_mask.sum())
if removed_count > 0:
    dfHouses = dfHouses[~null_mask].reset_index(drop=True)
print(f"Удалено {removed_count} домов с cadastre == null")

# Print houses statistics
houses_total = len(dfHouses.index)
flats_total = dfHouses['flats'].sum()
print("\nDOM.GOSUSLUGI.RU houses loaded:")
print(dfHouses)
print(houses_total," houses found.")
print(flats_total," flats found.")

# Load GeoJSON
with open(folder / 'osm.geojson', encoding='utf-8') as f:
    gjOSM = geojson.load(f)
gdfOSM = gpd.read_file(gjOSM)
print("\nOSM.ORG GeoJSON loaded:")
print(gdfOSM)

# Load PKK points
pointsPKK = []
with open(folder / 'pkk.txt', encoding='utf-8') as f:
    for line in f:
        data = line.rstrip().split(',')
        if data[1]:
            # Add point to collection
            geo = geojson.Feature( geometry=geojson.Point((float(data[1]),float(data[2]))) )
            geo.properties['cadastre'] = 'CDR'+data[0] # Add some letters to cadastre number. So that it doesn't look like time
            pointsPKK.append(geo)
gjPKK = geojson.FeatureCollection(pointsPKK)
gjPKK['crs'] = {"type":"EPSG", "properties":{"code":3857}}
gdfPKK = gpd.read_file(gjPKK)
gdfPKK['cadastre'] = gdfPKK['cadastre'].str[3:] # Remove unnecessary letters
print("\nPKK.ROSREESTR.RU points of cadastre loaded:")
print(gdfPKK)

# Analyze gdfPKK: total number of points and number of points with duplicated coordinates
coords = gdfPKK.geometry.apply(lambda p: (p.x, p.y))
dup_mask = coords.duplicated(keep=False)
if dup_mask.any():
    removed = int(dup_mask.sum())
    gdfPKK = gdfPKK[~dup_mask].reset_index(drop=True)
    print(f"Removed {removed} PKK points with duplicated coordinates")

# Load Yandex points
pointsYandex = []
with open(folder / 'yandex.json', encoding='utf-8') as f:
    yandex = json.load(f)
    for fias in yandex:
        geo = geojson.Feature( geometry=geojson.Point((yandex[fias][0], yandex[fias][1])) )
        geo.properties['fias'] = fias
        pointsYandex.append(geo)
gjYandex = geojson.FeatureCollection(pointsYandex)
gjYandex['crs'] = {"type":"EPSG", "properties":{"code":3857}}
gdfYandex = gpd.read_file(gjYandex)
print("\nMAP.YANDEX.RU points of FIAS loaded:")
print(gdfYandex)

# Merge DOM.GOSUSLUGI.RU houses with PKK.ROSREESTR.RU and MAP.YANDEX.RU points
gdfHouses=dfHouses.merge(right=gdfPKK, how='left', left_on="cadastre", right_on="cadastre")
gdfHouses=gdfHouses.merge(right=gdfYandex, how='left', left_on="fias", right_on="fias")
gdfHouses['geometry'] = gdfHouses['geometry_x'].fillna(gdfHouses['geometry_y']) # PKK is more priority than Yandex
gdfHouses = gdfHouses.drop(['geometry_x','geometry_y'], axis='columns')
gdfHouses = gpd.GeoDataFrame(gdfHouses)
print("\nDOM.GOSUSLUGI.RU houses are merged with PKK.ROSREESTR.RU and MAP.YANDEX.RU map points:")
print(gdfHouses)

HousesNotFoundOnMap = gdfHouses[gdfHouses['geometry'].isnull()]
if len(HousesNotFoundOnMap.index) == 0:
    print("Congratulations! All houses have points on map!")
else:
    print("Warning: some houses form DOM.GOSUSLUGI.RU can not be found on map PKK.ROSREESTR.RU or MAP.YANDEX.RU:")
    print(HousesNotFoundOnMap)

# Merge PKK.ROSREESTR.RU and MAP.YANDEX.RU points with DOM.GOSUSLUGI.RU houses
gdfPKK = gpd.GeoDataFrame(gdfPKK.merge(right=dfHouses, how='left', left_on="cadastre", right_on='cadastre'))
gdfYandex = gpd.GeoDataFrame(gdfYandex.merge(right=dfHouses, how='left', left_on="fias", right_on='fias'))

# Function combine() -
# input: 
#   gdfMerged = geoDataFrame of OSM merged with Houses by attribute or spatial criteria
# output global variables:
#   gdfOSM_assigned - geoDataFrame of OSM buildings, witch are assigned with Houses
#   gdfOSM_unassigned - geoDataFrame of OSM buildings, witch are not assigned with Houses
#   gdfHouses_assigned - geoDataFrame of Houses, witch are assigned with OSM buildings
#   gdfHouses_assigned - geoDataFrame of Houses, witch are not assigned with OSM buildings
#   houses_assigned - count of houses, assigned to OSM building
#   flats_assigned - count of flats in houses, assigned to OSM building
# use global variables:
#   gdfHouses - geoDataFrame of DOM.GOSUSLUGI.RU Houses with PKK.ROSREESTR.RU and MAP.YANDEX.RU points
#   total_houses - total count of living Houses in DOM.GOSUSLUGI.RU data
#   total_flats - total count of flats in living Houses
gdfOSM_assigned = gpd.GeoDataFrame()
def combine(gdfMerged):
    global gdfOSM_assigned
    global gdfOSM_unassigned
    global gdfHouses
    global gdfHouses_assigned
    global gdfHouses_unassigned
    global total_houses
    global total_flats
    global houses_assigned
    global flats_assigned
    if 'index_right' in gdfMerged.columns:
        gdfMerged = gdfMerged.drop(['index_right'], axis='columns')
    gdfAssigned = gdfMerged[ gdfMerged['fias'].notnull() ]
    gdfOSM_assigned = gpd.GeoDataFrame(pd.concat([gdfOSM_assigned, gdfAssigned], ignore_index=True, sort=False))
    gdfOSM_unassigned = gdfMerged[ gdfMerged['fias'].isnull() ]
    gdfOSM_unassigned = gdfOSM_unassigned.drop(['fias', 'address', 'cadastre', 'type', 'floors', 'flats', 'guid', 'entrance', 'uk'], axis='columns')
    houses_assigned = len(gdfOSM_assigned['fias'].dropna().unique())
    flats_assigned = gdfOSM_assigned['flats'].sum()
    print(len(gdfAssigned.index)," buildings assigned:")
    print(houses_assigned," houses assigned (",round(houses_assigned/houses_total*100,1),"%)")
    print(flats_assigned," flats assigned (",round(flats_assigned/flats_total*100,1),"%)")
    gdfHousesMerged = gdfHouses.merge(right=gdfOSM_assigned[["fias","geometry"]], how='left', left_on="fias", right_on="fias", suffixes=[None, '_in'])
    gdfHousesMerged = gdfHousesMerged.sort_values('geometry_in')
    gdfHousesMerged = gdfHousesMerged.drop_duplicates(subset='fias', keep="first")
    gdfHouses_assigned = gdfHousesMerged[ gdfHousesMerged['geometry_in'].notnull() ]
    gdfHouses_unassigned = gdfHousesMerged[ gdfHousesMerged['geometry_in'].isnull() ]
    gdfHouses_unassigned = gdfHouses_unassigned.drop(['geometry_in'], axis='columns')
    gdfHouses_unassigned = gdfHouses_unassigned.sort_values('flats', ascending=False)
    print("Houses: ",houses_total," = ",len(gdfHouses_assigned.index)," (assigned) + ",len(gdfHouses_unassigned.index)," (unassigned)")
    print(gdfAssigned.sort_values('flats', ascending=False).head())
    
# For each OSM building find largest house 
print("\nAssign points of the houses to OSM buildings, that are contained in them...")
gdfOSM2 = gdfOSM.sjoin(gdfHouses, how="left", predicate='contains')
gdfOSM2 = gdfOSM2.sort_values('flats', na_position='first')
gdfOSM2 = gdfOSM2.drop_duplicates(subset='geometry', keep="last")
combine(gdfOSM2)
print("\nTOP-50 of unassigned houses:")
print(gdfHouses_unassigned.head(50).to_string())

# For unassigned OSM building find nearest houses
for distance in range(1,max_distance):
    print("\nAssign points of the houses to OSM buildings, that are located at a distance ",distance," meters or less...")
    gdfOSM3 = gdfOSM_unassigned.sjoin_nearest(gdfHouses_unassigned, how="left", max_distance=distance, distance_col="distance")
    gdfOSM3 = gdfOSM3.sort_values('distance')
    gdfOSM3 = gdfOSM3.drop_duplicates(subset='geometry', keep="first")
    combine(gdfOSM3)
 
# Create buildings of individual houses without its
gdfHousesIndividual = gdfHouses_unassigned[ gdfHouses_unassigned['flats']==1 ]
print("Total unassigned individual houses found: ",len(gdfHousesIndividual.index))
gdfOSM5 = gdfOSM.sjoin(gdfHousesIndividual, how="left", predicate='contains')
fiasToRemove = gdfOSM5[ gdfOSM5['fias'].notnull() ][['fias']]
gdfHousesIndividual = gdfHousesIndividual.merge(right=fiasToRemove, how='outer', left_on="fias", right_on="fias", indicator=True, suffixes=[None, '_in'])
gdfHousesIndividual = gdfHousesIndividual[ gdfHousesIndividual['_merge']=='left_only' ]
gdfHousesIndividual = gdfHousesIndividual.drop(['_merge'], axis='columns')
print("Unassigned individual houses not located on another building: ",len(gdfHousesIndividual.index))
print("\nBuild typical building for unassigned individual houses...")
gdfHousesIndividual['geometry'] = gdfHousesIndividual['geometry'].buffer(distance=individual_home_dimentions, cap_style='square')
gdfHousesIndividual = gpd.GeoDataFrame(pd.concat([gdfHousesIndividual, gdfOSM_unassigned], ignore_index=True, sort=False))
combine(gdfHousesIndividual)

print("\nTOP-20 of unassigned houses:")
print(gdfHouses_unassigned.head(20))

# Calculate median levels of different building types
print("\nCalculate median levels of different building types:")
floors = gdfOSM
floors["osm-levels"] = pd.to_numeric(floors["osm-levels"], errors='coerce')
floors = floors[ floors['osm-levels'].notnull() ]
medium_floors = pd.pivot_table(data = floors, index=['osm-building'], values=['osm-levels'], aggfunc={'osm-levels':'median'})
print(medium_floors)
total_median_levels = floors['osm-levels'].median()

# Take floors count from "osm-levels" field and take it to null "floors" field
gdfOSM_unassigned = gdfOSM_unassigned.merge(right=medium_floors, how='left', left_on="osm-building", right_on="osm-building", suffixes=[None, '_median'])
gdfOSM_unassigned["floors"] = gdfOSM_unassigned["osm-levels"].fillna(gdfOSM_unassigned["osm-levels_median"])
gdfOSM_unassigned = gdfOSM_unassigned.drop(['osm-levels_median'], axis='columns')
print("\n",len(floors.index)," unassigned building have floors info on OSM. ",len(gdfOSM_unassigned.index)-len(floors.index)," buildings have been assigned floors value from median values.")

# Check count of buildings without floors information
buildings_without_floors = gdfOSM_assigned['floors'].isnull().sum() + gdfOSM_unassigned['floors'].isnull().sum()
print("\n",buildings_without_floors," buildings without floors found:")
print(gdfOSM_unassigned[ gdfOSM_unassigned['floors'].isnull() ])
gdfOSM_unassigned["floors"] = gdfOSM_unassigned["floors"].fillna(total_median_levels)
print("Assign them median value of all cities buildings: ",total_median_levels)

# Save GeoJSON to file
gdfBuildings = gpd.GeoDataFrame(pd.concat([gdfOSM_assigned, gdfOSM_unassigned], ignore_index=True, sort=False))
gdfBuildings[['floors','flats']] = gdfBuildings[['floors','flats']].astype(float)
gdfBuildings.to_file(folder / 'buildings.geojson', driver="GeoJSON")  
gdfPoints = gpd.GeoDataFrame(pd.concat([gdfPKK, gdfYandex], ignore_index=True, sort=False))
gdfPoints.to_file(folder / 'points.geojson', driver="GeoJSON")  
print("GeoJSONs saved.")
