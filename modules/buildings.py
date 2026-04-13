# ============================================
# Module: Generate voxels for earth ground vector buildings
# ============================================

# Modules import
# ============================================

# Standart modules
import multiprocessing as mp # Use multiprocessing
import ctypes # Use primitive datatypes for multiprocessing data exchange
import numpy as np # For arrays of numbers
import pandas as pd # For tables of data
import geopandas as gpd # For vector objects
from vtkmodules.vtkCommonDataModel import vtkPolyData # Use 3D-primitives
from vtkmodules.vtkRenderingCore import (vtkActor, vtkPolyDataMapper) # Use VTK rendering
import vtk # Use other 3D-visualization features
import gc # For garbage collectors
from pathlib import Path # Crossplatform pathing

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition
import modules.earth # The earth's surface routines


# ============================================
# Process vector buildings and generate voxel's world
# ============================================
def GenerateBuildings():

    env.logger.info("Convert vector buildings to our world dimensions...")

    # Convert 2D-coordinates of buildings GeoDataFrame from meters (Web-Mercator ESPG:3857) to vtk's float
    env.logger.trace(env.gdfBuildings)
    env.gdfBuildings = env.gdfBuildings.set_crs(None, allow_override=True)
    env.gdfBuildings.geometry = env.gdfBuildings.geometry.scale(xfact=1.0, yfact=-1.0, zfact=1.0, origin=(0,0))
    env.logger.trace(env.gdfBuildings)
    env.gdfBuildings.geometry = env.gdfBuildings.geometry.translate(xoff=-env.boundsMin[0], yoff=env.boundsMax[1], zoff=0.0)
    env.logger.trace(env.gdfBuildings)
    env.logger.success("{} vector buildings found", env.printLong(len(env.gdfBuildings.index)))

    # Remove buildings outside of currend world
    env.gdfBuildings = env.gdfBuildings.loc[env.gdfBuildings.within(env.plgnBounds)]
    # Add unique identificator of building (UIB)
    env.gdfBuildings['UIB'] = np.arange(len(env.gdfBuildings.index))
    env.logger.success("{} buildings left after removing buildings outside of current world area", env.printLong(len(env.gdfBuildings.index)))
    env.logger.trace(env.gdfBuildings)

    env.logger.info("Split buildings to voxel's grid cells...")

    # Join buildings and centers of voxel's squares GeoDataFrames
    env.gdfCellsBuildings = env.gdfBuildings.sjoin(env.gdfCells, how='inner', predicate='contains')
    env.gdfCellsBuildings = env.gdfCellsBuildings.drop(labels='index_right', axis='columns')
    env.logger.trace(env.gdfCellsBuildings)
    env.logger.success("{} from {} cells are under buildings", 
                       env.printLong(len(env.gdfCellsBuildings.index)), env.printLong(len(env.gdfCells.index)))

    # Find ground points for each cell
    env.logger.info("Looking for ground points of each building...")
    gp = []  # Use "for" loop, not "apply" to show progress bar
    for cell in env.tqdm(env.gdfCellsBuildings.itertuples(), total=len(env.gdfCellsBuildings.index)):
        gp.append(modules.earth.getGroundHeight(cell.x, cell.y, None))
    env.gdfCellsBuildings['GP'] = gp
    #env.gdfCellsBuildings['GP'] = env.gdfCellsBuildings.apply(lambda x : modules.earth.getGroundHeight(x['x'],x['y'],None), axis='columns')
    env.logger.trace(env.gdfCellsBuildings)

    # Find common ground point for each buildnig
    if cfg.BuildingGroundMode != 'levels':
        pdMinGroundPoints = pd.pivot_table(data = env.gdfCellsBuildings, index=['UIB'], values=['GP'], aggfunc={'GP':cfg.BuildingGroundMode})
        env.logger.trace(pdMinGroundPoints)
        env.gdfBuildings = env.gdfBuildings.merge(right=pdMinGroundPoints, how='left', left_on='UIB', right_on='UIB')
        env.gdfCellsBuildings = env.gdfCellsBuildings.merge(right=pdMinGroundPoints, how='left', on='UIB', suffixes=[None, '_agg'])
        env.logger.trace(env.gdfBuildings)
        env.logger.trace(env.gdfCellsBuildings)
        del pdMinGroundPoints
        gc.collect()

    # Save buildings parameters
    # Save floors, flats and average ground for buildings by their UIBs
    env.logger.info("Allocate memory and store buildings parameters...")
    env.countBuildings = len(env.gdfBuildings.index)
    env.countBuildingsCells = len(env.gdfCellsBuildings.index)
    env.LivingBuildings = 0
    env.countFlats = 0
    env.buildings = mp.RawArray(ctypes.c_ushort, env.countBuildings*env.sizeBuilding)
    for b in env.gdfBuildings.itertuples(): # tqdm is not needed
        env.buildings[int(b.UIB*env.sizeBuilding)] = int(b.floors)
        if cfg.BuildingGroundMode != 'levels':
            if not(np.isnan(b.GP)):
                env.buildings[int(b.UIB*env.sizeBuilding+1)] = int(b.GP)
        if not(np.isnan(b.flats)):
            if b.flats>0:
                env.buildings[int(b.UIB*env.sizeBuilding+2)] = int(b.flats)
                env.LivingBuildings = env.LivingBuildings + 1
                env.countFlats = env.countFlats + int(b.flats)
    # Loop through cells and count voxels count. Save voxels index and UIBs for each cell
    env.countVoxels = 0
    env.countLivingVoxels = 0
    for cell in env.tqdm(env.gdfCellsBuildings.itertuples(), total=len(env.gdfCellsBuildings.index)):
        env.uib[cell.x*env.bounds[1]+cell.y] = int(cell.UIB)
        env.VoxelIndex[int(cell.x*env.bounds[1]+cell.y)] = int(env.countVoxels)
        env.countVoxels = env.countVoxels + int(cell.floors)
        if not(np.isnan(cell.flats)):
            if cell.flats>0:
                env.countLivingVoxels = env.countLivingVoxels + int(cell.floors)
        env.buildings[int(cell.UIB*env.sizeBuilding+3)] = env.buildings[int(cell.UIB*env.sizeBuilding+3)] + int(cell.floors)
    # Allocate memory for buildings voxels
    env.audibilityVoxels = mp.RawArray(ctypes.c_byte, env.countVoxels)
    env.logger.success("{} buildings stored (including {} living buildings). {} flats found", 
                       env.printLong(env.countBuildings), env.printLong(env.LivingBuildings), env.printLong(env.countFlats) )
    env.logger.success("{} voxels of buildings allocated (including {} living voxels)",
                       env.printLong(env.countVoxels), env.printLong(env.countLivingVoxels) )

# ============================================
# Generate necessary voxel VTK objects from vtkPoints 
# with the specified color and opacity to buildings vizualization
# IN: 
# points - vtkPoints collection
# color - tuple of three float number 0..1 for R,G,B values of color (0% .. 100%)
# opacity - float number 0..1 for opacity value (0% .. 100%)
# OUT:
# No return values. Modify variables of environment.py in which VTK objects for further vizualization
# ============================================
def VizualizePartOfVoxels(points, color, opacity):
    # Put Voxels on intersection points
    polyDataVoxels = vtkPolyData()
    polyDataVoxels.SetPoints(points)
    env.pldtVoxels.append(polyDataVoxels)
    cubeVoxel = vtk.vtkCubeSource()
    cubeVoxel.SetXLength(cfg.sizeVoxel-cfg.gapVoxel)
    cubeVoxel.SetYLength(cfg.sizeVoxel-cfg.gapVoxel)
    cubeVoxel.SetZLength(cfg.sizeVoxel-cfg.gapVoxel)
    env.cbVoxels.append(cubeVoxel)
    glyphVoxels = vtk.vtkGlyph3D()
    glyphVoxels.SetInputData(polyDataVoxels)
    glyphVoxels.SetSourceConnection(cubeVoxel.GetOutputPort())
    glyphVoxels.ScalingOff()
    glyphVoxels.Update()
    env.glphVoxels.append(glyphVoxels)
    pointsMapperVoxels = vtkPolyDataMapper()
    pointsMapperVoxels.SetInputConnection(glyphVoxels.GetOutputPort())
    pointsMapperVoxels.ScalarVisibilityOff()
    env.mapVoxels.append(pointsMapperVoxels)
    pointsActorVoxels = vtkActor()
    pointsActorVoxels.SetMapper(pointsMapperVoxels)
    pointsActorVoxels.GetProperty().SetColor(color)
    pointsActorVoxels.GetProperty().SetOpacity(opacity)
    env.actVoxels.append(pointsActorVoxels)

# ============================================
# Generate voxels of building vizualization
# from previously calculated and classified points
# ============================================
def VizualizeAllVoxels():
    env.logger.info("Build voxels of buildings...")

    idx2D = 0
    totalCells = 0
    totalVoxels = 0
    totalFlats = 0.0
    audibilityFactFlats = 0.0
    audibilityFactFlatsByMegaphonesOnly = 0.0
    audibilityFactFlatsByDoorphonesOnly = 0.0
    audibilityFactFlatsByMegaphonesAndDoorphones = 0.0
    audibilityPlanFlats = 0.0
    audibilityPlanFlatsByMegaphonesOnly = 0.0
    audibilityPlanFlatsByDoorphonesOnly = 0.0
    audibilityPlanFlatsByMegaphonesAndDoorphones = 0.0

    # Loop throught grid of the earth's surface cells audibility
    for x in env.tqdm(range(env.bounds[0])):
        for y in range(env.bounds[1]):
            uib = env.uib[idx2D]
            if uib>=0:
                totalCells = totalCells + 1
                idxZ = env.VoxelIndex[idx2D]
                floors = env.buildings[uib*env.sizeBuilding]
                flats = env.buildings[uib*env.sizeBuilding+2]
                voxels = env.buildings[uib*env.sizeBuilding+3]
                flatsPerVoxel = flats/voxels if voxels>0 else 0
                doorphones = env.buildings[uib*env.sizeBuilding+5]
                totalVoxels = totalVoxels + floors
                if cfg.BuildingGroundMode != 'levels':
                    z = env.buildings[uib*env.sizeBuilding+1]
                else:
                    z = env.ground[idx2D]
                for floor in range(floors):
                    audibility = env.audibilityVoxels[idxZ+floor]
                    totalFlats = totalFlats + flatsPerVoxel

                    # Count audibility flats for statistics
                    if (audibility>0) or (doorphones==1):
                        audibilityFactFlats = audibilityFactFlats + flatsPerVoxel
                        audibilityPlanFlats = audibilityPlanFlats + flatsPerVoxel
                    elif (audibility<0) and (doorphones==2):
                        audibilityPlanFlats = audibilityPlanFlats + flatsPerVoxel
                    if (audibility>0) and (doorphones==0):
                        audibilityFactFlatsByMegaphonesOnly = audibilityFactFlatsByMegaphonesOnly + flatsPerVoxel
                        audibilityPlanFlatsByMegaphonesOnly = audibilityPlanFlatsByMegaphonesOnly + flatsPerVoxel
                    elif (audibility>0) and (doorphones==1):
                        audibilityFactFlatsByMegaphonesAndDoorphones = audibilityFactFlatsByMegaphonesAndDoorphones + flatsPerVoxel
                        audibilityPlanFlatsByMegaphonesAndDoorphones = audibilityPlanFlatsByMegaphonesAndDoorphones + flatsPerVoxel
                    elif (audibility>0) and (doorphones==2):
                        audibilityFactFlatsByMegaphonesOnly = audibilityFactFlatsByMegaphonesOnly + flatsPerVoxel
                        audibilityPlanFlatsByMegaphonesAndDoorphones = audibilityPlanFlatsByMegaphonesAndDoorphones + flatsPerVoxel
                    elif (audibility<=0) and (doorphones==1):
                        audibilityFactFlatsByDoorphonesOnly = audibilityFactFlatsByDoorphonesOnly + flatsPerVoxel
                        audibilityPlanFlatsByDoorphonesOnly = audibilityPlanFlatsByDoorphonesOnly + flatsPerVoxel
                    elif (audibility<=0) and (doorphones==2):
                        audibilityPlanFlatsByDoorphonesOnly = audibilityPlanFlatsByDoorphonesOnly + flatsPerVoxel

                    # Store voxels points
                    if doorphones==1:
                        env.pntsVoxels_doorphones_fact.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.5+floor)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel)
                    elif doorphones==2:
                        env.pntsVoxels_doorphones_plan.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.5+floor)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel)
                    elif audibility>0:
                        env.pntsVoxels_yes.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.5+floor)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel)
                    elif audibility<0:
                        env.pntsVoxels_no.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.5+floor)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel)
                    else:
                        if flats>0:
                            env.pntsVoxels_no.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.5+floor)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel) # not env.pntsVoxels_living
                        else:
                            env.pntsVoxels_industrial.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.5+floor)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel)
            idx2D = idx2D + 1

    VizualizePartOfVoxels(env.pntsVoxels_yes, env.Colors.GetColor3d("Green"), 1)
    VizualizePartOfVoxels(env.pntsVoxels_no, env.Colors.GetColor3d("Tomato"), 1)
    VizualizePartOfVoxels(env.pntsVoxels_industrial, env.Colors.GetColor3d("Gray"), 1)
    VizualizePartOfVoxels(env.pntsVoxels_doorphones_fact, env.Colors.GetColor3d("Cyan"), 1)
    VizualizePartOfVoxels(env.pntsVoxels_doorphones_plan, env.Colors.GetColor3d("Magenta"), 1)

    env.vtkPoints2CSV('vox_industrial.csv', env.pntsVoxels_industrial)
    env.vtkPoints2CSV('vox_yes.csv', env.pntsVoxels_yes)
    env.vtkPoints2CSV('vox_no.csv', env.pntsVoxels_no)
    env.vtkPoints2CSV('vox_doorphones_fact.csv', env.pntsVoxels_doorphones_fact)
    env.vtkPoints2CSV('vox_doorphones_plan.csv', env.pntsVoxels_doorphones_plan)
    env.logger.success("Voxels exported")

    # Save buildings parameters to Excel for further analysis
    env.gdfBuildings.drop(columns="geometry").to_excel(Path('.',cfg.folderOUTPUT, "buildings.xlsx"), index=False)

    livingVoxels = env.pntsVoxels_doorphones_fact.GetNumberOfPoints() + env.pntsVoxels_doorphones_plan.GetNumberOfPoints() + \
        env.pntsVoxels_yes.GetNumberOfPoints() + env.pntsVoxels_no.GetNumberOfPoints()

    env.writeStat("=========================================================================================================")
    env.writeStat("|| BUILDINGS STATISTICS:")
    env.writeStat("|| {} ({}) doorphones fact voxels, {} ({}) doorphones plan voxels".format(
                    env.printLong(env.pntsVoxels_doorphones_fact.GetNumberOfPoints()),
                    f'{env.pntsVoxels_doorphones_fact.GetNumberOfPoints()/livingVoxels:.0%}',
                    env.printLong(env.pntsVoxels_doorphones_plan.GetNumberOfPoints()),
                    f'{env.pntsVoxels_doorphones_plan.GetNumberOfPoints()/livingVoxels:.0%}' ) )
    env.writeStat("|| {} ({}) audibility voxels, {} ({}) non-audibility voxels, {} non-living voxels".format(
                  env.printLong(env.pntsVoxels_yes.GetNumberOfPoints()),
                  f'{env.pntsVoxels_yes.GetNumberOfPoints()/livingVoxels:.0%}',
                  env.printLong(env.pntsVoxels_no.GetNumberOfPoints()),
                  f'{env.pntsVoxels_no.GetNumberOfPoints()/livingVoxels:.0%}',
                  env.printLong(env.pntsVoxels_industrial.GetNumberOfPoints()) ) )
    env.logger.debug("|| {} ({}) of {} building's cells analyzed",
                     env.printLong(totalCells), f'{totalCells/env.countBuildingsCells:.0%}', env.printLong(env.countBuildingsCells) )
    env.logger.debug("|| {} ({}) of {} voxels analyzed",
                     env.printLong(totalVoxels), f'{totalVoxels/env.countVoxels:.0%}', env.printLong(env.countVoxels) )
    env.writeStat("|| {} ({}) of {} living voxels analyzed".format(
                    env.printLong(livingVoxels), f'{livingVoxels/env.countLivingVoxels:.0%}', env.printLong(env.countLivingVoxels) ), "info" )
    env.writeStat("|| Now:")
    env.writeStat("|| {} ({}) of {} flats are audibility:".format(
        env.printLong(round(audibilityFactFlats)),
        f'{audibilityFactFlats/totalFlats:.0%}',
        env.printLong(round(totalFlats))
    ))
    env.writeStat("|| {} ({}) by doorphones, {} ({}) by megaphones, {} ({}) both".format(
        env.printLong(round(audibilityFactFlatsByDoorphonesOnly)),
        f'{audibilityFactFlatsByDoorphonesOnly/totalFlats:.0%}',
        env.printLong(round(audibilityFactFlatsByMegaphonesOnly)),
        f'{audibilityFactFlatsByMegaphonesOnly/totalFlats:.0%}',
        env.printLong(round(audibilityFactFlatsByMegaphonesAndDoorphones)),
        f'{audibilityFactFlatsByMegaphonesAndDoorphones/totalFlats:.0%}'
    ))
    env.writeStat("|| {} ({}) non-audibility flats".format(
        env.printLong(round(totalFlats)-round(audibilityFactFlats)),
        f'{(1-audibilityFactFlats/totalFlats):.0%}'
    ))

    env.writeStat("|| In the future:")
    env.writeStat("|| {} ({}) of {} flats are audibility:".format(
        env.printLong(round(audibilityPlanFlats)),
        f'{audibilityPlanFlats/totalFlats:.0%}',
        env.printLong(round(totalFlats))
    ))
    env.writeStat("|| {} ({}) by doorphones, {} ({}) by megaphones, {} ({}) both".format(
        env.printLong(round(audibilityPlanFlatsByDoorphonesOnly)),
        f'{audibilityPlanFlatsByDoorphonesOnly/totalFlats:.0%}',
        env.printLong(round(audibilityPlanFlatsByMegaphonesOnly)),
        f'{audibilityPlanFlatsByMegaphonesOnly/totalFlats:.0%}',
        env.printLong(round(audibilityPlanFlatsByMegaphonesAndDoorphones)),
        f'{audibilityPlanFlatsByMegaphonesAndDoorphones/totalFlats:.0%}'
    ))
    env.writeStat("|| {} ({}) non-audibility flats".format(
        env.printLong(round(totalFlats)-round(audibilityPlanFlats)),
        f'{(1-audibilityPlanFlats/totalFlats):.0%}'
    ))
    env.writeStat("|| {} ({}) of {} flats analyzed".format(
                       env.printLong(round(totalFlats)), f'{totalFlats/env.countFlats:.0%}', env.printLong(env.countFlats) ), "info" )
    env.writeStat("=========================================================================================================")
